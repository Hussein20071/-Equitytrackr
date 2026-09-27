# GSK (GSK.L) — Research Note

**SELL** · Target GBP 14.92 · Upside -19.39% · Thesis date 2026-09-27T13:58:52.710758+00:00

> SELL: target GBP 14.92 vs price GBP 18.51 (-19.4% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 18.51 against a blended 12-month target of GBP 14.92 (weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091}). The 2-stage FCF DCF on a base of GBP 4,756m latest-FY free cash flow (FX-converted from GBP) values the shares at GBP 7.85. Gordon DDM on trailing DPS GBP 0.84 (g = ROE x retention) values them at GBP 12.71. Peer-median P/E of 20.8x applied to EPS of GBP 1.43 implies GBP 29.67. Reported FCF has trended down over the last 4 financial years (GBP 5,145m -> GBP 4,756m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 14.92 (-19.4%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 14.92 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 4756.0 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.0129, -0.0065, 0.0, 0.0, 0.0] | growth: FCF CAGR -2.6% over 3y, 50% damped -> -1.3% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.0 | terminal g = min(rf 4.99%, explicit CAGR/2) = 0.00% |
| WACC (ke) | 0.1033 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 1.2401950000000002; implied pre-tax kd 4.1% disclosed only |
| Net debt | 13731.0 GBP m | Balance sheet latest FY |
| DCF value/share | 7.85 | 2-stage FCF model |
| DDM value/share | 12.7062 | g capped: ROE x retention 13.73% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 33.4% x retention 41% = 3.49% (raw 13.73%, capped); D1 = DPS TTM 0.84 x (1+g) = 0.87; value = D1 / (ke 10.33% - g 3.49%) = 12.71 |
| Comps P/E implied | 29.67 | median peer P/E x EPS |
| **Blended target** | **14.92** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 18.51

## Data sources & provenance
- **fx**: native GBP (n/a, 2026-09-27T13:58:50.310687+00:00)
- **income_statement**: converted GBP->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-27T13:58:50.488684+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), GBP->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-27T13:58:50.655409+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-27T13:58:50.870170+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (84.0000 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-27T13:58:51.215453+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:52.700549+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:52.586553+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-27T13:58:52.586553+00:00)
- **cost_of_equity**: ke = 4.99% + 1.24 x 4.31% = 10.33% (CAPM, 2026-09-27T13:58:52.586553+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 1.36 over 52 weekly observations (Yahoo feed beta unavailable) (OLS beta: GSK.L vs ^FTSE weekly returns, 1y, 2026-09-27T13:58:52.487293+00:00)
- **cost_of_equity**: beta raw 1.36 -> adjusted 1.24 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-27T13:58:52.487293+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 20.8x x EPS 1.43 = 29.67
- **peer_multiples**: EV/EBITDA leg: median 13.8x x EBITDA 10,402m - net debt 13,731m = equity 129,510m / 4,006m shares = 32.33
- **blend**: blend: dcf 7.85 x 55%
- **blend**: blend: ddm 12.71 x 18%
- **blend**: blend: comps_pe 29.67 x 18%
- **blend**: blend: comps_ev_ebitda 32.33 x 9%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-27T13:58:52.710758+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.