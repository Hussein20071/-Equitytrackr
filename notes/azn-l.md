# AstraZeneca (AZN.L) — Research Note

**SELL** · Target GBP 60.82 · Upside -48.76% · Thesis date 2026-10-04T12:58:08.994957+00:00

> SELL: target GBP 60.82 vs price GBP 118.70 (-48.8% upside) on blended DCF/DDM/comps

The model's blended 12-month target is GBP 60.82 against a market price of GBP 118.70 (-48.8%), which reads as SELL on the published recommendation bands. The target is a weighted blend of a 2-stage FCF DCF at GBP 45.05 per share, a Gordon DDM at GBP 48.66, peer multiples implying GBP 96.27 (P/E leg) -- the market is effectively pricing different assumptions than those frozen inputs, and the note shows exactly which. That gap exceeds the +/-30% guardrail, so the note is flagged 'Model outlier - under review' with the dcf leg driving it; the reverse DCF on the note page states what growth the market price implies instead.

## Catalysts
- Next results: 2026-10-30 (Yahoo calendar) -- reported FCF vs the frozen base is the decisive input
- Convergence (or divergence) vs the GBP 60.82 target over the 3-month review window

## Risks
- Fundamentals revision: a restated or materially different FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 6548.1 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.031, 0.031, 0.0233, 0.0155, 0.0078] | growth: FCF CAGR +6.2% over 3y, 50% damped -> +3.1% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.1021 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 1.210715; implied pre-tax kd 5.9% disclosed only |
| Net debt | 16334.0 GBP m | Balance sheet latest FY |
| DCF value/share | 45.05 | 2-stage FCF model |
| DDM value/share | 48.6576 | g capped: ROE x retention 8.04% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 22.0% x retention 37% = 3.49% (raw 8.04%, capped); D1 = DPS TTM 3.16 x (1+g) = 3.27; value = D1 / (ke 10.21% - g 3.49%) = 48.66 |
| Comps P/E implied | 96.27 | median peer P/E x EPS |
| **Blended target** | **60.82** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 118.7

## Data sources & provenance
- **fx**: 1 USD = 0.7553 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-10-04T12:43:41.296133+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-10-04T12:43:41.590020+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-10-04T12:43:41.725566+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-10-04T12:43:41.998224+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (315.7000 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-10-04T12:43:42.356901+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:08.482132+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:08.391087+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-10-04T12:58:08.391087+00:00)
- **cost_of_equity**: ke = 4.99% + 1.21 x 4.31% = 10.21% (CAPM, 2026-10-04T12:58:08.391087+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 1.31 over 104 weekly observations -- measured against the benchmark the portfolio tracks (^FTSE), per-name (OLS beta: AZN.L vs ^FTSE weekly returns, 2y, 2026-10-04T12:58:08.281426+00:00)
- **cost_of_equity**: beta raw 1.31 -> adjusted 1.21 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-10-04T12:58:08.281426+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 19.3x x EPS 4.98 = 96.27
- **peer_multiples**: EV/EBITDA leg: median 12.6x x EBITDA 14,732m - net debt 16,334m = equity 168,895m / 1,551m shares = 108.90
- **blend**: blend: dcf 45.05 x 55%
- **blend**: blend: ddm 48.66 x 18%
- **blend**: blend: comps_pe 96.27 x 18%
- **blend**: blend: comps_ev_ebitda 108.90 x 9%
- **model_choices**:  (, )

## Addenda
- [2026-10-04] **methodology**: 2026-10-04 model sanity review: (1) beta estimation window widened from 52 to ~104 weekly observations (2y) after the 1y window pinned BP and SHEL at the 0.40 beta floor; (2) DCF base FCF now falls back to a normalised multi-year average when the latest FY is missing/non-finite, and the DCF is excluded with an explicit reason when trailing FCF is non-positive; (3) a +/-30% model-outlier guardrail now runs at publication and flags the driving leg. Inputs were re-frozen from refetched live data; the tracked window and hit counting still start at first publication (2026-09-19).

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-10-04T12:58:08.994957+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.