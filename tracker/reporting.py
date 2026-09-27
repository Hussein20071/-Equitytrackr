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

from . import audit, config

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


def _perf_rows_html(perf_rows: list[dict], series_by_ticker: dict) -> str:
    if not perf_rows:
        return '<tr><td colspan="9" class="muted">No published notes yet.</td></tr>'
    out = []
    for r in perf_rows:
        slug = _note_filename(r["ticker"]).replace(".html", "")
        spark = _sparkline_svg(series_by_ticker.get(r["ticker"]) or [])
        out.append(
            "<tr>"
            f'<td><a href="#note-{slug}"><strong>{_esc(r["ticker"])}</strong></a></td>'
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


def _kpi_cards(summary: dict) -> str:
    if not summary or summary.get("n", 0) == 0:
        return '<div class="muted">Publish notes to build the track record.</div>'
    hit = summary.get("hit_rate_pct", 0)
    dir_acc = summary.get("directional_accuracy_pct", 0)
    cards = [
        ("NOTES TRACKED", summary["n"], "published & frozen", "kpi-neutral"),
        ("HIT RATE", f"{hit}%", "alpha > 0 vs FTSE", "kpi-good" if hit >= 50 else "kpi-warn"),
        ("DIRECTIONAL ACC", f"{dir_acc}%", "calls that moved the right way", "kpi-good" if dir_acc >= 50 else "kpi-warn"),
        ("AVG ALPHA", f"{summary.get('avg_alpha_pct', 0):+.2f}%", "vs FTSE 100", "kpi-good" if summary.get("avg_alpha_pct", 0) > 0 else "kpi-warn"),
        ("AVG RETURN", f"{summary.get('avg_return_pct', 0):+.2f}%", "since thesis dates", "kpi-neutral"),
        ("WORST DRAWDOWN", _fmt_pct(summary.get("worst_drawdown_pct")).replace('<span class="neg">', "").replace('<span class="zero">', "").replace("</span>", ""), "peak-to-trough", "kpi-warn"),
        ("AVG ANN. VOL", f"{_fmt_num(summary.get('avg_ann_vol_pct'), 1)}%", "of tracked names", "kpi-neutral"),
        ("TRADING DAYS", summary.get("total_trading_days", 0), "of evidence", "kpi-neutral"),
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

    inputs_rows = [
        ("Base FCF (latest FY)", _fmt_num(dcf.get("base_fcf_m"), 1) + " GBPm",
         "Yahoo cash_flow: OCF − capex, FX→GBP"),
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
  <div class="nc-stats">
    <div><span class="l">Target</span><span class="v">{_fmt_num(note.get('price_target_gbp'))}</span></div>
    <div><span class="l">Upside</span><span class="v">{upside_html}</span></div>
    <div><span class="l">Alpha so far</span><span class="v">{alpha_html}</span></div>
    <div><span class="l">Window</span>{progress}</div>
    <div class="nc-spark"><span class="l">Since thesis</span>{spark}</div>
  </div>
  <details>
    <summary>Full note — thesis, frozen inputs, provenance</summary>
    <p>{_esc(_round_raw_floats(thesis.get('summary') or ''))}</p>
    <div class="cols2">
      <div><h4>Catalysts</h4><ul class="tight">{li(thesis.get('catalysts', []))}</ul></div>
      <div><h4>Risks</h4><ul class="tight">{li(thesis.get('risks', []))}</ul></div>
    </div>
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
                    caption: str = "") -> None:
    """Render index.html (the dashboard) from current data."""
    DASH_FILE.parent.mkdir(parents=True, exist_ok=True)

    notes = notes or []
    perf_by_ticker = perf_by_ticker or {}
    monthly_by_ticker = monthly_by_ticker or {}
    series_by_ticker = series_by_ticker or {}
    qrows = _qrows(quotes)
    n_curve = len(curve or [])
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
  @media (max-width:640px) {{ .cols2 {{ grid-template-columns:1fr; }} }}
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
<main>
  <div class="caption"><b>Track record:</b> {_esc(caption)}</div>

  <h2>Market snapshot — live LSE quotes</h2>
  <p class="muted">The London Stock Exchange quotes in <b>pence (GBp)</b>; Yahoo shows "12,552" for AstraZeneca — the same security this table lists at <b>£125.52</b> (12,552p ÷ 100). All valuation work on this site is in GBP (£); the pence column is shown so you can cross-check against Yahoo/Google Finance directly.</p>
  <table>{_qtable(qrows)}</table>

  <h2>Track record vs FTSE 100 — 3-month window per thesis</h2>
  <div class="kpis">{_kpi_cards(summary)}</div>
  <table>
    <tr><th>Ticker</th><th>Thesis date</th><th>Price path</th><th>Chart</th><th>Return</th><th>Alpha</th><th>Ann. vol</th><th>Max DD</th><th>Rec</th></tr>
    {_perf_rows_html(perf_rows, series_by_ticker)}
  </table>
  <div class="muted" style="margin-top:6px">Vol = annualised volatility of daily returns · Max DD = maximum drawdown over the tracked window · click a ticker to jump to its note, expand the card for full inputs.</div>

  <h2>Research notes</h2>
  <div class="notecards">{cards_html}</div>

  <div class="card">
    <h2 style="margin-top:0">Model portfolio vs FTSE 100 (indexed to 100, trailing 3 months)</h2>
    <canvas id="curve" width="1100" height="300"></canvas>
    <div class="muted">{n_curve} trading days plotted. {CAPTION_NOTHING}</div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Methodology &amp; audit trail</h2>
    <ul class="tight">
      <li><b>Valuation:</b> 5-year explicit FCF forecast (growth = history-derived CAGR, 50% damped, −5%/+15% bounds), terminal g = min(10Y gilt, CAGR/2), WACC = CAPM cost of equity (Blume-adjusted beta, floor 0.40). Blend: 60% DCF / 20% DDM / 20% comps; banks 60% DDM / 40% P/E.</li>
      <li><b>Frozen inputs:</b> every input is snapshotted at publication with source + derivation; revisions archive under <code>notes/snapshots/</code>; corrections are dated addenda, never edits.</li>
      <li><b>Audit log:</b> every fetch, publication, and refresh appends to <code>data/audit_log.jsonl</code> — each note stores the audit ids of the fetches behind its numbers.</li>
      <li><b>Exclusions are recorded:</b> peer multiples above NM caps, single-peer medians, depressed-earnings P/E legs — each note shows what was excluded and why.</li>
    </ul>
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
  <span>Regenerated from live market data every refresh cycle &middot; <a href="#audit-trail" style="color:var(--navy)">view the append-only audit trail</a></span>
  <span>Python 3.11 &middot; yfinance &middot; FRED &middot; Damodaran</span>
</footer>
<script>
const curveData = {curve_data_js};
if (curveData.length > 1) {{
  new Chart(document.getElementById('curve'), {{
    type: 'line',
    data: {{ labels: curveData.map(r => r[0]),
      datasets: [
        {{ label: 'Model portfolio', data: curveData.map(r => r[1]), borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.08)', fill: true, tension: 0.2, pointRadius: 0, borderWidth: 2 }},
        {{ label: 'FTSE 100', data: curveData.map(r => r[2]), borderColor: '#94a3b8', borderDash: [6, 4], fill: false, tension: 0.2, pointRadius: 0, borderWidth: 1.5 }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: 'bottom' }} }},
      scales: {{ x: {{ ticks: {{ maxTicksLimit: 10 }} }}, y: {{ title: {{ display: true, text: 'Index (start = 100)' }} }} }}
    }}
  }});
}}
</script>
</body>
</html>"""
    DASH_FILE.write_text(doc, encoding="utf-8")

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
        ("Base FCF (latest FY)", _fmt_num(dcf.get("base_fcf_m"), 1) + " GBPm",
         "Yahoo cash_flow: OCF − capex, FX-converted to GBP"),
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
            "<h2>Tracked performance vs FTSE 100</h2>"
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
  ul {{ padding-left:20px; }}
  .disclaimer {{ color:#6b7a93; font-size:12px; border-top:1px solid #d7dee9; margin-top:30px; padding-top:12px; }}
  .muted {{ color:#6b7a93; font-size:12.5px; }}
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
  <span style="margin-left:8px;font-size:13.5px;color:#c7d4ea">Equity research note · FTSE 100 · thesis dated {note.get('published_at', '')[:10]}</span></div>
</div></div>
<main>
<div class="sumcard">
  <div class="headline">{_esc(_round_raw_floats(note.get('headline') or ''))}</div>
  <div class="sumgrid">
    <div class="cell"><div class="l">Price target</div><div class="v">{_fmt_num(note.get('price_target_gbp'))}</div></div>
    <div class="cell"><div class="l">Upside</div><div class="v">{_fmt_pct(note.get('upside_pct'))}</div></div>
    <div class="cell"><div class="l">Price at pub.</div><div class="v">{_fmt_num(ctx.get('price_gbp_at_publication'))}</div></div>
    <div class="cell"><div class="l">Alpha so far</div><div class="v">{_fmt_pct(perf['alpha_pct']) if perf else '<span class="zero">–</span>'}</div></div>
    <div class="cell"><div class="l">Review window</div><div class="v">{note.get('review_period_months')}m</div></div>
    <div class="cell"><div class="l">Audit id</div><div class="v" style="font-size:11px;font-weight:600">{_esc(note.get('publication_audit_id', ''))[:19]}</div></div>
  </div>
  <div class="btns no-print">
    <button class="btn" onclick="window.print()">Download PDF</button>
    <button class="btn" onclick="navigator.clipboard.writeText(location.href).then(()=>this.textContent='Link copied!').catch(()=>this.textContent='Copy failed')">Copy share link</button>
  </div>
</div>

<div class="chartbox">
  <h3 style="margin:2px 0 8px">Stock vs FTSE 100 since thesis (indexed to 100)</h3>
  <canvas id="pxchart" height="240"></canvas>
  <div class="muted">{len(series or [])} closes plotted{'' if series else ' — accrues daily from the first close after publication'}.</div>
</div>

<h2>Thesis</h2>
<p>{_esc(_round_raw_floats(thesis.get('summary') or ''))}</p>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
  <div><h3>Catalysts</h3><ul>{''.join(f'<li>{_esc(c)}</li>' for c in thesis.get('catalysts', []))}</ul></div>
  <div><h3>Risks</h3><ul>{''.join(f'<li>{_esc(r)}</li>' for r in thesis.get('risks', []))}</ul></div>
</div>

<h2>Valuation inputs (frozen at publication)</h2>
<table>
  <tr><th>Input</th><th>Value</th><th>Derivation / source</th></tr>
  {inputs_html}
</table>

{peer_section}

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

<div class="disclaimer">{_esc(config.DISCLAIMER)}</div>
</main>
<script>{series_js}</script>
</body>
</html>"""
    out = NOTES_HTML_DIR / _note_filename(note["ticker"])
    out.write_text(doc, encoding="utf-8")


def write_all_note_pages(notes: list[dict], perf_by_ticker: dict,
                         monthly_by_ticker: dict,
                         series_by_ticker: dict | None = None) -> None:
    series_by_ticker = series_by_ticker or {}
    for n in notes:
        if n.get("status") == "published":
            tk = n["ticker"]
            write_note_page(n, perf_by_ticker.get(tk),
                            monthly_by_ticker.get(tk) or [],
                            series_by_ticker.get(tk))


def _audit_rows_table(rows: list[dict]) -> str:
    """Render audit records as table rows (shared by audit.html + dashboard)."""
    return "".join(
        f"<tr><td>{_esc(str(r.get('ts', '')))[:19]}</td>"
        f"<td><code>{_esc(str(r.get('event', '')))}</code></td>"
        f"<td>{_esc(json.dumps({k: v for k, v in r.items() if k not in ('ts', 'event')}))[:160]}</td></tr>"
        for r in rows
    )


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
