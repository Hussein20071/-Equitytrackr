"""Reader scenarios: recompute the published valuation under rate shocks.

The published 12m target stays frozen — that is the audit discipline. A
scenario shifts the discount rate (WACC for the DCF, cost of equity for the
DDM) and re-derives each valuation leg from the FROZEN published inputs with
the same formulas as ``tracker.valuation``:

- DCF leg: 5-year FCF path and terminal g held at published values; only the
  discount rate moves. PV = sum(FCF_t / (1+w)^t) + TV/(1+w)^5.
- DDM leg: g = ROE x retention is a payout property, so it is held; value =
  DPS x (1+g) / (ke' - g), leg dropped when ke' no longer clears g.
- Comps legs (P/E, EV/EBITDA) are multiple-based and rate-insensitive, so
  they are carried at published values.
- Weights renormalise over the legs that remain valid, exactly like
  ``blend_legs``.

Nothing is fetched and nothing is illustrated: every scenario number is
formula-derived from data already frozen in the note. The shock = 0 row is
not recomputed at all — it is the published leg values and target, verbatim.
"""

from __future__ import annotations

# Discount-rate shocks shown in the grid / on the slider (percentage points).
SHOCKS = [-0.02, -0.01, -0.005, 0.0, 0.005, 0.01, 0.02]


def _dcf_value_at(dcf: dict, wacc: float) -> float | None:
    """Replicates tracker.valuation.run_dcf with the published frozen inputs."""
    base_fcf = dcf.get("base_fcf_m")
    path = dcf.get("fcf_growth_path") or []
    tg = dcf.get("terminal_growth")
    shares = dcf.get("shares_m")
    net_debt = dcf.get("net_debt_m")
    if not (base_fcf and path and tg is not None and shares and net_debt is not None):
        return None
    if wacc <= tg:
        return None
    fcf, pv = base_fcf, 0.0
    for i, g in enumerate(path):
        fcf = fcf * (1 + g)
        pv += fcf / (1 + wacc) ** (i + 1)
    tv = fcf * (1 + tg) / (wacc - tg) / (1 + wacc) ** len(path)
    return round((pv + tv - net_debt) / shares, 4)


def _ddm_value_at(ddm: dict, ke: float) -> float | None:
    """Replicates tracker.valuation.run_ddm at a shocked cost of equity."""
    dps, g = ddm.get("dps_ttm_gbp"), ddm.get("g")
    if not (dps and g is not None and ke):
        return None
    if not (0 <= g < ke * 0.9):
        return None
    return round(dps * (1 + g) / (ke - g), 4)


def scenario_grid(note: dict, shocks: list[float] | None = None) -> list[dict]:
    """Scenario targets for one published note, one entry per shock.

    Returns a list sorted by shock, e.g.
    ``[{"shock": -0.02, "target": 98.4, "legs": {...}}, ..., {"shock": 0.0,
    "target": <published target>}, ...]``. Empty list when the note carries
    no usable valuation legs.
    """
    v = (note or {}).get("valuation_inputs") or {}
    weights = note.get("target_weights") or {}
    dcf, ddm, comps = v.get("dcf") or {}, v.get("ddm") or {}, v.get("comps") or {}
    published_legs = {
        "dcf": (dcf.get("result") or {}).get("value_per_share"),
        "ddm": ddm.get("value_per_share"),
        "comps_pe": comps.get("implied_price_pe"),
        "comps_ev_ebitda": comps.get("implied_price_ev_ebitda"),
    }
    if not any(x is not None and x > 0 for x in published_legs.values()):
        return []

    grid = []
    for s in (shocks if shocks is not None else SHOCKS):
        if s == 0:
            # Anchor row: the published values verbatim, never recomputed.
            legs = {k: x for k, x in published_legs.items() if x is not None}
            used_w = {k: weights.get(k) for k in legs}
            wsum = sum(x for x in used_w.values() if x)
            target = note.get("price_target_gbp")
            grid.append({
                "shock": 0.0,
                "target": target,
                "legs": {k: round(x, 2) for k, x in legs.items()},
                "leg_weights": {k: round((used_w.get(k) or 0) / wsum, 3)
                                for k in legs} if wsum else {},
                "published": True,
            })
            continue

        legs: dict[str, float] = {}
        if published_legs["dcf"] and dcf.get("wacc") is not None:
            val = _dcf_value_at(dcf, dcf["wacc"] + s)
            if val is not None:
                legs["dcf"] = val
        if published_legs["ddm"] and ddm.get("ke") is not None:
            val = _ddm_value_at(ddm, ddm["ke"] + s)
            if val is not None:
                legs["ddm"] = val
        # Rate-insensitive legs carried at published values.
        if published_legs["comps_pe"]:
            legs["comps_pe"] = published_legs["comps_pe"]
        if published_legs["comps_ev_ebitda"]:
            legs["comps_ev_ebitda"] = published_legs["comps_ev_ebitda"]

        avail = {k: x for k, x in legs.items()
                 if x is not None and x > 0 and weights.get(k)}
        wsum = sum(weights[k] for k in avail)
        target = (round(sum(weights[k] / wsum * x for k, x in avail.items()), 2)
                  if wsum else None)
        grid.append({
            "shock": s,
            "target": target,
            "legs": {k: round(x, 2) for k, x in avail.items()},
            "leg_weights": {k: round(weights[k] / wsum, 3) for k in avail} if wsum else {},
            "published": False,
        })
    return grid


def diff_quotes(prev: dict | None, quotes: dict) -> dict | None:
    """What moved since the previous refresh cycle (real deltas, no guessing).

    Returns ``{"movers": ["AZN.L +0.8% since last refresh", ...],
    "big_move": bool}`` or None when there is no prior cycle to compare to.
    """
    if not prev:
        return None
    moves = []
    for tk, q in (quotes or {}).items():
        if tk.startswith("_") or tk.startswith("^"):
            continue
        old = (prev.get(tk) or {}).get("price_gbp")
        new = q.get("price_gbp")
        if old and new and old > 0:
            pct = (new / old - 1) * 100
            if abs(pct) >= 0.05:
                moves.append((abs(pct), tk, pct))
    if not moves:
        return {"movers": [], "big_move": False}
    moves.sort(reverse=True)
    movers = [f"{tk} {pct:+.2f}% since last refresh" for _, tk, pct in moves[:3]]
    return {"movers": movers, "big_move": bool(moves and moves[0][0] >= 2.0)}
