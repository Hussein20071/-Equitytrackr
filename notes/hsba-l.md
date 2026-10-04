# HSBC Holdings (HSBA.L) — Research Note

**SELL** · Target GBP 9.5 · Upside -34.13% · Thesis date 2026-10-04T12:58:12.787418+00:00

> SELL: target GBP 9.50 vs price GBP 14.42 (-34.1% upside) on blended DCF/DDM/comps

The model's blended 12-month target is GBP 9.50 against a market price of GBP 14.42 (-34.1%), which reads as SELL on the published recommendation bands. The target is a weighted blend of a 2-stage FCF DCF at GBP 29.78 per share, a Gordon DDM at GBP 8.80, peer multiples implying GBP 10.54 (P/E leg) -- the market is effectively pricing different assumptions than those frozen inputs, and the note shows exactly which. That gap exceeds the +/-30% guardrail, so the note is flagged 'Model outlier - under review' with the ddm leg driving it; the reverse DCF on the note page states what growth the market price implies instead.

## Catalysts
- Next results: 2026-10-27 (Yahoo calendar) -- reported FCF vs the frozen base is the decisive input
- Convergence (or divergence) vs the GBP 9.5 target over the 3-month review window

## Risks
- Fundamentals revision: a restated or materially different FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 18960.8 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.0944, 0.0944, 0.0708, 0.0472, 0.0236] | growth: FCF CAGR +18.9% over 3y, 50% damped -> +9.4% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.109 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 1.3716490000000001 |
| Net debt | -232421.5 GBP m | Balance sheet latest FY |
| DCF value/share | 29.78 | 2-stage FCF model |
| DDM value/share | 8.8047 | g capped: ROE x retention 4.71% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 13.1% x retention 36% = 3.49% (raw 4.71%, capped); D1 = DPS TTM 0.63 x (1+g) = 0.65; value = D1 / (ke 10.90% - g 3.49%) = 8.80 |
| Comps P/E implied | 10.54 | median peer P/E x EPS |
| **Blended target** | **9.5** | weights {'ddm': 0.6, 'comps_pe': 0.4} |

Price at publication: GBP 14.42199951171875

## Data sources & provenance
- **fx**: 1 USD = 0.7553 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-10-04T12:43:55.536343+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-10-04T12:43:55.704239+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-10-04T12:43:55.901804+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-10-04T12:43:56.091726+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (63.0280 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-10-04T12:43:56.726399+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:12.245306+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:12.072840+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-10-04T12:58:12.072840+00:00)
- **cost_of_equity**: ke = 4.99% + 1.37 x 4.31% = 10.90% (CAPM, 2026-10-04T12:58:12.072840+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 1.55 over 104 weekly observations -- measured against the benchmark the portfolio tracks (^FTSE), per-name (OLS beta: HSBA.L vs ^FTSE weekly returns, 2y, 2026-10-04T12:58:11.927362+00:00)
- **cost_of_equity**: beta raw 1.55 -> adjusted 1.37 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-10-04T12:58:11.927362+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 10.7x x EPS 0.98 = 10.54
- **blend**: FCF DCF omitted: bank operating cash flow includes deposit flows; DDM + P/E used (standard practice)
- **blend**: blend: ddm 8.80 x 60%
- **blend**: blend: comps_pe 10.54 x 40%
- **model_choices**:  (, )

## Addenda
- [2026-10-04] **methodology**: 2026-10-04 model sanity review: (1) beta estimation window widened from 52 to ~104 weekly observations (2y) after the 1y window pinned BP and SHEL at the 0.40 beta floor; (2) DCF base FCF now falls back to a normalised multi-year average when the latest FY is missing/non-finite, and the DCF is excluded with an explicit reason when trailing FCF is non-positive; (3) a +/-30% model-outlier guardrail now runs at publication and flags the driving leg. Inputs were re-frozen from refetched live data; the tracked window and hit counting still start at first publication (2026-09-19).

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-10-04T12:58:12.787418+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.