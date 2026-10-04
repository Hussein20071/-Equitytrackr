"""Performance attribution vs FTSE 100: per-note tracking, monthly
attribution, volatility, max drawdown, and hit-rate statistics.

The tracked window for each note runs from the first daily close on or
after the note's thesis date (falling back to the last close before it,
for notes published on non-trading days) through the latest close.
Values in GBP.
"""

from __future__ import annotations

import math
from datetime import datetime

import pandas as pd

from . import config


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)


def _window(hist: pd.DataFrame, ticker: str, start: datetime) -> pd.DataFrame | None:
    nh = hist[hist["Ticker"] == ticker].sort_values("Date")
    if nh.empty:
        return None
    after = nh[nh["Date"] >= pd.Timestamp(start.date())]
    if after.empty:
        before = nh[nh["Date"] <= pd.Timestamp(start.date())]
        if before.empty:
            return None
        base_date = before["Date"].iloc[-1]
        return nh[nh["Date"] >= base_date]
    return after


def _tracking_start(note: dict) -> datetime | None:
    """When did the live record for this note start?

    The FIRST publication date: corrections re-freeze inputs but do not
    reset the clock -- the track record stays continuous and the revision
    is visible in the note's addenda and published_at (revision date).
    """
    pub = (note.get("first_published_at") or note.get("published_at")
           or note.get("created_at"))
    return _parse(pub) if pub else None


def note_performance(note: dict, hist: pd.DataFrame, bench: pd.DataFrame) -> dict | None:
    """Live-record performance of one note vs the benchmark.

    Window: from the first daily close on or after the note's FIRST
    publication date (falling back to the last close before it, for notes
    published on non-trading days) through the latest close. Both window
    endpoints are returned so every figure can be date-stamped on screen.
    Values in GBP.
    """
    start = _tracking_start(note)
    if not start:
        return None

    tk = note["ticker"]
    nh = _window(hist, tk, start)
    if nh is None or len(nh) < 1:
        return None

    base_date = nh["Date"].iloc[0]
    base_px = float(nh["Close_gbp"].iloc[0])
    last_px = float(nh["Close_gbp"].iloc[-1])
    last_date = nh["Date"].iloc[-1]

    bh = bench.sort_values("Date")
    bh = bh[(bh["Date"] >= base_date) & (bh["Date"] <= last_date)]
    if bh.empty:
        return None
    b0 = float(bh["Close_gbp"].iloc[0])
    b1 = float(bh["Close_gbp"].iloc[-1])

    ret = last_px / base_px - 1
    bret = b1 / b0 - 1
    days = (last_date - base_date).days

    vol = annualized_vol(nh["Close_gbp"])
    mdd = max_drawdown(nh["Close_gbp"])

    return {
        "ticker": tk,
        "thesis_date": str(base_date.date()),
        "end_date": str(last_date.date()),
        "days_tracked": days,
        "trading_days": len(nh),
        "base_price": round(base_px, 2),
        "last_price": round(last_px, 2),
        "return_pct": round(ret * 100, 2),
        "bench_base": round(b0, 2),
        "bench_last": round(b1, 2),
        "bench_return_pct": round(bret * 100, 2),
        "alpha_pct": round((ret - bret) * 100, 2),
        "ann_vol_pct": vol,
        "max_drawdown_pct": mdd,
        "in_window": 0 < days <= 92,
        "pt": note.get("price_target_gbp",
                       note.get("valuation_inputs", {}).get("blended_target")),
        "rec": note.get("recommendation"),
    }


def annualized_vol(closes: pd.Series) -> float | None:
    """Annualised volatility of daily returns (percent)."""
    s = pd.Series(closes).astype(float).pct_change().dropna()
    if len(s) < 2:
        return None
    return round(float(s.std() * (252 ** 0.5) * 100), 2)


def max_drawdown(closes: pd.Series) -> float | None:
    """Max drawdown over the window (negative percent, 0 = no drawdown)."""
    s = pd.Series(closes).astype(float)
    if len(s) < 2:
        return None
    dd = s / s.cummax() - 1.0
    return round(float(dd.min()) * 100, 2)


