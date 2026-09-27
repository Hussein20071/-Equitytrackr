# Rio Tinto (RIO.L) — Research Note

**BUY** · Target GBP 117.05 · Upside 62.16% · Thesis date 2026-09-19T09:18:16.705548+00:00

> BUY: target GBP 117.05 vs price GBP 72.18 (+62.2% upside) on blended DCF/DDM/comps

Systematic note generated from live data. Market price GBP 72.18 against a blended 12-month target of GBP 117.05 (weights {'ddm': 0.667, 'comps_ev_ebitda': 0.333}). Gordon DDM on trailing DPS GBP 4.57 (g = ROE x retention) values them at GBP 97.80. Reported FCF has trended down over the last 4 financial years (GBP 7,005m -> GBP nanm), which drives the growth path shown in the inputs table.

## Catalysts
- Convergence toward the blended target of GBP 117.05 (+62.2%) over the 3-month review window
- Next FY results: reported FCF vs the latest-FY base used in the DCF

## Risks
- Thesis invalidation: price sustaining beyond GBP 117.05 in the opposite direction of the recommendation for 10+ sessions
- Fundamentals revision: a restated or materially different latest-FY FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the 10Y gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | nan GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.05, -0.025, 0.0, 0.0, 0.0] | latest-FY FCF is not a finite number on the feed |
| Terminal growth | 0.0 |  |
| WACC (ke) | 0.0833 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.77488; implied pre-tax kd 8.3% disclosed only |
| Net debt | 10808.9 GBP m | Balance sheet latest FY |
| DCF value/share | None | 2-stage FCF model |
| DDM value/share | 97.7958 | g capped: ROE x retention 4.43% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 19.3% x retention 23% = 3.49% (raw 4.43%, capped); D1 = DPS TTM 4.57 x (1+g) = 4.73; value = D1 / (ke 8.33% - g 3.49%) = 97.80 |
| Comps P/E implied | None | median peer P/E x EPS |
| **Blended target** | **117.05** | weights {'ddm': 0.667, 'comps_ev_ebitda': 0.333} |

Price at publication: GBP 72.18

## Data sources & provenance
- **fx**: 1 USD = 0.7465 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-09-19T09:18:11.363206+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-09-19T09:18:11.531261+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-09-19T09:18:11.741952+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-09-19T09:18:12.065208+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (457.0123 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-09-19T09:18:12.399561+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:18:16.680875+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-09-19T09:18:16.584060+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-09-19T09:18:16.584060+00:00)
- **cost_of_equity**: ke = 4.99% + 0.77 x 4.31% = 8.33% (CAPM, 2026-09-19T09:18:16.584060+00:00)
- **cost_of_equity**: beta raw 0.66 -> adjusted 0.77 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-09-19T09:18:16.390733+00:00)
- **peer_multiples**: P/E median not robust: only 1 valid peer multiple; leg dropped (need >=2)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: excluded from medians: GLEN.L P/E 241x > 60x cap
- **peer_multiples**: EV/EBITDA leg: median 12.0x x EBITDA 17,151m - net debt 10,809m = equity 195,160m / 1,255m shares = 155.55
- **blend**: blend: ddm 97.80 x 67%
- **blend**: blend: comps_ev_ebitda 155.55 x 33%
- **model_choices**:  (, )

## Addenda
_None yet._

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-09-19T09:18:16.700049+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.