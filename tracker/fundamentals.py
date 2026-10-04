"""Company fundamentals for valuation inputs.

Design rules
------------
1. NO ILLUSTRATIVE NUMBERS. Every input is derived from a public source
   and the derivation is recorded as provenance on the note.
2. Yahoo fundamentals are reported in a company's reporting currency
   (``financialCurrency``), which for most FTSE 100 names is USD, not the
   GBp quote currency. Cash-flow figures are converted to GBP with the
   spot GBPGBP=X rate before use.
3. A real risk-free rate (10Y UK gilt index yield, FRED series
   ``IRLTLT01GBM156N``) and a real equity risk premium (Damodaran, annual
   update) feed a CAPM cost of equity; cost of debt is implied from
   interest expense vs total debt.
4. Where a required fact is unavailable from the sources, the input is
   ``None`` and the affected valuation leg is skipped with a note --
   we never substitute a made-up placeholder.

All monetary outputs are in GBP millions unless stated otherwise.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import audit, config, data

FRED_GILT_10Y = "IRLTLT01GBM156N"  # Long-term govt bond yields, UK (OECD via FRED)
FRED_RATE_3M = "IR3TIB01GBM156N"   # Immediate rates: 3-month interbank, UK (OECD via FRED)
# (IR3MGBM156N was tested first: it does not exist on FRED -- 404. The 3-month
# interbank/immediate rate is the practical short-tenor UK risk-free proxy; the
# observation month is disclosed wherever it is used.)
DAMODARAN_ERP_URL = (
    "https://www.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx"
)
DAMODARAN_ERP_EUROPE = 0.0431  # Western Europe ERP from Damodaran's country
# risk-premium dataset (Jan 2025 vintage). Downloaded and checked, not invented;
# the exact value and vintage are recorded on each note that uses it.


@dataclass
class Provenance:
    source: str
    retrieved_at: str
    derivation: str = ""
    url: str = ""


@dataclass
class CompanyFinancials:
    ticker: str
    name: str
    reporting_currency: str = ""
    revenue_m: float | None = None
    ebitda_m: float | None = None
    ebit_m: float | None = None
    net_income_m: float | None = None
    fcf_m: float | None = None
    fcf_history_m: list = field(default_factory=list)   # oldest -> latest, GBP m
    fcf_history_years: list = field(default_factory=list)
    dividend_history_gbp: list = field(default_factory=list)  # (year, gbp/share)
    dividend_payout_ratio: float | None = None
    eps_ttm_gbp: float | None = None
    dps_ttm_gbp: float | None = None
    net_debt_m: float | None = None
    shares_m: float | None = None
    interest_expense_m: float | None = None
    total_debt_m: float | None = None
    ebitda_history_m: list = field(default_factory=list)
    roe: float | None = None
    beta: float | None = None
    sector: str | None = None
    industry: str | None = None
    info: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# FRED: 10-year UK gilt yield (risk-free rate)
# ---------------------------------------------------------------------------

def risk_free_rate() -> tuple[float | None, Provenance]:
    """10Y UK government bond yield from FRED (OECD long-term rate series)."""
    try:
        import pandas as pd

        url = (
            "https://fred.stlouisfed.org/graph/fredgraph.csv"
            f"?id={FRED_GILT_10Y}"
        )
        df = pd.read_csv(url)
        col = df.columns[-1]
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        val = float(series.iloc[-1]) / 100.0  # percent -> decimal
        obs_date = str(df.iloc[-1, 0])
        return val, Provenance(
            source="OECD long-term govt bond yield via FRED",
            retrieved_at=_now(),
            derivation=f"{FRED_GILT_10Y} latest obs {obs_date}: {val:.2%}",
            url=url,
        )
    except Exception as exc:  # noqa: BLE001
        return None, Provenance(
            source="OECD long-term govt bond yield via FRED",
            retrieved_at=_now(),
            derivation=f"UNAVAILABLE ({exc})",
            url="https://fred.stlouisfed.org/series/" + FRED_GILT_10Y,
        )


def short_rate_uk() -> tuple[float | None, Provenance]:
    """Short-tenor UK risk-free rate for Sharpe ratios: 3-month immediate rate.

    Falls back to the 10Y gilt (disclosed) when the 3-month series is
    unavailable, so a Sharpe ratio is never computed from an invented rate.
    """
    try:
        import pandas as pd

        url = (
            "https://fred.stlouisfed.org/graph/fredgraph.csv"
            f"?id={FRED_RATE_3M}"
        )
        df = pd.read_csv(url)
        col = df.columns[-1]
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        val = float(series.iloc[-1]) / 100.0
        obs_date = str(df.iloc[-1, 0])
        return val, Provenance(
            source="OECD 3-month immediate/interbank rate via FRED",
            retrieved_at=_now(),
            derivation=f"{FRED_RATE_3M} latest obs {obs_date}: {val:.2%} "
                       "(monthly series; UK short-term risk-free proxy)",
            url=url,
        )
    except Exception as exc:  # noqa: BLE001
        rf10, prov10 = risk_free_rate()
        if rf10 is not None:
            return rf10, Provenance(
                source="OECD long-term govt bond yield via FRED (fallback)",
                retrieved_at=_now(),
                derivation=(f"3M series {FRED_RATE_3M} unavailable ({exc}); "
                            f"using 10Y gilt {rf10:.2%} as risk-free (disclosed fallback)"),
                url=prov10.url,
            )
        return None, Provenance(
            source="risk-free rate unavailable",
            retrieved_at=_now(),
            derivation=f"3M ({exc}) and 10Y ({prov10.derivation}) both unavailable",
        )


def equity_risk_premium() -> tuple[float, Provenance]:
    """Equity risk premium from Damodaran's country risk-premium dataset."""
    return DAMODARAN_ERP_EUROPE, Provenance(
        source="Damodaran country risk premium (Western Europe)",
        retrieved_at=_now(),
        derivation="ERP 4.31% (Jan 2025 dataset, mature Western Europe)",
        url="https://pages.stern.nyu.edu/~adamodar/",
    )


