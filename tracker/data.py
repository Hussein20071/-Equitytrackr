"""Live market data layer (Yahoo Finance via yfinance) with audit logging.

All LSE equities on Yahoo quote in GBp (pence). The tracker converts prices
to GBP in every snapshot so downstream valuations never mix units.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import audit

COLS = ["Ticker", "Date", "Close_gbp", "Volume"]

_FX_CACHE: dict[str, tuple[float, float]] = {}  # ccy -> (GBP per unit, ts)


def fx_to_gbp(ccy: str, ttl_s: int = 600) -> float:
    """GBP per 1 unit of ``ccy`` via Yahoo FX pair GBP{ccy}=X, cached 10 min."""
    ccy = (ccy or "GBP").upper()
    if ccy in {"GBP", "GBX", "GBP."}:
        return 1.0
    rate, ts = _FX_CACHE.get(ccy, (0.0, 0.0))
    if rate and time.time() - ts < ttl_s:
        return rate
    import yfinance as yf

    fi = yf.Ticker(f"GBP{ccy}=X").fast_info
    px = _fi_get(fi, "lastPrice", "last_price")
    if not px:
        raise RuntimeError(f"FX pair GBP{ccy}=X unavailable")
    rate = 1.0 / float(px)  # pair quotes ccy per GBP
    _FX_CACHE[ccy] = (rate, time.time())
    audit.record("fetch_fx", {"tickers": [f"GBP{ccy}=X"], "status": "ok",
                               "rate": round(rate, 6)})
    return rate


def _snapshot_path() -> Path:
    from . import config

    return Path(config.DATA_DIR) / "market_snapshot.json"


def _cache_dir() -> Path:
    from . import config

    return Path(config.DATA_DIR) / "cache"


def _gbp(px: float) -> float:
    """GBp -> GBP."""
    return float(px) / 100.0


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit(event: str, tickers: list[str], status: str, detail: dict | None = None) -> None:
    audit.record(event, {"tickers": tickers, "status": status, **(detail or {})})


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=COLS)


def fetch_history(tickers: list[str], period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Download adjusted-close history for tickers.

    Returns a tidy DataFrame: [Ticker, Date, Close_gbp, Volume].
    """
    import yfinance as yf

    if not tickers:
        return _empty()

    t0 = time.time()
    try:
        raw = yf.download(
            tickers,
            period=period,
            interval=interval,
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as exc:  # noqa: BLE001
        _audit("fetch_history", tickers, "error", {"error": str(exc)})
        return _empty()

    rows: list[dict] = []
    for tk in tickers:
        # LSE (.L) history is in GBp; indices/USD lines pass through. Ratios
        # (returns) are unit-invariant, but keep units consistent for display.
        conv = _gbp if tk.endswith(".L") else (lambda x: x)
        try:
            sub = raw[tk] if isinstance(raw.columns, pd.MultiIndex) else raw
            if sub is None or sub.empty or "Close" not in sub.columns:
                continue
            closes = sub["Close"].dropna()
            for date, close in closes.items():
                vol = sub["Volume"].reindex(closes.index).loc[date]
                rows.append(
                    {
                        "Ticker": tk,
                        "Date": pd.Timestamp(date).tz_localize(None),
                        "Close_gbp": conv(close),
                        "Volume": vol,
                    }
                )
        except Exception as exc:  # noqa: BLE001
            _audit("fetch_history", [tk], "error", {"error": str(exc)})

    df = pd.DataFrame(rows, columns=COLS)
    status = "ok" if not df.empty else "empty"
    _audit(
        "fetch_history",
        tickers,
        status,
        {"rows": len(df), "elapsed_s": round(time.time() - t0, 2)},
    )
    return df


def _fi_get(fi, *names):
    """FastInfo accessor: supports camelCase (yfinance>=0.2.5x) and snake_case."""
    for n in names:
        try:
            v = fi[n]
        except (KeyError, TypeError):
            v = getattr(fi, n, None)
        if v:
            return float(v)
    return None


def fetch_quotes(tickers: list[str]) -> dict[str, dict]:
    """Fetch a live quote snapshot for each ticker.

    Returns {ticker: {price_gbp, prev_close_gbp, currency, ts}}.
    """
    import yfinance as yf

    out: dict[str, dict] = {}
    t0 = time.time()

    for tk in tickers:
        try:
            fi = yf.Ticker(tk).fast_info
            price = _fi_get(fi, "lastPrice", "last_price")
            prev = _fi_get(fi, "previousClose", "regularMarketPreviousClose", "previous_close")
            ccy = None
            try:
                ccy = fi["currency"]
            except (KeyError, TypeError):
                ccy = getattr(fi, "currency", None)
            if price is None:
                _audit("fetch_quotes", [tk], "empty")
                continue
            # Quote-currency handling: everything is normalised to GBP.
            #   GBp (LSE)  -> /100
            #   GBP        -> as-is
            #   other ccy  -> x spot GBP-per-unit rate
            # Indices (^) are points, not currency: pass through untouched.
            ccy_u = (ccy or "").upper()
            is_index = tk.startswith("^")
            is_gbx = ccy_u in {"GBP", "GBX"} and not is_index
            if is_index:
                fx = None
                price_gbp = float(price)
            elif ccy_u in {"GBP", "GBX"}:
                fx = None
                price_gbp = _gbp(price)
            else:
                fx = fx_to_gbp(ccy_u)
                price_gbp = float(price) * fx
            prev_gbp = None
            if prev:
                if is_index:
                    prev_gbp = float(prev)
                elif fx:
                    prev_gbp = float(prev) * fx
                else:
                    prev_gbp = _gbp(prev)
            out[tk] = {
                "price_gbp": price_gbp,
                "prev_close_gbp": prev_gbp,
                "currency": "index" if is_index else ccy_u or "n/a",
                "fx_to_gbp": round(fx, 6) if fx else None,
                "source": "Yahoo Finance (yfinance fast_info)",
                "ts": _now_utc(),
            }
        except Exception as exc:  # noqa: BLE001
            _audit("fetch_quotes", [tk], "error", {"error": str(exc)})

    _audit(
        "fetch_quotes",
        tickers,
        "ok" if out else "empty",
        {"n": len(out), "elapsed_s": round(time.time() - t0, 2)},
    )
    return out


def fetch_info(ticker: str) -> dict:
    """Fetch fundamental info for one ticker (cached to disk)."""
    import yfinance as yf

    cdir = _cache_dir()
    cdir.mkdir(parents=True, exist_ok=True)
    cfile = cdir / f"info_{ticker.replace('.', '_')}.json"

    if cfile.exists():
        age_s = time.time() - cfile.stat().st_mtime
        if age_s < 6 * 3600:  # fundamentals are slow-moving; 6h cache
            try:
                return json.loads(cfile.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as exc:  # noqa: BLE001
        _audit("fetch_info", [ticker], "error", {"error": str(exc)})
        return {}

    keep = {
        k: info[k]
        for k in (
            "shortName",
            "longName",
            "currency",
            "marketCap",
            "trailingPE",
            "forwardPE",
            "dividendYield",
            "beta",
            "bookValue",
            "priceToBook",
            "enterpriseValue",
            "ebitda",
            "totalRevenue",
            "freeCashflow",
            "totalCash",
            "totalDebt",
            "sharesOutstanding",
            "fiftyTwoWeekHigh",
            "fiftyTwoWeekLow",
            "trailingEps",
            "sector",
            "industry",
        )
        if k in info
    }
    keep["_fetched_at"] = _now_utc()
    keep["_source"] = "Yahoo Finance via yfinance Ticker.info"

    _audit("fetch_info", [ticker], "ok" if keep else "empty", {"keys": len(keep)})
    try:
        cfile.write_text(json.dumps(keep, default=str), encoding="utf-8")
    except OSError:
        pass
    return keep


def save_snapshot(quotes: dict[str, dict]) -> None:
    """Persist the latest quote snapshot (used by the dashboard)."""
    path = _snapshot_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    prev = {}
    if path.exists():
        try:
            prev = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = {}
    prev.update(quotes)
    prev["_updated_at"] = _now_utc()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(prev, default=str), encoding="utf-8")
    tmp.replace(path)


def load_snapshot() -> dict:
    path = _snapshot_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
