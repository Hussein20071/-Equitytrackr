# GSK (GSK.L) — Research Note

**BUY** · Target GBP 26.24 · Upside 39.76% · Thesis date 2026-09-19T09:18:03.157778+00:00

> BUY: target GBP 26.24 vs price GBP 18.775 (+39.8% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 18.775 against a blended 12-month target of GBP 26.24 (weights {'ddm': 0.4, 'comps_pe': 0.4, 'comps_ev_ebitda': 0.2}). Gordon DDM on trailing DPS GBP 0.84 (g = ROE x retention) values them at GBP 21.34. Peer-median P/E of 20.1x applied to EPS of GBP 1.43 implies GBP 28.64. Reported FCF has trended down over the last 4 financial years (GBP 5,145m -> GBP 4,756m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 26.24 (+39.8%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 26.24 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 4756.0 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.0129, -0.0065, 0.0, 0.0, 0.0] | Invalid DCF inputs: ['WACC must exceed terminal growth'] |
| Terminal growth | 0.0 |  |
| WACC (ke) | 0.0757 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.5980000000000001; implied pre-tax kd 4.1% disclosed only |
| Net debt | 13731.0 GBP m | Balance sheet latest FY |
| DCF value/share | None | 2-stage FCF model |
| DDM value/share | 21.3388 | g capped: ROE x retention 13.73% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 33.4% x retention 41% = 3.49% (raw 13.73%, capped); D1 = DPS TTM 0.84 x (1+g) = 0.87; value = D1 / (ke 7.57% - g 3.49%) = 21.34 |
| Comps P/E implied | 28.64 | median peer P/E x EPS |
| **Blended target** | **26.24** | weights {'ddm': 0.4, 'comps_pe': 0.4, 'comps_ev_ebitda': 0.2} |

Price at publication: GBP 18.775

## Data sources & provenance
- **fx**: native GBP (n/a, 2026-09-19T09:18:01.566150+00:00)
- **income_statement**: converted GBP->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-19T09:18:01.629392+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), GBP->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-19T09:18:01.692628+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-19T09:18:01.786019+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (84.0000 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-19T09:18:02.097208+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:18:03.141541+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:18:03.044798+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-19T09:18:03.044798+00:00)
- **cost_of_equity**: ke = 4.99% + 0.60 x 4.31% = 7.57% (CAPM, 2026-09-19T09:18:03.044798+00:00)
- **cost_of_equity**: beta raw 0.29 floored at 0.40 -> adjusted 0.60 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-19T09:18:02.949736+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 20.1x x EPS 1.43 = 28.64
- **peer_multiples**: EV/EBITDA leg: median 13.4x x EBITDA 10,402m - net debt 13,731m = equity 125,154m / 4,006m shares = 31.24
- **blend**: blend: ddm 21.34 x 40%
- **blend**: blend: comps_pe 28.64 x 40%
- **blend**: blend: comps_ev_ebitda 31.24 x 20%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-19T09:18:03.157778+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.