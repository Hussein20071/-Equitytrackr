# Product Roadmap — Ideas Agent

**Role:** second subagent — generate new directions, critique what exists, assist the QA pass by turning gaps into concrete, prioritized features.
**Date:** 2026-09-27 · for https://hussein20071.github.io/-Equitytrackr/

This roadmap is split into (A) ideas that make the site feel more alive, (B) ideas that deepen the research credibility, (C) ideas that reduce operational risk, and (D) a critique of the current build. Every idea is scoped for the project's hard rules: **free hosting, nothing illustrative — every number fetched or formula-derived, audit trail intact.**

---

## A. Make it feel alive (user-facing)

1. **Movers strip with day-change ticks** — a horizontal band of the 8 tickers under the hero, each a mini card with price, day %, and a colored up/down arrow. One glance answers "what happened today", which is what the user actually asks first. Data already exists (`prev_close_gbp`); zero new fetching.
2. **±2% in-page flash alerts** — the dashboard already polls every 60s; when the meta poll detects a changed day-change beyond ±2% vs the last-seen value, flash the row and toast once per ticker per session. Turns passive polling into an event feed, at zero cost.
3. **Sparks for the day** — the track-record Day column gets a tiny 5-point intraday sparkline built from the last 5 refresh snapshots (store a rolling `data/intraday.jsonl` in each refresh). Proves "live" visually and is one small file.
4. **"What changed in this refresh" changelog** — each refresh's meta gains a diff summary (which prices moved >0.5%, which KPIs changed). Rendered as a one-line caption under the hero: "Since 11:45: AZN +0.8%, HSBA −0.3%". Users trust what they can see change.
5. **PWA + desktop notifications** — add a manifest + service worker so the site installs as an app and can show OS-level "Prices updated" notifications via the Notifications API (user-granted, still 100% free). Closest free equivalent to a push service.

## B. Deepen research credibility (CV-grade)

6. **Scenario switches on note pages** — frozen base case stays frozen; add a client-side slider (WACC ±1pp, growth ±1pp) that recomputes the *published* model algebraically in JS from the frozen inputs, clearly labelled "your scenario, not the published target". Interactive but honest — nothing illustrated, everything derived from frozen inputs.
7. **Earnings-calendar catalyst tracker** — each note's catalysts get auto-checked against Yahoo's calendar data; note page shows "next catalyst: Q3 results, expected 12 Nov — 26 days". Turns the thesis into a dated monitor, not prose.
8. **Peer table hover-throughs** — the comps peer table already shows EV/EBITDA and P/E; make each row expandable to show the peer's market cap, net debt, and EBITDA with its own mini provenance line.
9. **Tracked-thesis PDF pack** — one "Download all 8 notes + dashboard as PDF" button (already have per-note print styles; a combined print view is mostly aggregation). CV-ready artifact.
10. **Alpha decay chart** — per note, plot cumulative alpha since thesis vs a ±2pp band; makes the 3-month review window visually meaningful and directly supports the hit-rate KPIs.

## C. Operational hardening (so it never "shits the bed")

11. **Self-monitoring page (status badge)** — a tiny `/status.json` written by the workflow: last run time, test count, quotes fetched, failures. A small "site health" chip on the dashboard renders green/amber/red from it. The site audits itself — on-brand and preempts "is it broken?" messages.
12. **Staleness watchdog inside the page** — client JS already knows the page timestamp; if meta hasn't changed for >45 min in market hours, show an amber "data may be stale — last refresh 11:45" chip. Honest failure display beats silent staleness.
13. **Fail-safe publishing** — if `yfinance` breaks (it has before), the workflow currently fails → no deploy → site goes stale. Add a fallback: on fetch failure, redeploy the previous snapshot with an amber "last good data" banner instead of leaving the old site silently aging.
14. **Rate-limit hygiene** — with 5-min crons, yfinance/FRED calls rise ~6×. Add conditional requests / ETag-style caching where APIs support it, and log call counts into the audit record so the audit log itself proves we're being polite.
15. **Dependency lockfile + weekly CI drill** — pin versions (requirements already exist; add hashes) and a Monday-morning workflow_dispatch drill run that exercises the full pipeline and posts the result into `status.json`.

## D. Critique of the current build (ideas agent's honest assessment)

- **Strong:** audit trail, provenance per input, frozen inputs, units cross-check (GBP + GBp), day-change column now matching Yahoo's convention, self-polling dashboard. Genuinely differentiating for a portfolio project.
- **Weak point 1 — the valuations can't be interrogated.** A recruiter can see *that* a DCF says 81.57 but can't poke it. Idea #6 (scenario switches) is the single highest-leverage addition: it makes the models feel real without breaking the frozen-input discipline.
- **Weak point 2 — no memory of the day.** Intraday history is discarded each refresh. #3 and #4 capture it cheaply and make the "live" claim visible.
- **Weak point 3 — silent failure modes.** The worst future bug is the one that makes the site stale *quietly*. #11–#13 convert silent failure into visible, honest status — which matches the project's "disclosed, not hidden" ethos.
- **Sequencing advice:** #1 + #4 (one afternoon, huge perceived liveness), then #11 + #12 (hardening), then #6 (the wow feature), then #5 (PWA). #7 is the sleeper: catalyst dates make theses falsifiable and that's what real analysts are judged on.

---

*Both agents' deliverables (this file + QA_REPORT.md) ship with the site so the workflow that built it is visible to anyone reading the repo.*
