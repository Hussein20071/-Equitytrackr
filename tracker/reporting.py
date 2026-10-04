"""Audit-ready HTML generation: dashboard + per-note pages.

Design: recruiter-first. Scannable headline cards, recommendation-coded
colour system, sparkline price paths, one-sentence performance captions,
one-click PDF (print stylesheet) and copy-link on every note. All pages
are static files regenerated every refresh cycle.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from . import audit, config, portfolio, scenario, valuation

DASH_FILE = Path(config.DASHBOARD_PATH)
NOTES_HTML_DIR = Path(config.NOTES_DIR) / "html"
NOTES_DIR = Path(config.NOTES_DIR)
SNAPSHOTS_DIR = NOTES_DIR / "snapshots"
PUBLISH_DIR = Path("publish")  # deployable static-site bundle (Pages root)

CAPTION_NOTHING = "Static weights, no rebalancing."

_RAW_FLOAT_RE = re.compile(
    r"(?<![\w.])(-?\d+\.\d{4,})(?=\b)"  # >=4 decimals with no thousands sep
)


def _round_raw_floats(text: str) -> str:
    """Display-side hygiene: round raw float artefacts in prose to 2dp.

    Frozen note JSON keeps full precision; only rendering tidies up.
    """
    return _RAW_FLOAT_RE.sub(lambda m: f"{float(m.group(1)):.2f}", text)

# Recommendation colour system (used across dashboard + notes)
REC_STYLES = {
    "BUY": {"bg": "#ecfdf5", "fg": "#047857", "border": "#10b981", "label": "BUY"},
    "HOLD": {"bg": "#eef2ff", "fg": "#4338ca", "border": "#6366f1", "label": "HOLD"},
    "SELL": {"bg": "#fef2f2", "fg": "#b91c1c", "border": "#ef4444", "label": "SELL"},
}


def _esc(s) -> str:
    return html.escape(str(s))


def _fmt_pct(x) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return '<span class="zero">–</span>'
    cls = "pos" if v > 0 else ("neg" if v < 0 else "zero")
    return f'<span class="{cls}">{v:+.2f}%</span>'


def _fmt_num(x, nd=2) -> str:
    try:
        return f"{float(x):,.{nd}f}"
    except (TypeError, ValueError):
        return "–"


def _badge(rec: str | None) -> str:
    st = REC_STYLES.get(rec or "", REC_STYLES["HOLD"])
    return f'<span class="badge" style="background:{st["bg"]};color:{st["fg"]}">{_esc(st["label"])}</span>'


def _note_filename(ticker: str) -> str:
    return ticker.lower().replace(".", "-").replace("^", "") + ".html"


def _sparkline_svg(series: list[dict], w=180, h=44, color="#0f3460") -> str:
    """Tiny inline SVG of the stock's normalised path vs a soft baseline."""
    if not series or len(series) < 2:
        return '<span class="muted">no chart yet</span>'
    vals = [p["stock"] for p in series]
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    step = w / (len(vals) - 1)
    pts = " ".join(
        f"{i * step:.1f},{h - 4 - (v - lo) / rng * (h - 8):.1f}"
        for i, v in enumerate(vals)
    )
    start = h - 4 - (vals[0] - lo) / rng * (h - 8)
    return (
        f'<svg width="{w}" height="{h}" class="spark">'
        f'<line x1="0" y1="{start:.1f}" x2="{w}" y2="{start:.1f}" '
        f'stroke="#cbd5e1" stroke-dasharray="3,3"/>'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.8"/>'
        f"</svg>"
    )


def _window_progress(days_tracked: int, months: int = 3) -> str:
    """Progress bar of the 3-month review window (92 days)."""
    total = months * 30.4
    pct = min(100.0, max(0.0, days_tracked / total * 100))
    return (
        f'<div class="winbar" title="{days_tracked} of ~{int(total)} days tracked">'
        f'<div class="winfill" style="width:{pct:.0f}%"></div></div>'
        f'<span class="muted" style="font-size:11px">{days_tracked}/~{int(total)}d</span>'
    )


def _qrows(quotes: dict) -> list[dict]:
    rows = []
    for tk, q in sorted((quotes or {}).items()):
        if tk.startswith("_"):
            continue
        last, prev = q.get("price_gbp"), q.get("prev_close_gbp")
        chg = ((last / prev - 1) * 100 if (last and prev) else None)
        is_index = tk.startswith("^")
        rows.append({
            "ticker": tk,
            "name": ("FTSE 100 (index points)" if is_index
                     else config.UNIVERSE.get(tk, tk)),
            "price": _fmt_num(last),
            "pence": ("" if is_index else f"{_fmt_num(last * 100)}p"),
            "chg_html": _fmt_pct(chg),
        })
    return rows


def _qtable(qrows: list[dict]) -> str:
    """Market snapshot table showing GBP and GBp (pence) side by side."""
    body = "".join(
        f"<tr><td><strong>{_esc(r['ticker'])}</strong></td>"
        f"<td>{_esc(r['name'])}</td>"
        f"<td>GBP {_esc(r['price'])}</td>"
        f"<td>{_esc(r.get('pence') or '')}</td>"
        f"<td>{r['chg_html']}</td></tr>"
        for r in qrows
    )
    return ('<tr><th>TICKER</th><th>NAME</th><th>PRICE (£)</th>'
            '<th>QUOTED (GBp)</th><th>DAY</th></tr>' + body)


def _portfolio_weights_table(weights_table: dict) -> str:
    """Explicit £100k holdings table: position £ and %, sector, price."""
    if not weights_table:
        return ""
    rows = "".join(
        f"<tr><td><strong>{_esc(r['ticker'])}</strong></td>"
        f"<td>{_esc(r['name'])}</td>"
        f"<td>{_esc(r['sector'])}</td>"
        f"<td>{r['weight_pct']}%</td>"
        f"<td>£{_fmt_num(r['position_gbp'])}</td>"
        f"<td>{_fmt_num(r.get('price_gbp'))}</td>"
        f"<td>{_fmt_num(r.get('approx_shares'), 0)}</td>"
        f"<td>£{_fmt_num(r.get('buy_cost_gbp'))}</td></tr>"
        for r in weights_table.get("rows", [])
    )
    return (
        f"<table><tr><th>Ticker</th><th>Name</th><th>Sector</th><th>Weight</th>"
        f"<th>Position (£100k notional)</th><th>Price (GBP)</th><th>~Shares</th>"
        f"<th>One-off buy cost</th></tr>{rows}</table>"
        f'<p class="muted">{_esc(weights_table.get("cost_assumption", ""))} '
        f"Total one-off buy cost £{_fmt_num(weights_table.get('total_buy_cost_gbp'))} "
        f"on £{_fmt_num(weights_table.get('notional_gbp'), 0)} notional. "
        f"{_esc(weights_table.get('return_basis', ''))}</p>"
    )


def _sector_chart_html(sector_mix: dict, ftse_sectors: dict | None) -> str:
    """Model portfolio sector mix vs FTSE 100 sector weights (side by side)."""
    if not sector_mix:
        return ""
    fw = (ftse_sectors or {}).get("weights") or {}
    as_of = (ftse_sectors or {}).get("as_of", "")[:10]
    src = (ftse_sectors or {}).get("source", "")
    sectors = sorted(set(list(sector_mix.keys()) + list(fw.keys())),
                     key=lambda s: -sector_mix.get(s, 0))
    rows = "".join(
        f"<tr><td>{_esc(s)}</td>"
        f"<td>{sector_mix.get(s, 0) * 100:.1f}%</td>"
        + (f"<td>{fw[s] * 100:.1f}%</td>" if s in fw else "<td>–</td>")
        + "</tr>"
        for s in sectors
    )
    note_html = (
        f'<p class="muted">FTSE 100 sector weights: {_esc(src)} '
        f"(as of {as_of}). </p>" if fw else
        '<p class="muted">FTSE 100 sector comparison omitted: the cached '
        "constituent-sector file is missing or stale — refresh it with "
        "<code>python -m tracker.cli sectors</code>. The portfolio mix is "
        "shown alone rather than compared against an invented benchmark.</p>"
    )
    return (
        '<table><tr><th>ICB supersector</th><th>Model portfolio</th>'
        + ("<th>FTSE 100</th>" if fw else "") + "</tr>" + rows + "</table>"
        + note_html
    )


def _portfolio_metrics_html(label: str, m: dict, curve: list[dict],
                            rf_prov: str = "") -> str:
    """Series-level risk metrics block, date-stamped and labelled."""
    if not m or not curve:
        return (f'<p class="muted">{label}: not yet computable — needs more '
                "trading days in the window.</p>")
    start, end = curve[0]["date"], curve[-1]["date"]
    rows = [
        ("Total return (net of costs)", f"{m['total_return_pct']:+.2f}%"),
        ("FTSE 100 total return", f"{m['bench_total_return_pct']:+.2f}%"),
        ("Annualised return (CAGR)", f"{m['ann_return_pct']:+.2f}%"),
        ("Annualised volatility", f"{m['ann_vol_pct']:.2f}%"),
        ("Max drawdown", f"{m['max_drawdown_pct']:.2f}%"),
        ("Beta vs FTSE 100", _fmt_num(m.get("beta_vs_bench"))),
        ("Tracking error (ann.)", f"{m.get('tracking_error_pct'):.2f}%"
         if m.get("tracking_error_pct") is not None else "–"),
        ("Sharpe ratio", _fmt_num(m.get("sharpe"))),
    ]
    body = "".join(
        f"<tr><td>{_esc(k)}</td><td>{v}</td></tr>" for k, v in rows
    )
    rf_line = f" Risk-free: {_esc(rf_prov)}." if rf_prov else ""
    return (
        f"<h4>{_esc(label)} — {start} to {end} ({m['n_obs']} trading days, "
        f"hypothetical £100k portfolio)</h4>"
        f"<table>{body}</table>"
        f'<p class="muted">Computed on the portfolio return series (not an '
        "average of stock-level stats). Total-return basis (adjusted close, "
        "dividends reinvested), net of the stated inception costs. Sharpe uses "
        "the UK short rate."
        f"{rf_line}</p>"
    )


