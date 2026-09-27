# Unilever (ULVR.L) — Research Note

**HOLD** · Target GBP 52.33 · Upside 13.24% · Thesis date 2026-09-19T09:18:01.341192+00:00

> HOLD: target GBP 52.33 vs price GBP 46.21 (+13.2% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 46.21 against a blended 12-month target of GBP 52.33 (weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091}). The 2-stage FCF DCF on a base of GBP 5,797m latest-FY free cash flow (FX-converted from EUR) values the shares at GBP 44.14. Gordon DDM on trailing DPS GBP 2.09 (g = ROE x retention) values them at GBP 51.18. Peer-median P/E of 21.3x applied to EPS of GBP 3.77 implies GBP 80.26. Reported FCF has trended up over the last 4 financial years (GBP 4,780m -> GBP 5,797m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 52.33 (+13.2%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 52.33 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 5797.2 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.0332, 0.0332, 0.0249, 0.0166, 0.0083] | growth: FCF CAGR +6.6% over 3y, 50% damped -> +3.3% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.0772 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.63351; implied pre-tax kd 4.2% disclosed only |
| Net debt | 18234.0 GBP m | Balance sheet latest FY |
| DCF value/share | 44.14 | 2-stage FCF model |
| DDM value/share | 51.1816 | g capped: ROE x retention 14.21% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 31.9% x retention 45% = 3.49% (raw 14.21%, capped); D1 = DPS TTM 2.09 x (1+g) = 2.16; value = D1 / (ke 7.72% - g 3.49%) = 51.18 |
| Comps P/E implied | 80.26 | median peer P/E x EPS |
| **Blended target** | **52.33** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 46.21

## Data sources & provenance
- **fx**: 1 EUR = 0.8577 GBP (spot GBPEUR=X inverted) (Yahoo Finance FX (yfinance), 2026-09-19T09:17:53.912519+00:00)
- **income_statement**: converted EUR->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-19T09:17:54.055247+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), EUR->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-19T09:17:54.329694+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-19T09:17:54.506526+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (209.0450 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-19T09:17:54.845879+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:18:01.325235+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:18:01.228183+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-19T09:18:01.228183+00:00)
- **cost_of_equity**: ke = 4.99% + 0.63 x 4.31% = 7.72% (CAPM, 2026-09-19T09:18:01.228183+00:00)
- **cost_of_equity**: beta raw 0.45 -> adjusted 0.63 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-19T09:18:01.117553+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 21.3x x EPS 3.77 = 80.26
- **peer_multiples**: EV/EBITDA leg: median 12.7x x EBITDA 9,558m - net debt 18,234m = equity 103,046m / 2,153m shares = 47.86
- **blend**: blend: dcf 44.14 x 55%
- **blend**: blend: ddm 51.18 x 18%
- **blend**: blend: comps_pe 80.26 x 18%
- **blend**: blend: comps_ev_ebitda 47.86 x 9%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-19T09:18:01.341192+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.