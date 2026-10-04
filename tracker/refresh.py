"""Scheduled live updates: refresh market data, re-render dashboard.

Runs every config.REFRESH_INTERVAL_MINUTES (default 5). Each cycle is
audited. Designed to run as a background process (python -m tracker.refresh)
or to be triggered externally (cron / Task Scheduler) via --once.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import audit, config, data, fundamentals, performance, portfolio, reporting, research, scenario

# Written into the deploy bundle each cycle; the dashboard JS polls it so an
# open tab can toast "Prices updated — view now" and auto-reload on a timer.
REFRESH_META = Path("publish/refresh_meta.json")


def _running_yn() -> bool:
    """Crude LSE-hours check (market open 08:00-16:30 London, Mon-Fri)."""
    # UTC offset for BST is +1; use 7:00-15:30 UTC as a safe window.
    now = datetime.now(timezone.utc)
    wd = now.weekday()
    h = now.hour + now.minute / 60
    return wd < 5 and 7.0 <= h < 15.5


def refresh_once(reason: str = "scheduled") -> dict:
    """One refresh cycle: quotes -> snapshot -> performance -> dashboard."""
    t0 = time.time()
    tickers = list(config.UNIVERSE) + [config.BENCHMARK]

    quotes = data.fetch_quotes(tickers)
    hist = data.fetch_history(list(config.UNIVERSE), period="2y")
    bench = data.fetch_history([config.BENCHMARK], period="2y")

    if quotes:
        data.save_snapshot(quotes)

    notes = research.list_notes()
    published = [n for n in notes if n.get("status") == "published"]
    perf_rows = [performance.note_performance(n, hist, bench) for n in published]
    monthly = {
        n["ticker"]: performance.monthly_attribution(n, hist, bench)
        for n in published
    }
    perf_by_ticker = {r["ticker"]: r for r in perf_rows if r}

    valid_rows = [r for r in perf_rows if r]
    summary = performance.summarize(valid_rows)

    # Two separate windows, never mixed on screen:
    #   live record  - portfolio from the first note's first publication
    #   backtest     - current weights over the trailing 3 months (hypothetical)
    first_pub = min(
        (n.get("first_published_at") or n.get("published_at") or "")
        for n in published
    )[:10] if published else None
    live_curve = performance.portfolio_curve(hist, bench, since=first_pub) \
        if first_pub else []
    backtest_curve = performance.portfolio_curve(hist, bench, months=3)
    live_curve = portfolio.apply_inception_cost(live_curve)
    backtest_curve = portfolio.apply_inception_cost(backtest_curve)

    rf_short, rf_prov = fundamentals.short_rate_uk()
    live_metrics = performance.portfolio_metrics(live_curve, rf=rf_short)
    backtest_metrics = performance.portfolio_metrics(backtest_curve, rf=rf_short)

    weights_table = portfolio.build_weights_table(quotes)
    sector_mix = portfolio.portfolio_sector_weights()
    ftse_sectors = portfolio.load_ftse_sector_weights()

    # Refresh-over-refresh diff: what actually moved since the previous cycle.
    prev_meta = {}
    if REFRESH_META.exists():
        try:
            prev_meta = json.loads(REFRESH_META.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev_meta = {}
    prev_quotes = prev_meta.get("quotes_snapshot")
    changes = scenario.diff_quotes(prev_quotes, quotes)

    # One timestamp shared by the dashboard, note pages, audit record and
    # refresh_meta.json — the client compares these, so they must be identical
    # or every page load would falsely believe newer data exists.
    now_ts = datetime.now(timezone.utc).isoformat()

    series_by_ticker = {
        n["ticker"]: performance.note_series(n, hist, bench)
        for n in published
    }
    caption = performance.performance_caption(summary, live_curve, "Live record")

    reporting.write_all_note_pages(published, perf_by_ticker, monthly,
                                   series_by_ticker, quotes=quotes)
    reporting.write_dashboard(
        quotes=quotes,
        curve=live_curve,
        backtest_curve=backtest_curve,
        perf_rows=valid_rows,
        summary=summary,
        refresh_ts=now_ts,
        notes=published,
        perf_by_ticker=perf_by_ticker,
        monthly_by_ticker=monthly,
        series_by_ticker=series_by_ticker,
        caption=caption,
        changes=changes,
        status_meta={"refreshed_at": now_ts},
        live_metrics=live_metrics,
        backtest_metrics=backtest_metrics,
        weights_table=weights_table,
        sector_mix=sector_mix,
        ftse_sectors=ftse_sectors,
    )
    # Deployable static-site bundle (GitHub Pages root) + raw audit log
    reporting.write_publish_bundle()

    # Live-update signal for open tabs: the dashboard polls this every 60s and
    # offers "Prices updated — view now"; it also drives the auto-reload timer.
    meta = {
        "refreshed_at": now_ts,
        "reason": reason,
        "quotes": len(quotes),
        "elapsed_s": round(time.time() - t0, 2),
        "market_open": _running_yn(),
        "changes": changes,
        "quotes_snapshot": {tk: {"price_gbp": q.get("price_gbp")}
                            for tk, q in (quotes or {}).items()
                            if not tk.startswith("_")},
    }
    REFRESH_META.parent.mkdir(parents=True, exist_ok=True)
    REFRESH_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    stats = {
        "reason": reason,
        "quotes": len(quotes),
        "notes_tracked": len([r for r in perf_rows if r]),
        "elapsed_s": round(time.time() - t0, 2),
    }
    audit.record("refresh", stats)
    print(f"[{datetime.now(timezone.utc).isoformat()}] refresh ok: {stats}")
    return stats


def _acquire_loop_lock() -> bool:
    """Singleton guard: the loop process itself owns a kernel mutex.

    Parent-side checks cannot prevent a spawn race when launchers retry
    under multiple interpreters; a kernel mutex owned by the CHILD makes
    the losing process exit no matter how it was started.
    """
    from .single_instance import acquire

    return acquire("FreebuffTrackerLoop")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Live refresh loop for the tracker")
    ap.add_argument("--once", action="store_true", help="run a single refresh and exit")
    ap.add_argument("--interval", type=int, default=None, help="minutes between refreshes")
    args = ap.parse_args(argv)

    interval = args.interval or config.REFRESH_INTERVAL_MINUTES

    if not _acquire_loop_lock():
        print("another refresh loop is already running (loop.lock held) -- exiting")
        return 0

    if args.once:
        refresh_once("manual")
        return 0

    stop = {"flag": False}

    def _sig(_sig_num, _frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    print(f"Starting refresh loop every {interval} min. Ctrl+C to stop.")
    while not stop["flag"]:
        try:
            refresh_once("scheduled")
        except Exception as exc:  # noqa: BLE001
            audit.record("refresh_error", {"error": str(exc)})
            print(f"refresh failed: {exc}", file=sys.stderr)
        # Sleep in 1s increments so Ctrl+C feels responsive
        for _ in range(interval * 60):
            if stop["flag"]:
                break
            time.sleep(1)
    print("Stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
