# Next CV Project — Associate Brief: M&A Deal Analyzer

**From:** the MD OS (MD_GUIDE.md) — this brief is written the way an MD hands work to an associate: intent, constraints, definition of done, and the traps you'd otherwise walk into.
**To:** the associate agent / the user's next build session.
**Why M&A:** the equity tracker proves *public-market research* skill. M&A proves *transaction* skill — deal intuition, LBO math, accretion/dilution, process sense — which is a different and complementary line on a CV. Recruiters read the pair as "can analyze markets AND execute a deal."

---

## 1. The product (one paragraph)

**DealLens: an audit-ready M&A deal analyzer.** Point it at any two public companies (acquirer + target), and it builds a defensible deal view from live data: standalone valuations, offer scenarios (premium bands), accretion/dilution analysis (cash, stock, and mixed consideration), leverage and LBO-feasibility checks, synergy sizing with stated methodology, and a written fairness-style summary — every input sourced and dated, every model choice disclosed, the whole thing regenerable and auditable. Ship it as a static site with the same discipline as the tracker: GitHub Pages + Actions, free, self-updating.

## 2. Why this passes the MD test (strategic thinking)

- **It reuses the moat.** The tracker's hardest-won assets — per-input provenance, frozen snapshots, append-only audit log, units discipline (GBp/GBP), the single-process ops guards — transfer directly. You are not starting from zero; you are compounding a franchise.
- **It fills the CV gap.** Public research ≠ deal execution. Accretion/dilution and LBO math are the language of banking interviews.
- **It is falsifiable.** Deal math is checkable: a recruiter can verify the accretion figure with a calculator. That is the brand (reliability with insight).

## 3. Scope — definition of done (v1, two focused sessions)

MUST ship (execution discipline: nothing half-done):
1. **Universe:** 4–6 real, currently-rumored or historical UK/EU deals with public data (e.g. re-run a completed deal like a post-mortem — "what would a fair offer have been?" — is the most defensible v1 because all data is known).
2. **Per-deal pages**, each containing:
   - Standalone values for both sides: market cap (live), EV bridge (net debt from balance sheet), and one simple multiple-based valuation (EV/EBITDA, P/E) with peer groups inherited from the tracker's peer logic.
   - **Offer construction:** premium scenarios (e.g. 20/30/40% over undisturbed price), implied equity value and EV, all in GBP with pence quoted side-by-side.
   - **Accretion/dilution:** pro-forma EPS for all-cash (with financing cost at a disclosed rate), all-stock (exchange ratio from both prices), and 50/50 mix; breakeven synergies stated ("this deal is accretive only if synergies exceed £X m").
   - **Synergy methodology:** revenue/cost synergy lines sized as % of target cost base with the assumption flagged as *assumed* (model choice), never presented as data.
   - **Leverage check:** pro-forma net debt/EBITDA vs a disclosed covenant-style ceiling; a red flag if the cash deal breaches it.
   - **Written summary:** 5 sentences, decision-first ("At a 30% premium in cash, this deal is dilutive by 3.1% unless synergies exceed £240m").
3. **Audit + provenance:** every input carries source + timestamp; the deal view is snapshotted; changes are dated addenda. Reuse `tracker/audit.py` as-is.
4. **Tests:** the accretion/dilution engine gets unit tests against hand-computed cases (a 3-line deal model on paper must reproduce exactly). If the test can't be written by hand, the engine isn't understood well enough yet.
5. **The site:** same pipeline — CI regenerates, Pages serves, `deal_meta.json` + toast pattern carried over.

EXPLICITLY OUT OF v1 (prioritisation mastery — name what you are NOT doing):
- Merger models with full balance-sheet combination (PPA, intangibles) — v2.
- Antitrust/regulatory scoring — v2 at the earliest.
- LBO with full debt schedules — v2; v1 has only the leverage check.
- Anything illustrative: no sample deals with made-up numbers, ever.

## 4. The traps (learn these now, not in review)

1. **Accretive ≠ good.** A cash deal funded at 5% to buy 4% earnings yield is accretive and value-destroying. The engine must show value creation (target value + synergies vs price paid), with accretion as a separate, secondary line. This is the #1 associate error; not making it is the differentiator.
2. **Stock deals and P/E illusion.** A low-P/E acquirer buying a high-P/E target is mechanically dilutive pre-synergies — say why (exchange ratio math), don't just report the number.
3. **Synergy hockey sticks.** Everything above 5–10% of combined cost base needs a written justification or a haircut; disclose the cap as a model choice.
4. **Undisturbed price discipline.** Premiums must anchor to the undisturbed date, not a leaky one — if you can't establish it, say so and use a disclosed proxy.
5. **Unit hell, again.** GBP vs GBp vs USD (if a US acquirer) — the FX layer from the tracker transfers; test it on day one, not at the end.

## 5. Architecture (reuse-first)

```
dealanalyzer/
  deals/            # one JSON per deal, frozen inputs + provenance (like notes/)
  engine.py         # offer construction, accretion/dilution, leverage (pure functions)
  data.py           # reuse tracker/data.py patterns: quotes, history, FX, audit
  reporting.py      # per-deal HTML + index, same CSS language, same honesty boxes
  scenarios.py      # premium grid + synergy grid (the tracker's scenario pattern)
tests/test_deals.py # hand-computed accretion cases; premium math; FX
.github/workflows   # same CI: pytest -> regenerate -> guard -> deploy
```

## 6. Standing orders (from the MD OS, applied)

- Decision speed: build the engine + one deal first, end to end, before adding deal #2. One finished thing beats three skeletons.
- Execution discipline: "done" = tests green + regenerated + verified in a browser + pushed. Not before.
- Analytical rigor: every number labelled measured / derived / assumed.
- Stakeholder management: the site's changelog tells the reader what changed — no silent edits.
- Resilience: when a data feed fails, the deal page shows the gap honestly (the tracker's data-quality box pattern), it does not quietly drop a leg.

**First deliverable:** `engine.py` with `accretion_dilution()` + its hand-computed test cases, committed before anything else. That is the 20% of the work that proves the 80% of the concept.
