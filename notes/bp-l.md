# BP (BP.L) — Research Note

**HOLD** · Target GBP 5.58 · Upside 0.04% · Thesis date 2026-10-04T12:58:18.541613+00:00

> HOLD: target GBP 5.58 vs price GBP 5.58 (+0.0% upside) on blended DCF/DDM/comps

The model's blended 12-month target is GBP 5.58 against a market price of GBP 5.58 (+0.0%), which reads as HOLD on the published recommendation bands. The target is a weighted blend of a 2-stage FCF DCF at GBP 5.41 per share, peer multiples implying GBP 0.04 (P/E leg) -- the market is effectively pricing different assumptions than those frozen inputs, and the note shows exactly which. The thesis is proven wrong if the shares sustain beyond the target in the opposite direction of the call for 10+ sessions, or if reported results break the frozen FCF/net-debt base.

## Catalysts
- Next results: 2026-10-30 (Yahoo calendar) -- reported FCF vs the frozen base is the decisive input
- Convergence (or divergence) vs the GBP 5.58 target over the 3-month review window

## Risks
- Fundamentals revision: a restated or materially different FCF/net-debt base than the frozen inputs
- Rate sensitivity: the CAPM cost of equity moves with the gilt yield

## Valuation inputs (frozen at publication)

| Input | Value | Derivation |
|---|---|---|
| Base FCF | 8513.3 GBP m | Latest FY OCF − capex, FX-converted |
| FCF growth path | [-0.05, -0.025, 0.0, 0.0, 0.0] | growth: FCF CAGR -26.9% over 3y, 50% damped -> -5.0% y1-2, tapering to ~0 by y5 (range floor/cap -5%/+15%) |
| Terminal growth | 0.0 | terminal g = min(rf 4.99%, explicit CAGR/2) = 0.00% |
| WACC (ke) | 0.0793 | WACC: cost of equity (CAPM) used directly; no leverage assumption introduced. beta 0.681884; implied pre-tax kd 8.8% disclosed only |
| Net debt | 16044.7 GBP m | Balance sheet latest FY |
| DCF value/share | 5.41 | 2-stage FCF model |
| DDM value/share | None | DDM skipped: g=-1022.00% not < ke*0.9=7.13% |
| Comps P/E implied | 0.04 | median peer P/E x EPS |
| **Blended target** | **5.58** | weights {'dcf': 0.857, 'comps_ev_ebitda': 0.143} |

Price at publication: GBP 5.577999877929687

## Data sources & provenance
- **fx**: 1 USD = 0.7553 GBP (spot GBPUSD=X inverted) (Yahoo Finance FX (yfinance), 2026-10-04T12:44:13.300070+00:00)
- **income_statement**: converted USD->GBP at spot (Yahoo Finance income_stmt (latest FY), 2026-10-04T12:44:13.337653+00:00)
- **cash_flow**: FCF = OCF + capex (capex negative), USD->GBP (Yahoo Finance cash_flow (FY Operating Cash Flow - Capex), 2026-10-04T12:44:13.363661+00:00)
- **balance_sheet**: net debt = total debt - cash & ST investments (Yahoo Finance balance_sheet (latest FY), 2026-10-04T12:44:13.395315+00:00)
- **dividends**: DPS TTM = sum of payments dated within 365d (31.2499 in listing units, GBp->GBP /100); payout = DPS/eps where eps = NI/shares (Yahoo Finance Ticker.dividends (actual payments), 2026-10-04T12:44:13.733777+00:00)
- **risk_free_rate**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:18.028849+00:00)
- **cost_of_equity**: IRLTLT01GBM156N latest obs 2026-08-01: 4.99% (OECD long-term govt bond yield via FRED, 2026-10-04T12:58:17.925130+00:00)
- **cost_of_equity**: ERP 4.31% (Jan 2025 dataset, mature Western Europe) (Damodaran country risk premium (Western Europe), 2026-10-04T12:58:17.925130+00:00)
- **cost_of_equity**: ke = 4.99% + 0.68 x 4.31% = 7.93% (CAPM, 2026-10-04T12:58:17.925130+00:00)
- **cost_of_equity**: beta = cov(r_stock, r_bench) / var(r_bench) = 0.53 over 104 weekly observations -- measured against the benchmark the portfolio tracks (^FTSE), per-name (OLS beta: BP.L vs ^FTSE weekly returns, 2y, 2026-10-04T12:58:17.836061+00:00)
- **cost_of_equity**: beta raw 0.53 -> adjusted 0.68 (0.67*raw + 0.33) (Blume (1971) beta adjustment + 0.40 beta floor, 2026-10-04T12:58:17.836061+00:00)
- **peer_multiples**: multiples computed per peer: EV = price x shares + net debt; EV/EBITDA and P/E on latest FY, all FX-converted to GBP; true median over multiples within the not-meaningful caps (P/E <= 60x, EV/EBITDA <= 30x)
- **peer_multiples**: P/E leg: median 15.2x x EPS 0.00 = 0.04
- **peer_multiples**: EV/EBITDA leg: median 5.1x x EBITDA 23,183m - net debt 16,045m = equity 101,953m / 15,452m shares = 6.60
- **peer_multiples**: P/E leg suppressed: subject trailing earnings base depressed (EPS GBP 0.0026882705293832885, implied trailing P/E 2075x); peer multiples not applied
- **blend**: blend: dcf 5.41 x 86%
- **blend**: blend: comps_ev_ebitda 6.60 x 14%
- **model_choices**:  (, )

## Addenda
- [2026-10-04] **methodology**: 2026-10-04 model sanity review: (1) beta estimation window widened from 52 to ~104 weekly observations (2y) after the 1y window pinned BP and SHEL at the 0.40 beta floor; (2) DCF base FCF now falls back to a normalised multi-year average when the latest FY is missing/non-finite, and the DCF is excluded with an explicit reason when trailing FCF is non-positive; (3) a +/-30% model-outlier guardrail now runs at publication and flags the driving leg. Inputs were re-frozen from refetched live data; the tracked window and hit counting still start at first publication (2026-09-19).

Review period: 3 months vs ^FTSE (tracking window anchored at publication).

Audit id: `2026-10-04T12:58:18.541613+00:00`

Educational project. Not investment advice. Data may be delayed or inaccurate; verify independently before acting on anything here.