def _about_html() -> str:
    """About section: who, why, tools, limitations."""
    return """
<div class="card" id="about">
  <h2 style="margin-top:0">About</h2>
  <p><strong>Hussein Mohamed</strong> — King's College London student and aspiring
  asset-management professional. I built this site to demonstrate the working
  habits the buy side actually runs on: research notes with frozen, sourced
  inputs; an append-only audit trail; a tracked record with honest dates; and
  corrections that are dated addenda, never silent edits.</p>
  <p><strong>Why built:</strong> a CV claim like "I follow UK equities" is not
  verifiable; a site that shows every input, formula, fetch, and mistake is.
  The notes are generated systematically from live public data — my contribution
  is the methodology, the guardrails, and the discipline of publishing results
  (good and bad) with their dates.</p>
  <p><strong>Tools:</strong> Python (yfinance, pandas, pytest), FRED (gilt yields),
  Damodaran (ERP), GitHub Actions (refresh + deploy every 5 minutes in market
  hours), GitHub Pages.</p>
  <p><strong>Known limitations:</strong> fundamentals come from Yahoo Finance and
  may be delayed or restated; the universe is 8 large-caps, not the full FTSE 100;
  the model portfolio is notional £100,000 with stated (not real) transaction
  costs; ESG data is absent for some names and disclosed as such; the track record
  is short and means nothing statistically yet. Nothing here is investment advice.</p>
</div>"""


def _perf_rows_html(perf_rows: list[dict], series_by_ticker: dict,
                    quotes: dict | None = None) -> str:
    if not perf_rows:
        return '<tr><td colspan="10" class="muted">No published notes yet.</td></tr>'
    out = []
    for r in perf_rows:
        slug = _note_filename(r["ticker"]).replace(".html", "")
        spark = _sparkline_svg(series_by_ticker.get(r["ticker"]) or [])
        q = (quotes or {}).get(r["ticker"]) or {}
        day_chg = ((q.get("price_gbp") / q.get("prev_close_gbp") - 1) * 100
                   if (q.get("price_gbp") and q.get("prev_close_gbp")) else None)
        hot = " class=\"hot\"" if (day_chg is not None and abs(day_chg) >= 2.0) else ""
        out.append(
            f"<tr{hot}>"
            f'<td><a href="#note-{slug}"><strong>{_esc(r["ticker"])}</strong></a></td>'
            f"<td>{_fmt_pct(day_chg)}</td>"
            f"<td>{_esc(r['thesis_date'])}</td>"
            f"<td>{_fmt_num(r['base_price'])} → {_fmt_num(r['last_price'])}</td>"
            f"<td>{spark}</td>"
            f"<td>{_fmt_pct(r['return_pct'])}</td>"
            f"<td>{_fmt_pct(r['alpha_pct'])}</td>"
            f"<td>{_fmt_pct(r.get('ann_vol_pct'))}</td>"
            f"<td>{_fmt_pct(r.get('max_drawdown_pct'))}</td>"
            f"<td>{_badge(r.get('rec'))}</td>"
            "</tr>"
        )
    return "".join(out)


def _guardrail_banner(note: dict) -> str:
    """Red banner when the blended target breaches the +/-30% guardrail."""
    g = note.get("model_checks") or {}
    if not g.get("is_outlier"):
        return ""
    driver = g.get("driver_leg") or "n/a"
    contrib = g.get("driver_contribution_pct")
    dev = g.get("deviation_pct")
    leg_devs = g.get("leg_deviation_pct") or {}
    legs_txt = " ".join(
        f"{k} {v:+.0f}%" for k, v in leg_devs.items()
    ) or "no legs"
    return (
        '<div class="guard-box"><b>Model outlier &mdash; under review.</b> '
        f"The blended target is {dev:+.1f}% vs the market price, beyond the "
        f"±30% guardrail. Driver: the <b>{_esc(driver)}</b> leg "
        + (f"(weighted contribution {_esc(f'{contrib:+.0f}pp')} of the gap). " if contrib is not None else ". ")
        + f"Leg deviations vs price: {_esc(legs_txt)}. "
        "Read the note as a model-vs-market disagreement, not a trade "
        "recommendation; see the reverse DCF for what the market price "
        "implies instead.</div>"
    )


def _reverse_dcf_html(note: dict, current_price: float | None) -> str:
    """Reverse DCF: what growth does the CURRENT price imply?"""
    v = note.get("valuation_inputs") or {}
    dcf = v.get("dcf") or {}
    res = dcf.get("result") or {}
    if not res.get("value_per_share"):
        return ""
    base = dcf.get("base_fcf_used_m") or dcf.get("base_fcf_m")
    r = valuation.reverse_dcf_growth(
        base, dcf.get("wacc"), dcf.get("net_debt_m"),
        dcf.get("shares_m"), current_price or 0.0,
    )
    if r.get("g_implied") is None:
        return (f'<p class="muted">Reverse DCF: {_esc(r.get("detail") or "unavailable")}.</p>')
    g = r["g_implied"]
    return (
        f'<p><b>Reverse DCF:</b> at the frozen WACC ({dcf.get("wacc"):.2%}), '
        f"the current price of GBP {_fmt_num(current_price)} implies "
        f"<b>{g:.1%} FCF growth in perpetuity</b> (years 1-5 and terminal). "
        f"Compare with the published growth path {_esc(dcf.get('fcf_growth_path'))}. "
        f"<span class='muted'>{_esc(r['detail'])}</span></p>"
    )


def _sensitivity_grid_html(note: dict) -> str:
    """5x5 DCF sensitivity: WACC rows x terminal growth columns."""
    grid = scenario.sensitivity_grid(note)
    if not grid:
        return ""
    tgs = grid["tg_steps"]
    head = "<tr><th>WACC \\ g</th>" + "".join(
        f"<th>{tg0 * 100:+.2f}pp</th>" for tg0 in tgs
    ) + "</tr>"
    rows = ""
    for r in grid["rows"]:
        cells = "".join(
            f"<td>{_fmt_num(c)}</td>" if c is not None else "<td>–</td>"
            for c in r["cells"]
        )
        rows += f"<tr><td><strong>{r['wacc']:.2%}</strong> ({r['wacc_shock'] * 100:+.1f}pp)</td>{cells}</tr>"
    return (
        '<div class="sens-box"><h3>DCF sensitivity: WACC × terminal growth '
        "(5×5, frozen inputs, DCF leg only)</h3>"
        f'<p class="muted">Each cell re-derives the DCF value per share (GBP) '
        "from the frozen inputs at that WACC and terminal-growth offset; the "
        "centre row/column pair at 0.0/0.0 is the published DCF leg.</p>"
        f"<table>{head}{rows}</table></div>"
    )


def _bull_base_bear_html(note: dict) -> str:
    """Bull / base / bear with a price and the key assumption each."""
    cases = scenario.bull_base_bear(note)
    if not cases:
        return ""
    cls = {"Bull": "pos", "Bear": "neg", "Base": "zero"}
    rows = "".join(
        f"<tr><td><strong class='{cls.get(c['case'], '')}'>{c['case']}</strong></td>"
        f"<td>{_fmt_num(c.get('price'))}</td>"
        f"<td>{_fmt_pct(c.get('upside_pct')) if c.get('upside_pct') is not None else '<span class=zero>–</span>'}</td>"
        f"<td>{_esc(c['assumption'])}</td></tr>"
        for c in cases
    )
    return (
        '<h3>Bull / base / bear (same frozen inputs, one assumption moved)</h3>'
        f"<table><tr><th>Case</th><th>Price (GBP)</th><th>vs pub. price</th>"
        f"<th>Key assumption</th></tr>{rows}</table>"
    )


def _esg_html(note: dict) -> str:
    """2-3 line ESG / stewardship note from the feed's risk scores."""
    e = note.get("esg") or {}
    tk = note.get("ticker", "")
    if e.get("total_esg") is None:
        return (
            '<h3>ESG / stewardship</h3>'
            '<p class="muted">No ESG risk score available on the data feed for '
            f"{_esc(tk)} — omitted rather than estimated. Valuation impact: "
            "none modelled; any ESG-driven cash-flow or discount-rate effect "
            "is outside the frozen inputs.</p>"
        )
    t, env, soc, gov = (e.get("total_esg"), e.get("environment"),
                        e.get("social"), e.get("governance"))
    return (
        '<h3>ESG / stewardship</h3>'
        f"<p><b>Sustainalytics ESG risk score {t:.1f}</b> (lower = less risk; "
        f"environment {env:.1f} / social {soc:.1f} / governance {gov:.1f}). "
        "The score is a risk read, not a valuation input: it is disclosed so a "
        "reader can judge whether unmodelled ESG risk justifies a wider or "
        "narrower discount to the published target. No stewardship activity is "
        "claimed — this is a personal educational project with no assets under "
        "management.</p>"
    )


