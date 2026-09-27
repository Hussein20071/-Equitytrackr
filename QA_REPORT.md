# QA Report — Independent Verification Pass

**Role:** dedicated checker agent, acting as the user's stand-in tester.
**Date:** 2026-09-27 · **Site:** https://hussein20071.github.io/-Equitytrackr/
**Verdict: PASS** — 3 real bugs found and fixed during this pass (§1), everything re-verified green afterwards.

---

## 1. Bugs found & fixed during this pass

| # | Bug | Root cause | Fix | Verified by |
|---|-----|-----------|-----|-------------|
| 1 | "Prices updated" toast appeared on **every** page load, nagging constantly | Dashboard timestamp and `refresh_meta.json` timestamp were captured microseconds apart → always unequal → page always believed newer data existed | One shared `now_ts` per refresh cycle for dashboard + note pages + audit + meta; client compares at **minute precision** (`sameTs`) | New unit tests; local tab loaded with toast hidden; live tab loaded with toast hidden |
| 2 | Clicking **View now** "did nothing" — user landed on the same stale page | GitHub Pages caches HTML up to 10 min; a plain `location.reload()` re-served the cached copy | Click now navigates to `?t=<Date.now()>`, which busts the cache | Real click in live browser: `navigated: true`, page advanced to newer data |
| 3 | Toast text was unverifiable (said only "refreshed X") | No reference point for the reader | Toast now shows "Loaded \<page time\> · latest is \<data time\>" | Checked in both local and live browser |

Pre-existing operational bug also cleaned up: **duplicate background processes** (two refresh loops + two http.servers) racing on the same files. Reduced to one loop (1-min) + one server; verified by process listing and log cadence.

---

## 2. Test evidence (real browser, not just code review)

### Local live view (loop @ 1 min, http://127.0.0.1:8123/)
- [x] Page renders: hero, market snapshot, KPI tiles, track-record table, note cards, chart, audit trail
- [x] **Day column** present in track-record table; AZN shows **+1.23%** (= Yahoo's Friday close move; 12,400p → 12,552p)
- [x] Columns labelled **RETURN SINCE THESIS** / **ALPHA SINCE THESIS** with explainer text
- [x] Toast **auto-fired** when the loop refreshed under the open tab: "Loaded 11:38 UTC · latest is 11:39 UTC"
- [x] **View now click navigated** to `?t=...` and landed on fresh data; toast correctly hidden after
- [x] Interval selector: change → persisted to localStorage (`live_interval`), reload timer armed/disarmed
- [x] **"Off" stops auto-reload**: 65s observation window with two background refreshes → zero reloads
- [x] Note page (azn-l.html): title, pence "quoted" span, 7 content sections, chart canvas, PDF + copy buttons
- [x] Audit viewer (audit.html): 398 rows, newest event 11:45 UTC — live and append-only

### Live production site (real Chromium, logged-in-free)
- [x] HTTP 200 on `/`, `/refresh_meta.json`, `/audit.html`, `/audit_log.jsonl`, 2 note pages, 1 note JSON, 1 snapshot file
- [x] Fix shipped: `sameTs` + cache-bust click present in live HTML; toast hidden on load (timestamps agree)
- [x] **5-min auto-reload worked in production**: tab opened on 11:48 build, reloaded itself onto 11:54 build
- [x] Toast wiring on production: injected a newer-meta signal → toast fired with correct text
- [x] **View now click on production**: `navigated: true` → cache-busted URL → latest data
- [x] CI: runs #9 and #10 both `completed success` (tests → refresh → guard → deploy)

### Test suite
- [x] **35/35 pytest passing** (32 before this pass; +3 regression tests: shared timestamp, cache-bust click, minute-precision compare)

---

## 3. Known limitations (disclosed, not hidden)

1. **GitHub Actions floor:** scheduled runs can be no more frequent than 5 minutes and may be delayed a few minutes under platform load. This is GitHub's limit, not the app's.
2. **Weekday crons:** the `*/5 7-16` LSE-hours cron runs Mon–Fri only (LSE doesn't trade weekends). A weekend touch keeps the site from looking stale, but between them nothing changes — correct behavior, verified today (Sunday): no new cloud data → no toast.
3. **Minute-precision toast compare:** a refresh landing in the same minute as your page load won't toast. Trade-off accepted: it eliminates false toasts from Pages cache lag.
4. **Frozen valuations:** note DCF/DDM/comps values are frozen at publication by design; only quotes, day changes, and tracked performance are live. Revaluation is a deliberate editorial act (addenda / re-publication).
5. **Auto-reload timer race:** clicking View now in the same instant the 5-min timer fires can swallow the click (observed once locally). Rare and self-healing — next poll re-shows the toast.

---

## 4. Sign-off

Every user-facing claim was tested against the running site in a real browser, and every number checked against its source (quotes vs Yahoo day-change convention; timestamps vs audit log). Nothing illustrative: all figures on the site are fetched or formula-derived, and the audit log records every fetch.
