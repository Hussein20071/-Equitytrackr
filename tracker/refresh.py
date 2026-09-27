"""Scheduled live updates: refresh market data, re-render dashboard.

Runs every config.REFRESH_INTERVAL_MINUTES (default 5). Each cycle is
audited. Designed to run as a background process (python -m tracker.refresh)
or to be triggered externally (cron / Task Scheduler) via --once.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from datetime import datetime, timezone

from . import audit, config, data, performance, reporting, research


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

    curve = performance.portfolio_curve(hist, bench)
    valid_rows = [r for r in perf_rows if r]
    summary = performance.summarize(valid_rows)

    series_by_ticker = {
        n["ticker"]: performance.note_series(n, hist, bench)
        for n in published
    }
    caption = performance.performance_caption(summary, curve)

    reporting.write_all_note_pages(published, perf_by_ticker, monthly,
                                   series_by_ticker)
    reporting.write_dashboard(
        quotes=quotes,
        curve=curve,
        perf_rows=valid_rows,
        summary=summary,
        refresh_ts=datetime.now(timezone.utc).isoformat(),
        notes=published,
        perf_by_ticker=perf_by_ticker,
        monthly_by_ticker=monthly,
        series_by_ticker=series_by_ticker,
        caption=caption,
    )
    # Deployable static-site bundle (GitHub Pages root) + raw audit log
    reporting.write_publish_bundle()

    stats = {
        "reason": reason,
        "quotes": len(quotes),
        "notes_tracked": len([r for r in perf_rows if r]),
        "elapsed_s": round(time.time() - t0, 2),
    }
    audit.record("refresh", stats)
    print(f"[{datetime.now(timezone.utc).isoformat()}] refresh ok: {stats}")
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Live refresh loop for the tracker")
    ap.add_argument("--once", action="store_true", help="run a single refresh and exit")
    ap.add_argument("--interval", type=int, default=None, help="minutes between refreshes")
    args = ap.parse_args(argv)

    interval = args.interval or config.REFRESH_INTERVAL_MINUTES

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
