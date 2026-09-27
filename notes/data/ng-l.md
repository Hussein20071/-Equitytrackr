# National Grid (NG.L) — Research Note

**HOLD** · Target GBP 11.1 · Upside -3.31% · Thesis date 2026-09-19T09:18:11.050368+00:00

> HOLD: target GBP 11.1 vs price GBP 11.48 (-3.3% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 11.48 against a blended 12-month target of GBP 11.1 (weights {'comps_pe': 0.667, 'comps_ev_ebitda': 0.333}). Peer-median P/E of 21.2x applied to EPS of GBP 0.64 implies GBP 13.66. Reported FCF has trended down over the last 4 financial years (GBP 6m -> GBP -2,746m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 11.1 (-3.3%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 11.10 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | -2746.0 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.0, 0.0, 0.0, 0.0, 0.0] | Invalid DCF inputs: ['base FCF must be positive and finite'] |
| Terminal growth | 0.025 |  |
| WACC (ke) | 0.0811 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.72463; implied pre-tax kd 3.6% disclosed only |
| Net debt | 43034.0 GBP m | Balance sheet latest FY |
| DCF value/share | None | 2-stage FCF model |
| DDM value/share | None | DDM skipped: g=-1.94% not < ke*0.9=7.30% |
| Comps P/E implied | 13.66 | median peer P/E x EPS |
| **Blended target** | **11.1** | weights {'comps_pe': 0.667, 'comps_ev_ebitda': 0.333} |

Price at publication: GBP 11.48

## Data sources & provenance
- **fx**: native GBP (n/a, 2026-09-19T09:18:04.974962+00:00)
- **income_statement**: converted GBP->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-19T09:18:05.143203+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), GBP->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-19T09:18:05.367432+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-19T09:18:05.593118+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (79.3700 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-19T09:18:05.900673+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:18:11.038162+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:18:10.943162+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-19T09:18:10.943162+00:00)
- **cost_of_equity**: ke = 4.99% + 0.72 x 4.31% = 8.11% (CAPM, 2026-09-19T09:18:10.943162+00:00)
- **cost_of_equity**: beta raw 0.59 -> adjusted 0.72 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-19T09:18:10.845348+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 21.2x x EPS 0.64 = 13.66
- **peer_multiples**: EV/EBITDA leg: median 9.1x x EBITDA 8,078m - net debt 43,034m = equity 30,084m / 5,027m shares = 5.98
- **blend**: blend: comps_pe 13.66 x 67%
- **blend**: blend: comps_ev_ebitda 5.98 x 33%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-19T09:18:11.048363+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.