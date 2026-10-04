# Changelog

All notable changes to the tracker. Dates are UTC. Corrections to published
notes are additionally recorded as dated addenda on the notes themselves and
in the append-only audit log — entries here never replace those.

## 2026-10-04 — Professional upgrade: track-record honesty, model sanity, portfolio construction, note depth, finish

### 1. Track-record honesty
- Dashboard split into **"Live record"** (each note tracked from its first-publication
  close — 2026-09-19 — to the latest close; revisions do not reset the clock) and a
  separate **"Backtest"** section labelled **HYPOTHETICAL** (current weights applied to
  the trailing 3 months). The two windows are never mixed on screen.
- Fixed the "64 vs ~40 trading days" inconsistency by labelling both numbers precisely:
  the portfolio chart shows its own window with start/end dates; the KPI is renamed
  **"NOTE-DAYS"** with the subtitle "sum of per-note trading days" (not calendar days,
  not the portfolio window length).
- Every performance figure is date-stamped: per-note rows show thesis date → end date;
  KPI cards carry the window span; the caption states start → end and trading-day count.
- On-screen definitions added: **hit rate** (share of notes beating FTSE, alpha > 0) vs
  **directional accuracy** (share of calls that moved the recommended way: BUY up /
  SELL down / HOLD ±10%), plus alpha and day-change definitions.
- `performance.note_performance` now anchors at `first_published_at` (new note field,
  inherited from the earliest `notes/snapshots/` entry) and returns `end_date`.
- "Price at publication" and "Current price" are separate labelled fields on the
  dashboard cards and note pages; note pages also show the first-publication price.

### 2. Model sanity checks
- New **±30% model-outlier guardrail** (`valuation.outlier_check`): runs at publication,
  stored on the note (`model_checks`), audited (`model_outlier_flagged`), and rendered as
  a red banner naming the **driving leg** (largest weighted contribution to the gap) with
  per-leg deviations vs price.
- **AZN diagnosis (SELL −52%):** no input error found — latest-FY FCF (GBP 6,548m) is the
  *highest* of the trailing four years; growth is the +6.2% historical CAGR damped 50% to
  +3.1%; WACC 10.2% is genuinely implied by measured 2-year beta 1.31. The model-vs-market
  gap is now disclosed rather than buried: AZN (and HSBA) carry the "Model outlier — under
  review" banner, and the reverse DCF states what growth the market price implies
  (AZN: ~7.3% perpetual at the frozen WACC vs +6.2% achieved historically).
- **Beta methodology upgraded:** 2-year weekly OLS vs ^FTSE (~104 obs, min 52) replaces the
  1-year window after BP and SHEL pinned at the 0.40 beta floor (1y betas −0.23 / +0.12).
  All 8 notes re-frozen and re-published with the dated correction addendum.
- **RIO (FCF = NaN):** DCF leg restored on a **normalised multi-year FCF average**
  (GBP 5,900m over the finite FY2022–24); derivation discloses the substitution. RIO's
  recommendation changed BUY → SELL (−17.8%, inside the guardrail band) — a dated
  thesis_check addendum explains the flip and flags the sharp leg disagreement
  (DCF 35.86 vs EV/EBITDA leg 156.92).
- **NG (negative FCF):** DCF excluded with the explicit recorded reason ("FY FCF
  non-positive in 3 of the 4 trailing financial years (6, −514, −2,498, −2,746 GBPm) — a
  DCF cannot be run from a negative base"); blend re-weights transparently (comps only).
- Data-quality box upgraded to show the recorded exclusion/normalisation reasons verbatim.

### 3. Portfolio construction
- New `tracker/portfolio.py`: explicit **weights table** on a **£100,000 notional** —
  position £ and %, sector (ICB supersector, disclosed mapping), price, approx shares,
  per-position one-off buy cost.
- **Return basis stated:** total return (Yahoo adjusted close, dividends reinvested).
- **Transaction-cost assumption stated:** 0.5% stamp duty reserve tax + 0.1% commission on
  buys, applied once at inception (−0.6% start-of-period drag; benchmark untouched).
- **Portfolio-level risk metrics computed on the portfolio return series** (never an
  average of stock stats): annualised volatility, max drawdown, beta vs FTSE 100,
  tracking error, Sharpe (UK 3M immediate rate, FRED `IR3TIB01GBM156N`, obs date
  disclosed; 10Y fallback), CAGR. Formulas shown in the on-site methodology.
- **Sector exposure vs FTSE 100:** model mix per ICB supersector against real FTSE 100
  sector weights (Wikipedia constituent table, attributed to Bloomberg; cached to
  `data/ftse_sector_weights.json` with retrieval date; `python -m tracker.cli sectors`
  refreshes; comparison omitted honestly if the cache is stale).

### 4. Each stock note
- **Three-sentence plain-English thesis** (what the model says vs price; why — the leg
  drivers; what would prove it wrong), generated from computed facts only.
- **Bull / base / bear** with a price and the key assumption per case (same frozen-input
  machinery as the reader scenarios: ±2pp discount rate; base = published anchor, never
  recomputed).
- **2–3 dated catalysts** from the Yahoo earnings calendar where a *future* date exists;
  honest "not published by the feed" fallback otherwise (past dates are never labelled
  "next"). "What would make me wrong" list on every note and page.
- **5×5 WACC × terminal-growth sensitivity grid** (DCF leg, frozen inputs) and a
  **reverse DCF** ("the current price implies X% FCF growth in perpetuity").
- **ESG/stewardship note**: Sustainalytics risk scores via the Yahoo feed where available
  (direction of scale stated); explicit "no score available on the feed — omitted rather
  than estimated" otherwise. Valuation impact stated as none-modelled.

### 5. Professional finish
- **About section** on the dashboard (who, why, tools, known limitations).
- **Footer disclaimer** on every page: "Personal educational project. Not investment
  advice. Not affiliated with any firm." + GitHub repo link.
- **README** rewritten: architecture map, data sources, methodology with formulas, run
  instructions, honesty rules, limitations. **CHANGELOG.md** added (this file).
- **58 pytest tests** (from 41): guardrail attribution, reverse DCF round-trip, 5×5 grid
  shape/monotonicity, bull/base/bear ordering, portfolio metrics (vol/DD/beta/TE/Sharpe),
  inception-cost application, weights-table arithmetic, first-publication tracking anchor,
  correction-preserving re-publication. Deploy badge already present (workflow runs pytest).
- **Audit-log truncation fixed**: long payloads now render fully inside a per-row
  expandable `<details>` (short rows stay plain).
- **Top navigation** (Overview / Portfolio / Notes / Methodology / Audit / About /
  Audit viewer) and **mobile-friendly CSS** (wrapping nav, overflow-safe tables,
  collapsed grids).
- Note pages gained a back-to-dashboard link and revised/first-published dates in the header.

### Verification
- 58/58 pytest; dashboard regenerated from live data; guardrail banners verified for
  AZN (−48.8%, driver DCF) and HSBA (−34.1%); portfolio table, sector table, live vs
  backtest metric blocks and definitions verified in rendered HTML and in the browser;
  CI guard string ("Data refreshed 20") preserved.
