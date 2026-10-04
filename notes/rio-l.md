# Rio Tinto (RIO.L) — Research Note

**SELL** · Target GBP 58.01 · Upside -17.79% · Thesis date 2026-10-04T12:58:21.975330+00:00

> SELL: target GBP 58.01 vs price GBP 70.56 (-17.8% upside) on blended DCF/DDM/comps

The model's blended 12-month target is GBP 58.01 against a market price of GBP 70.56 (-17.8%), which reads as SELL on the published recommendation bands. The target is a weighted blend of a 2-stage FCF DCF at GBP 35.86 per share, a Gordon DDM at GBP 75.04 -- the market is effectively pricing different assumptions than those frozen inputs, and the note shows exactly which. The thesis is proven wrong if the shares sustain beyond the target in the opposite direction of the call for 10+ sessions, or if reported results break the frozen FCF/net-debt base.

## Catalysts
- Next results date: not published by the Yahoo calendar feed -- check the company's investor-relations page; the decisive input is reported FCF vs the frozen base
- Convergence (or divergence) vs the GBP 58.01 target over the 3-month review window

## Risks
- Fundamentals revision: a restated or materially different FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | nan GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.05, -0.025, 0.0, 0.0, 0.0] | growth: FCF CAGR -20.2% over 2y, 50% damped -> -5.0% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.0 | terminal g = min(rf 4.99%, explicit CAGR/2) = 0.00% |
| WACC (ke) | 0.0979 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 1.115173; implied pre-tax kd 8.3% disclosed only |
| Net debt | 10935.4 GBP m | Balance sheet latest FY |
| DCF value/share | 35.86 | 2-stage FCF model |
| DDM value/share | 75.0394 | g capped: ROE x retention 4.60% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 19.3% x retention 24% = 3.49% (raw 4.60%, capped); D1 = DPS TTM 4.57 x (1+g) = 4.73; value = D1 / (ke 9.79% - g 3.49%) = 75.04 |
| Comps P/E implied | None | median peer P/E x EPS |
| **Blended target** | **58.01** | weights {'dcf': 0.667, 'ddm': 0.222, 'comps_ev_ebitda': 0.111} |

Price at publication: GBP 70.56

## Data sources & provenance
- **fx**: 1 USD = 0.7553 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-10-04T12:44:22.337609+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-10-04T12:44:22.542045+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-10-04T12:44:22.746197+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-10-04T12:44:23.068316+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (457.0123 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-10-04T12:44:23.420625+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:21.462855+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:21.368658+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-10-04T12:58:21.368658+00:00)
- **cost_of_equity**: ke = 4.99% + 1.12 x 4.31% = 9.79% (CAPM, 2026-10-04T12:58:21.368658+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 1.17 over 104 weekly observations -- measured against the benchmark the portfolio tracks (^FTSE), per-name (OLS beta: RIO.L vs ^FTSE weekly returns, 2y, 2026-10-04T12:58:21.263144+00:00)
- **cost_of_equity**: beta raw 1.17 -> adjusted 1.12 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-10-04T12:58:21.263144+00:00)
- **peer_multiples**: P/E median not robust: only 1 valid peer multiple; leg dropped (need >=2)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: excluded from medians: GLEN.L P/E 240x > 60x cap
- **peer_multiples**: EV/EBITDA leg: median 12.0x x EBITDA 17,351m - net debt 10,935m = equity 196,872m / 1,255m shares = 156.92
- **blend**: blend: dcf 35.86 x 67%
- **blend**: blend: ddm 75.04 x 22%
- **blend**: blend: comps_ev_ebitda 156.92 x 11%
- **blend**: base FCF = normalised multi-year average of the 3 finite trailing FYs (7,087, 6,098, 4,515) = 5,900 GBPm; latest-FY value missing/non-finite on the feed (latest-FY FCF is not a finite number on the feed)
- **model_choices**:  (, )

## Addenda
- [2026-10-04] **methodology**: 2026-10-04 model sanity review: (1) beta estimation window widened from 52 to ~104 weekly observations (2y) after the 1y window pinned BP and SHEL at the 0.40 beta floor; (2) DCF base FCF now falls back to a normalised multi-year average when the latest FY is missing/non-finite, and the DCF is excluded with an explicit reason when trailing FCF is non-positive; (3) a +/-30% model-outlier guardrail now runs at publication and flags the driving leg. Inputs were re-frozen from refetched live data; the tracked window and hit counting still start at first publication (2026-09-19).
- [2026-10-04] **thesis_check**: Recommendation changed BUY -> SELL at the 2026-10-04 revision, so readers comparing the live record should note: the tracked window (from first publication 2026-09-19) initially measured a BUY. The flip is driven by restoring the DCF leg on a normalised multi-year FCF average (GBP 5,900m over FY2022-24 after the feed returned NaN for FY2025) whose history-derived growth path is -5% tapering to 0 - i.e. the model reads Rio's declining free cash flow as worth GBP 35.86/share vs price ~70. The EV/EBITDA leg (GBP 156.92) disagrees sharply upward; both are shown so you can judge the blend.

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-10-04T12:58:21.975330+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.