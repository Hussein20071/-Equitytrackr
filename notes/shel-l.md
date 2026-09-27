# Shell (SHEL.L) — Research Note

**HOLD** · Target GBP 36.62 · Upside 3.48% · Thesis date 2026-09-19T09:32:46.744364+00:00

> HOLD: target GBP 36.62 vs price GBP 35.39 (+3.5% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 35.39 against a blended 12-month target of GBP 36.62 (weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091}). The 2-stage FCF DCF on a base of GBP 17,854m latest-FY free cash flow (FX-converted from USD) values the shares at GBP 36.10. Gordon DDM on trailing DPS GBP 1.39 (g = ROE x retention) values them at GBP 35.42. Peer-median P/E of 18.1x applied to EPS of GBP 2.33 implies GBP 42.27. Reported FCF has trended down over the last 4 financial years (GBP 34,201m -> GBP 17,854m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 36.62 (+3.5%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 36.62 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 17853.8 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.05, -0.025, 0.0, 0.0, 0.0] | growth: FCF CAGR -19.5% over 3y, 50% damped -> -5.0% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.0 | terminal g = min(rf 4.99%, explicit CAGR/2) = 0.00% |
| WACC (ke) | 0.0757 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.5980000000000001; implied pre-tax kd 10.1% disclosed only |
| Net debt | 12750.6 GBP m | Balance sheet latest FY |
| DCF value/share | 36.1 | 2-stage FCF model |
| DDM value/share | 35.4224 | g capped: ROE x retention 5.76% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 14.3% x retention 40% = 3.49% (raw 5.76%, capped); D1 = DPS TTM 1.39 x (1+g) = 1.44; value = D1 / (ke 7.57% - g 3.49%) = 35.42 |
| Comps P/E implied | 42.27 | median peer P/E x EPS |
| **Blended target** | **36.62** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 35.39

## Data sources & provenance
- **fx**: 1 USD = 0.7465 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-19T09:17:40.312501+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-19T09:17:40.439324+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-19T09:17:40.694202+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-19T09:17:40.948257+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (139.4400 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-19T09:17:41.280915+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:32:46.730296+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:32:46.588283+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-19T09:32:46.588283+00:00)
- **cost_of_equity**: ke = 4.99% + 0.60 x 4.31% = 7.57% (CAPM, 2026-09-19T09:32:46.588283+00:00)
- **cost_of_equity**: beta raw -0.22 floored at 0.40 -> adjusted 0.60 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-19T09:32:46.459171+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: excluded from medians: BP.L P/E 2103x > 60x cap
- **peer_multiples**: P/E leg: median 18.1x x EPS 2.33 = 42.27
- **peer_multiples**: EV/EBITDA leg: median 4.5x x EBITDA 42,301m - net debt 12,751m = equity 175,893m / 5,712m shares = 30.80
- **blend**: blend: dcf 36.10 x 55%
- **blend**: blend: ddm 35.42 x 18%
- **blend**: blend: comps_pe 42.27 x 18%
- **blend**: blend: comps_ev_ebitda 30.80 x 9%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-19T09:32:46.744364+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.