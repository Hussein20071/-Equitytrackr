# Unilever (ULVR.L) — Research Note

**BUY** · Target GBP 52.24 · Upside 16.52% · Thesis date 2026-10-04T12:58:14.877053+00:00

> BUY: target GBP 52.24 vs price GBP 44.84 (+16.5% upside) on blended DCF/DDM/comps

The model's blended 12-month target is GBP 52.24 against a market price of GBP 44.84 (+16.5%), which reads as BUY on the published recommendation bands. The target is a weighted blend of a 2-stage FCF DCF at GBP 44.53 per share, a Gordon DDM at GBP 52.14, peer multiples implying GBP 78.23 (P/E leg) -- the market is effectively pricing different assumptions than those frozen inputs, and the note shows exactly which. The thesis is proven wrong if the shares sustain beyond the target in the opposite direction of the call for 10+ sessions, or if reported results break the frozen FCF/net-debt base.

## Catalysts
- Next results date: not published by the Yahoo calendar feed -- check the company's investor-relations page; the decisive input is reported FCF vs the frozen base
- Convergence (or divergence) vs the GBP 52.24 target over the 3-month review window

## Risks
- Fundamentals revision: a restated or materially different FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 5746.0 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [0.0332, 0.0332, 0.0249, 0.0166, 0.0083] | growth: FCF CAGR +6.6% over 3y, 50% damped -> +3.3% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.025 | terminal g = min(rf 4.99%, explicit CAGR/2) = 2.50% |
| WACC (ke) | 0.0764 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.6154200000000001; implied pre-tax kd 4.2% disclosed only |
| Net debt | 18072.8 GBP m | Balance sheet latest FY |
| DCF value/share | 44.53 | 2-stage FCF model |
| DDM value/share | 52.1434 | g capped: ROE x retention 14.05% from a single-year base exceeds the sustainable-perpetual cap 0.7 x risk-free = 3.49%; g = ROE 31.9% x retention 44% = 3.49% (raw 14.05%, capped); D1 = DPS TTM 2.09 x (1+g) = 2.16; value = D1 / (ke 7.64% - g 3.49%) = 52.14 |
| Comps P/E implied | 78.23 | median peer P/E x EPS |
| **Blended target** | **52.24** | weights {'dcf': 0.545, 'ddm': 0.182, 'comps_pe': 0.182, 'comps_ev_ebitda': 0.091} |

Price at publication: GBP 44.835

## Data sources & provenance
- **fx**: 1 EUR = 0.8501 GBP (spot GBPEUR=X inverted) (Yahoo Finance FX (yfinance), 2026-10-04T12:44:02.871376+00:00)
- **income_statement**: converted EUR->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-10-04T12:44:03.081444+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), EUR->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-10-04T12:44:03.289284+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-10-04T12:44:03.466934+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (209.0450 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-10-04T12:44:03.786257+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:14.152793+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:14.053985+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-10-04T12:58:14.053985+00:00)
- **cost_of_equity**: ke = 4.99% + 0.62 x 4.31% = 7.64% (CAPM, 2026-10-04T12:58:14.053985+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 0.43 over 104 weekly observations -- measured against the benchmark the portfolio tracks (^FTSE), per-name (OLS beta: ULVR.L vs ^FTSE weekly returns, 2y, 2026-10-04T12:58:13.960519+00:00)
- **cost_of_equity**: beta raw 0.43 -> adjusted 0.62 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-10-04T12:58:13.960519+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 20.9x x EPS 3.74 = 78.23
- **peer_multiples**: EV/EBITDA leg: median 12.5x x EBITDA 9,474m - net debt 18,073m = equity 100,531m / 2,154m shares = 46.68
- **blend**: blend: dcf 44.53 x 55%
- **blend**: blend: ddm 52.14 x 18%
- **blend**: blend: comps_pe 78.23 x 18%
- **blend**: blend: comps_ev_ebitda 46.68 x 9%
- **model_choices**:  (, )

## Addenda
- [2026-10-04] **methodology**: 2026-10-04 model sanity review: (1) beta estimation window widened from 52 to ~104 weekly observations (2y) after the 1y window pinned BP and SHEL at the 0.40 beta floor; (2) DCF base FCF now falls back to a normalised multi-year average when the latest FY is missing/non-finite, and the DCF is excluded with an explicit reason when trailing FCF is non-positive; (3) a +/-30% model-outlier guardrail now runs at publication and flags the driving leg. Inputs were re-frozen from refetched live data; the tracked window and hit counting still start at first publication (2026-09-19).

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-10-04T12:58:14.877053+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.