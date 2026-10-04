"""Command-line interface for the tracker.

Usage:
  python -m tracker.cli refresh              # one refresh cycle now
  python -m tracker.cli loop [--interval M]  # run the 5-minute loop
  python -m tracker.cli notes [TICKER...]    # build+publish notes from live data
  python -m tracker.cli notes --force        # refetch fundamentals first
  python -m tracker.cli addendum TK KIND TXT # add dated learning/thesis note
  python -m tracker.cli status               # snapshot, notes, audit tail
"""

from __future__ import annotations

import argparse
import json
import sys

from . import audit, config, data, refresh


def cmd_notes(args) -> int:
    from . import auto_notes

    argv = list(args.tickers or [])
    if args.force:
        argv.append("--force")
    if getattr(args, "correction", None):
        argv += ["--correction", args.correction]
    return auto_notes.main(argv)


def cmd_addendum(args) -> int:
    from . import research

    note = research.add_addendum(args.ticker.upper(), args.kind, " ".join(args.text))
    if not note:
        print(f"failed: no published note for {args.ticker}", file=sys.stderr)
        return 1
    print(f"addendum added to {args.ticker.upper()} ({args.kind})")
    return 0


def cmd_sectors(_args) -> int:
    """Refresh the cached FTSE 100 sector weights (run before deploy/CI)."""
    from . import portfolio

    payload = portfolio.fetch_ftse_sector_weights()
    if not payload:
        print("failed: could not fetch/parse FTSE 100 sector weights "
              "(cache left untouched)", file=sys.stderr)
        return 1
    for s, w in payload["weights"].items():
        print(f"  {s:42s} {w * 100:5.1f}%")
    print(f"cached to {portfolio._CACHE} (as of {payload['as_of'][:10]})")
    return 0


def cmd_status(_args) -> None:
    snap = data.load_snapshot()
    print("=== Market snapshot ===")
    print(f"updated: {snap.get('_updated_at', 'never')}")
    for tk in config.UNIVERSE:
        q = snap.get(tk)
        if q:
            print(f"  {tk:8s} GBP {q['price_gbp']:>8.2f}  ({q.get('source', '')})")
        else:
            print(f"  {tk:8s} -- no data")

    print("\n=== Published notes ===")
    from . import research

    notes = research.list_notes()
    if not notes:
        print("  (none — run `python -m tracker.cli notes`)")
    for n in notes:
        if n.get("status") == "published":
            print(
                f"  {n['ticker']:8s} {n.get('recommendation') or '—':5s} "
                f"target GBP {n.get('price_target_gbp')}  "
                f"upside {n.get('upside_pct')}%  addenda {len(n.get('addenda', []))}"
            )

    print("\n=== Audit log (last 10) ===")
    for r in audit.tail(10):
        print(f"  {r['ts'][:19]}  {r['event']:20s} {json.dumps(r.get('tickers', ''))[:60]}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tracker", description="UK Equity Research Tracker")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("refresh", help="run one refresh cycle now")
    p_loop = sub.add_parser("loop", help="run the scheduled refresh loop (default 5 min)")
    p_loop.add_argument("--interval", type=int, default=None)
    p_notes = sub.add_parser("notes", help="build+publish notes from live data")
    p_notes.add_argument("tickers", nargs="*")
    p_notes.add_argument("--force", action="store_true", help="refetch cached fundamentals")
    p_notes.add_argument("--correction", default=None,
                         help="dated correction text appended to republished notes")
    p_add = sub.add_parser("addendum", help="add a dated addendum to a published note")
    p_add.add_argument("ticker")
    p_add.add_argument("kind", choices=["learning", "thesis_check", "methodology"])
    p_add.add_argument("text", nargs="+")
    sub.add_parser("sectors", help="refresh cached FTSE 100 sector weights")
    sub.add_parser("status", help="show snapshot, notes, and audit tail")

    args = ap.parse_args(argv)

    if args.cmd == "refresh":
        refresh.refresh_once("cli")
        return 0
    if args.cmd == "loop":
        return refresh.main(["--interval", str(args.interval)] if args.interval else [])
    if args.cmd == "notes":
        return cmd_notes(args)
    if args.cmd == "addendum":
        return cmd_addendum(args)
    if args.cmd == "sectors":
        return cmd_sectors(args)
    if args.cmd == "status":
        cmd_status(args)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
