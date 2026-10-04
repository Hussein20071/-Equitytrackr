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


def generate_narrative(fin, note: dict) -> tuple[str, str, list[str], list[str], list[str]]:
    """Assemble headline, thesis, catalysts, risks, wrong-if from facts.

    The thesis is three plain-English sentences: (1) what the model says
    vs the market price, (2) why -- the drivers behind the target, (3)
    what would prove or disprove it. Every number quoted is computed on
    the note; narrative wording is the only hand-shaped element.
    """
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

    rec = note["recommendation"]
    guard = note.get("model_checks") or {}

    headline = (
        f"{rec}: target GBP {tgt:.2f} vs price GBP {price:.2f} "
        f"({up:+.1f}% upside) on blended DCF/DDM/comps"
    )

    # --- three-sentence plain-English thesis ---
    s1 = (
        f"The model's blended 12-month target is GBP {tgt:.2f} against a "
        f"market price of GBP {price:.2f} ({up:+.1f}%), which reads as "
        f"{rec} on the published recommendation bands."
    )
    why = []
    if dcf_v:
        why.append(f"a 2-stage FCF DCF at GBP {dcf_v:.2f} per share")
    if ddm_v:
        why.append(f"a Gordon DDM at GBP {ddm_v:.2f}")
    if comps_pe:
        why.append(f"peer multiples implying GBP {comps_pe:.2f} (P/E leg)")
    s2 = (
        "The target is a weighted blend of "
        + (", ".join(why) if why else "the surviving valuation legs")
        + " -- the market is effectively pricing different assumptions "
        "than those frozen inputs, and the note shows exactly which."
    )
    if guard.get("is_outlier"):
        s3 = (
            f"That gap exceeds the +/-30% guardrail, so the note is flagged "
            f"'Model outlier - under review' with the {guard.get('driver_leg')} "
            f"leg driving it; the reverse DCF on the note page states what "
            f"growth the market price implies instead."
        )
    else:
        s3 = (
            "The thesis is proven wrong if the shares sustain beyond the "
            "target in the opposite direction of the call for 10+ sessions, "
            "or if reported results break the frozen FCF/net-debt base."
        )
    summary = f"{s1} {s2} {s3}"

    # --- catalysts: dated where the feed publishes a date ---
    events = note.get("next_events") or {}
    catalysts = []
    if events.get("earnings_date"):
        catalysts.append(
            f"Next results: {events['earnings_date']} (Yahoo calendar) -- "
            "reported FCF vs the frozen base is the decisive input"
        )
    else:
        catalysts.append(
            "Next results date: not published by the Yahoo calendar feed -- "
            "check the company's investor-relations page; the decisive input "
            "is reported FCF vs the frozen base"
        )
    if dy:
        catalysts.append(
            f"Total-return support from the {_pct(dy)} trailing dividend yield"
        )
    catalysts.append(
        f"Convergence (or divergence) vs the GBP {tgt} target over the "
        f"{research.REVIEW_PERIOD_MONTHS}-month review window"
    )

    risks = [
        "Fundamentals revision: a restated or materially different "
        "FCF/net-debt base than the frozen inputs",
        "Rate sensitivity: the CAPM cost of equity moves with the gilt yield",
    ]

    wrong_if = [
        f"Price sustains beyond GBP {tgt:.2f} for 10+ sessions in the "
        f"opposite direction of the {rec} call",
        "Reported free cash flow diverges from the frozen base year by more "
        "than the growth path allows for",
        "Peer multiples re-rate by more than one standard deviation of their "
        "trailing history",
    ]

    return headline, summary, catalysts, risks, wrong_if


def build_and_publish(ticker: str, force: bool = False,
                      correction: str | None = None) -> dict:
    if force:
        from . import fundamentals
        fundamentals.get_financials(ticker, force=True)
    fin = None  # reloaded inside build_note
    note = research.build_note(ticker)
    from . import fundamentals as f  # fetch (cached) for narrative
    fin = f.get_financials(ticker)
    headline, summary, cats, risks, wrong_if = generate_narrative(fin, note)
    published = research.publish(
        note, headline=headline, summary=summary,
        catalysts=cats, risks=risks, published_by="auto_notes",
        correction=correction, wrong_if=wrong_if,
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
    correction = None
    if "--correction" in args:
        idx = args.index("--correction")
        tail = args[idx + 1:]
        args = args[:idx]
        if tail:
            correction = " ".join(tail)
    args = [a for a in args if not a.startswith("--")]
    tickers = [t.upper() for t in args] if args else list(config.UNIVERSE)

    ok, failed = [], []
    for tk in tickers:
        try:
            build_and_publish(tk, force=force, correction=correction)
            ok.append(tk)
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED {tk}: {exc}", file=sys.stderr)
            failed.append(tk)
    print(f"\n{len(ok)} published, {len(failed)} failed"
          + (f": {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