def _kpi_color(v) -> str:
    """Shared pos/neg/zero class so raw cells colour-match _fmt_pct spans."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "zero"
    return "pos" if x > 0 else ("neg" if x < 0 else "zero")


def _movers_strip(qrows: list[dict]) -> str:
    """At-a-glance day movers: one chip per ticker, coloured by sign."""
    chips = []
    for r in qrows:
        m = re.search(r"([+-][\d.]+)%", r.get("chg_html") or "")
        if not m:
            continue
        pct = float(m.group(1))
        cls = "up" if pct > 0 else ("down" if pct < 0 else "flat")
        arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "•")
        chips.append(
            f'<span class="mover {cls}"><b>{_esc(r["ticker"]).replace(".L", "")}</b> '
            f'{arrow} {pct:+.2f}%</span>'
        )
    if not chips:
        return ""
    return '<div class="movers"><span class="movers-label">Day movers</span>' \
        + "".join(chips) + "</div>"


def _change_line(changes: dict | None) -> str:
    """One honest line: what actually changed in the latest refresh cycle."""
    if not changes:
        return ('<div class="muted" style="margin:4px 0 0;font-size:12.5px">'
                "First refresh this session — cycle-over-cycle change tracking "
                "starts with the next refresh.</div>")
    movers = changes.get("movers") or []
    if not movers:
        return ('<div class="muted" style="margin:4px 0 0;font-size:12.5px">'
                "Latest refresh: every quote within 0.05% of the previous "
                "cycle — no meaningful moves.</div>")
    return ('<div class="muted" style="margin:4px 0 0;font-size:12.5px">'
            "Since the previous refresh: " + _esc(" · ".join(movers)) + "</div>")


def _status_chip(meta: dict | None) -> str:
    """Self-monitoring chip: green when the pipeline is flowing, amber when
    data is older than an hour, red after 24h. Honest failure display."""
    try:
        from datetime import datetime, timezone
        ts = (meta or {}).get("refreshed_at")
        age_h = (datetime.now(timezone.utc)
                 - datetime.fromisoformat(ts)).total_seconds() / 3600 if ts else None
    except Exception:
        age_h = None
    if age_h is None:
        cls, label = "red", "no data"
    elif age_h > 24:
        cls, label = "red", f"stale {age_h:.0f}h — pipeline stopped?"
    elif age_h > 1:
        cls, label = "amber", f"last refresh {age_h:.1f}h ago"
    else:
        label = f"live · refreshed {age_h * 60:.0f} min ago"
        cls = "green"
    return (f'<span class="chip"><span class="status-dot {cls}"></span> {_esc(label)}</span>')


def _scenario_grid_html(grid: list[dict], pub_px) -> str:
    """Reader what-if table: published target anchored at 0.0pp."""
    if not grid:
        return ""
    rows = []
    for r in grid:
        t = r.get("target")
        pct = (f'{(t / pub_px - 1) * 100:+.1f}%' if (t and pub_px) else "–")
        anchor = " <span class='muted'>(published)</span>" if r.get("published") else ""
        tcls = _kpi_color((t / pub_px - 1) * 100 if (t and pub_px) else None)
        rows.append(
            f"<tr><td>{r['shock'] * 100:+.1f}pp</td>"
            f"<td>{_fmt_num(t)}{anchor}</td>"
            f"<td class=\"{tcls}\">{pct}</td></tr>"
        )
    return (
        "<table><tr><th>Rate shock</th><th>Implied target (GBP)</th>"
        f"<th>vs price now</th></tr>{''.join(rows)}</table>"
    )


def _scenario_matrix_html(notes: list[dict]) -> str:
    """One row per note: published target plus the ±0.5/±1/±2pp scenarios."""
    shocks = [-0.02, -0.01, -0.005, 0.005, 0.01, 0.02]
    rows = []
    for n in notes:
        grid = scenario.scenario_grid(n)
        if not grid:
            continue
        by_shock = {r["shock"]: r.get("target") for r in grid}
        pub = n.get("price_target_gbp")
        slug = _note_filename(n["ticker"]).replace(".html", "")
        cells = "".join(
            f"<td>{_fmt_num(by_shock.get(s))}</td>" for s in shocks
        )
        rows.append(
            f'<tr><td><a href="#note-{slug}"><strong>{_esc(n["ticker"])}</strong></a></td>'
            f"<td><strong>{_fmt_num(pub)}</strong></td>{cells}</tr>"
        )
    if not rows:
        return "<p class='muted'>No published notes with usable valuation legs.</p>"
    head = "<tr><th>Ticker</th><th>Published target</th>" + "".join(
        f"<th>{s * 100:+.1f}pp</th>" for s in shocks
    ) + "</tr>"
    return f"<table>{head}{''.join(rows)}</table>"


def _kpi_cards(summary: dict) -> str:
    if not summary or summary.get("n", 0) == 0:
        return '<div class="muted">Publish notes to build the track record.</div>'
    hit = summary.get("hit_rate_pct", 0)
    dir_acc = summary.get("directional_accuracy_pct", 0)
    cards = [
        ("NOTES TRACKED", summary["n"], "published & frozen", "kpi-neutral"),
        ("HIT RATE", f"{hit}%", "notes beating FTSE (alpha > 0)", "kpi-good" if hit >= 50 else "kpi-warn"),
        ("DIRECTIONAL ACC", f"{dir_acc}%", "calls that moved the right way", "kpi-good" if dir_acc >= 50 else "kpi-warn"),
        ("AVG ALPHA", f"{summary.get('avg_alpha_pct', 0):+.2f}%", "vs FTSE 100, per note", "kpi-good" if summary.get("avg_alpha_pct", 0) > 0 else "kpi-warn"),
        ("AVG RETURN", f"{summary.get('avg_return_pct', 0):+.2f}%", "since first publication", "kpi-neutral"),
        ("WORST DRAWDOWN", _fmt_pct(summary.get("worst_drawdown_pct")).replace('<span class="neg">', "").replace('<span class="zero">', "").replace("</span>", ""), "peak-to-trough, worst note", "kpi-warn"),
        ("AVG ANN. VOL", f"{_fmt_num(summary.get('avg_ann_vol_pct'), 1)}%", "per-note average", "kpi-neutral"),
        ("NOTE-DAYS", summary.get("total_trading_days", 0), "sum of per-note trading days", "kpi-neutral"),
    ]
    return "".join(
        f'<div class="kpi {cls}"><div class="v">{v}</div>'
        f'<div class="l">{_esc(label)}</div><div class="s">{_esc(sub)}</div></div>'
        for label, v, sub, cls in cards
    )

def _note_card(note: dict, perf: dict | None, monthly: list[dict],
               series: list[dict] | None) -> str:
    """Rec-coloured summary card for one note, with expandable full detail."""
    slug = _note_filename(note["ticker"]).replace(".html", "")
    st = REC_STYLES.get(note.get("recommendation") or "", REC_STYLES["HOLD"])
    v = note["valuation_inputs"]
    dcf, ddm, comps = v["dcf"], v["ddm"], v["comps"]
    dcf_res = dcf.get("result") or {}
    thesis = note.get("thesis") or {}
    addenda = note.get("addenda") or []

    upside = note.get("upside_pct")
    upside_html = _fmt_pct(upside)
    progress = _window_progress(perf["days_tracked"]) if perf else _window_progress(0)
    alpha_html = _fmt_pct(perf["alpha_pct"]) if perf else '<span class="zero">–</span>'
    spark = _sparkline_svg(series or [], w=220, h=56,
                           color=st["border"])

    def li(items):
        return "".join(f"<li>{_esc(i)}</li>" for i in items)

    ctx = note.get("market_context") or {}
    pub_px = ctx.get("price_gbp_at_publication")
    first_px = ctx.get("price_gbp_at_first_publication") or pub_px
    guard = note.get("model_checks") or {}

    inputs_rows = [
        ("Base FCF (used)", _fmt_num(dcf.get("base_fcf_used_m") or dcf.get("base_fcf_m"), 1) + " GBPm",
         dcf.get("base_fcf_source") or "Yahoo cash_flow: OCF − capex, FX→GBP"),
        ("Base FCF (latest FY as reported)", _fmt_num(dcf.get("base_fcf_m"), 1) + " GBPm",
         "as on the feed (NaN = missing)"),
        ("FCF growth path", _esc(dcf.get("fcf_growth_path")),
         (dcf.get("derivation") or [""])[0]),
        ("Terminal growth", _esc(dcf.get("terminal_growth")),
         (dcf.get("derivation") or ["", ""])[1] if len(dcf.get("derivation") or []) > 1 else ""),
        ("WACC (CAPM ke)", _esc(round(dcf["wacc"], 4)) if dcf.get("wacc") else "–",
         dcf.get("wacc_source", "")),
        ("Net debt", _fmt_num(dcf.get("net_debt_m"), 1) + " GBPm",
         "total debt − cash & ST investments"),
        ("Shares", _fmt_num(dcf.get("shares_m"), 1) + " m", "Yahoo sharesOutstanding"),
        ("DCF value/share", _fmt_num(dcf_res.get("value_per_share")),
         "2-stage FCF DCF" if dcf_res.get("value_per_share") else "omitted (bank/data gap)"),
        ("DDM value/share", _fmt_num(ddm.get("value_per_share")),
         "; ".join(ddm.get("derivation") or []) or "skipped: missing inputs"),
        ("Comps median P/E", _fmt_num(comps.get("median_pe"), 1) + "x",
         "peer multiples, FX-converted, NM-excluded"),
        ("Blended target", f"<strong>{_fmt_num(note.get('price_target_gbp'))} GBP</strong>",
         f"weights {_esc(note.get('target_weights'))}"),
    ]
    inputs_html = "".join(
        f"<tr><td><strong>{a}</strong></td><td>{b}</td><td>{_esc(c)}</td></tr>"
        for a, b, c in inputs_rows
    )

    monthly_html = ""
    if monthly:
        rows = "".join(
            f"<tr><td>{m['month']}</td><td>{_fmt_pct(m['stock_pct'])}</td>"
            f"<td>{_fmt_pct(m['bench_pct'])}</td><td>{_fmt_pct(m['alpha_pct'])}</td></tr>"
            for m in monthly
        )
        monthly_html = (
            "<h4>Monthly attribution vs FTSE 100</h4>"
            "<table><tr><th>Month</th><th>Stock</th><th>FTSE</th><th>Alpha</th></tr>"
            + rows + "</table>"
        )

    addenda_html = ""
    if addenda:
        rows = "".join(
            f"<li><strong>[{a['ts'][:10]}] {_esc(a['kind'])}:</strong> {_esc(a['text'])}</li>"
            for a in addenda
        )
        addenda_html = f"<h4>Addenda (dated, never edited)</h4><ul class='tight'>{rows}</ul>"

    wrong_if = thesis.get("wrong_if") or []
    wrong_if_html = (""
        if not wrong_if else
        "<h4>What would make me wrong</h4><ul class='tight'>" + li(wrong_if) + "</ul>")
    esg_html = _esg_html(note)
    bbb_html = _bull_base_bear_html(note)
    sens_html = _sensitivity_grid_html(note)
    guard_banner = _guardrail_banner(note)
    current_price = (perf or {}).get("last_price")

    price_cells = (
        f"<div><span class='l'>Price at publication</span><span class='v'>{_fmt_num(pub_px)}</span></div>"
        f"<div><span class='l'>Current price</span><span class='v'>{_fmt_num(current_price)}</span></div>"
    )
    if first_px != pub_px:
        price_cells += (
            f"<div><span class='l'>Price at 1st publication</span>"
            f"<span class='v'>{_fmt_num(first_px)}</span></div>"
        )

    return f"""
<article class="notecard" id="note-{slug}" style="border-left-color:{st['border']}">
  <header>
    <div class="nc-head">
      {_badge(note.get('recommendation'))}
      <span class="nc-ticker">{_esc(note['ticker'])}</span>
      <span class="nc-name">{_esc(note['name'])}</span>
    </div>
    <div class="nc-headline">{_esc(_round_raw_floats(note.get('headline') or ''))}</div>
  </header>
  {guard_banner}
  <div class="nc-stats">
    <div><span class="l">Target</span><span class="v">{_fmt_num(note.get('price_target_gbp'))}</span></div>
    <div><span class="l">Upside</span><span class="v">{upside_html}</span></div>
    {price_cells}
    <div><span class="l">Alpha so far</span><span class="v">{alpha_html}</span></div>
    <div><span class="l">Window</span>{progress}</div>
    <div class="nc-spark"><span class="l">Since thesis</span>{spark}</div>
  </div>
  <details>
    <summary>Full note — thesis, frozen inputs, provenance</summary>
    <p>{_esc(_round_raw_floats(thesis.get('summary') or ''))}</p>
    {bbb_html}
    <div class="cols2">
      <div><h4>Catalysts</h4><ul class="tight">{li(thesis.get('catalysts', []))}</ul></div>
      <div><h4>Risks</h4><ul class="tight">{li(thesis.get('risks', []))}</ul></div>
    </div>
    {wrong_if_html}
    {esg_html}
    {sens_html}
    <h4>Valuation inputs (frozen at publication)</h4>
    <table><tr><th>Input</th><th>Value</th><th>Derivation / source</th></tr>{inputs_html}</table>
    {monthly_html}
    {addenda_html}
    <p class="muted">Audit id <code>{_esc(note.get('publication_audit_id', ''))}</code> ·
    print-ready page: <a href="notes/html/{_note_filename(note['ticker'])}">notes/html/{_note_filename(note['ticker'])}</a></p>
  </details>