def monthly_attribution(note: dict, hist: pd.DataFrame, bench: pd.DataFrame) -> list[dict]:
    """Calendar-month return vs benchmark since the note's first publication.

    Returns [{month, stock_pct, bench_pct, alpha_pct}] oldest first.
    """
    pub = note.get("published_at") or note.get("created_at")
    if not pub:
        return []
    nh = _window(hist, note["ticker"], _parse(pub))
    if nh is None or nh.empty:
        return []
    bh = bench.sort_values("Date")

    rows = []
    months = sorted(set(nh["Date"].dt.strftime("%Y-%m")))
    for m in months:
        mh = nh[nh["Date"].dt.strftime("%Y-%m") == m]
        if mh.empty:
            continue
        s0, s1 = float(mh["Close_gbp"].iloc[0]), float(mh["Close_gbp"].iloc[-1])
        mb = bh[(bh["Date"] >= mh["Date"].iloc[0]) & (bh["Date"] <= mh["Date"].iloc[-1])]
        if mb.empty:
            continue
        b0, b1 = float(mb["Close_gbp"].iloc[0]), float(mb["Close_gbp"].iloc[-1])
        sp, bp = (s1 / s0 - 1) * 100, (b1 / b0 - 1) * 100
        rows.append({
            "month": m,
            "stock_pct": round(sp, 2),
            "bench_pct": round(bp, 2),
            "alpha_pct": round(sp - bp, 2),
        })
    return rows


def note_series(note: dict, hist: pd.DataFrame, bench: pd.DataFrame,
                max_points: int = 40) -> list[dict] | None:
    """Normalised stock vs FTSE series since the note's thesis date.

    Both series indexed to 100 at the first tracked close, downsampled to
    at most ``max_points`` for embedding as inline JSON in note pages.
    Returns None when there is no tracked data yet.
    """
    pub = note.get("published_at") or note.get("created_at")
    if not pub:
        return None
    nh = _window(hist, note["ticker"], _parse(pub))
    if nh is None or nh.empty:
        return None
    bh = bench.sort_values("Date")
    b0_date = nh["Date"].iloc[0]
    bh = bh[(bh["Date"] >= b0_date) & (bh["Date"] <= nh["Date"].iloc[-1])]
    if bh.empty:
        return None

    s = nh.set_index("Date")["Close_gbp"].astype(float)
    b = bh.set_index("Date")["Close_gbp"].astype(float)
    idx = s.index.union(b.index)
    s = s.reindex(idx).ffill().dropna()
    b = b.reindex(idx).ffill().dropna()
    common = s.index.intersection(b.index)
    s, b = s.loc[common], b.loc[common]
    if len(common) < 2:
        return None

    sn = (s / s.iloc[0] * 100.0)
    bn = (b / b.iloc[0] * 100.0)
    step = max(1, math.ceil(len(common) / max_points))
    sel = list(range(0, len(common), step))
    if sel[-1] != len(common) - 1:
        sel.append(len(common) - 1)
    return [
        {
            "date": str(common[i].date()),
            "stock": round(float(sn.iloc[i]), 2),
            "bench": round(float(bn.iloc[i]), 2),
        }
        for i in sel
    ]


def performance_caption(summary: dict, curve: list[dict], label: str = "Live record") -> str:
    """One-sentence, date-stamped summary of model-portfolio performance."""
    n = summary.get("n", 0) if summary else 0
    days = len(curve or [])
    if not n or days < 2:
        return ("Track record accrues daily; the first trading days are "
                "shown below.")
    start, end = curve[0]["date"], curve[-1]["date"]
    p0, p1 = curve[0]["portfolio"], curve[-1]["portfolio"]
    b0, b1 = curve[0]["benchmark"], curve[-1]["benchmark"]
    ret, bret = p1 - 100.0, b1 - 100.0
    rel = "ahead of" if ret > bret else ("behind" if ret < bret else "in line with")
    hit = summary.get("hit_rate_pct")
    return (
        f"{label}: model portfolio {ret:+.1f}% vs FTSE 100 {bret:+.1f}% "
        f"over {days} trading days ({start} to {end}; {rel} benchmark by "
        f"{abs(ret - bret):.1f}pp); {n} note{'s' if n != 1 else ''} tracked "
        f"since first publication, hit rate {hit:.0f}%; "
        "static weights, no rebalancing."
    )


