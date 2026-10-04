# National Grid (NG.L) — Research Note

**HOLD** · Target GBP 11.23 · Upside -2.05% · Thesis date 2026-10-04T12:58:20.327950+00:00

> HOLD: target GBP 11.23 vs price GBP 11.46 (-2.0% upside) on blended DCF/DDM/comps

The model's blended 12-month target is GBP 11.23 against a market price of GBP 11.46 (-2.0%), which reads as HOLD on the published recommendation bands. The target is a weighted blend of peer multiples implying GBP 13.79 (P/E leg) -- the market is effectively pricing different assumptions than those frozen inputs, and the note shows exactly which. The thesis is proven wrong if the shares sustain beyond the target in the opposite direction of the call for 10+ sessions, or if reported results break the frozen FCF/net-debt base.

## Catalysts
- Next results: 2026-11-05 (Yahoo calendar) -- reported FCF vs the frozen base is the decisive input
- Convergence (or divergence) vs the GBP 11.23 target over the 3-month review window

## Risks
- Fundamentals revision: a restated or materially different FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | -2746.0 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.0, 0.0, 0.0, 0.0, 0.0] | latest-FY FCF is GBP -2,746m (non-positive on the feed) |
| Terminal growth | 0.025 | DCF excluded: FY free cash flow (OCF - capex) is non-positive in 3 of the 4 trailing financial years (6, -514, -2,498, -2,746 GBPm; latest FY -2,746) -- a DCF cannot be run from a negative base; the blend re-weights over the surviving legs |
| WACC (ke) | 0.0859 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.835582; implied pre-tax kd 3.6% disclosed only |
| Net debt | 43034.0 GBP m | Balance sheet latest FY |
| DCF value/share | None | 2-stage FCF model |
| DDM value/share | None | DDM skipped: g=-1.94% not < ke*0.9=7.73% |
| Comps P/E implied | 13.79 | median peer P/E x EPS |
| **Blended target** | **11.23** | weights {'comps_pe': 0.667, 'comps_ev_ebitda': 0.333} |

Price at publication: GBP 11.465

## Data sources & provenance
- **fx**: native GBP (n/a, 2026-10-04T12:44:15.621375+00:00)
- **income_statement**: converted GBP->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-10-04T12:44:15.748139+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), GBP->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-10-04T12:44:15.988670+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-10-04T12:44:16.171967+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (79.3700 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-10-04T12:44:16.468230+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:19.783911+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:19.673842+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-10-04T12:58:19.673842+00:00)
- **cost_of_equity**: ke = 4.99% + 0.84 x 4.31% = 8.59% (CAPM, 2026-10-04T12:58:19.673842+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 0.75 over 104 weekly observations -- measured against the benchmark the portfolio tracks (^FTSE), per-name (OLS beta: NG.L vs ^FTSE weekly returns, 2y, 2026-10-04T12:58:19.584728+00:00)
- **cost_of_equity**: beta raw 0.75 -> adjusted 0.84 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-10-04T12:58:19.584728+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 21.4x x EPS 0.64 = 13.79
- **peer_multiples**: EV/EBITDA leg: median 9.1x x EBITDA 8,078m - net debt 43,034m = equity 30,800m / 5,027m shares = 6.13
- **blend**: blend: comps_pe 13.79 x 67%
- **blend**: blend: comps_ev_ebitda 6.13 x 33%
- **model_choices**:  (, )

## Addenda
- [2026-10-04] **methodology**: 2026-10-04 model sanity review: (1) beta estimation window widened from 52 to ~104 weekly observations (2y) after the 1y window pinned BP and SHEL at the 0.40 beta floor; (2) DCF base FCF now falls back to a normalised multi-year average when the latest FY is missing/non-finite, and the DCF is excluded with an explicit reason when trailing FCF is non-positive; (3) a +/-30% model-outlier guardrail now runs at publication and flags the driving leg. Inputs were re-frozen from refetched live data; the tracked window and hit counting still start at first publication (2026-09-19).

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-10-04T12:58:20.327950+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.