"""Research-note lifecycle v2: auto-build from live data, publish, addenda.

Notes are built with ``build_note(ticker, peers)``: every valuation input
is fetched from public sources and tagged with provenance. Published
notes are immutable JSON + markdown; revisions archive the prior version
under ``notes/snapshots/``. Post-publication commentary lives in
``addenda`` (learning notes, thesis checks) rather than edits.

A note is keyed by ticker; ``review_period`` (from config) is stamped at
publication so the tracking window is defined up front.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import audit, config, data, fundamentals, valuation

REVIEW_PERIOD_MONTHS = 3

# Peer groups (LSE tickers). Used to compute live multiples per note.
PEER_GROUPS: dict[str, list[str]] = {
    "HSBA.L": ["BARC.L", "LLOY.L", "NWG.L", "STAN.L"],
    "BP.L": ["SHEL.L", "TTE.PA", "EQNR.OL"],
    "ULVR.L": ["PG", "CL", "RKT.L", "BN.PA"],
    "AZN.L": ["GSK.L", "NVS", "PFE", "MRK"],
    "SHEL.L": ["BP.L", "TTE.PA", "EQNR.OL"],
    "GSK.L": ["AZN.L", "NVS", "PFE", "MRK"],
    "NG.L": ["SSE.L", "ENEL.MI", "IBE.MC", "ENGI.PA"],
    "RIO.L": ["AAL.L", "ANTO.L", "GLEN.L"],
}

# Model choices disclosed on each note (NOT presented as data).
MODEL_CHOICES = {
    "dcf_weight": 0.6,
    "ddm_weight": 0.2,
    "comps_weight": 0.2,
    "growth_damping": "50% toward 0, floor/cap -5%/+15%",
    "terminal_g_rule": "min(rf, explicit CAGR/2)",
    "recommendation_bands": "BUY >= +15% upside, SELL <= -15%, else HOLD",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(ticker: str) -> str:
    return ticker.replace(".", "-").replace("^", "").lower()


def _notes_dir() -> Path:
    return Path(config.NOTES_DIR)


def build_note(ticker: str) -> dict:
    """Build a complete note for ``ticker`` from live sources only.

    Raises ``RuntimeError`` if a valuation is impossible on available data.
    """
    ticker = ticker.upper()
    if ticker not in config.UNIVERSE:
        raise ValueError(f"{ticker} not in universe")

    fin = fundamentals.get_financials(ticker)
    price = data.fetch_quotes([ticker]).get(ticker, {}).get("price_gbp")

    # --- peer financials (fetched first: beta fallback may need them) ---
    peers_fin, peers_px = [], {}
    peer_warnings = []
    for pt in PEER_GROUPS.get(ticker, []):
        try:
            pf = fundamentals.get_financials(pt)
            px = data.fetch_quotes([pt]).get(pt, {}).get("price_gbp")
            if pf.shares_m and px:
                peers_fin.append(pf)
                peers_px[pt] = px
            else:
                peer_warnings.append(f"{pt}: incomplete fundamentals/price")
        except Exception as exc:  # noqa: BLE001
            peer_warnings.append(f"{pt}: {exc}")

    # --- market data -----------------------------------------------
    import math
    import statistics

    beta_raw = fin.beta
    beta_fallback_prov = None
    if beta_raw is None:
        pb = [p.beta for p in peers_fin if p.beta is not None]
        if pb:
            beta_raw = statistics.median(pb)
            beta_fallback_prov = {
                "source": "Peer-median beta fallback",
                "retrieved_at": _now_utc(),
                "derivation": f"subject beta unavailable on feed; raw beta "
                              f"{beta_raw:.2f} = median of peers {[p.ticker for p in peers_fin if p.beta is not None]}",
            }
    beta = None
    blume_prov = None
    if beta_raw is not None:
        # Beta floor 0.40: an equity cannot sustainably carry a (near-)zero
        # systematic risk loading; negative raw betas are feed artifacts of
        # unusual windows. Disclosed as a model choice.
        BETA_FLOOR = 0.40
        beta_floored = max(beta_raw, BETA_FLOOR)
        # Blume (1971) adjustment: betas regress toward 1 over time; this is
        # the standard published adjustment (0.67*raw + 0.33), disclosed here.
        beta = 0.67 * beta_floored + 0.33
        blume_prov = {
            "source": "Blume (1971) beta adjustment + 0.40 beta floor",
            "retrieved_at": _now_utc(),
            "derivation": f"beta raw {beta_raw:.2f}"
                          + (f" floored at {BETA_FLOOR:.2f}" if beta_raw < BETA_FLOOR else "")
                          + f" -> adjusted {beta:.2f} (0.67*raw + 0.33)",
        }
    ke, ke_provs = fundamentals.capm_cost_of_equity(fin, beta)
    if beta_fallback_prov:
        ke_provs.append(beta_fallback_prov)
    if blume_prov:
        ke_provs.append(blume_prov)
    kd = fundamentals.implied_cost_of_debt(fin)

    # WACC: we use cost of equity (no target leverage assumption made up);
    # disclosed on the note.
    wacc = ke
    wacc_deriv = (
        f"WACC: cost of equity (CAPM) used directly; no leverage assumption "
        f"introduced. beta {beta if beta is not None else 'n/a'}"
        + (f"; implied pre-tax kd {kd:.1%} disclosed only" if kd else "")
    )

    # --- DCF leg ----------------------------------------------------
    # Banks: FCF DCF is omitted deliberately -- their operating cash flow
    # includes deposit flows, so OCF-capex is not a valuation-consistent FCF
    # (standard practice is DDM + P/E for banks). Disclosed on the note.
    industry = (fin.industry or "")
    is_bank = "bank" in industry.lower()

    growth, growth_deriv, cagr = valuation.derive_fcf_growth(fin.fcf_history_m)
    rf, rf_prov = fundamentals.risk_free_rate()
    tg, tg_deriv = valuation.derive_terminal_growth(rf, cagr)

    dcf_leg = None
    dcf_res = None
    dcf_errs = []
    fcf_base = fin.fcf_m
    if fcf_base is not None and not math.isfinite(fcf_base):
        dcf_errs.append("latest-FY FCF is not a finite number on the feed")
        fcf_base = None
    if (fcf_base and fin.shares_m and fin.net_debt_m is not None and wacc):
        try:
            dcf_res = valuation.run_dcf(valuation.DCFInputs(
                ticker=ticker,
                base_fcf_m=fcf_base,
                fcf_growth=growth,
                terminal_growth=tg,
                wacc=wacc,
                net_debt_m=fin.net_debt_m,
                shares_m=fin.shares_m,
                derivation=[growth_deriv, tg_deriv, wacc_deriv] + [p["derivation"] for p in ke_provs],
            ))
            dcf_leg = dcf_res.value_per_share
        except ValueError as exc:
            dcf_errs.append(str(exc))

    # --- DDM leg ----------------------------------------------------
    # g is capped at 0.7 x risk-free rate: ROE x retention from a single
    # cyclical year is not a sustainable perpetual growth rate.
    ddm = valuation.run_ddm(fin.dps_ttm_gbp, fin.roe,
                            fin.dividend_payout_ratio, ke,
                            max_g=(0.7 * rf) if rf else None)
    ddm_leg = ddm.value_per_share

    # --- comps leg ---------------------------------------------------
    comps = valuation.run_comps(fin, peers_fin, peers_px)
    if peer_warnings:
        comps.derivation.append("peer data gaps: " + "; ".join(peer_warnings))

    # Suppress the P/E leg when the subject's own earnings base is depressed:
    # applying healthy peer multiples to trough earnings overstates value.
    pe_leg = comps.implied_price_pe
    subject_pe = (price / fin.eps_ttm_gbp
                  if (price and fin.eps_ttm_gbp and fin.eps_ttm_gbp > 0) else None)
    if pe_leg is not None and (
        fin.eps_ttm_gbp is None or fin.eps_ttm_gbp <= 0
        or (subject_pe is not None and subject_pe > valuation.PE_MAX)
    ):
        comps.derivation.append(
            f"P/E leg suppressed: subject trailing earnings base depressed "
            f"(EPS GBP {fin.eps_ttm_gbp}, implied trailing P/E "
            f"{subject_pe and round(subject_pe)}x); peer multiples not applied"
        )
        pe_leg = None

    # --- blend --------------------------------------------------------
    bank_note = None
    if is_bank:
        legs = [
            ("ddm", ddm_leg, 0.6),
            ("comps_pe", pe_leg, 0.4),
        ]
        bank_note = (
            "FCF DCF omitted: bank operating cash flow includes deposit "
            "flows; DDM + P/E used (standard practice)"
        )
    else:
        legs = [
            ("dcf", dcf_leg, MODEL_CHOICES["dcf_weight"]),
            ("ddm", ddm_leg, MODEL_CHOICES["ddm_weight"]),
            ("comps_pe", pe_leg, MODEL_CHOICES["comps_weight"]),
            ("comps_ev_ebitda", comps.implied_price_ev_ebitda,
             MODEL_CHOICES["comps_weight"] * 0.5),
        ]
    target, weights, blend_deriv = valuation.blend_legs(legs)
    if bank_note:
        blend_deriv.insert(0, bank_note)
    if target is None:
        raise RuntimeError(
            f"{ticker}: no valuation leg could be computed from live data "
            f"(dcf errs: {dcf_errs or 'none'})"
        )

    upside = round(target / price - 1, 4) if price else None

    provenance = {
        "fx": fin.provenance.get("fx"),
        "income_statement": fin.provenance.get("income_stmt"),
        "cash_flow": fin.provenance.get("cash_flow"),
        "balance_sheet": fin.provenance.get("balance_sheet"),
        "dividends": fin.provenance.get("dividends"),
        "risk_free_rate": rf_prov.__dict__,
        "cost_of_equity": ke_provs,
        "peer_multiples": comps.derivation,
        "blend": blend_deriv,
        "model_choices": dict(MODEL_CHOICES),
    }

    return {
        "schema": "uk-equity-note/2",
        "ticker": ticker,
        "name": config.UNIVERSE[ticker],
        "status": "draft",
        "analyst": "system",
        "created_at": _now_utc(),
        "published_at": None,
        "published_by": None,
        "headline": None,           # filled by caller: one-line thesis
        "thesis": {
            "summary": None,        # filled by caller
            "catalysts": [],
            "risks": [],
        },
        "recommendation": _recommend(target, price),
        "price_target_gbp": target,
        "target_weights": weights,
        "upside_pct": (round(upside * 100, 2) if upside is not None else None),
        "valuation_inputs": {
            "is_bank": is_bank,
            "beta_raw": beta_raw,
            "beta_adjusted": beta,
            "dcf": {
                "base_fcf_m": fin.fcf_m,
                "fcf_growth_path": growth,
                "terminal_growth": tg,
                "wacc": wacc,
                "wacc_source": wacc_deriv,
                "net_debt_m": fin.net_debt_m,
                "shares_m": fin.shares_m,
                "result": {
                    "value_per_share": round(dcf_leg, 2) if dcf_leg else None,
                    "pv_explicit_m": round(dcf_res.pv_explicit, 1) if dcf_res else None,
                    "pv_terminal_m": round(dcf_res.pv_terminal, 1) if dcf_res else None,
                    "equity_value_m": round(dcf_res.equity_value_m, 1) if dcf_res else None,
                    "projections": dcf_res.projections if dcf_res else [],
                },
                "derivation": dcf_res.derivation if dcf_res else dcf_errs,
            },
            "ddm": {
                "dps_ttm_gbp": fin.dps_ttm_gbp,
                "roe": fin.roe,
                "payout": fin.dividend_payout_ratio,
                "ke": ke,
                "g": ddm.g,
                "value_per_share": ddm_leg,
                "derivation": ddm.derivation,
            },
            "comps": {
                "entries": comps.entries,
                "median_ev_ebitda": comps.median_ev_ebitda,
                "median_pe": comps.median_pe,
                "implied_price_pe": (round(comps.implied_price_pe, 2)
                                     if comps.implied_price_pe else None),
                "implied_price_ev_ebitda": (round(comps.implied_price_ev_ebitda, 2)
                                            if comps.implied_price_ev_ebitda else None),
                "derivation": comps.derivation,
            },
        },
        "market_context": {
            "price_gbp_at_publication": price,
            "price_source": "Yahoo Finance (yfinance fast_info)",
            "currency_note": "LSE quotes GBp; converted to GBP",
        },
        "provenance": provenance,
        "audit_refs": [],
        "benchmark": config.BENCHMARK,
        "review_period_months": REVIEW_PERIOD_MONTHS,
        "review_due_at": None,
        "addenda": [],
    }


def _recommend(target: float | None, price: float | None) -> str | None:
    if not target or not price:
        return None
    up = target / price - 1
    if up >= 0.15:
        return "BUY"
    if up <= -0.15:
        return "SELL"
    return "HOLD"


def publish(note: dict, headline: str, summary: str,
            catalysts: list[str], risks: list[str],
            published_by: str = "system") -> dict:
    """Finalize a draft: stamp thesis text, freeze inputs, archive priors.

    Only the analyst-written *narrative* is provided here; every number
    already on the note came from live sources at build time.
    """
    if note.get("status") != "draft":
        raise ValueError("Only draft notes can be published")
    if not headline or not summary:
        raise ValueError("headline and summary are required")
    if not note.get("recommendation"):
        price = data.fetch_quotes([note["ticker"]]).get(note["ticker"], {}).get("price_gbp")
        note["recommendation"] = _recommend(note["price_target_gbp"], price)
        if price:
            note["market_context"]["price_gbp_at_publication"] = price

    note["headline"] = headline
    note["thesis"] = {"summary": summary, "catalysts": catalysts or [], "risks": risks or []}

    note["audit_refs"] = [
        r for r in audit.tail(400)
        if r.get("event") in {"fetch_info", "fetch_quotes", "fetch_fundamentals"}
        and r.get("tickers") == [note["ticker"]]
    ][-8:]

    rec = audit.record("note_published", {
        "ticker": note["ticker"],
        "target": note["price_target_gbp"],
        "recommendation": note["recommendation"],
        "published_by": published_by,
        "schema": note["schema"],
    })
    note["status"] = "published"
    note["published_at"] = _now_utc()
    note["published_by"] = published_by
    note["publication_audit_id"] = rec["ts"]
    note["review_due_at"] = rec["ts"]  # tracking window anchored at publication
    _save(note)
    return note


def add_addendum(ticker: str, kind: str, text: str) -> dict | None:
    """Append a dated addendum (learning note, thesis check) to a note.

    Allowed kinds: 'learning', 'thesis_check', 'methodology'. Addenda are
    additions, never edits, so the original publication stays intact.
    """
    note = load_note(ticker)
    if not note or note.get("status") != "published":
        return None
    if kind not in {"learning", "thesis_check", "methodology"}:
        raise ValueError(f"bad addendum kind: {kind}")
    entry = {"kind": kind, "ts": _now_utc(), "text": text}
    note["addenda"].append(entry)
    audit.record("addendum_added", {"ticker": note["ticker"], "kind": kind})
    _save(note)
    return note


def _save(note: dict) -> None:
    d = _notes_dir()
    d.mkdir(parents=True, exist_ok=True)
    base = _slug(note["ticker"])
    jpath = d / f"{base}.json"
    mpath = d / f"{base}.md"

    if jpath.exists():
        try:
            prev = json.loads(jpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = None
        if prev and prev.get("status") == "published":
            snaps = d / "snapshots"
            snaps.mkdir(exist_ok=True)
            ts = (prev.get("published_at") or "na").replace(":", "").replace(".", "")
            (snaps / f"{base}_{ts}.json").write_text(
                json.dumps(prev, indent=2, default=str), encoding="utf-8")

    jpath.write_text(json.dumps(note, indent=2, default=str), encoding="utf-8")
    mpath.write_text(render_markdown(note), encoding="utf-8")


def render_markdown(note: dict) -> str:
    v = note["valuation_inputs"]
    dcf = v["dcf"]
    ctx = note["market_context"]
    lines = [
        f"# {note['name']} ({note['ticker']}) — Research Note",
        "",
        f"**{note.get('recommendation') or '—'}** · "
        f"Target GBP {note['price_target_gbp']} · "
        f"Upside {note.get('upside_pct')}% · "
        f"Thesis date {note.get('published_at') or note.get('created_at')}",
        "",
        f"> {note.get('headline') or ''}",
        "",
        note["thesis"].get("summary") or "",
        "",
        "## Catalysts",
    ]
    lines += [f"- {c}" for c in note["thesis"].get("catalysts", [])]
    lines += ["", "## Risks"]
    lines += [f"- {r}" for r in note["thesis"].get("risks", [])]
    lines += [
        "",
        "## Valuation inputs (frozen at publication)",
        "",
        "| Input | Value | Derivation |",
        "|---|---|---|",
        f"| Base FCF | {dcf['base_fcf_m'] and round(dcf['base_fcf_m'], 1)} GBP m | "
        f"Latest FY OCF − capex, FX-converted |",
        f"| FCF growth path | {dcf['fcf_growth_path']} | {dcf['derivation'][0] if dcf['derivation'] else ''} |",
        f"| Terminal growth | {dcf['terminal_growth']} | {dcf['derivation'][1] if len(dcf['derivation']) > 1 else ''} |",
        f"| WACC (ke) | {round(dcf['wacc'], 4) if dcf['wacc'] else None} | {dcf['wacc_source']} |",
        f"| Net debt | {dcf['net_debt_m'] and round(dcf['net_debt_m'], 1)} GBP m | Balance sheet latest FY |",
        f"| DCF value/share | {dcf['result']['value_per_share']} | 2-stage FCF model |",
        f"| DDM value/share | {v['ddm']['value_per_share']} | {'; '.join(v['ddm']['derivation'])} |",
        f"| Comps P/E implied | {v['comps']['implied_price_pe']} | median peer P/E x EPS |",
        f"| **Blended target** | **{note['price_target_gbp']}** | weights {note['target_weights']} |",
        "",
        f"Price at publication: GBP {ctx.get('price_gbp_at_publication')}",
        "",
        "## Data sources & provenance",
    ]
    for key, p in (note.get("provenance") or {}).items():
        if not p:
            continue
        items = p if isinstance(p, list) else [p]
        for item in items:
            if isinstance(item, dict):
                lines.append(f"- **{key}**: {item.get('derivation', '')} "
                             f"({item.get('source', '')}, {item.get('retrieved_at', '')})")
            else:
                lines.append(f"- **{key}**: {item}")

    lines += ["", "## Addenda"]
    adds = note.get("addenda") or []
    if not adds:
        lines.append("_None yet._")
    for a in adds:
        lines.append(f"- [{a['ts'][:10]}] **{a['kind']}**: {a['text']}")

    lines += [
        "",
        f"Review period: {note.get('review_period_months')} months vs "
        f"{note.get('benchmark')} (tracking window anchored at publication).",
        "",
        f"Audit id: `{note.get('publication_audit_id')}`",
        "",
        config.DISCLAIMER,
    ]
    return "\n".join(lines)


def load_note(ticker: str) -> dict | None:
    p = _notes_dir() / f"{_slug(ticker)}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def list_notes() -> list[dict]:
    out = []
    for p in sorted(_notes_dir().glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return out
