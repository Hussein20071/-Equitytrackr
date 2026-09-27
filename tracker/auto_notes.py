"""Auto-build and publish research notes for the whole universe.

Every number on every note comes from live public data (Yahoo Finance
fundamentals/quotes, FRED, Damodaran). The narrative itself is assembled
from the computed facts — valuation vs market price, multiples vs peer
medians, FCF trend — so nothing on a note is hand-invented. Addenda
(learning notes) are appended later from real reviews via
``python -m tracker.cli addendum``.

Usage:
  python -m tracker.auto_notes            # build + publish all universe names
  python -m tracker.auto_notes HSBA.L     # just one
  python -m tracker.auto_notes --force    # refetch fundamentals, not cache
"""

from __future__ import annotations

import sys

from . import config, research


def _pct(x, digits=1) -> str:
    return "n/a" if x is None else f"{x * 100:.{digits}f}%"


def _money(x) -> str:
    return "n/a" if x is None else f"{x:,.0f}"


def generate_narrative(fin, note: dict) -> tuple[str, str, list[str], list[str]]:
    """Assemble headline, summary, catalysts, risks from computed facts only."""
    v = note["valuation_inputs"]
    price = note["market_context"].get("price_gbp_at_publication")
    tgt = note["price_target_gbp"]
    up = note.get("upside_pct")

    dcf_v = v["dcf"]["result"]["value_per_share"]
    ddm_v = v["ddm"]["value_per_share"]
    comps_pe = v["comps"]["implied_price_pe"]
    median_pe = v["comps"]["median_pe"]
    pe_subject = fin.info.get("trailingPE")
    dy = fin.info.get("dividendYield")
    fcf_hist = fin.fcf_history_m
    fcf_years = fin.fcf_history_years

    rec = note["recommendation"]

    headline = (
        f"{rec}: target GBP {tgt:.2f} vs price GBP {price:.2f} "
        f"({up:+.1f}% upside) on blended DCF/DDM/comps"
    )

    parts = [
        f"Systematic note generated from live data. Market price GBP {price:.2f} "
        f"against a blended 12-month target of GBP {tgt:.2f} "
        f"(weights {note['target_weights']})."
    ]
    if dcf_v:
        parts.append(
            f"The 2-stage FCF DCF on a base of GBP {_money(fin.fcf_m)}m latest-FY "
            f"free cash flow (FX-converted from {fin.reporting_currency}) values "
            f"the shares at GBP {dcf_v:.2f}."
        )
    if ddm_v:
        parts.append(
            f"Gordon DDM on trailing DPS GBP {fin.dps_ttm_gbp:.2f} "
            f"(g = ROE x retention) values them at GBP {ddm_v:.2f}."
        )
    if median_pe and comps_pe:
        parts.append(
            f"Peer-median P/E of {median_pe:.1f}x applied to EPS of "
            f"GBP {fin.eps_ttm_gbp:.2f} implies GBP {comps_pe:.2f}; the shares "
            f"trade at {pe_subject:.1f}x trailing earnings."
            if pe_subject else
            f"Peer-median P/E of {median_pe:.1f}x applied to EPS of "
            f"GBP {fin.eps_ttm_gbp:.2f} implies GBP {comps_pe:.2f}."
        )
    elif median_pe and not comps_pe:
        parts.append(
            f"A peer-median P/E of {median_pe:.1f}x was computed, but applying "
            f"it to the subject's depressed earnings base (EPS GBP "
            f"{fin.eps_ttm_gbp}) was suppressed; see the inputs table."
        )
    if len(fcf_hist) >= 2:
        trend = "up" if fcf_hist[-1] > fcf_hist[0] else "down"
        parts.append(
            f"Reported FCF has trended {trend} over the last {len(fcf_hist)} "
            f"financial years (GBP {fcf_hist[0]:,.0f}m -> GBP {fcf_hist[-1]:,.0f}m), "
            f"which drives the growth path shown in the inputs table."
        )
    if dy:
        parts.append(f"The shares offer a trailing dividend yield of {_pct(dy)}.")
    summary = " ".join(parts)

    catalysts = [
        f"Convergence toward the blended target of GBP {tgt} "
        f"({up:+.1f}%) over the {research.REVIEW_PERIOD_MONTHS}-month review window",
    ]
    if dy:
        catalysts.append(f"Total-return support from the {_pct(dy)} trailing dividend yield")
    catalysts.append(
        "Next FY results: reported FCF vs the latest-FY base used in the DCF"
    )

    risks = [
        f"Thesis invalidation: price sustaining beyond GBP {tgt:.2f} in the "
        f"opposite direction of the recommendation for 10+ sessions",
        "Fundamentals revision: a restated or materially different latest-FY "
        "FCF/net-debt base than the frozen inputs",
        "Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield",
    ]

    return headline, summary, catalysts, risks


def build_and_publish(ticker: str, force: bool = False) -> dict:
    if force:
        from . import fundamentals
        fundamentals.get_financials(ticker, force=True)
    fin = None  # reloaded inside build_note
    note = research.build_note(ticker)
    from . import fundamentals as f  # fetch (cached) for narrative
    fin = f.get_financials(ticker)
    headline, summary, cats, risks = generate_narrative(fin, note)
    published = research.publish(
        note, headline=headline, summary=summary,
        catalysts=cats, risks=risks, published_by="auto_notes",
    )
    print(
        f"published {published['ticker']}: {published['recommendation']} "
        f"target GBP {published['price_target_gbp']} "
        f"(upside {published['upside_pct']}%)"
    )
    return published


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args = list(argv)
    force = "--force" in args
    args = [a for a in args if not a.startswith("--")]
    tickers = [t.upper() for t in args] if args else list(config.UNIVERSE)

    ok, failed = [], []
    for tk in tickers:
        try:
            build_and_publish(tk, force=force)
            ok.append(tk)
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED {tk}: {exc}", file=sys.stderr)
            failed.append(tk)
    print(f"\n{len(ok)} published, {len(failed)} failed"
          + (f": {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