</article>"""


def write_dashboard(quotes: dict, curve: list[dict], perf_rows: list[dict],
                    summary: dict, refresh_ts: str = "",
                    notes: list[dict] | None = None,
                    perf_by_ticker: dict | None = None,
                    monthly_by_ticker: dict | None = None,
                    series_by_ticker: dict | None = None,
                    caption: str = "",
                    changes: dict | None = None,
                    status_meta: dict | None = None,
                    backtest_curve: list[dict] | None = None,
                    live_metrics: dict | None = None,
                    backtest_metrics: dict | None = None,
                    weights_table: dict | None = None,
                    sector_mix: dict | None = None,
                    ftse_sectors: dict | None = None) -> None:
    """Render index.html (the dashboard) from current data."""
    DASH_FILE.parent.mkdir(parents=True, exist_ok=True)

    notes = notes or []
    perf_by_ticker = perf_by_ticker or {}
    monthly_by_ticker = monthly_by_ticker or {}
    series_by_ticker = series_by_ticker or {}
    backtest_curve = backtest_curve or []
    live_metrics = live_metrics or {}
    backtest_metrics = backtest_metrics or {}
    weights_table = weights_table or {}
    sector_mix = sector_mix or {}
    qrows = _qrows(quotes)
    n_curve = len(curve or [])
    n_backtest = len(backtest_curve)
    cards_html = "".join(
        _note_card(n, perf_by_ticker.get(n["ticker"]),
                   monthly_by_ticker.get(n["ticker"]) or [],
                   series_by_ticker.get(n["ticker"]))
        for n in notes
    )
    curve_data_js = (
        "[" + ",".join(
            f'["{c["date"]}",{c["portfolio"]},{c["benchmark"]}]' for c in (curve or [])
        ) + "]"
    )
    bt_data_js = (
        "[" + ",".join(
            f'["{c["date"]}",{c["portfolio"]},{c["benchmark"]}]' for c in backtest_curve
        ) + "]"
    )
    audit_rows_html = _audit_rows_table(audit.tail(300))

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Audit-ready UK equity research: dated theses, DCF/DDM/comparables valuations from live public data, 12m price targets, and 3-month tracked performance vs the FTSE 100 with a full append-only audit trail.">
<title>UK Equity Research & Portfolio Tracker</title>
<style>
  :root {{ --navy:#0f3460; --ink:#16233b; --pos:#047857; --neg:#b91c1c; --line:#e5e7eb; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif; margin: 0; color: var(--ink); background:#f4f6fa; }}
  .hero {{ background: linear-gradient(135deg, #0f3460 0%, #162b57 55%, #1e3a6e 100%); color:#fff; padding: 34px 20px 30px; }}
  .hero-inner {{ max-width: 1180px; margin: 0 auto; }}
  .hero h1 {{ margin: 0 0 6px; font-size: 30px; letter-spacing: -0.02em; }}
  .hero .sub {{ color:#c7d4ea; font-size: 14.5px; max-width: 860px; }}
  .chips {{ margin-top: 14px; display:flex; gap:8px; flex-wrap:wrap; }}
  .chip {{ background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.25); color:#e7eefb; padding:3px 11px; border-radius:999px; font-size:12px; }}
  main {{ max-width: 1180px; margin: 0 auto; padding: 18px 20px 40px; }}
  .caption {{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--navy); border-radius:10px; padding:14px 18px; margin:18px 0; font-size:15px; }}
  .caption b {{ color:var(--navy); }}
  h2 {{ color:var(--navy); font-size:17px; margin:26px 0 10px; }}
  table {{ border-collapse: collapse; width: 100%; background:#fff; border-radius:10px; overflow:hidden; box-shadow:0 1px 2px rgba(15,23,42,0.06); }}
  th, td {{ border-bottom:1px solid var(--line); padding:9px 12px; text-align:left; font-size:13.5px; }}
  th {{ background:#eef2f8; font-size:11px; text-transform:uppercase; letter-spacing:0.06em; color:#51617a; }}
  .pos {{ color:var(--pos); font-weight:600; }}
  .neg {{ color:var(--neg); font-weight:600; }}
  .zero {{ color:#5b6b83; }}
  .badge {{ display:inline-block; padding:3px 11px; border-radius:999px; font-size:12px; font-weight:700; letter-spacing:0.03em; }}
  .card {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:16px 20px; margin:16px 0; box-shadow:0 1px 2px rgba(15,23,42,0.05); }}
  .muted {{ color:#6b7a93; font-size:12.5px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:14px 0; }}
  .kpi {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:13px 15px; }}
  .kpi .v {{ font-size:23px; font-weight:750; color:var(--navy); line-height:1.15; }}
  .kpi .l {{ font-size:11px; color:#51617a; font-weight:700; letter-spacing:0.05em; margin-top:4px; }}
  .kpi .s {{ font-size:11.5px; color:#8593aa; margin-top:1px; }}
  .kpi-good {{ border-top:3px solid #10b981; }}
  .kpi-warn {{ border-top:3px solid #f59e0b; }}
  .kpi-neutral {{ border-top:3px solid #64748b; }}
  .movers {{ display:flex; gap:7px; flex-wrap:wrap; align-items:center; margin:10px 0 2px; }}
  .movers-label {{ font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:#51617a; margin-right:4px; }}
  .mover {{ background:#fff; border:1px solid var(--line); border-radius:999px; padding:3px 10px; font-size:12.5px; box-shadow:0 1px 2px rgba(15,23,42,0.05); }}
  .mover.up {{ color:var(--pos); }}
  .mover.down {{ color:var(--neg); }}
  .mover.flat {{ color:#5b6b83; }}
  .status-dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:4px; vertical-align:middle; }}
  .status-dot.green {{ background:#10b981; }}
  .status-dot.amber {{ background:#f59e0b; }}
  .status-dot.red {{ background:#ef4444; }}
  tr.hot td {{ background:#fffbeb; }}
  .notecards {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:14px; }}
  .notecard {{ background:#fff; border:1px solid var(--line); border-left:5px solid #64748b; border-radius:12px; padding:14px 16px; box-shadow:0 1px 3px rgba(15,23,42,0.07); }}
  .nc-head {{ display:flex; align-items:center; gap:9px; }}
  .nc-ticker {{ font-weight:800; font-size:17px; color:var(--navy); }}
  .nc-name {{ color:#6b7a93; font-size:13px; }}
  .nc-headline {{ font-size:13.5px; color:#33415c; margin:8px 0 10px; }}
  .nc-stats {{ display:flex; gap:16px; flex-wrap:wrap; align-items:flex-end; }}
  .nc-stats > div {{ display:flex; flex-direction:column; gap:2px; }}
  .nc-stats .l {{ font-size:10.5px; color:#8593aa; text-transform:uppercase; letter-spacing:0.05em; }}
  .nc-stats .v {{ font-size:16px; font-weight:700; color:var(--ink); }}
  .winbar {{ width:110px; height:7px; background:#e8edf5; border-radius:999px; overflow:hidden; margin-top:3px; }}
  .winfill {{ height:100%; background:linear-gradient(90deg,#3b82f6,#10b981); }}
  .nc-spark {{ min-width:220px; }}
  details {{ margin-top:8px; }}
  details summary {{ cursor:pointer; font-size:13px; color:var(--navy); font-weight:600; }}
  details[open] summary {{ margin-bottom:8px; }}
  details h4 {{ margin:12px 0 4px; color:var(--navy); font-size:13.5px; }}
  ul.tight {{ margin:4px 0; padding-left:18px; }}
  ul.tight li {{ margin:2px 0; font-size:13.5px; }}
  .cols2 {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
  .topnav {{ position:sticky; top:0; z-index:40; background:#0f3460ee; backdrop-filter:blur(4px); }}
  .topnav-inner {{ max-width:1180px; margin:0 auto; padding:0 20px; display:flex; gap:2px; flex-wrap:wrap; }}
  .topnav a {{ color:#dbe6f7; font-size:13px; padding:9px 12px; display:inline-block; font-weight:600; }}
  .topnav a:hover {{ background:#ffffff22; text-decoration:none; color:#fff; }}
  .guard-box {{ background:#fef2f2; border:1px solid #fecaca; border-left:5px solid #ef4444; border-radius:10px; padding:10px 14px; margin:8px 0; font-size:13.5px; color:#7f1d1d; }}
  .sens-box {{ background:#f8fafc; border:1px solid var(--line); border-radius:10px; padding:10px 12px; margin:8px 0; }}
  .sens-box table {{ font-size:12px; }}
  .metric-def {{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:10px 14px; margin:10px 0; font-size:12.5px; color:#44526b; }}
  .metric-def b {{ color:var(--navy); }}
  .honesty-split {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
  @media (max-width:900px) {{
    .honesty-split {{ grid-template-columns:1fr; }}
    .hero h1 {{ font-size:24px; }}
    .topnav-inner {{ padding:0 8px; }}
    .topnav a {{ padding:8px 9px; font-size:12px; }}
  }}
  @media (max-width:640px) {{
    .cols2 {{ grid-template-columns:1fr; }}
    main {{ padding:14px 12px 30px; }}
    th, td {{ padding:7px 8px; font-size:12.5px; }}
    .table-wrap {{ overflow-x:auto; }}
    .table-wrap table {{ min-width:640px; }}
  }}
  details table {{ font-size:12.5px; margin:6px 0; }}
  canvas {{ max-height:300px; }}
  a {{ color:var(--navy); text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  code {{ background:#f1f5f9; padding:1px 5px; border-radius:4px; font-size:12px; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <h1>UK Equity Research &amp; Portfolio Tracker</h1>
    <div class="sub">Audit-ready research on 8 FTSE 100 names — every valuation input fetched from public data and frozen at publication, every thesis tracked for 3 months against the FTSE 100 with alpha, hit-rate, volatility and drawdown evidence.</div>
    <div class="chips">
      <span class="chip">Data refreshed {_esc(refresh_ts[:16].replace('T', ' '))} UTC</span>
      <span class="chip">Yahoo Finance</span><span class="chip">FRED 10Y gilt</span>
      <span class="chip">Damodaran ERP</span><span class="chip">Append-only audit log</span>
      <span class="chip">Immutable notes + snapshots</span>
    </div>
  </div>
</div>
<nav class="topnav no-print"><div class="topnav-inner">
  <a href="#top">Overview</a>
  <a href="#portfolio">Portfolio</a>
  <a href="#notes">Notes</a>
  <a href="#methodology">Methodology</a>
  <a href="#audit-trail">Audit</a>
  <a href="#about">About</a>
  <a href="audit.html">Audit viewer</a>
</div></nav>
<main id="top">
  {_status_chip(status_meta)}
  <div class="caption"><b>Track record:</b> {_esc(caption)}</div>
  {_movers_strip(qrows)}
  {_change_line(changes)}
  <div class="metric-def">
    <b>Reading the numbers — definitions used everywhere on this site:</b><br>
    <b>Hit rate</b> = share of tracked notes beating the FTSE 100 (alpha &gt; 0) since each note's first publication.<br>
    <b>Directional accuracy</b> = share of calls where price moved the way the recommendation said (BUY up / SELL down / HOLD within ±10%) over the same window — direction only, regardless of size.<br>
    <b>Alpha</b> = note return − FTSE 100 return over the same dated window. <b>Day</b> = last close vs previous close.
  </div>

  <h2>Market snapshot — live LSE quotes</h2>
  <p class="muted">The London Stock Exchange quotes shares in <b>pence (GBp)</b>; this site expresses every price, target, and valuation in <b>GBP (£) = pence ÷ 100</b>. The QUOTED column shows the same live price in pence so you can cross-check directly against Yahoo or Google Finance.</p>
  <table>{_qtable(qrows)}</table>

  <h2 id="track-record">Track record — live vs backtest, clearly separated</h2>
  <div class="honesty-split">
    <div class="card" style="margin:0">
      <h3 style="margin-top:0;color:var(--pos)">Live record — since first publication ({summary.get('window_start') or 'n/a'} onward)</h3>
      <p class="muted">Real decisions, published before the fact: each note's window starts at its first-publication close and runs to {summary.get('window_end') or 'n/a'}. Notes are frozen at publication; corrections are dated addenda. This is the only section that counts as a track record.</p>
      <div class="kpis">{_kpi_cards(summary)}</div>
      <table>
        <tr><th>Ticker</th><th>Day</th><th>Thesis date</th><th>Price path</th><th>Chart</th><th>Return since thesis</th><th>Alpha since thesis</th><th>Ann. vol</th><th>Max DD</th><th>Rec</th></tr>
        {_perf_rows_html(perf_rows, series_by_ticker, quotes)}
      </table>
      <div class="muted" style="margin-top:6px">Every figure above runs {summary.get('window_start') or 'n/a'} → {summary.get('window_end') or 'n/a'} (per-note start dates in the Thesis date column; windows are per-note, the KPI header shows the full span). {summary.get('total_trading_days', 0)} note-days of evidence in total (sum of per-note trading days — not calendar days, and not the portfolio window length).</div>
    </div>
    <div class="card" style="margin:0">
      <h3 style="margin-top:0;color:#b45309">Backtest — HYPOTHETICAL (current weights applied to trailing history)</h3>
      <p class="muted">The current model portfolio, back-run over the trailing 3 months with today's weights. <b>Hypothetical:</b> the notes did not all exist at the start of this window and the weights were chosen with hindsight; it is a model-behaviour illustration, not a track record.</p>
      <div class="muted">{n_backtest} trading days plotted (trailing 3-month window, cost-adjusted).</div>
      <canvas id="btcurve" width="520" height="240"></canvas>
    </div>
  </div>

  <h2 id="portfolio">Portfolio construction — notional £100,000</h2>
  <div class="card">
    <h3 style="margin-top:0">Explicit weights</h3>
    {_portfolio_weights_table(weights_table)}
  </div>
  <div class="honesty-split">
    <div class="card" style="margin:0">
      <h3 style="margin-top:0;color:var(--pos)">Live record — portfolio risk metrics</h3>
      {_portfolio_metrics_html("Live record", live_metrics, curve)}
      <canvas id="curve" width="520" height="240"></canvas>
      <div class="muted">{n_curve} trading days plotted (first publication → latest close; cost-adjusted).</div>
    </div>
    <div class="card" style="margin:0">
      <h3 style="margin-top:0;color:#b45309">Backtest — HYPOTHETICAL</h3>
      {_portfolio_metrics_html("Backtest (hypothetical)", backtest_metrics, backtest_curve)}
    </div>
  </div>
  <div class="card">
    <h3 style="margin-top:0">Sector exposure vs FTSE 100</h3>
    {_sector_chart_html(sector_mix, ftse_sectors)}
  </div>

  <h2 id="notes">Research notes</h2>
  <div class="notecards">{cards_html}</div>

  <div class="card">
    <h2 style="margin-top:0">What if rates move? — scenarios re-derived from frozen inputs</h2>
    <p class="muted">Each cell re-discounts that note's <b>frozen</b> cash-flow inputs at a shocked cost of equity (−2pp to +2pp), with weights renormalised over the surviving legs — same formulas as the published model, no new data, nothing fetched. The published target is the 0.0pp anchor and is never recomputed. Comps legs are multiple-based and rate-insensitive; notes valued purely on comps (e.g. NG) are correctly flat.</p>
    {_scenario_matrix_html(notes)}
    <div class="muted" style="margin-top:6px">Interactive per-note versions with a live slider are on each note page under “Your scenario”. These are <b>your</b> scenarios, not the published recommendation.</div>
  </div>

  <div class="card" id="methodology">
    <h2 style="margin-top:0">Methodology &amp; audit trail</h2>
    <ul class="tight">
      <li><b>Valuation:</b> 5-year explicit FCF forecast (growth = history-derived CAGR, 50% damped, −5%/+15% bounds), terminal g = min(10Y gilt, CAGR/2), WACC = CAPM cost of equity (Blume-adjusted beta vs ^FTSE over 2y of weekly data, floor 0.40). Blend: 60% DCF / 20% DDM / 20% comps; banks 60% DDM / 40% P/E. A ±30% <b>model-outlier guardrail</b> flags any target beyond that band vs the market price and names the driving leg.</li>
      <li><b>Performance formulas:</b> annualised volatility = std(daily portfolio returns) × √252 (sample, ddof=1); max drawdown = min(V<sub>t</sub>/max(V<sub>0..t</sub>) − 1); beta = cov(r<sub>p</sub>, r<sub>b</sub>)/var(r<sub>b</sub>); tracking error = std(r<sub>p</sub> − r<sub>b</sub>) × √252; annualised return (CAGR) = (1 + total return)<sup>252/n</sup> − 1; Sharpe = (CAGR − risk-free) / annualised volatility, risk-free = UK 3-month immediate rate (FRED IR3TIB01GBM156N). All computed on the <b>portfolio return series</b>, never an average of stock-level statistics.</li>
      <li><b>Return basis:</b> total return — Yahoo adjusted close, dividends reinvested. Transaction costs: 0.5% stamp duty reserve tax + 0.1% commission on buys, applied once at inception as a start-of-period drag; no ongoing costs modelled.</li>
      <li><b>Live vs backtest:</b> the live record only counts decisions published before the fact, measured from each note's first-publication close; the backtest applies <i>current</i> weights to trailing history and is labelled hypothetical everywhere it appears.</li>
      <li><b>Frozen inputs:</b> every input is snapshotted at publication with source + derivation; revisions archive under <code>notes/snapshots/</code>; corrections are dated addenda, never edits. The tracked window starts at first publication and is not reset by revisions.</li>
      <li><b>Audit log:</b> every fetch, publication, guardrail flag, and refresh appends to <code>data/audit_log.jsonl</code> — each note stores the audit ids of the fetches behind its numbers.</li>
      <li><b>Exclusions are recorded:</b> peer multiples above NM caps, single-peer medians, depressed-earnings P/E legs, missing-data legs (DCF excluded with the reason) — each note shows what was excluded and why.</li>
    </ul>
  </div>
  {_about_html()}
  <div id="update-toast" style="position:fixed;left:50%;transform:translateX(-50%);bottom:72px;z-index:60;display:none;background:#0f3460;color:#fff;padding:11px 18px;border-radius:12px;box-shadow:0 8px 22px rgba(15,23,42,0.28);font-size:13.5px">
    <b>Prices updated</b> — <span id="toast-ts"></span>
    · <a href="#" id="toast-reload" style="color:#9fd0ff;text-decoration:underline">view the latest</a>
    <button id="toast-close" aria-label="Dismiss" style="margin-left:10px;background:none;border:none;color:#c7d4ea;cursor:pointer;font-size:14px">&#10005;</button>
  </div>
  <div style="position:fixed;right:14px;bottom:14px;z-index:50;display:flex;gap:8px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:999px;box-shadow:0 4px 14px rgba(15,23,42,0.14);padding:7px 13px;font-size:12.5px">
    <span style="width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block"></span>
    <label for="live-interval" style="color:#51617a">Auto-reload</label>
    <select id="live-interval" style="border:1px solid #cbd5e1;border-radius:6px;padding:2px 4px;font-size:12.5px">
      <option value="0">Off</option>
      <option value="60">1 min</option>
      <option value="300" selected>5 min</option>
      <option value="600">10 min</option>
    </select>
  </div>
  <details id="audit-trail" style="margin-top:18px">
    <summary style="cursor:pointer;font-weight:700;color:var(--navy);background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 16px">Append-only audit trail — every fetch, publication, and refresh (last 300 events)</summary>
    <p class="muted" style="margin:10px 4px">Machine-readable log: <code>data/audit_log.jsonl</code> in the repo, served as <code>audit_log.jsonl</code> and browsable at <code>audit.html</code> on the deployed site.</p>
    <div style="overflow-x:auto">
      <table>
        <tr><th>Timestamp (UTC)</th><th>Event</th><th>Detail</th></tr>
        {audit_rows_html}
      </table>
    </div>
  </details>
</main>
<footer style="max-width:1180px;margin:26px auto 0;padding:14px 20px 34px;border-top:1px solid var(--line);color:#6b7a93;font-size:12.5px;display:flex;gap:14px;flex-wrap:wrap;justify-content:space-between">
  <span>Personal educational project. Not investment advice. Not affiliated with any firm.<br>
  Regenerated from live market data every refresh cycle &middot; <a href="#audit-trail" style="color:var(--navy)">view the append-only audit trail</a> &middot;
  <a href="{config.REPO_URL}" style="color:var(--navy)">GitHub repo (source, methodology, audit log)</a></span>
  <span>Python 3.11 &middot; yfinance &middot; FRED &middot; Damodaran</span>
</footer>
<script>
const curveData = {curve_data_js};
const btData = {bt_data_js};
function drawCurve(id, rows, hint) {{
  if (!rows || rows.length < 2) return;
  const el = document.getElementById(id);
  if (!el) return;
  new Chart(el, {{
    type: 'line',
    data: {{ labels: rows.map(r => r[0]),
      datasets: [
        {{ label: 'Model portfolio', data: rows.map(r => r[1]), borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.08)', fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2 }},
        {{ label: 'FTSE 100', data: rows.map(r => r[2]), borderColor: '#94a3b8', borderDash: [6, 4], fill: false, tension: 0.2, pointRadius: 0, borderWidth: 1.5 }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: 'bottom' }}, subtitle: {{ display: !!hint, text: hint }} }},
      scales: {{ x: {{ ticks: {{ maxTicksLimit: 10 }} }}, y: {{ title: {{ display: true, text: 'Index (start = 100, gross of nothing; line starts at 99.4 = net of costs)' }} }} }}
    }}
  }});
}}
drawCurve('curve', curveData, 'Live record: {summary.get('window_start') or 'n/a'} → {summary.get('window_end') or 'n/a'}');
drawCurve('btcurve', btData, 'Backtest — HYPOTHETICAL: trailing 3 months, current weights');
// ---- live updates: poll refresh_meta.json, toast on new data, optional auto-reload ----
const PAGE_TS = '{refresh_ts}';
const liveSel = document.getElementById('live-interval');
const updateToast = document.getElementById('update-toast');
let toastShownFor = '';
try {{ const saved = localStorage.getItem('live_interval'); if (saved !== null) liveSel.value = saved; }} catch (e) {{}}
function sameTs(a, b) {{
  // Compare at minute precision: GitHub Pages may serve HTML cached up to
  // 10 min, and refreshes land at ~5 min cadence, so seconds-level diffs
  // are meaningless (and would make View now reload into the same page).
  return String(a || '').slice(0, 16) === String(b || '').slice(0, 16);
}}
function pollRefresh() {{
  fetch('refresh_meta.json', {{ cache: 'no-store' }})
    .then(r => r.ok ? r.json() : null)
    .then(m => {{
      if (m && m.refreshed_at && !sameTs(m.refreshed_at, PAGE_TS) && m.refreshed_at !== toastShownFor) {{
        toastShownFor = m.refreshed_at;
        const mv = (m.changes && m.changes.movers && m.changes.movers.length)
          ? ' · ' + m.changes.movers.join(', ') : '';
        document.getElementById('toast-ts').textContent =
          'Loaded ' + String(PAGE_TS).replace('T', ' ').slice(0, 16) + ' UTC · latest is ' +
          String(m.refreshed_at).replace('T', ' ').slice(0, 16) + ' UTC' + mv;
        updateToast.style.display = 'block';
      }}
    }})
    .catch(() => {{}});
}}
setInterval(pollRefresh, 60000);
pollRefresh();
function armAutoReload() {{
  const secs = parseInt(liveSel.value, 10);
  try {{ localStorage.setItem('live_interval', liveSel.value); }} catch (e) {{}}
  if (window.__liveTimer) {{ clearInterval(window.__liveTimer); window.__liveTimer = null; }}
  if (secs > 0) window.__liveTimer = setInterval(() => location.reload(), secs * 1000);
}}
liveSel.addEventListener('change', armAutoReload);
armAutoReload();
document.getElementById('toast-reload').addEventListener('click', e => {{
  e.preventDefault();
  // Bust GitHub Pages' 10-min HTML cache so the click actually lands you on
  // the refreshed page instead of re-serving what you're already viewing.
  location.replace(location.pathname + '?t=' + Date.now() + location.hash);
}});
document.getElementById('toast-close').addEventListener('click', () => {{ updateToast.style.display = 'none'; }});
</script>
</body>
</html>"""
    DASH_FILE.write_text(doc, encoding="utf-8")

