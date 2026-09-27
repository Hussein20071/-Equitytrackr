# Shell (SHEL.L) — Research Note

**HOLD** · Target GBP 36.84 · Upside 2.02% · Thesis date 2026-09-27T13:58:44.104453+00:00

> HOLD: target GBP 36.84 vs price GBP 36.11 (+2.0% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 36.11 against a blended 12-month target of GBP 36.84 (weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091}). The 2-stage FCF DCF on a base of GBP 18,045m latest-FY free cash flow (FX-converted from USD) values the shares at GBP 36.54. Gordon DDM on trailing DPS GBP 1.39 (g = ROE x retention) values them at GBP 35.42. Peer-median P/E of 17.9x applied to EPS of GBP 2.36 implies GBP 42.15. Reported FCF has trended down over the last 4 financial years (GBP 34,568m -> GBP 18,045m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 36.84 (+2.0%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 36.84 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 18045.1 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.05, -0.025, 0.0, 0.0, 0.0] | growth: FCF CAGR -19.5% over 3y, 50% damped -> -5.0% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.0 | terminal g = min(rf 4.99%, explicit CAGR/2) = 0.00% |
| WACC (ke) | 0.0757 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.5980000000000001; implied pre-tax kd 10.1% disclosed only |
| Net debt | 12887.2 GBP m | Balance sheet latest FY |
| DCF value/share | 36.54 | 2-stage FCF model |
| DDM value/share | 35.4224 | g capped: ROE x retention 5.86% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 14.3% x retention 41% = 3.49% (raw 5.86%, capped); D1 = DPS TTM 1.39 x (1+g) = 1.44; value = D1 / (ke 7.57% - g 3.49%) = 35.42 |
| Comps P/E implied | 42.15 | median peer P/E x EPS |
| **Blended target** | **36.84** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 36.11

## Data sources & provenance
- **fx**: 1 USD = 0.7545 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-27T13:58:41.923377+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-27T13:58:42.091432+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-27T13:58:42.224525+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-27T13:58:42.401103+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (139.4400 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-27T13:58:42.733913+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:44.083441+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:58:43.980399+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-27T13:58:43.980399+00:00)
- **cost_of_equity**: ke = 4.99% + 0.60 x 4.31% = 7.57% (CAPM, 2026-09-27T13:58:43.980399+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 0.08 over 52 weekly observations (Yahoo feed beta unavailable) (OLS beta: SHEL.L vs ^FTSE weekly returns, 1y, 2026-09-27T13:58:43.885495+00:00)
- **cost_of_equity**: beta raw 0.08 floored at 0.40 -> adjusted 0.60 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-27T13:58:43.885495+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: excluded from medians: BP.L P/E 2080x > 60x cap
- **peer_multiples**: P/E leg: median 17.9x x EPS 2.36 = 42.15
- **peer_multiples**: EV/EBITDA leg: median 4.4x x EBITDA 42,754m - net debt 12,887m = equity 176,013m / 5,705m shares = 30.85
- **blend**: blend: dcf 36.54 x 55%
- **blend**: blend: ddm 35.42 x 18%
- **blend**: blend: comps_pe 42.15 x 18%
- **blend**: blend: comps_ev_ebitda 30.85 x 9%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-27T13:58:44.104453+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.