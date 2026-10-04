"""Model portfolio construction: explicit weights, costs, and sector mix.

This module turns config.PORTFOLIO into what an asset manager actually
reviews: a weights table with a notional £100,000 account, a stated
return basis, a stated transaction-cost assumption, and a sector
exposure comparison against the FTSE 100.

Honesty rules inherited from the rest of the tracker:
- Every weight and price comes from config + live quotes; nothing assumed.
- The return basis is stated (Yahoo adjusted close = total return with
  dividends reinvested) rather than left implicit.
- Transaction costs are a disclosed assumption (UK stamp duty reserve
  tax 0.5% on buys + 0.1% commission), applied once at inception, never
  silently ignored.
- Sector classifications are a static, disclosed mapping per ticker
  (ICB supersector names, matching the FTSE 100 comparison source).
- The FTSE 100 sector weights come from a cached, dated file built from
  public constituent data (Wikipedia FTSE 100 table: ICB supersector
  market capitalisation, attributed there to Bloomberg). If the cache is
  missing, the comparison is omitted -- never approximated on the fly.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import config

NOTIONAL_GBP = 100_000.0
STAMP_DUTY_RATE = 0.005      # UK stamp duty reserve tax on share purchases
COMMISSION_RATE = 0.001      # assumed broker commission per buy
TOTAL_BUY_COST_RATE = STAMP_DUTY_RATE + COMMISSION_RATE

RETURN_BASIS = (
    "Total return: Yahoo Finance adjusted close (auto_adjust), i.e. price "
    "change with dividends reinvested. Not price-only."
)

COST_ASSUMPTION = (
    f"Transaction costs: {STAMP_DUTY_RATE:.1%} UK stamp duty reserve tax on "
    f"buys + {COMMISSION_RATE:.1%} commission = {TOTAL_BUY_COST_RATE:.2%} "
    "one-off drag applied at portfolio inception; no ongoing costs modelled."
)

# Disclosed ICB supersector classification for the 8 model holdings. These
# are the same supersector names the FTSE 100 comparison uses (Wikipedia's
# FTSE 100 table, attributed to Bloomberg). Classification, not measurement:
# stated here so a reviewer can disagree with the mapping explicitly.
SECTOR_MAP: dict[str, str] = {
    "AZN.L": "Health Care",
    "GSK.L": "Health Care",
    "SHEL.L": "Energy",
    "BP.L": "Energy",
    "HSBA.L": "Banks",
    "ULVR.L": "Personal Care Drug and Grocery Stores",
    "NG.L": "Utilities",
    "RIO.L": "Basic Resources",
}

SECTOR_MAP_SOURCE = (
    "Sector classification: ICB supersector per holding, assigned by the "
    "author and disclosed in tracker/portfolio.py (SECTOR_MAP); same buckets "
    "as the FTSE 100 comparison."
)

_CACHE = Path(config.DATA_DIR) / "ftse_sector_weights.json"


def build_weights_table(quotes: dict[str, dict] | None) -> dict:
    """Explicit holdings table for the £100,000 notional portfolio.

    Returns {rows: [...], total_cost_pct, notional, return_basis,
    cost_assumption}. Weight = config.PORTFOLIO (target weights, no
    rebalancing); £ position = weight x notional; the buy cost line shows
    the one-off drag. Positions are stated in GBP.
    """
    rows = []
    for tk, w in config.PORTFOLIO.items():
        q = (quotes or {}).get(tk) or {}
        px = q.get("price_gbp")
        pounds = w * NOTIONAL_GBP
        shares = (pounds / px) if px else None  # whole-share rounding at display
        rows.append({
            "ticker": tk,
            "name": config.UNIVERSE.get(tk, tk),
            "sector": SECTOR_MAP.get(tk, "Unclassified"),
            "weight_pct": round(w * 100, 1),
            "position_gbp": round(pounds, 2),
            "price_gbp": px,
            "approx_shares": int(shares) if shares else None,
            "buy_cost_gbp": round(pounds * TOTAL_BUY_COST_RATE, 2),
        })
    return {
        "notional_gbp": NOTIONAL_GBP,
        "rows": rows,
        "weight_sum_pct": round(sum(w for w in config.PORTFOLIO.values()) * 100, 1),
        "total_buy_cost_gbp": round(NOTIONAL_GBP * TOTAL_BUY_COST_RATE, 2),
        "return_basis": RETURN_BASIS,
        "cost_assumption": COST_ASSUMPTION,
        "sector_source": SECTOR_MAP_SOURCE,
    }


def portfolio_sector_weights() -> dict[str, float]:
    """Model portfolio sector mix: weight x sector, aggregated."""
    out: dict[str, float] = {}
    for tk, w in config.PORTFOLIO.items():
        s = SECTOR_MAP.get(tk, "Unclassified")
        out[s] = out.get(s, 0.0) + w
    return {k: round(v, 4) for k, v in sorted(out.items(), key=lambda kv: -kv[1])}


def apply_inception_cost(curve: list[dict]) -> list[dict]:
    """Apply the one-off buy cost as a start-of-period drag.

    Every portfolio index point is scaled by (1 - total buy cost), so the
    plotted line starts at 99.4 (indexed to 100 gross) and every return
    figure computed downstream is net of the stated transaction costs.
    Benchmark points pass through untouched.
    """
    factor = 1.0 - TOTAL_BUY_COST_RATE
    return [{**c, "portfolio": round(c["portfolio"] * factor, 4)}
            for c in (curve or [])]


def fetch_ftse_sector_weights() -> dict | None:
    """Fetch real FTSE 100 sector weights (Wikipedia ICB supersector caps).

    Writes the dated cache file this module's readers rely on. Called from
    the CLI (`sectors` command) so the per-5-minute CI refresh never pays
    this cost or depends on Wikipedia uptime. Returns the cache payload,
    or None when the fetch/parse failed (cache left untouched).
    """
    import io

    import pandas as pd
    import urllib.request

    url = "https://en.wikipedia.org/wiki/FTSE_100_Index"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (equity-trackr; educational)"})
        html = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "ignore")
        tables = pd.read_html(io.StringIO(html))
    except Exception:
        return None

    cap_table = None
    for t in tables:
        cols = [str(c).lower() for c in t.columns.astype(str)]
        if len(t.columns) == 2 and any("supersector" in c for c in cols) \
                and any("marketcap" in c.replace(" ", "") for c in cols):
            cap_table = t
            break
    if cap_table is None or len(cap_table) < 10:
        return None

    weights: dict[str, float] = {}
    try:
        caps = {}
        for _, row in cap_table.iterrows():
            name = str(row.iloc[0]).strip()
            cap = pd.to_numeric(row.iloc[1], errors="coerce")
            if name and cap == cap and cap > 0:
                caps[name] = float(cap)
        total = sum(caps.values())
        if total <= 0 or len(caps) < 10:
            return None
        weights = {k: round(v / total, 4) for k, v in caps.items()}
    except Exception:
        return None

    payload = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source": (
            "FTSE 100 constituent ICB supersector market capitalisation, "
            "Wikipedia 'FTSE 100 Index' (attributed there to Bloomberg); "
            "normalised to 100%."
        ),
        "weights": dict(sorted(weights.items(), key=lambda kv: -kv[1])),
    }
    _CACHE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_ftse_sector_weights(max_age_days: int = 21) -> dict | None:
    """Read the cached FTSE 100 sector weights, with an age guard.

    Returns the payload or None (caller then omits the comparison and
    says so, rather than showing a made-up benchmark).
    """
    if not _CACHE.exists():
        return None
    try:
        payload = json.loads(_CACHE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    try:
        as_of = datetime.fromisoformat(payload.get("as_of"))
        age_days = (datetime.now(timezone.utc) - as_of).days
    except (ValueError, TypeError):
        return payload  # unreadable timestamp: still show, as-is
    if age_days > max_age_days:
        return None
    return payload
