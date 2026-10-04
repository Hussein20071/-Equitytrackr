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

    # Beta methodology (in priority order, all disclosed):
    #   1. OLS regression vs the benchmark we actually track (^FTSE), 2 years
    #      of weekly observations (~104 obs, minimum 52) -- per-name by
    #      construction. Yahoo's feed beta for .L names is computed against
    #      the S&P 500 (AZN feed 0.20 vs measured-vs-FTSE ~1.3), the wrong
    #      benchmark for a FTSE 100 tracker. The 2-year window replaced the
    #      original 1-year window on 2026-10-04: with 52 obs, BP and SHEL
    #      pinned at the 0.40 beta floor (1y betas of -0.23 and +0.12 are
    #      window noise); 104 weekly obs stabilises them without changing
    #      the estimator.
    #   2. Feed beta (fallback, basis undisclosed by the vendor).
    #   3. Peer-median (last resort; collapsed to one shared number historically).
    beta_raw = None
    beta_fallback_prov = None
    from . import data as _data

    beta_raw, beta_reg_prov = _data.regression_beta(ticker, period="2y", min_weeks=52)
    if beta_raw is not None:
        beta_fallback_prov = beta_reg_prov
    elif fin.beta is not None:
        beta_raw = fin.beta
        beta_fallback_prov = {
            "source": "Yahoo feed beta (fallback)",
            "retrieved_at": _now_utc(),
            "derivation": (
                f"regression vs ^FTSE unavailable ({beta_reg_prov.get('derivation') or 'no data'}); "
                f"using vendor beta {fin.beta:.2f} -- benchmark basis undisclosed"
            ),
        }
    else:
        pb = [p.beta for p in peers_fin if p.beta is not None]
        if pb:
            beta_raw = statistics.median(pb)
            beta_fallback_prov = {
                "source": "Peer-median beta fallback",
                "retrieved_at": _now_utc(),
                "derivation": (
                    f"regression failed ({beta_reg_prov.get('derivation') or 'no data'}) "
                    f"and feed beta missing; raw beta {beta_raw:.2f} = median of peers "
                    f"{[p.ticker for p in peers_fin if p.beta is not None]}"
                ),
            }
        else:
            beta_fallback_prov = {
                "source": "Beta unavailable",
                "retrieved_at": _now_utc(),
                "derivation": (
                    "regression failed, feed beta missing, no peer betas; "
                    "cost of equity unavailable this cycle"
                ),
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
    fcf_base_note = None
    if fcf_base is not None and not math.isfinite(fcf_base):
        dcf_errs.append("latest-FY FCF is not a finite number on the feed")
        fcf_base = None
    if fcf_base is not None and fcf_base <= 0:
        dcf_errs.append(
            f"latest-FY FCF is GBP {fcf_base:,.0f}m (non-positive on the feed)"
        )
        fcf_base = None
    if fcf_base is None:
        # Missing latest FY (e.g. RIO: NaN on the feed): fall back to a
        # normalised multi-year FCF average over the finite trailing FYs,
        # disclosed. If the average itself is not positive (e.g. NG: FCF
        # negative in 3 of 4 trailing years), the DCF is excluded with an
        # explicit data-driven reason and the blend re-weights over the
        # surviving legs.
        finite = [v for v in (fin.fcf_history_m or [])
                  if isinstance(v, (int, float)) and math.isfinite(v)]
        if len(finite) >= 2:
            avg = sum(finite) / len(finite)
            if avg > 0:
                fcf_base = avg
                fcf_base_note = (
                    f"base FCF = normalised multi-year average of the "
                    f"{len(finite)} finite trailing FYs ("
                    + ", ".join(f"{v:,.0f}" for v in finite)
                    + f") = {avg:,.0f} GBPm; latest-FY value missing/non-finite "
                    f"on the feed ({'; '.join(dcf_errs) or 'no value'})"
                )
                dcf_errs = []
            else:
                neg = sum(1 for v in finite if v <= 0)
                dcf_errs.append(
                    f"DCF excluded: FY free cash flow (OCF - capex) is "
                    f"non-positive in {neg} of the {len(finite)} trailing "
                    f"financial years (" + ", ".join(f"{v:,.0f}" for v in finite)
                    + f" GBPm; latest FY {fin.fcf_m and f'{fin.fcf_m:,.0f}'}"
                    + ") -- a DCF cannot be run from a negative base; "
                    "the blend re-weights over the surviving legs"
                )
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
                derivation=[growth_deriv, tg_deriv, wacc_deriv]
                           + ([fcf_base_note] if fcf_base_note else [])
                           + [p["derivation"] for p in ke_provs],
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
    if fcf_base_note:
        blend_deriv.append(fcf_base_note)
    if target is None:
        raise RuntimeError(
            f"{ticker}: no valuation leg could be computed from live data "
            f"(dcf errs: {dcf_errs or 'none'})"
        )

    # --- model sanity guardrail --------------------------------------
    # ±30% band vs the market price, with leg attribution. Stored on the
    # note at build time so the site can show the flag everywhere the
    # target appears; also audited.
    guard = valuation.outlier_check(
        target, price,
        {"dcf": dcf_leg, "ddm": ddm_leg, "comps_pe": pe_leg,
         "comps_ev_ebitda": comps.implied_price_ev_ebitda},
        weights,
    )
    guard["checked_at"] = _now_utc()
    guard["price_used"] = price
    if guard["is_outlier"]:
        audit.record("model_outlier_flagged", {
            "tickers": [ticker],
            "deviation_pct": guard["deviation_pct"],
            "driver_leg": guard["driver_leg"],
            "driver_contribution_pct": guard["driver_contribution_pct"],
        })

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
        "model_checks": guard,
        "valuation_inputs": {
            "is_bank": is_bank,
            "beta_raw": beta_raw,
            "beta_adjusted": beta,
            "dcf": {
                "base_fcf_m": fin.fcf_m,
                "base_fcf_used_m": (round(fcf_base, 1) if dcf_res else None),
                "base_fcf_source": (fcf_base_note or
                                    "latest FY OCF - capex, FX-converted"),
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
        "next_events": _fetch_next_events(ticker),
        "esg": _fetch_esg(ticker),
        "provenance": provenance,
        "audit_refs": [],
        "benchmark": config.BENCHMARK,
        "review_period_months": REVIEW_PERIOD_MONTHS,
        "review_due_at": None,
        "addenda": [],
    }


def _fetch_esg(ticker: str) -> dict | None:
    """Sustainalytics ESG risk scores from the Yahoo feed, or None.

    Scores are RISK scores (lower = less risk) on a 0-40+ scale; the
    direction is stated wherever displayed. Missing data returns None and
    the note says so -- never a fabricated score.
    """
    try:
        import yfinance as yf

        s = yf.Ticker(ticker).sustainability
        if s is None or getattr(s, "empty", True):
            return None

        def _get(key: str) -> float | None:
            try:
                return float(s.loc[key].iloc[0])
            except (KeyError, IndexError, TypeError, ValueError):
                return None

        out = {
            "total_esg": _get("totalEsg"),
            "environment": _get("environmentScore"),
            "social": _get("socialScore"),
            "governance": _get("governanceScore"),
            "source": "Yahoo Finance Ticker.sustainability (Sustainalytics ESG risk score; lower = less risk)",
            "retrieved_at": _now_utc(),
        }
        return out if out["total_esg"] is not None else None
    except Exception:  # noqa: BLE001
        return None


def _fetch_next_events(ticker: str) -> dict | None:
    """Next announced earnings date from the Yahoo calendar, or None.

    yfinance returns either a dict ({"Earnings Date": [ts, ts, ts]}) or a
    DataFrame depending on version; both handled. LSE names frequently
    have no calendar entry -- the note then says the feed has none rather
    than inventing a date.
    """
    try:
        import yfinance as yf

        cal = yf.Ticker(ticker).calendar
        date = None
        if isinstance(cal, dict):
            d = cal.get("Earnings Date")
            if isinstance(d, (list, tuple)) and d:
                date = str(d[0])[:10]
            elif d is not None:
                date = str(d)[:10]
        elif cal is not None and getattr(cal, "empty", True) is False:
            try:
                row = cal.loc["Earnings Date"]
                vals = list(row.dropna().values)
                if vals:
                    date = str(vals[0])[:10]
            except (KeyError, IndexError):
                date = None
        if not date:
            return None
        # Only a FUTURE date counts as "next results"; a past date from the
        # feed is the last announced set and must not be labelled next.
        try:
            if datetime.fromisoformat(date) < datetime.now():
                return None
        except ValueError:
            return None
        return {
            "earnings_date": date,
            "source": "Yahoo Finance Ticker.calendar (next announced earnings date)",
            "retrieved_at": _now_utc(),
        }
    except Exception:  # noqa: BLE001
        return None


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
            published_by: str = "system",
            correction: str | None = None,
            wrong_if: list[str] | None = None) -> dict:
    """Finalize a draft: stamp thesis text, freeze inputs, archive priors.

    Only the analyst-written *narrative* is provided here; every number
    already on the note came from live sources at build time.

    Re-publication keeps the live record continuous: when a published
    note for the same ticker already exists, the new note inherits
    ``first_published_at`` and the original publication price, carries
    over prior addenda, and (when ``correction`` is given) appends a dated
    addendum describing the change. ``published_at`` becomes the revision
    date; the tracked window still starts at first publication.
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

    prior = load_note(note["ticker"])
    if prior and prior.get("status") == "published":
        note["first_published_at"] = (prior.get("first_published_at")
                                      or prior.get("published_at"))
        prior_px = ((prior.get("market_context") or {})
                    .get("price_gbp_at_first_publication")
                    or (prior.get("market_context") or {})
                    .get("price_gbp_at_publication"))
        if prior_px is not None:
            note["market_context"]["price_gbp_at_first_publication"] = prior_px
        note["addenda"] = list(prior.get("addenda") or [])
    else:
        note["first_published_at"] = note.get("created_at")

    # The live record anchors at the EARLIEST publication of this note, which
    # may predate the immediately-prior revision (revision chains lose the
    # original otherwise). Snapshots are append-only, so the earliest one is
    # the true first publication.
    base_slug = _slug(note["ticker"])
    snap_dir = _notes_dir() / "snapshots"
    earliest = note.get("first_published_at")
    earliest_px = None
    snap_cands = []
    if snap_dir.exists():
        for sp in sorted(snap_dir.glob(f"{base_slug}_*.json")):
            try:
                spd = json.loads(sp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            sp_pub = spd.get("published_at")
            sp_px = (spd.get("market_context") or {}).get(
                "price_gbp_at_publication")
            if sp_pub:
                snap_cands.append((sp_pub, sp_px))
    if snap_cands:
        min_pub, _ = min(snap_cands, key=lambda t: t[0])
        if earliest is None or min_pub < earliest:
            earliest = min_pub
        # The price at first publication comes from the earliest snapshot
        # THAT CARRIES A PRICE (early snapshots can predate the quote fetch),
        # even when the prior revision chain already carries a (later) one.
        priced = [(p, x) for p, x in snap_cands if x is not None]
        if priced:
            earliest_px = min(priced, key=lambda t: t[0])[1]
    if earliest_px is None:
        earliest_px = ((note.get("market_context") or {})
                       .get("price_gbp_at_first_publication"))
    note["first_published_at"] = earliest
    if earliest_px is not None:
        note["market_context"]["price_gbp_at_first_publication"] = earliest_px
    if correction:
        note["addenda"].append({
            "kind": "methodology",
            "ts": _now_utc(),
            "text": correction,
        })

    note["headline"] = headline
    note["thesis"] = {
        "summary": summary,
        "catalysts": catalysts or [],
        "risks": risks or [],
        "wrong_if": wrong_if or [],
    }

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
        f"| DCF value/share | {(dcf.get('result') or {}).get('value_per_share')} | 2-stage FCF model |",
        f"| DDM value/share | {v['ddm'].get('value_per_share')} | {'; '.join(v['ddm'].get('derivation') or [])} |",
        f"| Comps P/E implied | {v['comps'].get('implied_price_pe')} | median peer P/E x EPS |",
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