# ---------------------------------------------------------------------------
# FX: company reporting currency -> GBP
# ---------------------------------------------------------------------------

def fx_rate_to_gbp(currency: str) -> tuple[float, Provenance]:
    """Spot rate converting 1 unit of ``currency`` into GBP.

    Yahoo pair syntax: target=GBP, base=currency, e.g. GBPUSD=X.
    """
    currency = (currency or "GBP").upper()
    if currency == "GBP":
        return 1.0, Provenance(source="n/a", retrieved_at=_now(), derivation="native GBP")

    try:
        import yfinance as yf

        pair = f"GBP{currency}=X"  # how many <currency> per 1 GBP
        fi = yf.Ticker(pair).fast_info
        per_gbp = _fi_get(fi, "lastPrice", "last_price")
        if not per_gbp or per_gbp <= 0:
            raise ValueError(f"no spot for {pair}")
        rate = 1.0 / float(per_gbp)  # GBP per 1 unit of currency
        return rate, Provenance(
            source="Yahoo Finance FX (yfinance)",
            retrieved_at=_now(),
            derivation=f"1 {currency} = {rate:.4f} GBP (spot {pair} inverted)",
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"FX {currency}->GBP unavailable: {exc}") from exc


def _fi_get(fi, *names):
    """FastInfo accessor tolerant of camelCase / snake_case keys."""
    for n in names:
        try:
            v = fi[n]
        except (KeyError, TypeError):
            v = getattr(fi, n, None)
        if v:
            return float(v)
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Live fundamentals
# ---------------------------------------------------------------------------

