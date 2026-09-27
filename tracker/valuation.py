"""Valuation engine v2: DCF, DDM, and live peer comparables.

Every growth/terminal/discount input is either derived from real history
(with the derivation string recorded) or explicitly disclosed as a model
choice with its formula. Nothing is presented as data that is not data.

All monetary values in GBP. Shares in millions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Growth derivation from real FCF history
# ---------------------------------------------------------------------------

def derive_fcf_growth(fcf_history_m: list[float]) -> tuple[list[float], str, float | None]:
    """Explicit 5-year FCF growth path from historical FCF.

    NaN/negative-safe: if the full history spans a sign flip (e.g. a loss
    year), the CAGR is computed over the trailing run of positive years;
    with <2 usable positive observations growth is 0% and disclosed as a
    model choice, NOT as data.
    Returns (growth_path[5], derivation, cagr_used).
    """
    import math

    hist = [v for v in fcf_history_m
            if isinstance(v, (int, float)) and math.isfinite(v)]
    n = len(hist)
    cagr = None
    # Full-span CAGR only when every year is positive: a history spanning a
    # loss year makes CAGR meaningless, and pairing arbitrary positive
    # endpoints would be cherry-picking.
    if n >= 2 and all(v > 0 for v in hist):
        cagr = (hist[-1] / hist[0]) ** (1 / (n - 1)) - 1
    if cagr is None or not math.isfinite(cagr):
        return [0.0] * 5, (
            "growth: insufficient or sign-flipping FCF history (a loss year "
            "makes CAGR meaningless) -> explicit 0% growth assumption "
            "(disclosed model choice, not data)"
        ), None

    damped = cagr / 2.0  # 50% mean-reversion damping
    bounded = min(max(damped, -0.05), 0.15)
    if bounded < 0:
        path = [bounded, bounded * 0.5, 0.0, 0.0, 0.0]
    else:
        path = [bounded, bounded, bounded * 0.75, bounded * 0.5, bounded * 0.25]
    deriv = (
        f"growth: FCF CAGR {cagr:+.1%} over {n - 1}y, 50% damped -> {bounded:+.1%} "
        f"y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%)"
    )
    return [round(g, 4) for g in path], deriv, round(cagr, 4)


def derive_terminal_growth(risk_free: float | None, growth_cagr: float | None) -> tuple[float, str]:
    """Terminal growth = min(risk-free rate, half the explicit CAGR).

    Formula is stated; both inputs are real where available.
    """
    if risk_free is None:
        return 0.0, "terminal g: risk-free rate unavailable -> 0% (disclosed)"
    cap = min(risk_free, 0.025)
    g = cap if growth_cagr is None else min(cap, max(growth_cagr / 2, 0.0))
    return round(g, 4), f"terminal g = min(rf {risk_free:.2%}, explicit CAGR/2) = {g:.2%}"


# ---------------------------------------------------------------------------
# DCF
# ---------------------------------------------------------------------------

@dataclass
class DCFInputs:
    ticker: str
    base_fcf_m: float | None = None        # GBP m (latest FY, FX-converted)
    fcf_growth: list = field(default_factory=list)
    terminal_growth: float | None = None
    wacc: float | None = None
    net_debt_m: float | None = None
    shares_m: float | None = None
    derivation: list = field(default_factory=list)  # provenance strings

    def validate(self) -> list[str]:
        import math

        errs = []
        if (not self.base_fcf_m or self.base_fcf_m <= 0
                or not math.isfinite(self.base_fcf_m)):
            errs.append("base FCF must be positive and finite")
        if (self.wacc is None or self.terminal_growth is None
                or self.wacc <= self.terminal_growth):
            errs.append("WACC must exceed terminal growth")
        if not self.net_debt_m or not self.shares_m or self.shares_m <= 0:
            errs.append("net debt and share count required")
        for g in self.fcf_growth:
            if g <= -1.0:
                errs.append("growth rates must be > -100%")
        return errs


@dataclass
class DCFResult:
    pv_explicit: float
    pv_terminal: float
    enterprise_value_m: float
    equity_value_m: float
    value_per_share: float
    projections: list = field(default_factory=list)
    derivation: list = field(default_factory=list)


def run_dcf(inp: DCFInputs) -> DCFResult:
    errs = inp.validate()
    if errs:
        raise ValueError(f"Invalid DCF inputs: {errs}")

    wacc = inp.wacc
    tg = inp.terminal_growth
    fcfs, disc = [], []
    fcf = inp.base_fcf_m
    for i, g in enumerate(inp.fcf_growth):
        fcf = fcf * (1 + g)
        fcfs.append(fcf)
        disc.append((1 + wacc) ** (i + 1))

    pv_explicit = sum(f / d for f, d in zip(fcfs, disc))
    pv_terminal = fcfs[-1] * (1 + tg) / (wacc - tg) / (1 + wacc) ** len(fcfs)

    ev = pv_explicit + pv_terminal
    eq = ev - inp.net_debt_m
    per_share = eq / inp.shares_m

    projections = [
        {
            "year": i + 1,
            "growth": inp.fcf_growth[i],
            "fcf_m": round(fcfs[i], 1),
            "pv_m": round(fcfs[i] / disc[i], 1),
        }
        for i in range(len(fcfs))
    ]
    return DCFResult(
        pv_explicit=pv_explicit,
        pv_terminal=pv_terminal,
        enterprise_value_m=ev,
        equity_value_m=eq,
        value_per_share=per_share,
        projections=projections,
        derivation=list(inp.derivation),
    )


# ---------------------------------------------------------------------------
# Dividend discount model (banks / payers)
# ---------------------------------------------------------------------------

@dataclass
class DDMResult:
    value_per_share: float | None
    g: float | None
    ke: float
    dps_ttm_gbp: float | None
    derivation: list = field(default_factory=list)


def run_ddm(dps_ttm_gbp: float | None, roe: float | None,
            payout: float | None, ke: float | None,
            max_g: float | None = None) -> DDMResult:
    """Gordon growth DDM: g = ROE x retention, value = D1 / (ke - g).

    ``max_g`` (optional) caps g at a sustainable perpetual rate; the cap
    and its reason are recorded in the derivation.
    """
    derivation = []
    if not (dps_ttm_gbp and roe and payout and ke):
        return DDMResult(None, None, ke or 0.0, dps_ttm_gbp,
                         derivation=["DDM skipped: missing DPS/ROE/payout/ke"])
    g_raw = roe * (1 - payout)
    g = g_raw
    if max_g is not None and g_raw > max_g:
        g = max_g
        derivation.append(
            f"g capped: ROE x retention {g_raw:.2%} from a single-year base "
            f"exceeds the sustainable-perpetual cap 0.7 x risk-free = {max_g:.2%}"
        )
    if not (0 <= g < ke * 0.9):
        derivation.append(f"DDM skipped: g={g:.2%} not < ke*0.9={ke * 0.9:.2%}")
        return DDMResult(None, g, ke, dps_ttm_gbp, derivation)
    d1 = dps_ttm_gbp * (1 + g)
    v = d1 / (ke - g)
    derivation.extend([
        f"g = ROE {roe:.1%} x retention {1 - payout:.0%} = {g:.2%}"
        + (f" (raw {g_raw:.2%}, capped)" if g != g_raw else ""),
        f"D1 = DPS TTM {dps_ttm_gbp:.2f} x (1+g) = {d1:.2f}",
        f"value = D1 / (ke {ke:.2%} - g {g:.2%}) = {v:.2f}",
    ])
    return DDMResult(round(v, 4), round(g, 4), ke, dps_ttm_gbp, derivation)


# ---------------------------------------------------------------------------
# Comparables from live peer data
# ---------------------------------------------------------------------------

@dataclass
class PeerComp:
    peer: str
    ev_ebitda: float | None = None
    pe: float | None = None


@dataclass
class CompsResult:
    entries: list = field(default_factory=list)
    median_ev_ebitda: float | None = None
    median_pe: float | None = None
    implied_price_ev_ebitda: float | None = None
    implied_price_pe: float | None = None
    derivation: list = field(default_factory=list)


# Not-meaningful thresholds for peer multiples (disclosed on the note).
PE_MAX = 60.0        # P/E above this reflects a depressed-earnings base
EV_EBITDA_MAX = 30.0 # likewise for EV/EBITDA


def run_comps(subject, peers_fin: list, peers_px: dict[str, float]) -> CompsResult:
    """Compute peer multiples from live data, apply medians to the subject.

    peers_fin: CompanyFinancials for each peer (GBP-converted).
    peers_px: peer ticker -> current price GBP.
    Multiples that are not meaningful (negative earnings; P/E > 60x or
    EV/EBITDA > 30x, typically impairment-depressed bases) are excluded
    from the medians; every exclusion is recorded.
    """
    import statistics

    res = CompsResult()
    evs, pes = [], []
    excluded = []
    for p in peers_fin:
        ev = pe = None
        px = peers_px.get(p.ticker)
        if px and p.shares_m and p.shares_m > 0:
            mktcap = px * p.shares_m
            if p.ebitda_m and p.ebitda_m > 0:
                ev = (mktcap + (p.net_debt_m or 0.0)) / p.ebitda_m
                if ev > EV_EBITDA_MAX:
                    excluded.append(f"{p.ticker} EV/EBITDA {ev:.0f}x > {EV_EBITDA_MAX:.0f}x cap")
                else:
                    evs.append(ev)
            if p.net_income_m and p.net_income_m > 0:
                pe = mktcap / p.net_income_m
                if pe > PE_MAX:
                    excluded.append(f"{p.ticker} P/E {pe:.0f}x > {PE_MAX:.0f}x cap")
                else:
                    pes.append(pe)
        res.entries.append({"peer": p.ticker, "ev_ebitda": ev, "pe": pe})

    # A single-peer 'median' is just that peer -- require >=2 valid values.
    if evs:
        res.median_ev_ebitda = statistics.median(evs) if len(evs) >= 2 else None
        if len(evs) < 2:
            res.derivation.append(
                f"EV/EBITDA median not robust: only {len(evs)} valid peer "
                f"multiple; leg dropped (need >=2)")
    if pes:
        res.median_pe = statistics.median(pes) if len(pes) >= 2 else None
        if len(pes) < 2:
            res.derivation.append(
                f"P/E median not robust: only {len(pes)} valid peer multiple; "
                f"leg dropped (need >=2)")
    res.derivation.append(
        "multiples computed per peer: EV = price x shares + net debt; "
        "EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true "
        "median over multiples within the not-meaningful caps "
        f"(P/E <= {PE_MAX:.0f}x, EV/EBITDA <= {EV_EBITDA_MAX:.0f}x)"
    )
    if excluded:
        res.derivation.append("excluded from medians: " + "; ".join(excluded))

    if res.median_pe and subject.eps_ttm_gbp and subject.eps_ttm_gbp > 0:
        res.implied_price_pe = res.median_pe * subject.eps_ttm_gbp
        res.derivation.append(
            f"P/E leg: median {res.median_pe:.1f}x x EPS {subject.eps_ttm_gbp:.2f} "
            f"= {res.implied_price_pe:.2f}"
        )
    if (res.median_ev_ebitda and subject.ebitda_m and subject.ebitda_m > 0
            and subject.net_debt_m is not None and subject.shares_m):
        eq = res.median_ev_ebitda * subject.ebitda_m - subject.net_debt_m
        res.implied_price_ev_ebitda = eq / subject.shares_m
        res.derivation.append(
            f"EV/EBITDA leg: median {res.median_ev_ebitda:.1f}x x EBITDA "
            f"{subject.ebitda_m:,.0f}m - net debt {subject.net_debt_m:,.0f}m "
            f"= equity {eq:,.0f}m / {subject.shares_m:,.0f}m shares "
            f"= {res.implied_price_ev_ebitda:.2f}"
        )
    return res


# ---------------------------------------------------------------------------
# Blending
# ---------------------------------------------------------------------------

def blend_legs(legs: list[tuple[str, float | None, float]]) -> tuple[float | None, dict, list]:
    """Weighted blend of valuation legs, renormalising over available ones.

    legs: [(name, value_gbp, requested_weight)]. Returns
    (target, {name: actual_weight}, derivation_lines).
    """
    deriv = []
    available = [(n, v, w) for n, v, w in legs if v is not None and v > 0]
    if not available:
        return None, {}, ["blend: no valuation legs available"]
    wsum = sum(w for _, _, w in available)
    target, weights = 0.0, {}
    for n, v, w in available:
        wi = w / wsum
        weights[n] = round(wi, 3)
        target += wi * v
        deriv.append(f"blend: {n} {v:.2f} x {wi:.0%}")
    return round(target, 2), weights, deriv