def portfolio_curve(hist: pd.DataFrame, bench: pd.DataFrame,
                    months: int | None = 3,
                    since: str | datetime | None = None) -> list[dict]:
    """Daily model-portfolio value vs benchmark over a window.

    Static weights from config.PORTFOLIO renormalised over available
    tickers; no rebalancing (buy-and-hold: each position compounds from
    its start-of-window weight share).

    Window: ``since`` (a date string) for the live-record window, or the
    trailing ``months`` for the backtest window. Callers must label which
    window they are showing -- the two are never mixed on screen.
    """
    if since is not None:
        cutoff = pd.Timestamp(since).tz_localize(None)
    else:
        months = months or 3
        cutoff = pd.Timestamp.utcnow().tz_localize(None) - pd.DateOffset(months=months)
    sub = hist[hist["Date"] >= cutoff]
    if sub.empty:
        return []

    weights = {t: w for t, w in config.PORTFOLIO.items() if t in set(sub["Ticker"])}
    wsum = sum(weights.values())
    weights = {t: w / wsum for t, w in weights.items()} if wsum else {}

    piv = sub.pivot_table(index="Date", columns="Ticker", values="Close_gbp").sort_index()
    piv = piv.ffill()
    norm = piv / piv.iloc[0] * 100.0

    bsub = bench[bench["Date"] >= cutoff].sort_values("Date")
    if bsub.empty:
        return []
    bnorm = bsub.set_index("Date")["Close_gbp"]
    bnorm = bnorm / bnorm.iloc[0] * 100.0

    curve = []
    for d in norm.index.intersection(bnorm.index):
        port = sum(w * norm.loc[d, t] for t, w in weights.items())
        curve.append({
            "date": str(d.date()),
            "portfolio": round(port, 2),
            "benchmark": round(float(bnorm.loc[d]), 2),
        })
    return curve


def portfolio_metrics(curve: list[dict], rf: float | None = None) -> dict:
    """Risk/return statistics computed ON the portfolio return series.

    These are series-level statistics (the daily returns of the whole
    £100k model portfolio), never an average of individual stock stats.
    Total return is measured from the £100 index base, so the stated
    inception transaction-cost drag (the curve starts at 99.4 net) is
    included — the investor-realised figure, matching the chart caption.
    Formulas (also shown in the site methodology):
      daily returns   r_t = V_t / V_{t-1} - 1
      ann. volatility  = std(r) x sqrt(252)          (sample std, ddof=1)
      max drawdown     = min over t of V_t / max(V_0..V_t) - 1
      beta vs FTSE     = cov(r_p, r_b) / var(r_b)
      tracking error   = std(r_p - r_b) x sqrt(252)
      total return     = V_last / 100 - 1   (100 = gross index base)
      ann. return (CAGR) = (1 + total_return)^(252 / n_obs) - 1
      Sharpe           = (CAGR - risk-free) / ann. volatility
    """
    if not curve or len(curve) < 3:
        return {}
    v = pd.Series([c["portfolio"] for c in curve], dtype=float)
    b = pd.Series([c["benchmark"] for c in curve], dtype=float)
    rp = v.pct_change().dropna()
    rb = b.pct_change().dropna()
    n = len(curve)
    total_return = float(v.iloc[-1] / 100.0 - 1)
    ann_return = (1 + total_return) ** (252 / n) - 1 if n > 0 else None
    bench_total = float(b.iloc[-1] / 100.0 - 1)
    bench_ann = (1 + bench_total) ** (252 / n) - 1 if n > 0 else None
    aligned = pd.concat([rp, rb.reindex(rp.index)], axis=1).dropna()
    ann_vol = float(rp.std(ddof=1) * (252 ** 0.5)) if len(rp) > 1 else None
    mdd = float((v / v.cummax() - 1.0).min())
    beta = te = None
    if len(aligned) > 1:
        var_b = float(aligned.iloc[:, 1].var(ddof=1))
        if var_b > 0:
            beta = float(aligned.iloc[:, 0].cov(aligned.iloc[:, 1]) / var_b)
        te = float((aligned.iloc[:, 0] - aligned.iloc[:, 1]).std(ddof=1) * (252 ** 0.5))
    sharpe = None
    if ann_vol and ann_vol > 0 and rf is not None:
        sharpe = round((ann_return - rf) / ann_vol, 2)
    return {
        "n_obs": n,
        "total_return_pct": round(total_return * 100, 2),
        "ann_return_pct": round(ann_return * 100, 2) if ann_return is not None else None,
        "bench_total_return_pct": round(bench_total * 100, 2),
        "bench_ann_return_pct": round(bench_ann * 100, 2) if bench_ann is not None else None,
        "ann_vol_pct": round(ann_vol * 100, 2) if ann_vol is not None else None,
        "max_drawdown_pct": round(mdd * 100, 2),
        "beta_vs_bench": round(beta, 2) if beta is not None else None,
        "tracking_error_pct": round(te * 100, 2) if te is not None else None,
        "sharpe": sharpe,
        "rf": rf,
    }