def _scenario_widget_html(note: dict) -> str:
    """Per-note scenario table + slider harness (slider JS wired below)."""
    grid = scenario.scenario_grid(note)
    if not grid:
        return ""
    px = (note.get("market_context") or {}).get("price_gbp_at_publication")
    rows = []
    for r in grid:
        t = r.get("target")
        pct = (f'{(t / px - 1) * 100:+.1f}%' if (t and px) else "–")
        anchor = " <span class='muted'>(published)</span>" if r.get("published") else ""
        tcls = _kpi_color((t / px - 1) * 100 if (t and px) else None)
        rows.append(
            f"<tr data-shock=\"{r['shock']:+.3f}\"><td>{r['shock'] * 100:+.1f}pp</td>"
            f"<td class=\"sc-target\">{_fmt_num(t)}{anchor}</td>"
            f"<td class=\"{tcls}\">{pct}</td></tr>"
        )
    return (
        '<div class="scenario-box">'
        '<h3>Your scenario — discount-rate shock (reader tool, not the published call)</h3>'
        '<p class="muted">Slides re-discount the frozen cash flows at a different cost of equity. '
        'Same formulas, same frozen inputs, no new data. The published target never changes.</p>'
        '<input type="range" id="sc-slider" min="-2" max="2" step="0.1" value="0" style="width:60%"> '
        '<span id="sc-readout" style="font-weight:700;color:var(--navy)">0.0pp → published target</span>'
        '<table id="sc-table"><tr><th>Shock</th><th>Implied target (GBP)</th><th>vs price at publication</th></tr>'
        + "".join(rows) + "</table></div>"
    )


