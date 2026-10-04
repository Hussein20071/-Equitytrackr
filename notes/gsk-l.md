# GSK (GSK.L) — Research Note

**SELL** · Target GBP 14.98 · Upside -15.82% · Thesis date 2026-10-04T12:58:16.838081+00:00

> SELL: target GBP 14.98 vs price GBP 17.80 (-15.8% upside) on blended DCF/DDM/comps

The model's blended 12-month target is GBP 14.98 against a market price of GBP 17.80 (-15.8%), which reads as SELL on the published recommendation bands. The target is a weighted blend of a 2-stage FCF DCF at GBP 8.34 per share, a Gordon DDM at GBP 13.57, peer multiples implying GBP 28.45 (P/E leg) -- the market is effectively pricing different assumptions than those frozen inputs, and the note shows exactly which. The thesis is proven wrong if the shares sustain beyond the target in the opposite direction of the call for 10+ sessions, or if reported results break the frozen FCF/net-debt base.

## Catalysts
- Next results: 2026-10-28 (Yahoo calendar) -- reported FCF vs the frozen base is the decisive input
- Convergence (or divergence) vs the GBP 14.98 target over the 3-month review window

## Risks
- Fundamentals revision: a restated or materially different FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 4756.0 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.0129, -0.0065, 0.0, 0.0, 0.0] | growth: FCF CAGR -2.6% over 3y, 50% damped -> -1.3% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.0 | terminal g = min(rf 4.99%, explicit CAGR/2) = 0.00% |
| WACC (ke) | 0.099 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 1.139092; implied pre-tax kd 4.1% disclosed only |
| Net debt | 13731.0 GBP m | Balance sheet latest FY |
| DCF value/share | 8.34 | 2-stage FCF model |
| DDM value/share | 13.5705 | g capped: ROE x retention 13.73% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 33.4% x retention 41% = 3.49% (raw 13.73%, capped); D1 = DPS TTM 0.84 x (1+g) = 0.87; value = D1 / (ke 9.90% - g 3.49%) = 13.57 |
| Comps P/E implied | 28.45 | median peer P/E x EPS |
| **Blended target** | **14.98** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 17.795

## Data sources & provenance
- **fx**: native GBP (n/a, 2026-10-04T12:44:10.449850+00:00)
- **income_statement**: converted GBP->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-10-04T12:44:10.598244+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), GBP->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-10-04T12:44:10.743887+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-10-04T12:44:10.917305+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (84.0000 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-10-04T12:44:11.275712+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:16.348129+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:16.137428+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-10-04T12:58:16.137428+00:00)
- **cost_of_equity**: ke = 4.99% + 1.14 x 4.31% = 9.90% (CAPM, 2026-10-04T12:58:16.137428+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 1.21 over 104 weekly observations -- measured against the benchmark the portfolio tracks (^FTSE), per-name (OLS beta: GSK.L vs ^FTSE weekly returns, 2y, 2026-10-04T12:58:15.963232+00:00)
- **cost_of_equity**: beta raw 1.21 -> adjusted 1.14 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-10-04T12:58:15.963232+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 19.9x x EPS 1.43 = 28.45
- **peer_multiples**: EV/EBITDA leg: median 13.2x x EBITDA 10,402m - net debt 13,731m = equity 123,102m / 4,007m shares = 30.72
- **blend**: blend: dcf 8.34 x 55%
- **blend**: blend: ddm 13.57 x 18%
- **blend**: blend: comps_pe 28.45 x 18%
- **blend**: blend: comps_ev_ebitda 30.72 x 9%
- **model_choices**:  (, )

## Addenda
- [2026-10-04] **methodology**: 2026-10-04 model sanity review: (1) beta estimation window widened from 52 to ~104 weekly observations (2y) after the 1y window pinned BP and SHEL at the 0.40 beta floor; (2) DCF base FCF now falls back to a normalised multi-year average when the latest FY is missing/non-finite, and the DCF is excluded with an explicit reason when trailing FCF is non-positive; (3) a +/-30% model-outlier guardrail now runs at publication and flags the driving leg. Inputs were re-frozen from refetched live data; the tracked window and hit counting still start at first publication (2026-09-19).

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-10-04T12:58:16.838081+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.