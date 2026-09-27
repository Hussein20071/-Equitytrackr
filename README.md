# UK Equity Research & Portfolio Tracker

[![Deploy dashboard](https://github.com/Xzarth/-Equitytrackr/actions/workflows/deploy.yml/badge.svg)](https://github.com/Xzarth/-Equitytrackr/actions/workflows/deploy.yml) **Live site:** https://xzarth.github.io/-Equitytrackr/

An **audit-ready equity research and portfolio attribution system** for FTSE 100 names. Every published research note contains a dated thesis, explicit valuation inputs derived from live public data, a clear 12-month price target, per-input provenance — and is then **tracked for 3 months against the FTSE 100**, with alpha, hit-rate, volatility, and drawdown statistics on a live dashboard.

**No illustrative numbers.** Every input on every note is either fetched from a public source or derived by a formula that is printed on the note itself. When a required fact is unavailable, the valuation leg is skipped and the note says so — nothing is substituted.

## Methodology (short form, as used on every note)

> DCF using a 5-year explicit forecast; growth = FCF CAGR (FY21–FY25 statements via yfinance), 50% damped toward 0, floor/cap −5%/+15%; terminal growth = min(10Y UK gilt yield, half the explicit CAGR); WACC = CAPM cost of equity (FRED 10Y gilt, Damodaran Western-Europe ERP 4.31%, Blume-adjusted beta, floor 0.40); blended 12-month target = 60% DCF / 20% Gordon DDM / 20% peer-median comparables (weights renormalise over available legs; banks use 60% DDM / 40% P/E).

## CV bullet (paste verbatim)

*Built an independent UK equity research & portfolio tracker that publishes dated stock pitches with DCF (CAPM-derived WACC), DDM, and comparables valuations from live public data (yfinance, FRED, Damodaran), each with a price target, frozen inputs, and per-input provenance in an append-only audit log; benchmarked every thesis vs the FTSE 100 over a 3-month window and reports hit rate, directional accuracy, alpha, volatility, and max drawdown on an auto-refreshed dashboard.*

## What a published note contains

- **Scannable headline**: recommendation, target, upside, thesis date
- **Frozen input table**: every valuation input with its value and derivation/source
- **Provenance section**: source, derivation string, and retrieval timestamp per input, plus explicitly disclosed model choices (damping, caps, weights)
- **Peer comparables**: live multiples per peer, with not-meaningful exclusions recorded
- **Tracked performance**: return, FTSE return, alpha, annualised volatility, max drawdown, monthly attribution
- **Dated addenda**: learning notes and thesis checks appended after publication — never edits

## Data sources

| Input | Source |
|---|---|
| Prices, statements, dividends | Yahoo Finance via `yfinance` (FX-converted to GBP) |
| Risk-free rate | FRED `IRLTLT01GBM156N` (10Y UK gilt, OECD LT rate) |
| Equity risk premium | Damodaran country risk premium (Western Europe, Jan 2025) |
| Benchmark history | Yahoo Finance `^FTSE` daily closes |

Every fetch is appended to `data/audit_log.jsonl` (JSONL, append-only): event, tickers, status, counts, timestamps. Published notes store audit references for the exact fetches behind their inputs.

## Quick start

```bash
pip install -r requirements.txt

# publish notes for the whole universe from live data (or list tickers)
python -m tracker.cli notes            # add --force to refetch cached fundamentals

# one refresh cycle now, or the continuous 5-minute loop
python -m tracker.cli refresh
python -m tracker.cli loop             # --interval N for a custom cadence

# dated post-publication commentary (never edits the note)
python -m tracker.cli addendum HSBA.L learning "what changed and why"

# inspect state
python -m tracker.cli status
```

Outputs: `dashboard/index.html` (dashboard with expandable notes), `notes/html/<ticker>.html` (standalone print/PDF-ready note pages), `notes/<ticker>.json|.md` (machine + markdown), `data/audit_log.jsonl`.

## Free hosting (GitHub Pages)

The dashboard deploys as a static site that **GitHub Actions rebuilds from live data on a schedule** — the cloud reruns `python -m tracker.cli refresh` (real Yahoo/FRED fetches, real valuation math), assembles the `publish/` bundle, and deploys it. The site stays fresh with your laptop off.

One-time setup:

```bash
# 1. create an empty public repo on github.com (e.g. uk-equity-tracker), then:
git config user.name "Your Name"        # + --global to set for all repos
git config user.email "you@example.com" # use your GitHub noreply email if you prefer

git init -b main
git add .
git commit -m "Initial commit: audit-ready UK equity research tracker"
git remote add origin https://github.com/<you>/uk-equity-tracker.git
git push -u origin main

# 2. on github.com: Settings -> Pages -> Source: "GitHub Actions"
# 3. Actions tab -> "Deploy dashboard" -> Run workflow (first deploy)
```

After that the workflow schedule takes over: every 30 minutes during LSE hours (07:00–16:30 UTC, Mon–Fri) plus one post-close run at 21:00 UTC, the dashboard and audit trail are regenerated from live market data and redeployed. Site URLs: the dashboard root, `notes/html/<ticker>.html` per-note pages (PDF-ready), `audit.html` (audit-log viewer), and `audit_log.jsonl` (raw append-only log).

## Honesty rules the code enforces

1. **Units are converted, not assumed.** LSE quotes are GBp (÷100); foreign-listed peers are converted at spot (`GBPxxx=X`); dividend history follows the listing currency (pence on `.L`, units elsewhere); EPS is derived as net income ÷ shares because Yahoo's `trailingEps` is inconsistent across listing venues.
2. **A missing fact skips a leg — it never becomes a placeholder.** The blend renormalises over available legs and each note shows what was omitted and why.
3. **Cyclical/distorted data is excluded with a recorded reason**: peer P/E > 60× or EV/EBITDA > 30× (impairment-depressed bases), single-peer "medians" (need ≥2), subject P/E legs when the subject's own earnings are depressed, DDM `g` capped at 0.7× the risk-free rate, sign-flipping FCF histories fall back to disclosed 0% growth.
4. **Model choices are labelled as model choices** — damping, caps, and weights are printed on every note under "Model choices (disclosed, not data)".
5. **Published notes are immutable.** Revisions archive the prior version under `notes/snapshots/`; corrections after publication are dated addenda.
6. **Banks get a bank valuation**: FCF DCF is omitted (operating cash flow includes deposit flows); DDM + P/E is used instead, and the note says so.

## Tests

```bash
python -m pytest tests/ -v    # 24 tests: DCF math, growth derivation, DDM caps,
                              # comps exclusions, blending, attribution, drawdown,
                              # display hygiene, deploy-bundle layout
```

## Known limitations (disclosed, not hidden)

- Base FCF is a single latest-FY figure, not a normalised mid-cycle estimate; commodity names will screen cheap at earnings peaks.
- yfinance fundamentals are occasionally restated mid-stream; the frozen inputs + audit log make any restatement visible.
- Damodaran's ERP updates annually; the vintage in use is recorded on each note.
- The 3-month tracked window is short; hit-rate statistics become meaningful only as the track record accumulates.

## Disclaimer

Educational project. Not investment advice. Third-party data may be delayed or inaccurate; verify independently before acting on anything here.