def _data_quality_html(note: dict) -> str:
    """Explicit, recruiter-visible disclosure of missing-source legs."""
    v = note.get("valuation_inputs") or {}
    dcf = v.get("dcf") or {}
    ddm = v.get("ddm") or {}
    comps = v.get("comps") or {}
    issues = []
    dcf_res = dcf.get("result") or {}
    base = dcf.get("base_fcf_m")
    if not dcf_res.get("value_per_share"):
        if base is None or base != base:
            reason = "latest-FY free cash flow missing/NaN on the feed"
        else:
            # Pull the recorded reason (e.g. NG: FCF negative in 3 of 4 FYs)
            # from the derivation when the model recorded an explicit exclusion.
            deriv = "; ".join(dcf.get("derivation") or [])
            reason = (deriv[:400] if "DCF excluded" in deriv else
                      "inputs failed validation (see derivation row)")
        issues.append(
            f"<li><b>DCF leg excluded — reason:</b> {_esc(reason)}. The blend "
            "re-weights over the surviving legs — the published target is "
            "derived only from sources that returned real numbers.</li>"
        )
    elif dcf.get("base_fcf_used_m") and dcf.get("base_fcf_m") != dcf.get("base_fcf_used_m"):
        issues.append(
            f"<li><b>DCF base normalised:</b> latest-FY FCF on the feed is "
            f"{_esc(_fmt_num(dcf.get('base_fcf_m'), 1))} GBPm (missing or "
            "non-finite); the DCF instead uses a normalised multi-year average "
            f"of {_esc(_fmt_num(dcf.get('base_fcf_used_m'), 1))} GBPm over the "
            "finite trailing FYs — disclosed in the derivation column.</li>"
        )
    if not ddm.get("value_per_share"):
        issues.append("<li><b>DDM leg omitted:</b> DPS/ROE/payout incomplete on the feed.</li>")
    if not comps.get("implied_price_pe"):
        issues.append("<li><b>P/E comps leg omitted:</b> peer median not robust or subject earnings depressed.</li>")
    if not comps.get("implied_price_ev_ebitda"):
        issues.append("<li><b>EV/EBITDA comps leg omitted:</b> peer median not robust or subject data gap.</li>")
    if not issues:
        return ""
    return (
        '<div class="dq-box"><h3>Data-quality disclosure (read before quoting this note)</h3>'
        "<ul class='tight'>" + "".join(issues) + "</ul>"
        '<p class="muted">Nothing is illustrated: where a source returns no valid '
        'number, the affected leg is dropped and the omission is recorded here and in '
        'the audit log, rather than the target being silently computed from bad data.</p></div>'
    )


