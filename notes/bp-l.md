# BP (BP.L) — Research Note

**HOLD** · Target GBP 5.77 · Upside 3.28% · Thesis date 2026-09-19T09:32:46.135401+00:00

> HOLD: target GBP 5.77 vs price GBP 5.587000122070313 (+3.3% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 5.587000122070313 against a blended 12-month target of GBP 5.77 (weights {'dcf': 0.857, 'comps_ev_ebitda': 0.143}). The 2-stage FCF DCF on a base of GBP 8,415m latest-FY free cash flow (FX-converted from USD) values the shares at GBP 5.65. Peer-median P/E of 15.3x applied to EPS of GBP 0.00 implies GBP 0.04. Reported FCF has trended down over the last 4 financial years (GBP 21,547m -> GBP 8,415m), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 5.77 (+3.3%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 5.77 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 8414.8 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.05, -0.025, 0.0, 0.0, 0.0] | growth: FCF CAGR -26.9% over 3y, 50% damped -> -5.0% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.0 | terminal g = min(rf 4.99%, explicit CAGR/2) = 0.00% |
| WACC (ke) | 0.0757 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.5980000000000001; implied pre-tax kd 8.8% disclosed only |
| Net debt | 15859.1 GBP m | Balance sheet latest FY |
| DCF value/share | 5.65 | 2-stage FCF model |
| DDM value/share | None | DDM skipped: g=-1034.09% not < ke*0.9=6.81% |
| Comps P/E implied | 0.04 | median peer P/E x EPS |
| **Blended target** | **5.77** | weights {'dcf': 0.857, 'comps_ev_ebitda': 0.143} |

Price at publication: GBP 5.587000122070313

## Data sources & provenance
- **fx**: 1 USD = 0.7465 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-19T09:18:03.371436+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-19T09:18:03.413703+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-19T09:18:03.445372+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-19T09:18:03.476552+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (31.2499 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-19T09:18:03.816378+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:32:46.119702+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:32:45.968168+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-19T09:32:45.968168+00:00)
- **cost_of_equity**: ke = 4.99% + 0.60 x 4.31% = 7.57% (CAPM, 2026-09-19T09:32:45.968168+00:00)
- **cost_of_equity**: beta raw -0.22 floored at 0.40 -> adjusted 0.60 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-19T09:32:45.650647+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 15.3x x EPS 0.00 = 0.04
- **peer_multiples**: EV/EBITDA leg: median 5.1x x EBITDA 22,915m - net debt 15,859m = equity 100,547m / 15,452m shares = 6.51
- **peer_multiples**: P/E leg suppressed: subject trailing earnings base depressed (EPS GBP 0.0026570972394862956, implied trailing P/E 2103x); peer multiples not applied
- **blend**: blend: dcf 5.65 x 86%
- **blend**: blend: comps_ev_ebitda 6.51 x 14%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-19T09:32:46.134394+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.