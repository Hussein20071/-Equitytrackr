# HSBC Holdings (HSBA.L) — Research Note

**HOLD** · Target GBP 12.96 · Upside -14.32% · Thesis date 2026-09-19T09:17:53.652836+00:00

> HOLD: target GBP 12.96 vs price GBP 15.126 (-14.3% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 15.126 against a blended 12-month target of GBP 12.96 (weights {'ddm': 0.6, 'comps_pe': 0.4}). The 2-stage FCF DCF on a base of GBP 18,741m latest-FY free cash flow (FX-converted from USD) values the shares at GBP 37.71. Gordon DDM on trailing DPS GBP 0.63 (g = ROE x retention) values them at GBP 14.28. Peer-median P/E of 11.3x applied to EPS of GBP 0.97 implies GBP 10.99. Reported FCF has trended up over the last 4 financial years (GBP 11,157m -> GBP 18,741m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 12.96 (-14.3%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 12.96 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 18741.4 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.0944, 0.0944, 0.0708, 0.0472, 0.0236] | growth: FCF CAGR +18.9% over 3y, 50% damped -> +9.4% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.0806 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.7125699999999999 |
| Net debt | -229731.8 GBP m | Balance sheet latest FY |
| DCF value/share | 37.71 | 2-stage FCF model |
| DDM value/share | 14.2803 | g capped: ROE x retention 4.61% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 13.1% x retention 35% = 3.49% (raw 4.61%, capped); D1 = DPS TTM 0.63 x (1+g) = 0.65; value = D1 / (ke 8.06% - g 3.49%) = 14.28 |
| Comps P/E implied | 10.99 | median peer P/E x EPS |
| **Blended target** | **12.96** | weights {'ddm': 0.6, 'comps_pe': 0.4} |

Price at publication: GBP 15.126

## Data sources & provenance
- **fx**: 1 USD = 0.7465 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-19T09:17:47.073526+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-19T09:17:47.237804+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-19T09:17:47.456687+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-19T09:17:47.649632+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (63.0280 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-19T09:17:47.987445+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:17:53.636745+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:17:53.523649+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-19T09:17:53.523649+00:00)
- **cost_of_equity**: ke = 4.99% + 0.71 x 4.31% = 8.06% (CAPM, 2026-09-19T09:17:53.523649+00:00)
- **cost_of_equity**: beta raw 0.57 -> adjusted 0.71 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-19T09:17:53.410053+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 11.3x x EPS 0.97 = 10.99
- **blend**: FCF DCF omitted: bank operating cash flow includes deposit flows; DDM + P/E used (standard practice)
- **blend**: blend: ddm 14.28 x 60%
- **blend**: blend: comps_pe 10.99 x 40%
- **model_choices**:  (, )

## Addenda
- [2026-09-19] **learning**: During construction, three currency-unit defects were caught and fixed before any numbers were published as final: (1) foreign-listed peers were not FX-converted, inflating comps multiples ~100x for CHF/NOK lines; (2) LSE dividend history is in pence while US lines are in currency units, so DPS TTM required listing-aware conversion; (3) Yahoo trailingEps is inconsistent across listing venues (local vs ADR), so EPS is now derived as net income / shares instead. Lesson: in multi-currency universes, every per-unit input needs an explicit unit test against the listing currency before it enters a valuation.

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-19T09:17:53.636745+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.