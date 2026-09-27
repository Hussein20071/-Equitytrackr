# AstraZeneca (AZN.L) — Research Note

**SELL** · Target GBP 81.57 · Upside -34.74% · Thesis date 2026-09-19T09:17:40.061488+00:00

> SELL: target GBP 81.57 vs price GBP 125.0 (-34.7% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 125.0 against a blended 12-month target of GBP 81.57 (weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091}). The 2-stage FCF DCF on a base of GBP 6,472m latest-FY free cash flow (FX-converted from USD) values the shares at GBP 73.01. Gordon DDM on trailing DPS GBP 3.16 (g = ROE x retention) values them at GBP 80.20. Peer-median P/E of 19.5x applied to EPS of GBP 4.92 implies GBP 95.80. Reported FCF has trended up over the last 4 financial years (GBP 5,403m -> GBP 6,472m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 81.57 (-34.7%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 81.57 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 6472.3 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.031, 0.031, 0.0233, 0.0155, 0.0078] | growth: FCF CAGR +6.2% over 3y, 50% damped -> +3.1% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.0757 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.5980000000000001; implied pre-tax kd 5.9% disclosed only |
| Net debt | 16145.0 GBP m | Balance sheet latest FY |
| DCF value/share | 73.01 | 2-stage FCF model |
| DDM value/share | 80.1982 | g capped: ROE x retention 7.88% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 22.0% x retention 36% = 3.49% (raw 7.88%, capped); D1 = DPS TTM 3.16 x (1+g) = 3.27; value = D1 / (ke 7.57% - g 3.49%) = 80.20 |
| Comps P/E implied | 95.8 | median peer P/E x EPS |
| **Blended target** | **81.57** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 125.0

## Data sources & provenance
- **fx**: 1 USD = 0.7465 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-19T09:17:33.201945+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-19T09:17:33.341571+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-19T09:17:33.539707+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-19T09:17:33.766200+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (315.7000 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-19T09:17:34.042083+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:17:40.037180+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:17:39.933542+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-19T09:17:39.933542+00:00)
- **cost_of_equity**: ke = 4.99% + 0.60 x 4.31% = 7.57% (CAPM, 2026-09-19T09:17:39.933542+00:00)
- **cost_of_equity**: beta raw 0.20 floored at 0.40 -> adjusted 0.60 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-19T09:17:39.594238+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 19.5x x EPS 4.92 = 95.80
- **peer_multiples**: EV/EBITDA leg: median 12.5x x EBITDA 14,562m - net debt 16,145m = equity 166,213m / 1,551m shares = 107.17
- **blend**: blend: dcf 73.01 x 55%
- **blend**: blend: ddm 80.20 x 18%
- **blend**: blend: comps_pe 95.80 x 18%
- **blend**: blend: comps_ev_ebitda 107.17 x 9%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-19T09:17:40.061488+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.