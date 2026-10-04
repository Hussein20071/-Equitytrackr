# Shell (SHEL.L) — Research Note

**HOLD** · Target GBP 34.0 · Upside -5.46% · Thesis date 2026-10-04T12:58:10.841858+00:00

> HOLD: target GBP 34.00 vs price GBP 35.97 (-5.5% upside) on blended DCF/DDM/comps

The model's blended 12-month target is GBP 34.00 against a market price of GBP 35.97 (-5.5%), which reads as HOLD on the published recommendation bands. The target is a weighted blend of a 2-stage FCF DCF at GBP 33.64 per share, a Gordon DDM at GBP 30.69, peer multiples implying GBP 39.93 (P/E leg) -- the market is effectively pricing different assumptions than those frozen inputs, and the note shows exactly which. The thesis is proven wrong if the shares sustain beyond the target in the opposite direction of the call for 10+ sessions, or if reported results break the frozen FCF/net-debt base.

## Catalysts
- Next results: 2026-10-29 (Yahoo calendar) -- reported FCF vs the frozen base is the decisive input
- Convergence (or divergence) vs the GBP 34.0 target over the 3-month review window

## Risks
- Fundamentals revision: a restated or materially different FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 18062.8 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.05, -0.025, 0.0, 0.0, 0.0] | growth: FCF CAGR -19.5% over 3y, 50% damped -> -5.0% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.0 | terminal g = min(rf 4.99%, explicit CAGR/2) = 0.00% |
| WACC (ke) | 0.0819 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.7437250000000001; implied pre-tax kd 10.1% disclosed only |
| Net debt | 12899.8 GBP m | Balance sheet latest FY |
| DCF value/share | 33.64 | 2-stage FCF model |
| DDM value/share | 30.6908 | g capped: ROE x retention 5.88% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 14.3% x retention 41% = 3.49% (raw 5.88%, capped); D1 = DPS TTM 1.39 x (1+g) = 1.44; value = D1 / (ke 8.19% - g 3.49%) = 30.69 |
| Comps P/E implied | 39.93 | median peer P/E x EPS |
| **Blended target** | **34.0** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 35.965

## Data sources & provenance
- **fx**: 1 USD = 0.7553 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-10-04T12:43:49.704250+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-10-04T12:43:49.830672+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-10-04T12:43:49.959465+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-10-04T12:43:50.195337+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (139.4400 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-10-04T12:43:50.436582+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:10.277142+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:10.183773+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-10-04T12:58:10.183773+00:00)
- **cost_of_equity**: ke = 4.99% + 0.74 x 4.31% = 8.19% (CAPM, 2026-10-04T12:58:10.183773+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 0.62 over 104 weekly observations -- measured against the benchmark the portfolio tracks (^FTSE), per-name (OLS beta: SHEL.L vs ^FTSE weekly returns, 2y, 2026-10-04T12:58:10.084641+00:00)
- **cost_of_equity**: beta raw 0.62 -> adjusted 0.74 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-10-04T12:58:10.084641+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: excluded from medians: BP.L P/E 2075x > 60x cap
- **peer_multiples**: P/E leg: median 16.9x x EPS 2.36 = 39.93
- **peer_multiples**: EV/EBITDA leg: median 4.4x x EBITDA 42,796m - net debt 12,900m = equity 175,826m / 5,698m shares = 30.86
- **blend**: blend: dcf 33.64 x 55%
- **blend**: blend: ddm 30.69 x 18%
- **blend**: blend: comps_pe 39.93 x 18%
- **blend**: blend: comps_ev_ebitda 30.86 x 9%
- **model_choices**:  (, )

## Addenda
- [2026-10-04] **methodology**: 2026-10-04 model sanity review: (1) beta estimation window widened from 52 to ~104 weekly observations (2y) after the 1y window pinned BP and SHEL at the 0.40 beta floor; (2) DCF base FCF now falls back to a normalised multi-year average when the latest FY is missing/non-finite, and the DCF is excluded with an explicit reason when trailing FCF is non-positive; (3) a +/-30% model-outlier guardrail now runs at publication and flags the driving leg. Inputs were re-frozen from refetched live data; the tracked window and hit counting still start at first publication (2026-09-19).

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-10-04T12:58:10.836707+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.