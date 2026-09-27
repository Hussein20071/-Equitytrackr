# Unilever (ULVR.L) — Research Note

**HOLD** · Target GBP 49.99 · Upside 7.17% · Thesis date 2026-09-27T13:58:49.811295+00:00

> HOLD: target GBP 49.99 vs price GBP 46.65 (+7.2% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 46.65 against a blended 12-month target of GBP 49.99 (weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091}). The 2-stage FCF DCF on a base of GBP 5,812m latest-FY free cash flow (FX-converted from EUR) values the shares at GBP 41.07. Gordon DDM on trailing DPS GBP 2.09 (g = ROE x retention) values them at GBP 47.41. Peer-median P/E of 21.2x applied to EPS of GBP 3.78 implies GBP 80.30. Reported FCF has trended up over the last 4 financial years (GBP 4,792m -> GBP 5,812m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 49.99 (+7.2%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 49.99 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 5812.2 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.0332, 0.0332, 0.0249, 0.0166, 0.0083] | growth: FCF CAGR +6.6% over 3y, 50% damped -> +3.3% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.0806 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.7114980000000001; implied pre-tax kd 4.2% disclosed only |
| Net debt | 18281.0 GBP m | Balance sheet latest FY |
| DCF value/share | 41.07 | 2-stage FCF model |
| DDM value/share | 47.4114 | g capped: ROE x retention 14.25% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 31.9% x retention 45% = 3.49% (raw 14.25%, capped); D1 = DPS TTM 2.09 x (1+g) = 2.16; value = D1 / (ke 8.06% - g 3.49%) = 47.41 |
| Comps P/E implied | 80.3 | median peer P/E x EPS |
| **Blended target** | **49.99** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 46.645

## Data sources & provenance
- **fx**: 1 EUR = 0.8599 GBP (spot GBPEUR=X inverted) (Yahoo Finance FX (yfinance), 2026-09-27T13:58:47.585274+00:00)
- **income_statement**: converted EUR->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-27T13:58:47.730426+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), EUR->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-27T13:58:47.905451+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-27T13:58:48.100604+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (209.0450 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-27T13:58:48.424180+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:49.794871+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:49.691429+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-27T13:58:49.691429+00:00)
- **cost_of_equity**: ke = 4.99% + 0.71 x 4.31% = 8.06% (CAPM, 2026-09-27T13:58:49.691429+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 0.57 over 52 weekly observations (Yahoo feed beta unavailable) (OLS beta: ULVR.L vs ^FTSE weekly returns, 1y, 2026-09-27T13:58:49.596262+00:00)
- **cost_of_equity**: beta raw 0.57 -> adjusted 0.71 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-27T13:58:49.596262+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 21.2x x EPS 3.78 = 80.30
- **peer_multiples**: EV/EBITDA leg: median 12.7x x EBITDA 9,583m - net debt 18,281m = equity 103,372m / 2,153m shares = 48.01
- **blend**: blend: dcf 41.07 x 55%
- **blend**: blend: ddm 47.41 x 18%
- **blend**: blend: comps_pe 80.30 x 18%
- **blend**: blend: comps_ev_ebitda 48.01 x 9%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-27T13:58:49.811295+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.