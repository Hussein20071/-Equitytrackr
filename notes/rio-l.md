# Rio Tinto (RIO.L) — Research Note

**BUY** · Target GBP 99.23 · Upside 40.0% · Thesis date 2026-09-27T13:59:01.135210+00:00

> BUY: target GBP 99.23 vs price GBP 70.88 (+40.0% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 70.88 against a blended 12-month target of GBP 99.23 (weights {'ddm': 0.667, 'comps_ev_ebitda': 0.333}). Gordon DDM on trailing DPS GBP 4.57 (g = ROE x retention) values them at GBP 69.78. Reported FCF has trended down over the last 4 financial years (GBP 7,080m -> GBP nanm), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 99.23 (+40.0%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 99.23 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | nan GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.05, -0.025, 0.0, 0.0, 0.0] | latest-FY FCF is not a finite number on the feed |
| Terminal growth | 0.0 |  |
| WACC (ke) | 0.1027 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 1.225321; implied pre-tax kd 8.3% disclosed only |
| Net debt | 10924.7 GBP m | Balance sheet latest FY |
| DCF value/share | None | 2-stage FCF model |
| DDM value/share | 69.7833 | g capped: ROE x retention 4.59% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 19.3% x retention 24% = 3.49% (raw 4.59%, capped); D1 = DPS TTM 4.57 x (1+g) = 4.73; value = D1 / (ke 10.27% - g 3.49%) = 69.78 |
| Comps P/E implied | None | median peer P/E x EPS |
| **Blended target** | **99.23** | weights {'ddm': 0.667, 'comps_ev_ebitda': 0.333} |

Price at publication: GBP 70.88

## Data sources & provenance
- **fx**: 1 USD = 0.7545 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-27T13:58:58.855428+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-27T13:58:59.034485+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-27T13:58:59.220213+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-27T13:58:59.480191+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (457.0123 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-27T13:58:59.802662+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:59:01.123495+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-27T13:59:01.003347+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-27T13:59:01.003347+00:00)
- **cost_of_equity**: ke = 4.99% + 1.23 x 4.31% = 10.27% (CAPM, 2026-09-27T13:59:01.003347+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 1.34 over 52 weekly observations (Yahoo feed beta unavailable) (OLS beta: RIO.L vs ^FTSE weekly returns, 1y, 2026-09-27T13:59:00.880300+00:00)
- **cost_of_equity**: beta raw 1.34 -> adjusted 1.23 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-27T13:59:00.890122+00:00)
- **peer_multiples**: P/E median not robust: only 1 valid peer multiple; leg dropped (need >=2)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: excluded from medians: GLEN.L P/E 243x > 60x cap
- **peer_multiples**: EV/EBITDA leg: median 12.1x x EBITDA 17,334m - net debt 10,925m = equity 198,384m / 1,255m shares = 158.12
- **blend**: blend: ddm 69.78 x 67%
- **blend**: blend: comps_ev_ebitda 158.12 x 33%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-27T13:59:01.135210+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.