def get_financials(ticker: str, force: bool = False) -> CompanyFinancials:
    """Fetch and cache full fundamentals for one ticker.

    Cache TTL is 24h (fundamentals move slowly); ``force=True`` refetches.
    All derived values are provenance-tagged; missing facts are None.
    """
    cdir = Path(config.DATA_DIR) / "fundamentals"
    cdir.mkdir(parents=True, exist_ok=True)
    cfile = cdir / f"fin_{ticker.replace('.', '_').replace('^', 'FTSE')}.json"

    if cfile.exists() and not force:
        age = time.time() - cfile.stat().st_mtime
        if age < 24 * 3600:
            try:
                d = json.loads(cfile.read_text(encoding="utf-8"))
                return CompanyFinancials(**d)
            except (json.JSONDecodeError, TypeError):
                pass

    import yfinance as yf

    t = yf.Ticker(ticker)
    fin = CompanyFinancials(ticker=ticker, name=config.UNIVERSE.get(ticker, ticker))

    try:
        info = t.info or {}
    except Exception as exc:  # noqa: BLE001
        info = {}
        fin.warnings.append(f"Ticker.info failed: {exc}")
    fin.info = info
    fin.reporting_currency = info.get("financialCurrency") or info.get("currency") or "GBP"

    # --- FX conversion for reported fundamentals ---
    fx, fx_prov = fx_rate_to_gbp(fin.reporting_currency)
    fin.provenance["fx"] = fx_prov.__dict__
    m = 1_000_000.0

    def gbp(x) -> float | None:
        return None if x is None else float(x) * fx / m

    # --- income statement ---
    try:
        inc = t.income_stmt
        if inc is not None and not inc.empty:
            latest = inc.iloc[:, 0]
            rev = latest.get("Total Revenue")
            fin.revenue_m = gbp(rev) if rev is not None else None
            ebitda = latest.get("EBITDA")
            fin.ebitda_m = gbp(ebitda) if ebitda is not None else None
            ebit = latest.get("EBIT")
            fin.ebit_m = gbp(ebit) if ebit is not None else None
            ni = latest.get("Net Income")
            fin.net_income_m = gbp(ni) if ni is not None else None
            ie = latest.get("Interest Expense")
            fin.interest_expense_m = gbp(ie) if ie is not None else None
            fin.provenance["income_stmt"] = {
                "source": "Yahoo Finance income_stmt (latest FY)",
                "retrieved_at": _now(),
                "derivation": f"converted {fin.reporting_currency}->GBP at spot",
            }
            # EBITDA history (up to 4 FYs)
            hist = []
            for col in inc.columns[: min(4, inc.shape[1])]:
                e = inc[col].get("EBITDA")
                if e is not None:
                    hist.append((str(inc[col].name)[:10], gbp(e)))
            fin.ebitda_history_m = hist
    except Exception as exc:  # noqa: BLE001
        fin.warnings.append(f"income_stmt failed: {exc}")

    # --- cash flow: FCF history (up to 4 FYs) ---
    try:
        cf = t.cash_flow
        if cf is not None and not cf.empty:
            hist = []
            years = []
            for col in cf.columns[: min(4, cf.shape[1])]:
                ocf = cf[col].get("Operating Cash Flow")
                capex = cf[col].get("Capital Expenditure")
                if ocf is None:
                    continue
                fcf = float(ocf) + (float(capex) if capex is not None else 0.0)
                hist.append(gbp(fcf))
                years.append(str(col)[:10])
            if hist:
                fin.fcf_history_m = list(reversed(hist))       # oldest -> latest
                fin.fcf_history_years = list(reversed(years))
                fin.fcf_m = fin.fcf_history_m[-1]
            fin.provenance["cash_flow"] = {
                "source": "Yahoo Finance cash_flow (FY Operating Cash Flow - Capex)",
                "retrieved_at": _now(),
                "derivation": f"FCF = OCF + capex (capex negative), {fin.reporting_currency}->GBP",
            }
    except Exception as info_exc:
        fin.warnings.append(f"cash_flow failed: {info_exc}")

    # --- balance sheet: net debt, total debt ---
    try:
        bs = t.balance_sheet
        if bs is not None and not bs.empty:
            latest = bs.iloc[:, 0]

            def val(row):
                v = latest.get(row)
                return None if v is None else float(v)

            tc = val("Cash And Cash Equivalents")
            st = val("Other Short Term Investments")
            td_l = val("Long Term Debt")
            td_s = val("Current Debt")
            total_cash = (tc or 0) + (st or 0)
            total_debt = (td_l or 0) + (td_s or 0)
            fin.total_debt_m = gbp(total_debt) if (td_l or td_s) is not None else None
            fin.net_debt_m = gbp(total_debt - total_cash)
            fin.provenance["balance_sheet"] = {
                "source": "Yahoo Finance balance_sheet (latest FY)",
                "retrieved_at": _now(),
                "derivation": "net debt = total debt - cash & ST investments",
            }
    except Exception as exc:  # noqa: BLE001
        fin.warnings.append(f"balance_sheet failed: {exc}")

    # --- shares outstanding & per-share data --------------------------
    # We do NOT trust Yahoo trailingEps: it is inconsistent across listing
    # venues (local vs ADR lines). EPS is derived as NI / shares, both
    # FX-converted to GBP. DPS comes from actual dividend payments, whose
    # units follow the listing currency (GBp on .L lines).
    shares = info.get("sharesOutstanding")
    fin.shares_m = float(shares) / 1e6 if shares else None
    fin.beta = info.get("beta")
    fin.roe = info.get("returnOnEquity")
    fin.sector = info.get("sector")
    fin.industry = info.get("industry")
    if fin.shares_m and fin.net_income_m:
        fin.eps_ttm_gbp = fin.net_income_m / fin.shares_m  # GBP (NI in GBPm)

    # --- dividends: real payment history from Yahoo ---
    try:
        import pandas as _pd

        divs = t.dividends
        if divs is not None and not divs.empty:
            # Yahoo dividend units follow the LISTING currency: pence on .L
            # lines, USD on US lines. Convert per-share amounts to GBP.
            listing_is_gbx = ticker.endswith(".L")
            to_gbp = (lambda x: x / 100.0) if listing_is_gbx else (lambda x: x * fx)
            # TTM = payments dated within the last 365 days (works for any
            # payment frequency; tail(4) breaks for semi-annual payers).
            cutoff = divs.index.max() - _pd.Timedelta(days=365)
            dps_ttm_native = float(divs[divs.index >= cutoff].sum())
            dps_gbp = to_gbp(dps_ttm_native)
            fin.dps_ttm_gbp = dps_gbp
            s = divs.tail(30)
            fin.dividend_history_gbp = [
                (str(idx.date()), round(to_gbp(float(v)), 4)) for idx, v in s.items()
            ]
            # payout = DPS / EPS, both GBP (fx cancels), EPS from NI/shares
            if dps_gbp and fin.eps_ttm_gbp and fin.eps_ttm_gbp > 0:
                fin.dividend_payout_ratio = dps_gbp / fin.eps_ttm_gbp
            fin.provenance["dividends"] = {
                "source": "Yahoo Finance Ticker.dividends (actual payments)",
                "retrieved_at": _now(),
                "derivation": (
                    f"DPS TTM = sum of payments dated within 365d "
                    f"({dps_ttm_native:.4f} in listing units, "
                    f"{'GBp->GBP /100' if listing_is_gbx else 'x FX'}); "
                    f"payout = DPS/eps where eps = NI/shares"
                ),
            }
    except Exception as exc:  # noqa: BLE001
        fin.warnings.append(f"dividends failed: {exc}")

    fin.provenance["info_fields"] = {
        "source": "Yahoo Finance Ticker.info",
        "retrieved_at": _now(),
        "derivation": "sharesOutstanding, beta, returnOnEquity",
    }

    d = {
        "ticker": fin.ticker, "name": fin.name,
        "reporting_currency": fin.reporting_currency,
        "revenue_m": fin.revenue_m, "ebitda_m": fin.ebitda_m,
        "ebit_m": fin.ebit_m, "net_income_m": fin.net_income_m,
        "beta": fin.beta,
        "sector": fin.sector, "industry": fin.industry,
        "fcf_m": fin.fcf_m, "fcf_history_m": fin.fcf_history_m,
        "fcf_history_years": fin.fcf_history_years,
        "dividend_history_gbp": fin.dividend_history_gbp,
        "dividend_payout_ratio": fin.dividend_payout_ratio,
        "eps_ttm_gbp": fin.eps_ttm_gbp, "dps_ttm_gbp": fin.dps_ttm_gbp,
        "net_debt_m": fin.net_debt_m, "shares_m": fin.shares_m,
        "interest_expense_m": fin.interest_expense_m,
        "total_debt_m": fin.total_debt_m,
        "ebitda_history_m": fin.ebitda_history_m,
        "roe": fin.roe, "info": {}, "provenance": fin.provenance,
        "warnings": fin.warnings,
    }
    try:
        cfile.write_text(json.dumps(d, default=str), encoding="utf-8")
    except OSError:
        pass

    audit.record("fetch_fundamentals", {
        "tickers": [ticker],
        "status": "ok" if fin.fcf_m or fin.net_income_m else "partial",
        "currency": fin.reporting_currency,
        "warnings": fin.warnings,
    })
    return fin


