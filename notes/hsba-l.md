# HSBC Holdings (HSBA.L) — Research Note

**SELL** · Target GBP 9.86 · Upside -34.8% · Thesis date 2026-09-27T13:58:46.960158+00:00

> SELL: target GBP 9.86 vs price GBP 15.12 (-34.8% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 15.12 against a blended 12-month target of GBP 9.86 (weights {'ddm': 0.6, 'comps_pe': 0.4}). The 2-stage FCF DCF on a base of GBP 18,942m latest-FY free cash flow (FX-converted from USD) values the shares at GBP 30.05. Gordon DDM on trailing DPS GBP 0.63 (g = ROE x retention) values them at GBP 8.99. Peer-median P/E of 11.4x applied to EPS of GBP 0.98 implies GBP 11.17. Reported FCF has trended up over the last 4 financial years (GBP 11,277m -> GBP 18,942m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 9.86 (-34.8%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 9.86 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 18942.2 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.0944, 0.0944, 0.0708, 0.0472, 0.0236] | growth: FCF CAGR +18.9% over 3y, 50% damped -> +9.4% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.1075 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 1.33634 |
| Net debt | -232193.7 GBP m | Balance sheet latest FY |
| DCF value/share | 30.05 | 2-stage FCF model |
| DDM value/share | 8.9894 | g capped: ROE x retention 4.70% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 13.1% x retention 36% = 3.49% (raw 4.70%, capped); D1 = DPS TTM 0.63 x (1+g) = 0.65; value = D1 / (ke 10.75% - g 3.49%) = 8.99 |
| Comps P/E implied | 11.17 | median peer P/E x EPS |
| **Blended target** | **9.86** | weights {'ddm': 0.6, 'comps_pe': 0.4} |

Price at publication: GBP 15.12199951171875

## Data sources & provenance
- **fx**: 1 USD = 0.7545 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-27T13:58:44.697249+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-27T13:58:44.867278+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-27T13:58:45.026089+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-27T13:58:45.185235+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (63.0280 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-27T13:58:45.573544+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:46.945813+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:46.850305+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-27T13:58:46.850305+00:00)
- **cost_of_equity**: ke = 4.99% + 1.34 x 4.31% = 10.75% (CAPM, 2026-09-27T13:58:46.850305+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 1.50 over 52 weekly observations (Yahoo feed beta unavailable) (OLS beta: HSBA.L vs ^FTSE weekly returns, 1y, 2026-09-27T13:58:46.734628+00:00)
- **cost_of_equity**: beta raw 1.50 -> adjusted 1.34 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-27T13:58:46.734628+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 11.4x x EPS 0.98 = 11.17
- **blend**: FCF DCF omitted: bank operating cash flow includes deposit flows; DDM + P/E used (standard practice)
- **blend**: blend: ddm 8.99 x 60%
- **blend**: blend: comps_pe 11.17 x 40%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-27T13:58:46.950393+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.