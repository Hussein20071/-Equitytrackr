# UK Equity Research & Portfolio Tracker

[![Deploy dashboard](https://github.com/Hussein20071/-Equitytrackr/actions/workflows/deploy.yml/badge.svg)](https://github.com/Hussein20071/-Equitytrackr/actions/workflows/deploy.yml) **Live site:** https://hussein20071.github.io/-Equitytrackr/

An **audit-ready equity research and portfolio attribution system** for 8 FTSE 100 names (AZN, SHEL, HSBA, ULVR, GSK, BP, NG, RIO), built by Hussein Mohamed (King's College London; aspiring asset-management professional). Every published research note contains a dated thesis, explicit valuation inputs derived from live public data, a blended 12-month price target with a ±30% model-outlier guardrail, per-input provenance in an **append-only audit log** — and is then **tracked against the FTSE 100**, with the track record split honestly into a live record (since first publication) and a labelled-hypothetical backtest.

**No illustrative numbers.** Every input on every note is either fetched from a public source or derived by a formula printed on the note itself. When a required fact is unavailable, the affected valuation leg is dropped with the reason on the note — nothing is substituted or estimated.

## Architecture

```
tracker/
  data.py          Yahoo Finance fetch layer: quotes, history (adjusted close =
                   total return), FX, per-name OLS beta vs ^FTSE (2y weekly)
  fundamentals.py  Statements via yfinance, FX-converted to GBP; FRED 10Y gilt
                   (valuation rf) + FRED 3M UK rate (Sharpe rf); Damodaran ERP
  valuation.py     Pure math: DCF, DDM, comps, blend, ±30% outlier guardrail,
                   reverse DCF (price → implied perpetual growth)
  research.py      Note build/publish: frozen inputs, guardrail storage, ESG +
                   calendar fetchers, correction-preserving re-publication
  scenario.py      Reader scenarios: rate shocks, 5×5 WACC×terminal-g grid,
                   bull/base/bear, refresh-over-refresh quote diffs
  performance.py   Live-record tracking per note (first publication → latest
                   close), hit rate / directional accuracy, portfolio-curve
                   metrics (vol, max DD, beta, tracking error, Sharpe)
  portfolio.py     £100k weights table, 0.5% stamp + 0.1% commission cost
                   basis, sector mix, cached FTSE 100 sector weights
  reporting.py     All HTML: dashboard, note pages, audit viewer, mobile CSS
  refresh.py       One refresh cycle: fetch → value → render → audit
  cli.py           refresh / loop / notes / addendum / sectors / status
.github/workflows/deploy.yml   pytest → refresh → guard → GitHub Pages deploy
```

## Methodology

- **Valuation:** 5-year explicit FCF forecast (growth = history-derived FCF CAGR, 50% damped toward 0, bounds −5%/+15%; falls back to a disclosed 0% path when the FCF history is insufficient or sign-flipping). Terminal growth = min(10Y gilt, explicit CAGR/2). WACC = CAPM cost of equity: beta from a 2-year weekly OLS regression vs ^FTSE (per-name; Blume-adjusted, floor 0.40), FRED 10Y gilt risk-free, Damodaran Western-Europe ERP 4.31% (Jan 2025 vintage, recorded on each note). Blend 60% DCF / 20% DDM / 20% comps; banks 60% DDM / 40% P/E (FCF DCF omitted for banks — deposit flows).
- **Base FCF:** latest-FY OCF − capex. If the latest FY is missing/non-finite, a **normalised multi-year average** of the finite trailing FYs is used (disclosed in the derivation). If trailing FCF is non-positive (e.g. NG's heavy network capex), the **DCF is excluded with the recorded reason** and the blend re-weights over surviving legs.
- **Guardrail:** any blended target more than **±30%** from the market price is flagged **"Model outlier — under review"** with the driving leg (largest weighted contribution to the gap) named on the note. The **reverse DCF** then states what perpetual FCF growth the *current price* implies at the frozen WACC.
- **Performance:** live record = each note tracked from its **first-publication close** (revisions do not reset the clock) to the latest close. **Hit rate** = share of notes with alpha > 0 vs FTSE 100; **directional accuracy** = share of calls that moved the way the recommendation said (BUY up / SELL down / HOLD ±10%). Portfolio metrics are computed **on the portfolio return series** (never averaged stock stats): ann. vol = std(daily r)×√252; max drawdown = min(V_t/max(V)−1); beta = cov(r_p,r_b)/var(r_b); tracking error = std(r_p−r_b)×√252; CAGR = (1+total)^(252/n)−1; Sharpe = (CAGR − UK 3M rate)/ann. vol.
- **Return basis & costs:** total return (Yahoo adjusted close, dividends reinvested). Costs: 0.5% stamp duty reserve tax + 0.1% commission on buys, applied once at inception (−0.6% start-of-period drag). No ongoing costs modelled.
- **Frozen inputs:** every input is snapshotted at publication with source + derivation; revisions archive under `notes/snapshots/`; corrections are dated addenda, never edits. The tracked window anchors at first publication.

## Data sources

| Input | Source |
|---|---|
| Prices, statements, dividends, ESG scores, calendars | Yahoo Finance via `yfinance` (FX-converted to GBP) |
| Valuation risk-free rate | FRED `IRLTLT01GBM156N` (10Y UK gilt, OECD LT rate) |
| Sharpe risk-free rate | FRED `IR3TIB01GBM156N` (3M UK immediate rate; 10Y fallback, disclosed) |
| Equity risk premium | Damodaran country risk premium (Western Europe, Jan 2025) |
| Benchmark history | Yahoo Finance `^FTSE` daily closes (adjusted) |
| FTSE 100 sector weights | Wikipedia FTSE 100 table (ICB supersector market caps, attributed there to Bloomberg), cached to `data/ftse_sector_weights.json` with retrieval date |

Every fetch is appended to `data/audit_log.jsonl` (JSONL, append-only): event, tickers, status, counts, timestamps. Published notes store audit references for the exact fetches behind their inputs. Long audit payloads render expandably on the site (no truncation).

## Quick start

```bash
pip install -r requirements.txt
python -m pytest tests/ -q               # 58 tests

# publish notes for the whole universe from live data (or list tickers)
python -m tracker.cli notes              # --force refetches cached fundamentals
                                         # --correction "text" appends a dated
                                         # correction addendum on re-publication

# one refresh cycle now, or the continuous loop
python -m tracker.cli refresh
python -m tracker.cli loop --interval 5

# refresh the cached FTSE 100 sector weights (run occasionally; committed)
python -m tracker.cli sectors

# dated post-publication commentary (never edits the note)
python -m tracker.cli addendum HSBA.L learning "what changed and why"

# inspect state
python -m tracker.cli status
```

Outputs: `dashboard/index.html`, `notes/html/<ticker>.html` (print/PDF-ready), `notes/<ticker>.json|.md`, `notes/snapshots/`, `data/audit_log.jsonl`, `publish/` (deploy bundle).

## Live updates

- **Cloud (this site):** GitHub Actions re-fetches every quote and re-renders the whole site **every 5 minutes during London market hours** (Mon–Fri), once after the US close, and once each weekend day. GitHub's scheduler minimum is 5 minutes and runs can be delayed under load — platform floor, not the app.
- **Your open tab:** the dashboard polls `refresh_meta.json` every 60s → **"Prices updated — view now"** toast (cache-busted) or an **auto-reload interval** (off / 1 / 5 / 10 min), remembered in `localStorage`.
- **Local (optional):** `python -m tracker.cli loop --interval 1`.

## Honesty rules the code enforces

1. **Units are converted, not assumed** — LSE quotes are GBp (÷100); peers convert at spot; EPS is derived as NI ÷ shares (Yahoo's `trailingEps` is inconsistent across listing venues).
2. **A missing fact skips a leg — never a placeholder.** The blend renormalises; the note shows what was omitted and why.
3. **Distorted data is excluded with a recorded reason** — peer P/E > 60× or EV/EBITDA > 30×, single-peer "medians", depressed subject earnings, DDM g capped at 0.7×rf, non-positive FCF histories.
4. **Model choices are labelled as model choices** (damping, caps, weights, sector classification) on every note.
5. **Published notes are immutable**; corrections are dated addenda; the audit log records guardrail flags and revisions.
6. **Banks get a bank valuation** (DDM + P/E), utilities with negative FCF get an explicit DCF exclusion, and every deviation beyond ±30% is flagged rather than buried.

## Known limitations (disclosed, not hidden)

- 8-name universe, not the full FTSE 100; sector comparison uses ICB supersector caps as of the cached retrieval date.
- Yahoo fundamentals can be restated mid-stream; frozen inputs + audit log make restatements visible.
- ESG scores (Sustainalytics via Yahoo) are unavailable for several LSE names — omitted, never estimated.
- A short track record: hit-rate/directional-accuracy figures become meaningful only as the windows accumulate; the backtest is hypothetical by construction.
- Transaction costs are an assumption (stated), not executed-trade data.

## Disclaimer

Personal educational project. Not investment advice. Not affiliated with any firm. Third-party data may be delayed or inaccurate; verify independently.