def summarize(perf_rows: list[dict]) -> dict:
    """Hit-rate and risk statistics across tracked notes.

    Two distinct metrics, defined once and displayed verbatim on the site:
      hit rate            = share of notes with alpha > 0 vs FTSE 100
      directional accuracy = share of calls where price moved the way the
                             recommendation said (BUY up / SELL down /
                             HOLD within +/-10%) over the same window
    """
    rows = [r for r in perf_rows if r]
    n = len(rows)
    if not n:
        return {"n": 0}
    wins = [r for r in rows if r["alpha_pct"] > 0]
    direction_correct = [
        r for r in rows
        if (r["rec"] == "BUY" and r["return_pct"] > 0)
        or (r["rec"] == "SELL" and r["return_pct"] < 0)
        or (r["rec"] == "HOLD" and abs(r["return_pct"]) <= 10)
    ]
    pt_hits = [
        r for r in rows if r["pt"] and (
            (r["rec"] == "BUY" and r["last_price"] >= r["pt"])
            or (r["rec"] == "SELL" and r["last_price"] <= r["pt"])
        )
    ]
    vols = [r["ann_vol_pct"] for r in rows if r.get("ann_vol_pct") is not None]
    mdds = [r["max_drawdown_pct"] for r in rows if r.get("max_drawdown_pct") is not None]
    starts = [r["thesis_date"] for r in rows if r.get("thesis_date")]
    ends = [r["end_date"] for r in rows if r.get("end_date")]
    return {
        "n": n,
        "hit_rate_pct": round(100 * len(wins) / n, 1),
        "directional_accuracy_pct": round(100 * len(direction_correct) / n, 1),
        "pt_hit_pct": round(100 * len(pt_hits) / n, 1),
        "avg_alpha_pct": round(sum(r["alpha_pct"] for r in rows) / n, 2),
        "avg_return_pct": round(sum(r["return_pct"] for r in rows) / n, 2),
        "avg_ann_vol_pct": round(sum(vols) / len(vols), 2) if vols else None,
        "worst_drawdown_pct": min(mdds) if mdds else None,
        "total_trading_days": sum(r.get("trading_days", 0) for r in rows),
        "window_start": min(starts) if starts else None,
        "window_end": max(ends) if ends else None,
        "best": max(rows, key=lambda r: r["alpha_pct"])["ticker"],
        "worst": min(rows, key=lambda r: r["alpha_pct"])["ticker"],
    }
