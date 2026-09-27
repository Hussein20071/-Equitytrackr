# AstraZeneca (AZN.L) — Research Note

**SELL** · Target GBP 60.03 · Upside -52.17% · Thesis date 2026-09-27T13:58:41.327815+00:00

> SELL: target GBP 60.03 vs price GBP 125.52 (-52.2% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 125.52 against a blended 12-month target of GBP 60.03 (weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091}). The 2-stage FCF DCF on a base of GBP 6,542m latest-FY free cash flow (FX-converted from USD) values the shares at GBP 42.43. Gordon DDM on trailing DPS GBP 3.16 (g = ROE x retention) values them at GBP 46.07. Peer-median P/E of 20.2x applied to EPS of GBP 4.97 implies GBP 100.25. Reported FCF has trended up over the last 4 financial years (GBP 5,460m -> GBP 6,542m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 60.03 (-52.2%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 60.03 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 6541.7 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.031, 0.031, 0.0233, 0.0155, 0.0078] | growth: FCF CAGR +6.2% over 3y, 50% damped -> +3.1% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.1058 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 1.2981500000000001; implied pre-tax kd 5.9% disclosed only |
| Net debt | 16318.0 GBP m | Balance sheet latest FY |
| DCF value/share | 42.43 | 2-stage FCF model |
| DDM value/share | 46.072 | g capped: ROE x retention 8.03% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 22.0% x retention 37% = 3.49% (raw 8.03%, capped); D1 = DPS TTM 3.16 x (1+g) = 3.27; value = D1 / (ke 10.58% - g 3.49%) = 46.07 |
| Comps P/E implied | 100.25 | median peer P/E x EPS |
| **Blended target** | **60.03** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 125.52

## Data sources & provenance
- **fx**: 1 USD = 0.7545 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-27T13:58:38.780931+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-27T13:58:38.945364+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-27T13:58:39.110974+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-27T13:58:39.311968+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (315.7000 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-27T13:58:39.623431+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:41.307831+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:41.206129+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-27T13:58:41.206129+00:00)
- **cost_of_equity**: ke = 4.99% + 1.30 x 4.31% = 10.58% (CAPM, 2026-09-27T13:58:41.206129+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 1.45 over 52 weekly observations (Yahoo feed beta unavailable) (OLS beta: AZN.L vs ^FTSE weekly returns, 1y, 2026-09-27T13:58:41.034088+00:00)
- **cost_of_equity**: beta raw 1.45 -> adjusted 1.30 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-27T13:58:41.036120+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 20.2x x EPS 4.97 = 100.25
- **peer_multiples**: EV/EBITDA leg: median 13.0x x EBITDA 14,718m - net debt 16,318m = equity 175,361m / 1,551m shares = 113.07
- **blend**: blend: dcf 42.43 x 55%
- **blend**: blend: ddm 46.07 x 18%
- **blend**: blend: comps_pe 100.25 x 18%
- **blend**: blend: comps_ev_ebitda 113.07 x 9%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-27T13:58:41.322763+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.