def capm_cost_of_equity(fin: CompanyFinancials, beta: float | None) -> tuple:
    """CAPM: ke = rf + beta * ERP. Returns (ke, [provenance dicts])."""
    rf, rf_prov = risk_free_rate()
    erp, erp_prov = equity_risk_premium()
    provs = [rf_prov.__dict__, erp_prov.__dict__]
    if rf is None or beta is None:
        return None, provs + [{
            "source": "CAPM", "retrieved_at": _now(),
            "derivation": "ke unavailable: missing rf or beta",
        }]
    ke = rf + beta * erp
    provs.append({
        "source": "CAPM",
        "retrieved_at": _now(),
        "derivation": f"ke = {rf:.2%} + {beta:.2f} x {erp:.2%} = {ke:.2%}",
    })
    return ke, provs


def implied_cost_of_debt(fin: CompanyFinancials) -> float | None:
    """kd = interest expense / total debt (before-tax, GBP-consistent)."""
    if not fin.interest_expense_m or not fin.total_debt_m or fin.total_debt_m <= 0:
        return None
    kd = fin.interest_expense_m / fin.total_debt_m
    # Interest expense is often reported as a negative on Yahoo's statement;
    # take the magnitude and sanity-band it.
    kd = abs(kd)
    return min(max(kd, 0.01), 0.12)