def write_note_page(note: dict, perf: dict | None, monthly: list[dict],
                    series: list[dict] | None = None) -> None:
    """Standalone, print-ready HTML page for one published note."""
    if not note or note.get("status") != "published":
        return
    NOTES_HTML_DIR.mkdir(parents=True, exist_ok=True)
    v = note["valuation_inputs"]
    prov = note.get("provenance") or {}
    ctx = note["market_context"]
    thesis = note.get("thesis") or {}
    addenda = note.get("addenda") or []
    dcf, ddm, comps = v["dcf"], v["ddm"], v["comps"]
    dcf_res = dcf.get("result") or {}
    st = REC_STYLES.get(note.get("recommendation") or "", REC_STYLES["HOLD"])

    chart_json = json.dumps(series or [], default=str)
    series_js = ("const series = " + chart_json + ";\n"
                 "if (series.length > 1) { new Chart(document.getElementById('pxchart'), {"
                 "type: 'line', data: { labels: series.map(p => p.date), datasets: ["
                 "{ label: 'Stock (indexed 100)', data: series.map(p => p.stock), borderColor: '#3b82f6', fill: true, backgroundColor: 'rgba(59,130,246,0.08)', pointRadius: 0, borderWidth: 2, tension: 0.15 },"
                 "{ label: 'FTSE 100 (indexed 100)', data: series.map(p => p.bench), borderColor: '#94a3b8', borderDash: [6,4], pointRadius: 0, borderWidth: 1.5, tension: 0.15 }] },"
                 "options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { x: { ticks: { maxTicksLimit: 8 } } } } }); }")

    inputs_rows = [
        ("Base FCF (used)", _fmt_num(dcf.get("base_fcf_used_m") or dcf.get("base_fcf_m"), 1) + " GBPm",
         dcf.get("base_fcf_source") or "Yahoo cash_flow: OCF − capex, FX-converted to GBP"),
        ("Base FCF (latest FY as reported)", _fmt_num(dcf.get("base_fcf_m"), 1) + " GBPm",
         "as on the feed (NaN = missing)"),
        ("FCF growth path", _esc(dcf.get("fcf_growth_path")),
         (dcf.get("derivation") or [""])[0]),
        ("Terminal growth", _esc(dcf.get("terminal_growth")),
         (dcf.get("derivation") or ["", ""])[1] if len(dcf.get("derivation") or []) > 1 else ""),
        ("WACC (= ke, CAPM)", _esc(round(dcf.get("wacc"), 4)) if dcf.get("wacc") else "–",
         dcf.get("wacc_source", "")),
        ("Net debt", _fmt_num(dcf.get("net_debt_m"), 1) + " GBPm",
         "Balance sheet: total debt − cash & ST investments"),
        ("Shares outstanding", _fmt_num(dcf.get("shares_m"), 1) + " m", "Yahoo sharesOutstanding"),
        ("DCF value/share", _fmt_num(dcf_res.get("value_per_share")),
         "2-stage FCF DCF" if dcf_res.get("value_per_share") else "omitted (bank, or data gap)"),
        ("DDM value/share", _fmt_num(ddm.get("value_per_share")),
         "; ".join(ddm.get("derivation") or []) or "skipped: missing inputs"),
        ("Comps: median P/E", _fmt_num(comps.get("median_pe"), 1) + "x",
         "; ".join([d for d in comps.get("derivation", []) if "P/E" in d][:1])),
        ("Comps implied (P/E)", _fmt_num(comps.get("implied_price_pe")),
         "peer median x derived EPS (suppressed if earnings depressed)"),
        ("Comps implied (EV/EBITDA)", _fmt_num(comps.get("implied_price_ev_ebitda")),
         "peer median x EBITDA, less net debt"),
        ("Blended 12m target", f"<strong>{_fmt_num(note.get('price_target_gbp'))} GBP</strong>",
         f"weights {_esc(note.get('target_weights'))}"),
    ]
    inputs_html = "".join(
        f"<tr><td><strong>{label}</strong></td><td>{val}</td><td>{_esc(deriv)}</td></tr>"
        for label, val, deriv in inputs_rows
    )

    peer_rows = "".join(
        f"<tr><td>{_esc(e['peer'])}</td><td>{_fmt_num(e['ev_ebitda'], 1)}</td>"
        f"<td>{_fmt_num(e['pe'], 1)}</td></tr>"
        for e in comps.get("entries", [])
    )
    peer_section = (
        "<h2>Peer comparables (live)</h2>"
        "<table><tr><th>Peer</th><th>EV/EBITDA</th><th>P/E</th></tr>"
        + peer_rows + "</table>" if peer_rows else ""
    )

    prov_rows_html = []
    for key, p in prov.items():
        if not p or key == "model_choices":
            continue
        items = p if isinstance(p, list) else [p]
        for item in items:
            if isinstance(item, dict):
                prov_rows_html.append(
                    f"<tr><td>{_esc(key)}</td><td>{_esc(item.get('source', ''))}</td>"
                    f"<td>{_esc(item.get('derivation', ''))}</td>"
                    f"<td>{_esc(str(item.get('retrieved_at', ''))[:19])}</td></tr>"
                )
            elif item:
                prov_rows_html.append(
                    f"<tr><td>{_esc(key)}</td><td colspan='3'>{_esc(item)}</td></tr>")
    prov_html = "".join(prov_rows_html)
    mc = prov.get("model_choices") or {}
    mc_html = "".join(
        f"<li><code>{_esc(k)}</code> = {_esc(vv)}</li>" for k, vv in mc.items()
    )

    perf_html = ""
    if perf:
        perf_html = (
            "<h2>Tracked performance vs FTSE 100 (live record)</h2>"
            "<p class='muted'>Window: " + _esc(perf['thesis_date']) + " → "
            + _esc(perf.get('end_date', '')) + " (" + str(perf.get('trading_days', '–'))
            + " trading days). Live record = performance since first publication "
            "only; corrections do not reset the clock.</p>"
            "<table><tr><th>Thesis date</th><th>Tracked</th><th>Price path</th>"
            "<th>Return</th><th>FTSE</th><th>Alpha</th><th>Ann. vol</th><th>Max DD</th></tr>"
            f"<tr><td>{_esc(perf['thesis_date'])}</td>"
            f"<td>{perf['days_tracked']}d / {perf.get('trading_days', '–')}td</td>"
            f"<td>{_fmt_num(perf['base_price'])} → {_fmt_num(perf['last_price'])}</td>"
            f"<td>{_fmt_pct(perf['return_pct'])}</td>"
            f"<td>{_fmt_pct(perf['bench_return_pct'])}</td>"
            f"<td>{_fmt_pct(perf['alpha_pct'])}</td>"
            f"<td>{_fmt_pct(perf.get('ann_vol_pct'))}</td>"
            f"<td>{_fmt_pct(perf.get('max_drawdown_pct'))}</td></tr></table>"
        )

    monthly_html = ""
    if monthly:
        rows = "".join(
            f"<tr><td>{m['month']}</td><td>{_fmt_pct(m['stock_pct'])}</td>"
            f"<td>{_fmt_pct(m['bench_pct'])}</td><td>{_fmt_pct(m['alpha_pct'])}</td></tr>"
            for m in monthly
        )
        monthly_html = (
            "<h2>Monthly attribution vs FTSE 100</h2><table>"
            "<tr><th>Month</th><th>Stock</th><th>FTSE 100</th><th>Alpha</th></tr>"
            + rows + "</table>"
        )

    addenda_html = ""
    if addenda:
        rows = "".join(
            f"<li><strong>[{a['ts'][:10]}] {_esc(a['kind'])}:</strong> {_esc(a['text'])}</li>"
            for a in addenda
        )
        addenda_html = f"<h2>Addenda (dated, never edited)</h2><ul>{rows}</ul>"

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{_esc(_round_raw_floats(note['name'] + ' (' + note['ticker'] + '): ' + (note.get('headline') or '')[:155]))}">
<title>{_esc(note['name'])} ({note['ticker']}) — Research Note</title>
<style>
  :root {{ --navy:#0f3460; --pos:#047857; --neg:#b91c1c; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif; margin:0; background:#f4f6fa; color:#16233b; }}
  .band {{ background: linear-gradient(135deg, #0f3460, #1e3a6e); color:#fff; padding:26px 20px 22px; }}
  .band-inner {{ max-width:900px; margin:0 auto; }}
  .band h1 {{ margin:0; font-size:27px; letter-spacing:-0.02em; }}
  .band .tick {{ color:#9fb4d8; font-weight:600; }}
  main {{ max-width:900px; margin:0 auto; padding:20px; }}
  .sumcard {{ background:#fff; border:1px solid #e5e7eb; border-radius:14px; box-shadow:0 2px 6px rgba(15,23,42,0.07); padding:18px 20px; margin-top:-34px; position:relative; }}
  .sumgrid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:12px; margin-top:6px; }}
  .sumgrid .cell {{ border:1px solid #edf1f7; border-radius:10px; padding:9px 12px; }}
  .sumgrid .l {{ font-size:10.5px; color:#8593aa; text-transform:uppercase; letter-spacing:0.05em; }}
  .sumgrid .v {{ font-size:19px; font-weight:750; color:var(--navy); margin-top:2px; }}
  .headline {{ font-size:15.5px; color:#33415c; margin:12px 0 2px; }}
  h2 {{ font-size:16px; color:var(--navy); border-bottom:2px solid var(--navy); padding-bottom:4px; margin-top:30px; }}
  h3 {{ font-size:13.5px; margin-bottom:4px; }}
  table {{ border-collapse:collapse; width:100%; margin:10px 0; font-size:13.5px; background:#fff; }}
  th, td {{ border:1px solid #d7dee9; padding:6px 9px; text-align:left; vertical-align:top; }}
  th {{ background:#eef2f8; font-size:12px; text-transform:uppercase; letter-spacing:0.04em; color:#51617a; }}
  .badge {{ display:inline-block; padding:4px 14px; border-radius:999px; font-weight:800; letter-spacing:0.04em; }}
  .pos {{ color:var(--pos); font-weight:600; }}
  .neg {{ color:var(--neg); font-weight:600; }}
  .zero {{ color:#5b6b83; }}
  .btns {{ display:flex; gap:10px; margin:12px 0 0; }}
  .btn {{ border:1px solid #cbd5e1; background:#fff; color:var(--navy); font-weight:700; font-size:13px; padding:8px 14px; border-radius:8px; cursor:pointer; }}
  .btn:hover {{ background:#eef2f8; }}
  .chartbox {{ background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:12px 14px; margin:14px 0; }}
  .chartbox canvas {{ max-height:260px; width:100%; }}
  .scenario-box, .dq-box {{ background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:14px 16px; margin:14px 0; }}
  .dq-box {{ border-left:4px solid #f59e0b; background:#fffbeb; }}
  .scenario-box h3, .dq-box h3 {{ margin:0 0 6px; color:var(--navy); }}
  #sc-table {{ margin-top:10px; }}
  ul {{ padding-left:20px; }}
  .disclaimer {{ color:#6b7a93; font-size:12px; border-top:1px solid #d7dee9; margin-top:30px; padding-top:12px; }}
  .muted {{ color:#6b7a93; font-size:12.5px; }}
  .guard-box {{ background:#fef2f2; border:1px solid #fecaca; border-left:5px solid #ef4444; border-radius:10px; padding:10px 14px; margin:12px 0; font-size:13.5px; color:#7f1d1d; }}
  .backlink {{ font-size:13px; margin-bottom:12px; }}
  .backlink a {{ color:var(--navy); font-weight:700; }}
  @media (max-width:640px) {{
    main {{ padding:14px 12px 30px; }}
    .band h1 {{ font-size:22px; }}
    .sumgrid {{ grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); }}
    body > div[style*="grid-template-columns"], main > div[style*="grid-template-columns"] {{ grid-template-columns:1fr !important; }}
    th, td {{ padding:5px 7px; font-size:12.5px; }}
    .table-wrap {{ overflow-x:auto; }}
  }}
  @media print {{
    body {{ background:#fff; }}
    .band {{ background: var(--navy) !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .btns {{ display:none; }}
    .sumcard {{ box-shadow:none; margin-top:10px; }}
    h2 {{ page-break-after: avoid; }}
    table, ul {{ page-break-inside: avoid; }}
  }}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>
<div class="band"><div class="band-inner">
  <h1>{_esc(note['name'])} <span class="tick">({note['ticker']})</span></h1>
  <div style="margin-top:6px">{_badge(note.get('recommendation'))}
  <span style="margin-left:8px;font-size:13.5px;color:#c7d4ea">Equity research note · FTSE 100 · thesis dated {(note.get('first_published_at') or note.get('published_at') or '')[:10]} · revised {(note.get('published_at') or '')[:10]}</span></div>
</div></div>
<main>
<div class="backlink no-print"><a href="../../index.html#note-{_esc(note['ticker']).replace('.', '-').lower()}">← Back to dashboard</a></div>
<div class="sumcard">
  <div class="headline">{_esc(_round_raw_floats(note.get('headline') or ''))}</div>
  <div class="sumgrid">
    <div class="cell"><div class="l">Price target</div><div class="v">{_fmt_num(note.get('price_target_gbp'))}</div></div>
    <div class="cell"><div class="l">Upside</div><div class="v">{_fmt_pct(note.get('upside_pct'))}</div></div>
    <div class="cell"><div class="l">Price at publication</div><div class="v">{_fmt_num(ctx.get('price_gbp_at_publication'))}
      <span style="font-size:10.5px;font-weight:500;color:#8593aa"> = {_fmt_num((ctx.get('price_gbp_at_publication') or 0) * 100)}p quoted</span></div></div>
    <div class="cell"><div class="l">Current price</div><div class="v">{_fmt_num((perf or {}).get('last_price'))}
      <span style="font-size:10.5px;font-weight:500;color:#8593aa">refreshed each cycle</span></div></div>
    <div class="cell"><div class="l">Alpha so far</div><div class="v">{_fmt_pct(perf['alpha_pct']) if perf else '<span class="zero">–</span>'}</div></div>
    <div class="cell"><div class="l">Review window</div><div class="v">{note.get('review_period_months')}m</div></div>
    <div class="cell"><div class="l">Audit id</div><div class="v" style="font-size:11px;font-weight:600">{_esc(note.get('publication_audit_id', ''))[:19]}</div></div>
  </div>
  <div class="btns no-print">
    <button class="btn" onclick="window.print()">Download PDF</button>
    <button class="btn" onclick="navigator.clipboard.writeText(location.href).then(()=>this.textContent='Link copied!').catch(()=>this.textContent='Copy failed')">Copy share link</button>
  </div>
</div>

{_guardrail_banner(note)}
{_scenario_widget_html(note)}
{_data_quality_html(note)}

<div class="chartbox">
  <h3 style="margin:2px 0 8px">Stock vs FTSE 100 since thesis (indexed to 100)</h3>
  <canvas id="pxchart" height="240"></canvas>
  <div class="muted">{len(series or [])} closes plotted{'' if series else ' — accrues daily from the first close after publication'}.</div>
</div>

<h2>Thesis</h2>
<p>{_esc(_round_raw_floats(thesis.get('summary') or ''))}</p>
{_bull_base_bear_html(note)}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
  <div><h3>Catalysts</h3><ul>{''.join(f'<li>{_esc(c)}</li>' for c in thesis.get('catalysts', []))}</ul></div>
  <div><h3>Risks</h3><ul>{''.join(f'<li>{_esc(r)}</li>' for r in thesis.get('risks', []))}</ul></div>
</div>
<h3>What would make me wrong</h3>
<ul>{''.join(f'<li>{_esc(w)}</li>' for w in (thesis.get('wrong_if') or ['Not defined on this revision of the note.']))}</ul>
{_esg_html(note)}

<h2>Valuation inputs (frozen at publication)</h2>
<table>
  <tr><th>Input</th><th>Value</th><th>Derivation / source</th></tr>
  {inputs_html}
</table>

{peer_section}

{_sensitivity_grid_html(note)}
{_reverse_dcf_html(note, (perf or {}).get('last_price'))}

{perf_html}
{monthly_html}
{addenda_html}

<h2>Data sources & provenance</h2>
<table>
  <tr><th>Input</th><th>Source</th><th>Derivation</th><th>Retrieved (UTC)</th></tr>
  {prov_html}
</table>
<h3>Model choices (disclosed, not data)</h3>
<ul>{mc_html}</ul>

<h2>How this note was built</h2>
<p class="muted">Generated from live public data by <code>tracker/auto_notes.py</code>:
fundamentals via yfinance (statements FX-converted to GBP at spot), risk-free rate
from FRED (<code>IRLTLT01GBM156N</code>), ERP from Damodaran (Western Europe 4.31%,
Jan 2025 vintage), CAPM cost of equity with Blume-adjusted beta, peer multiples
computed from live prices and statements. The full fetch trail is in
<code>data/audit_log.jsonl</code> (audit id <code>{_esc(note.get('publication_audit_id', ''))}</code>).</p>

<div class="disclaimer"><b>Personal educational project. Not investment advice. Not affiliated with any firm.</b><br>{_esc(config.DISCLAIMER)}
Source &amp; methodology: <a href="{config.REPO_URL}">{config.REPO_URL}</a></div>
</main>
<script>{series_js}</script>
<script>
(() => {{
  const slider = document.getElementById('sc-slider');
  if (!slider) return;
  const table = document.getElementById('sc-table');
  const readout = document.getElementById('sc-readout');
  const rows = Array.from(table.querySelectorAll('tr[data-shock]'));
  const anchors = rows.map(r => ({{ shock: parseFloat(r.dataset.shock), targetEl: r.querySelector('.sc-target') }}));
  const pubRow = anchors.find(a => Math.abs(a.shock) < 1e-9);
  const pubText = pubRow ? pubRow.targetEl.textContent.trim() : null;
  slider.addEventListener('input', () => {{
    // Slider reads in percentage points (-2..2); grid shocks are stored as
    // decimal fractions (-0.02..0.02). Convert once, use consistently.
    const vpp = parseFloat(slider.value);
    const v = vpp / 100;
    const target = vpp === 0 ? (pubText ? 'published target' : '')
      : (() => {{
        const sorted = anchors.slice().sort((a, b) => a.shock - b.shock);
        let lo = sorted[0], hi = sorted[sorted.length - 1];
        for (let i = 0; i < sorted.length - 1; i++) {{
          if (sorted[i].shock <= v && v <= sorted[i + 1].shock) {{ lo = sorted[i]; hi = sorted[i + 1]; break; }}
        }}
        const parse = s => parseFloat(String(s).replace(/[^0-9.\\-]/g, ''));
        const t0 = parse(lo.targetEl.textContent), t1 = parse(hi.targetEl.textContent);
        const val = (hi.shock === lo.shock) ? t0 : t0 + (t1 - t0) * (v - lo.shock) / (hi.shock - lo.shock);
        return val.toFixed(2) + ' GBP';
      }})();
    readout.textContent = (vpp > 0 ? '+' : '') + vpp.toFixed(1) + 'pp → ' + target;
  }});
}})();
</script>
</body>
</html>"""
    out = NOTES_HTML_DIR / _note_filename(note["ticker"])
    out.write_text(doc, encoding="utf-8")


def write_all_note_pages(notes: list[dict], perf_by_ticker: dict,
                         monthly_by_ticker: dict,
                         series_by_ticker: dict | None = None,
                         quotes: dict | None = None) -> None:
    series_by_ticker = series_by_ticker or {}
    quotes = quotes or {}
    for n in notes:
        if n.get("status") == "published":
            tk = n["ticker"]
            perf = perf_by_ticker.get(tk)
            if perf is None:
                # No tracked window yet: show the live quote as the current
                # price so the field is still labelled and populated.
                q = quotes.get(tk) or {}
                if q.get("price_gbp"):
                    perf = {"last_price": q.get("price_gbp")}
            write_note_page(n, perf,
                            monthly_by_ticker.get(tk) or [],
                            series_by_ticker.get(tk))


def _audit_rows_table(rows: list[dict]) -> str:
    """Render audit records as table rows (shared by audit.html + dashboard).

    Detail is shown in full inside an expandable <details> per row: the old
    160-character hard truncation cut off provenance payloads (derivation
    strings, beta diagnostics) entirely.
    """
    out = []
    for r in rows:
        detail = json.dumps({k: v for k, v in r.items() if k not in ("ts", "event")})
        if len(detail) > 160:
            summary = _esc(detail[:160]) + " …"
            body = (f'<details><summary style="cursor:pointer">{summary}</summary>'
                    f'<pre style="white-space:pre-wrap;margin:6px 0 0;font-size:11.5px">'
                    f"{_esc(detail)}</pre></details>")
        else:
            body = _esc(detail)
        out.append(
            f"<tr><td>{_esc(str(r.get('ts', '')))[:19]}</td>"
            f"<td><code>{_esc(str(r.get('event', '')))}</code></td>"
            f"<td>{body}</td></tr>"
        )
    return "".join(out)


def write_publish_bundle() -> None:
    """Assemble the deployable static site under publish/.

    Copies dashboard/index.html as the root, all note pages, and the
    full machine-readable evidence trail (note JSON + markdown + snapshots).
    Also writes an audit.html viewer so the append-only log is inspectable
    straight from the deployed site.
    """
    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Dashboard at the root (links are relative: notes/html/<slug>.html)
    shutil.copyfile(DASH_FILE, PUBLISH_DIR / "index.html")

    # 2. Note pages (relies on write_all_note_pages having just run)
    if NOTES_HTML_DIR.exists():
        shutil.copytree(NOTES_HTML_DIR, PUBLISH_DIR / "notes" / "html",
                        dirs_exist_ok=True)

    # 3. Evidence trail: note JSON + markdown (top level only) + revision snapshots
    if NOTES_DIR.exists():
        dst = PUBLISH_DIR / "notes" / "data"
        dst.mkdir(parents=True, exist_ok=True)
        for pattern in ("*.json", "*.md"):
            for f in NOTES_DIR.glob(pattern):
                shutil.copyfile(f, dst / f.name)
    if SNAPSHOTS_DIR.exists():
        shutil.copytree(SNAPSHOTS_DIR, PUBLISH_DIR / "notes" / "snapshots",
                        dirs_exist_ok=True)

    # 4. Audit-log viewer: fetchable from the deployed site
    rows = audit.tail(500)
    body = _audit_rows_table(rows)
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<title>Audit log viewer</title><style>"
        "body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;margin:24px;color:#16233b;background:#f4f6fa}"
        "h1{color:#0f3460;font-size:22px}p{font-size:13px;color:#6b7a93}"
        "table{border-collapse:collapse;width:100%;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 2px rgba(15,23,42,0.06)}"
        "th,td{border-bottom:1px solid #e5e7eb;padding:7px 10px;text-align:left;font-size:12.5px}"
        "th{background:#eef2f8;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#51617a}"
        "code{font-size:11.5px}"
        "details summary{cursor:pointer;color:#0f3460}"
        "details pre{background:#f8fafc;border:1px solid #e5e7eb;border-radius:6px;padding:8px}"
        "@media(max-width:640px){body{margin:12px}th,td{padding:5px 7px;font-size:12px}}"
        "</style></head><body>"
        "<h1>Append-only audit log (last 500 events)</h1>"
        "<p>Raw JSONL: <a href='audit_log.jsonl'>audit_log.jsonl</a> "
        "&mdash; every quote fetch, note publication, and refresh cycle is recorded here, append-only.</p>"
        "<table><tr><th>Timestamp (UTC)</th><th>Event</th><th>Detail</th></tr>" + body +
        "</table></body></html>"
    )
    audit_page = PUBLISH_DIR / "audit.html"
    audit_page.write_text(html, encoding="utf-8")

    # 5. Raw JSONL: into the bundle (Pages) and next to the working dashboard
    #    (local preview), so the footer links resolve in both places.
    src_log = audit._log_path()
    if src_log.exists():
        shutil.copyfile(src_log, PUBLISH_DIR / "audit_log.jsonl")
        if DASH_FILE.parent != PUBLISH_DIR:
            shutil.copyfile(audit_page, DASH_FILE.parent / "audit.html")
            shutil.copyfile(src_log, DASH_FILE.parent / "audit_log.jsonl")
