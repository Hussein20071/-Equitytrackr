"""Unit tests for the tracker v2 core.

Run: python -m pytest tests/ -v
"""

from __future__ import annotations

import math
import tempfile
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

import pandas as pd

from tracker import audit, performance, valuation


def _fin(ticker, *, shares_m, net_debt_m, ebitda_m=None, net_income_m=None,
         eps_gbp=None, beta=None):
    return SimpleNamespace(
        ticker=ticker, shares_m=shares_m, net_debt_m=net_debt_m,
        ebitda_m=ebitda_m, net_income_m=net_income_m,
        eps_ttm_gbp=eps_gbp, beta=beta,
    )


class DCFTests(unittest.TestCase):
    def test_dcf_basic(self):
        inp = valuation.DCFInputs(
            ticker="TEST.L",
            base_fcf_m=100.0,
            fcf_growth=[0.05] * 5,
            terminal_growth=0.02,
            wacc=0.08,
            net_debt_m=50.0,
            shares_m=100.0,
        )
        res = valuation.run_dcf(inp)
        self.assertGreater(res.value_per_share, 0)
        self.assertAlmostEqual(
            res.enterprise_value_m - inp.net_debt_m, res.equity_value_m, places=6
        )

    def test_dcf_rejects_nan_base(self):
        inp = valuation.DCFInputs(
            ticker="TEST.L",
            base_fcf_m=math.nan,
            fcf_growth=[0.05],
            terminal_growth=0.02,
            wacc=0.08,
            net_debt_m=0.0,
            shares_m=1.0,
        )
        with self.assertRaises(ValueError):
            valuation.run_dcf(inp)

    def test_dcf_invalid_wacc(self):
        inp = valuation.DCFInputs(
            ticker="TEST.L", base_fcf_m=100.0, fcf_growth=[0.05],
            terminal_growth=0.02, wacc=0.01, net_debt_m=0.0, shares_m=1.0,
        )
        with self.assertRaises(ValueError):
            valuation.run_dcf(inp)


class GrowthDerivationTests(unittest.TestCase):
    def test_cagr_damped(self):
        path, deriv, cagr = valuation.derive_fcf_growth([100.0, 110.0, 121.0])
        self.assertAlmostEqual(cagr, 0.10, places=3)
        self.assertEqual(len(path), 5)
        self.assertGreater(path[0], 0)
        self.assertLess(path[4], path[0])
        self.assertIn("CAGR", deriv)

    def test_sign_flip_falls_back_to_zero(self):
        path, deriv, cagr = valuation.derive_fcf_growth([-500.0, 100.0, 120.0])
        self.assertEqual(path, [0.0] * 5)
        self.assertIsNone(cagr)
        self.assertIn("sign-flipping", deriv)

    def test_insufficient_history(self):
        path, deriv, cagr = valuation.derive_fcf_growth([100.0])
        self.assertEqual(path, [0.0] * 5)
        self.assertIn("disclosed model choice", deriv)

    def test_terminal_growth_rule(self):
        # min(rf 4%, explicit CAGR/2 = 3%, and the 2.5% absolute cap)
        tg, deriv = valuation.derive_terminal_growth(0.04, 0.06)
        self.assertAlmostEqual(tg, 0.025, places=6)
        tg2, _ = valuation.derive_terminal_growth(None, 0.06)
        self.assertEqual(tg2, 0.0)


class DDMTests(unittest.TestCase):
    def test_ddm_basic(self):
        res = valuation.run_ddm(dps_ttm_gbp=2.0, roe=0.15, payout=0.5, ke=0.10)
        g = 0.15 * 0.5
        self.assertAlmostEqual(res.value_per_share, 2.0 * (1 + g) / (0.10 - g), places=2)
        self.assertIn("g = ROE", res.derivation[0] or "")

    def test_ddm_g_capped(self):
        res = valuation.run_ddm(dps_ttm_gbp=2.0, roe=0.15, payout=0.5,
                                ke=0.10, max_g=0.035)
        # D1 uses the capped g (consistent Gordon): 2 x 1.035 / (0.10 - 0.035)
        self.assertAlmostEqual(res.g, 0.035, places=6)
        self.assertAlmostEqual(res.value_per_share, 2.0 * 1.035 / 0.065, places=2)
        self.assertTrue(any("capped" in d for d in res.derivation))

    def test_ddm_missing_inputs(self):
        res = valuation.run_ddm(None, 0.15, 0.5, 0.10)
        self.assertIsNone(res.value_per_share)


class CompsTests(unittest.TestCase):
    def test_median_and_implied(self):
        subject = _fin("SUB.L", shares_m=100.0, net_debt_m=0.0,
                       net_income_m=100.0, eps_gbp=1.0)
        peers = [
            _fin("A", shares_m=10.0, net_debt_m=0.0, net_income_m=100.0),   # pe 6
            _fin("B", shares_m=10.0, net_debt_m=0.0, net_income_m=100.0),   # pe 8
            _fin("C", shares_m=10.0, net_debt_m=0.0, net_income_m=100.0),   # pe 10
        ]
        px = {"A": 60.0, "B": 80.0, "C": 100.0}
        res = valuation.run_comps(subject, peers, px)
        self.assertAlmostEqual(res.median_pe, 8.0, places=6)
        self.assertAlmostEqual(res.implied_price_pe, 8.0, places=6)

    def test_degenerate_pe_excluded(self):
        subject = _fin("SUB.L", shares_m=100.0, net_debt_m=0.0,
                       net_income_m=100.0, eps_gbp=1.0)
        peers = [
            _fin("A", shares_m=10.0, net_debt_m=0.0, net_income_m=100.0),   # pe 6
            _fin("B", shares_m=10.0, net_debt_m=0.0, net_income_m=100.0),   # pe 8
            _fin("GLEN", shares_m=10.0, net_debt_m=0.0, net_income_m=1.0),  # pe 1000
        ]
        px = {"A": 60.0, "B": 80.0, "GLEN": 1000.0}
        res = valuation.run_comps(subject, peers, px)
        # True median of the even set [6, 8] is 7.0
        self.assertAlmostEqual(res.median_pe, 7.0, places=6)
        self.assertAlmostEqual(res.implied_price_pe, 7.0, places=6)
        self.assertTrue(any("excluded" in d for d in res.derivation))

    def test_single_peer_median_dropped(self):
        subject = _fin("SUB.L", shares_m=100.0, net_debt_m=0.0,
                       net_income_m=100.0, eps_gbp=1.0)
        peers = [_fin("A", shares_m=10.0, net_debt_m=0.0, net_income_m=100.0)]
        res = valuation.run_comps(subject, peers, {"A": 60.0})
        self.assertIsNone(res.median_pe)


class BlendTests(unittest.TestCase):
    def test_blend_legs(self):
        tgt, w, deriv = valuation.blend_legs(
            [("dcf", 10.0, 0.5), ("comps", 8.0, 0.25), ("comps2", 12.0, 0.25)]
        )
        self.assertAlmostEqual(tgt, 10.0, places=6)
        self.assertAlmostEqual(sum(w.values()), 1.0, places=6)

    def test_blend_dcf_only(self):
        tgt, w, _ = valuation.blend_legs([("dcf", 7.5, 0.6)])
        self.assertAlmostEqual(tgt, 7.5, places=6)
        self.assertAlmostEqual(w["dcf"], 1.0, places=6)

    def test_blend_no_legs(self):
        tgt, w, deriv = valuation.blend_legs([("dcf", None, 0.6)])
        self.assertIsNone(tgt)
        self.assertEqual(w, {})


class PerformanceTests(unittest.TestCase):
    def _hist(self, rows):
        return pd.DataFrame(rows)

    def test_note_performance_basic(self):
        t0 = datetime(2025, 6, 2)
        days = [t0 + timedelta(days=i) for i in range(0, 91, 7)]
        hist = self._hist([
            {"Ticker": "TEST.L", "Date": d, "Close_gbp": 100.0 + i, "Volume": 1}
            for i, d in enumerate(days)
        ])
        bench = self._hist([
            {"Ticker": "^FTSE", "Date": d, "Close_gbp": 100.0, "Volume": 1}
            for d in days
        ])
        note = {"ticker": "TEST.L", "published_at": t0.isoformat(),
                "price_target_gbp": 110.0, "recommendation": "BUY"}
        res = performance.note_performance(note, hist, bench)
        self.assertEqual(res["bench_return_pct"], 0.0)
        self.assertGreater(res["alpha_pct"], 0)
        self.assertTrue(res["in_window"])

    def test_fallback_to_pre_thesis_close(self):
        # Note published after the last available close.
        t0 = datetime(2025, 6, 10)
        days = [datetime(2025, 6, 2) + timedelta(days=i) for i in range(5)]
        hist = self._hist([
            {"Ticker": "TEST.L", "Date": d, "Close_gbp": 100.0 + 5 * i, "Volume": 1}
            for i, d in enumerate(days)
        ])
        bench = self._hist([
            {"Ticker": "^FTSE", "Date": d, "Close_gbp": 100.0, "Volume": 1}
            for d in days
        ])
        note = {"ticker": "TEST.L", "published_at": t0.isoformat(),
                "price_target_gbp": 110.0, "recommendation": "BUY"}
        res = performance.note_performance(note, hist, bench)
        self.assertIsNotNone(res)
        self.assertEqual(res["base_price"], 120.0)  # last close before thesis

    def test_vol_and_drawdown(self):
        closes = pd.Series([100, 110, 99, 105, 95])
        mdd = performance.max_drawdown(closes)
        self.assertAlmostEqual(mdd, (95 / 110 - 1) * 100, places=2)  # percent
        vol = performance.annualized_vol(closes)
        self.assertGreater(vol, 0)

    def test_monthly_attribution(self):
        days = pd.date_range("2025-06-02", periods=70, freq="D")
        hist = self._hist([
            {"Ticker": "TEST.L", "Date": d, "Close_gbp": 100.0, "Volume": 1}
            for d in days
        ])
        bench = self._hist([
            {"Ticker": "^FTSE", "Date": d, "Close_gbp": 100.0 + i * 0.1, "Volume": 1}
            for i, d in enumerate(days)
        ])
        note = {"ticker": "TEST.L", "published_at": days[0].isoformat(),
                "price_target_gbp": 110.0, "recommendation": "BUY"}
        rows = performance.monthly_attribution(note, hist, bench)
        self.assertGreaterEqual(len(rows), 2)
        self.assertIn("alpha_pct", rows[0])

    def test_summarize(self):
        rows = [
            {"ticker": "A", "alpha_pct": 3.0, "return_pct": 5.0, "rec": "BUY",
             "pt": 110.0, "last_price": 111.0, "ann_vol_pct": 20.0,
             "max_drawdown_pct": -5.0, "trading_days": 60},
            {"ticker": "B", "alpha_pct": -1.0, "return_pct": 1.0, "rec": "HOLD",
             "pt": None, "last_price": 100.0, "ann_vol_pct": 10.0,
             "max_drawdown_pct": -2.0, "trading_days": 60},
        ]
        s = performance.summarize(rows)
        self.assertEqual(s["n"], 2)
        self.assertEqual(s["hit_rate_pct"], 50.0)
        self.assertEqual(s["avg_ann_vol_pct"], 15.0)
        self.assertEqual(s["worst_drawdown_pct"], -5.0)
        self.assertEqual(s["total_trading_days"], 120)


class AuditTests(unittest.TestCase):
    def test_record_and_tail(self):
        """Record/tail round-trip against an isolated log path.

        Patches audit._log_path directly: mutating config.DATA_DIR leaked
        into the real audit log via the cleanup clear() call, deleting
        production audit history on every test run.
        """
        import json as _json
        from pathlib import Path as _Path
        from unittest import mock as _mock

        with tempfile.TemporaryDirectory() as td:
            fake_log = _Path(td) / "audit_log.jsonl"
            with _mock.patch.object(audit, "_log_path", return_value=fake_log):
                audit.record("test_event", {"a": 1})
                audit.record("test_event", {"a": 2})
                entries = audit.tail(10)
                self.assertEqual(len(entries), 2)
                self.assertEqual(entries[0]["a"], 1)
                self.assertEqual(entries[1]["a"], 2)
            # patch exited: real path restored, and test events never reached it
            self.assertNotEqual(fake_log, audit._log_path())
            real = audit._log_path()
            if real.exists():
                self.assertNotIn("test_event", real.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


class DisplayHygieneTests(unittest.TestCase):
    """Raw-float normalisation for rendered prose (frozen JSON untouched)."""

    def test_round_raw_floats(self):
        from tracker.reporting import _round_raw_floats
        self.assertEqual(
            _round_raw_floats("price GBP 5.587000122070313 vs 125"),
            "price GBP 5.59 vs 125",
        )
        self.assertEqual(_round_raw_floats("vol 22.4589382904812%"), "vol 22.46%")
        # short decimals and dates pass through untouched
        self.assertEqual(_round_raw_floats("GBP 5.59 on 2026-09-26"), "GBP 5.59 on 2026-09-26")

    def test_publish_bundle_layout(self):
        """The Pages bundle has the dashboard at its root with links intact."""
        import json as _json
        import tempfile
        from pathlib import Path
        from unittest import mock

        import tracker.reporting as rep

        with tempfile.TemporaryDirectory() as tmp:
            dash = Path(tmp) / "dashboard"
            dash.mkdir()
            (dash / "index.html").write_text("<html>dash</html>", encoding="utf-8")
            pub = Path(tmp) / "publish"
            log = Path(tmp) / "audit_log.jsonl"
            log.write_text('{"ts":"t","event":"fetch_quotes","n":1}\n', encoding="utf-8")
            with mock.patch.object(rep, "DASH_FILE", dash / "index.html"), \
                 mock.patch.object(rep, "PUBLISH_DIR", pub), \
                 mock.patch.object(rep, "NOTES_HTML_DIR", Path(tmp) / "nope"), \
                 mock.patch.object(rep, "NOTES_DIR", Path(tmp) / "nope"), \
                 mock.patch.object(rep, "SNAPSHOTS_DIR", Path(tmp) / "nope"), \
                 mock.patch.object(rep.audit, "_log_path", return_value=log):
                rep.write_publish_bundle()
            self.assertTrue((pub / "index.html").is_file())
            self.assertTrue((pub / "audit.html").is_file())
            self.assertTrue((pub / "audit_log.jsonl").is_file())
            page = (pub / "audit.html").read_text(encoding="utf-8")
            self.assertIn("fetch_quotes", page)  # payload columns are populated


class UnitsTableTests(unittest.TestCase):
    """Market snapshot shows GBP and quoted pence side by side (no fake look)."""

    def test_qtable_shows_both_units(self):
        from tracker.reporting import _qtable
        html = _qtable([{
            "ticker": "AZN.L", "name": "AstraZeneca",
            "price": "125.52", "pence": "12,552.00p", "chg_html": "+1.2%",
        }])
        self.assertIn("QUOTED (GBp)", html)
        self.assertIn("12,552.00p", html)
        self.assertIn("125.52", html)

    def test_qrows_pence_conversion_and_index(self):
        from tracker.reporting import _qrows
        rows = _qrows({"AZN.L": {"price_gbp": 125.52, "prev_close_gbp": 124.0},
                       "^FTSE": {"price_gbp": 10659.1, "prev_close_gbp": 10600.0}})
        by = {r["ticker"]: r for r in rows}
        self.assertEqual(by["AZN.L"]["pence"], "12,552.00p")  # same format as Yahoo
        self.assertEqual(by["^FTSE"]["pence"], "")  # index points, not pence


class ScenarioTests(unittest.TestCase):
    """Reader scenarios re-derive the published valuation; 0.0pp is the anchor."""

    def _note(self):
        return {
            "ticker": "TEST.L", "price_target_gbp": 20.47,
            "target_weights": {"dcf": 0.6, "ddm": 0.2, "comps_pe": 0.2},
            "market_context": {"price_gbp_at_publication": 18.0},
            "valuation_inputs": {
                "dcf": {"base_fcf_m": 100.0, "fcf_growth_path": [0.05] * 5,
                        "terminal_growth": 0.02, "wacc": 0.08,
                        "net_debt_m": 50.0, "shares_m": 100.0,
                        "result": {"value_per_share": 18.87}},
                "ddm": {"dps_ttm_gbp": 1.0, "g": 0.03, "ke": 0.07,
                        "value_per_share": 25.75},
                "comps": {"implied_price_pe": 20.0,
                          "implied_price_ev_ebitda": None},
            },
        }

    def test_anchor_is_published_target(self):
        from tracker.scenario import scenario_grid
        grid = scenario_grid(self._note())
        anchor = next(r for r in grid if r["shock"] == 0.0)
        self.assertEqual(anchor["target"], 20.47)
        self.assertTrue(anchor["published"])

    def test_higher_rate_lowers_value_and_stays_continuous(self):
        from tracker.scenario import scenario_grid
        grid = scenario_grid(self._note())
        by = {r["shock"]: r["target"] for r in grid}
        pub = 20.47
        self.assertLess(by[0.005], pub)
        self.assertGreater(by[-0.005], pub)
        self.assertLess(by[0.01], by[0.005])          # monotone in the shock
        # A 5y Gordon DCF carries most PV in the terminal period, so ±0.5pp
        # legitimately moves the value ~5-8% (production notes: ~7%). Bound
        # only against explosion, not against the true sensitivity.
        self.assertLess(abs(by[0.005] - pub), pub * 0.12)

    def test_comps_only_note_is_rate_flat(self):
        from tracker.scenario import scenario_grid
        n = self._note()
        n["target_weights"] = {"comps_pe": 1.0}
        n["price_target_gbp"] = 20.0
        grid = scenario_grid(n)
        self.assertEqual({r["target"] for r in grid}, {20.0})

    def test_ddm_leg_drops_when_ke_gtr_g_fails(self):
        from tracker.scenario import scenario_grid
        n = self._note()
        n["valuation_inputs"]["ddm"]["g"] = 0.12   # ke 0.07 can't clear g
        n["valuation_inputs"]["ddm"]["value_per_share"] = None
        grid = scenario_grid(n)
        shocked = next(r for r in grid if r["shock"] == 0.005)
        self.assertNotIn("ddm", shocked["legs"])

    def test_diff_quotes_real_deltas_only(self):
        from tracker.scenario import diff_quotes
        prev = {"AZN.L": {"price_gbp": 100.0}, "^FTSE": {"price_gbp": 10000.0}}
        new = {"AZN.L": {"price_gbp": 101.5}, "^FTSE": {"price_gbp": 10500.0}}
        out = diff_quotes(prev, new)
        self.assertIn("AZN.L +1.50% since last refresh", out["movers"])
        self.assertFalse(out["big_move"])
        big = diff_quotes(prev, {"AZN.L": {"price_gbp": 102.5}})
        self.assertTrue(big["big_move"])
        self.assertIsNone(diff_quotes(None, new))


class BetaRegressionTests(unittest.TestCase):
    """Per-name OLS beta replaces the collapsed peer-median fallback."""

    def test_honest_failure_on_empty_history(self):
        import tempfile
        from unittest import mock

        from tracker import data as tracker_data

        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(tracker_data, "fetch_history",
                                   return_value=pd.DataFrame()):
                beta, prov = tracker_data.regression_beta("TEST.L")
        self.assertIsNone(beta)
        self.assertIn("empty", prov["derivation"])


class DayChangeTests(unittest.TestCase):
    """Day column = last close vs prev close — the number Yahoo shows."""

    def test_qrows_day_change_sign(self):
        from tracker.reporting import _qrows
        rows = _qrows({"AZN.L": {"price_gbp": 125.52, "prev_close_gbp": 124.0}})
        self.assertIn("+1.23%", rows[0]["chg_html"])

    def test_perf_rows_include_day_column(self):
        from tracker.reporting import _perf_rows_html
        perf = [{"ticker": "AZN.L", "thesis_date": "2026-09-21",
                 "base_price": 125.0, "last_price": 125.52,
                 "return_pct": -0.06, "alpha_pct": 0.34,
                 "ann_vol_pct": None, "max_drawdown_pct": None, "rec": "HOLD"}]
        quotes = {"AZN.L": {"price_gbp": 125.52, "prev_close_gbp": 124.0}}
        html = _perf_rows_html(perf, {"AZN.L": []}, quotes)
        self.assertIn("+1.23%", html)          # day change, Yahoo-equivalent
        self.assertIn("-0.06%", html)          # since-thesis return still present

    def test_empty_track_record_colspan(self):
        from tracker.reporting import _perf_rows_html
        html = _perf_rows_html([], {})
        self.assertIn('colspan="10"', html)


class LiveUpdateTests(unittest.TestCase):
    """Dashboard carries the update toast, interval selector, and meta polling."""

    def _render(self, tmp):
        import tempfile
        from pathlib import Path
        from unittest import mock

        import tracker.reporting as rep

        dash = Path(tmp) / "index.html"
        with mock.patch.object(rep, "DASH_FILE", dash):
            rep.write_dashboard(
                quotes=None, curve=[], perf_rows=[], summary={},
                refresh_ts="2026-09-27T10:00:00+00:00",
            )
        return dash.read_text(encoding="utf-8")

    def test_dashboard_has_live_update_ui(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            doc = self._render(tmp)
            self.assertIn("refresh_meta.json", doc)      # polled every 60s
            self.assertIn("update-toast", doc)           # "Prices updated" toast
            self.assertIn("live-interval", doc)          # auto-reload selector
            self.assertIn("setInterval(pollRefresh, 60000)", doc)

    def test_dashboard_labels_return_columns_as_since_thesis(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            doc = self._render(tmp)
            self.assertIn("Return since thesis", doc)
            self.assertIn("Alpha since thesis", doc)
            self.assertIn("<th>Day</th>", doc)

    def test_refresh_once_writes_meta(self):
        """refresh_once drops refresh_meta.json into the publish bundle."""
        import json as _json
        import tempfile
        from pathlib import Path
        from unittest import mock

        from tracker import refresh as ref

        with tempfile.TemporaryDirectory() as tmp:
            meta_file = Path(tmp) / "refresh_meta.json"
            dash_kwargs = {}
            with mock.patch.object(ref, "REFRESH_META", meta_file), \
                 mock.patch.object(ref.data, "fetch_quotes", return_value={}), \
                 mock.patch.object(ref.data, "fetch_history", return_value={}), \
                 mock.patch.object(ref.data, "save_snapshot"), \
                 mock.patch.object(ref.performance, "portfolio_curve", return_value=[]), \
                 mock.patch.object(ref.reporting, "write_all_note_pages"), \
                 mock.patch.object(ref.reporting, "write_dashboard",
                                   side_effect=lambda **kw: dash_kwargs.update(kw)), \
                 mock.patch.object(ref.reporting, "write_publish_bundle"), \
                 mock.patch.object(ref.audit, "record"), \
                 mock.patch.object(ref.research, "list_notes", return_value=[]):
                ref.refresh_once("test")
            meta = _json.loads(meta_file.read_text(encoding="utf-8"))
            self.assertEqual(meta["reason"], "test")
            self.assertIn("refreshed_at", meta)
            self.assertIn("market_open", meta)

    def test_dashboard_and_meta_share_one_timestamp(self):
        """Client compares page ts vs meta ts — they must be identical.

        Regression: they were captured microseconds apart, so every page
        load falsely believed newer data existed and the toast nagged.
        """
        import json as _json
        import tempfile
        from pathlib import Path
        from unittest import mock

        from tracker import refresh as ref

        with tempfile.TemporaryDirectory() as tmp:
            meta_file = Path(tmp) / "refresh_meta.json"
            dash_kwargs = {}
            with mock.patch.object(ref, "REFRESH_META", meta_file), \
                 mock.patch.object(ref.data, "fetch_quotes", return_value={}), \
                 mock.patch.object(ref.data, "fetch_history", return_value={}), \
                 mock.patch.object(ref.data, "save_snapshot"), \
                 mock.patch.object(ref.performance, "portfolio_curve", return_value=[]), \
                 mock.patch.object(ref.reporting, "write_all_note_pages"), \
                 mock.patch.object(ref.reporting, "write_dashboard",
                                   side_effect=lambda **kw: dash_kwargs.update(kw)), \
                 mock.patch.object(ref.reporting, "write_publish_bundle"), \
                 mock.patch.object(ref.audit, "record"), \
                 mock.patch.object(ref.research, "list_notes", return_value=[]):
                ref.refresh_once("test")
            meta = _json.loads(meta_file.read_text(encoding="utf-8"))
            self.assertEqual(dash_kwargs.get("refresh_ts"), meta["refreshed_at"])

    def test_toast_click_busts_pages_cache(self):
        """View-now must bypass GitHub Pages' 10-minute HTML cache."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            doc = self._render(tmp)
            self.assertIn("location.pathname + '?t=' + Date.now()", doc)

    def test_toast_compares_minutes_not_seconds(self):
        """Minute-precision compare: Pages HTML can lag meta by seconds."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            doc = self._render(tmp)
            self.assertIn("function sameTs", doc)
            self.assertIn(".slice(0, 16) ===", doc)

class GuardrailTests(unittest.TestCase):
    """±30% model-outlier guardrail with leg attribution."""

    def test_outlier_flags_and_names_driver(self):
        from tracker.valuation import outlier_check
        g = outlier_check(
            target=60.0, price=100.0,
            legs={"dcf": 40.0, "ddm": 90.0, "comps_pe": 105.0},
            weights={"dcf": 0.5, "ddm": 0.3, "comps_pe": 0.2},
        )
        self.assertTrue(g["is_outlier"])
        self.assertAlmostEqual(g["deviation_pct"], -40.0, places=6)
        # contributions: dcf 0.5*-0.60=-0.30; ddm 0.3*-0.10=-0.03; pe 0.2*+0.05=+0.01
        self.assertEqual(g["driver_leg"], "dcf")
        self.assertAlmostEqual(g["driver_contribution_pct"], -30.0, places=6)

    def test_within_band_not_flagged(self):
        from tracker.valuation import outlier_check
        g = outlier_check(110.0, 100.0, {"dcf": 120.0}, {"dcf": 1.0})
        self.assertFalse(g["is_outlier"])

    def test_no_target_no_flag(self):
        from tracker.valuation import outlier_check
        self.assertFalse(outlier_check(None, 100.0, {}, {})["is_outlier"])
        self.assertFalse(outlier_check(90.0, None, {}, {})["is_outlier"])


class ReverseDCFTests(unittest.TestCase):
    """Reverse DCF recovers the growth the market price implies."""

    def test_recovers_known_growth(self):
        from tracker.valuation import reverse_dcf_growth
        base, wacc, nd, sh, g = 100.0, 0.08, 0.0, 100.0, 0.04
        # value at g using the same machinery as the DCF (perpetual g)
        fcf, pv = base, 0.0
        for i in range(5):
            fcf *= (1 + g)
            pv += fcf / (1 + wacc) ** (i + 1)
        tv = fcf * (1 + g) / (wacc - g) / (1 + wacc) ** 5
        price = (pv + tv - nd) / sh
        r = reverse_dcf_growth(base, wacc, nd, sh, price)
        self.assertIsNotNone(r["g_implied"])
        self.assertAlmostEqual(r["g_implied"], g, places=3)

    def test_missing_inputs_returns_none(self):
        from tracker.valuation import reverse_dcf_growth
        r = reverse_dcf_growth(None, 0.08, 0.0, 100.0, 50.0)
        self.assertIsNone(r["g_implied"])

    def test_growth_at_wacc_bounded(self):
        from tracker.valuation import reverse_dcf_growth
        r = reverse_dcf_growth(100.0, 0.08, 0.0, 100.0, 1e9)
        # absurd price: implied perpetual growth reaches the discount rate
        self.assertIsNone(r["g_implied"])
        self.assertIsNotNone(r.get("g_bound"))


class SensitivityGridTests(unittest.TestCase):
    """5x5 WACC x terminal-growth DCF grid from frozen inputs."""

    def _note(self):
        return {"valuation_inputs": {"dcf": {
            "base_fcf_m": 100.0, "fcf_growth_path": [0.05] * 5,
            "terminal_growth": 0.02, "wacc": 0.08,
            "net_debt_m": 50.0, "shares_m": 100.0,
            "result": {"value_per_share": None}}}}

    def test_shape_and_centre_cell(self):
        from tracker.scenario import sensitivity_grid
        from tracker.valuation import DCFInputs, run_dcf
        grid = sensitivity_grid(self._note())
        self.assertEqual(len(grid["rows"]), 5)
        self.assertTrue(all(len(r["cells"]) == 5 for r in grid["rows"]))
        centre = grid["rows"][2]["cells"][2]
        ref = run_dcf(DCFInputs(
            ticker="T", base_fcf_m=100.0, fcf_growth=[0.05] * 5,
            terminal_growth=0.02, wacc=0.08, net_debt_m=50.0, shares_m=100.0,
        ))
        self.assertAlmostEqual(centre, round(ref.value_per_share, 2), places=2)

    def test_higher_wacc_lower_value(self):
        from tracker.scenario import sensitivity_grid
        grid = sensitivity_grid(self._note())
        r0 = [c for c in grid["rows"][0]["cells"] if c is not None]
        r4 = [c for c in grid["rows"][4]["cells"] if c is not None]
        self.assertGreater(sum(r0) / len(r0), sum(r4) / len(r4))


class BullBaseBearTests(unittest.TestCase):
    """Bull/base/bear: base = published anchor, monotone across cases."""

    def _note(self):
        return {
            "ticker": "TEST.L", "price_target_gbp": 20.47,
            "target_weights": {"dcf": 0.6, "ddm": 0.2, "comps_pe": 0.2},
            "market_context": {"price_gbp_at_publication": 18.0},
            "valuation_inputs": {
                "dcf": {"base_fcf_m": 100.0, "fcf_growth_path": [0.05] * 5,
                        "terminal_growth": 0.02, "wacc": 0.08,
                        "net_debt_m": 50.0, "shares_m": 100.0,
                        "result": {"value_per_share": 18.87}},
                "ddm": {"dps_ttm_gbp": 1.0, "g": 0.03, "ke": 0.07,
                        "value_per_share": 25.75},
                "comps": {"implied_price_pe": 20.0,
                          "implied_price_ev_ebitda": None},
            },
        }

    def test_cases_ordered_with_assumptions(self):
        from tracker.scenario import bull_base_bear
        cases = {c["case"]: c for c in bull_base_bear(self._note())}
        self.assertEqual(cases["Base"]["price"], 20.47)  # published verbatim
        self.assertGreater(cases["Bull"]["price"], cases["Base"]["price"])
        self.assertLess(cases["Bear"]["price"], cases["Base"]["price"])
        for c in cases.values():
            self.assertIn("assumption", c)


class PortfolioMetricsTests(unittest.TestCase):
    """Series-level risk metrics on the portfolio return series."""

    def _curve(self, n=40, drift=0.002, bench_drift=0.0):
        out = []
        p, b = 100.0, 5000.0
        for i in range(n):
            out.append({"date": f"2026-01-{(i % 28) + 1:02d}",
                        "portfolio": round(p, 4), "benchmark": round(b, 2)})
            # alternate the drift so daily returns have non-zero dispersion
            p *= (1 + drift) * (1.001 if i % 2 else 0.999)
            b *= (1 + bench_drift)
        return out

    def test_basic_metrics(self):
        from tracker.performance import portfolio_metrics
        m = portfolio_metrics(self._curve(), rf=0.037)
        expected = 1.0
        for i in range(39):
            expected *= 1.002 * (1.001 if i % 2 else 0.999)
        self.assertAlmostEqual(m["total_return_pct"],
                               (expected - 1) * 100, places=1)
        self.assertGreater(m["ann_vol_pct"], 0)
        self.assertEqual(m["max_drawdown_pct"], 0.0)   # monotone up
        self.assertIsNone(m["beta_vs_bench"])          # flat bench -> var 0
        self.assertGreater(m["tracking_error_pct"], 0)
        self.assertIsNotNone(m["sharpe"])

    def test_beta_with_varying_bench(self):
        from tracker.performance import portfolio_metrics
        m = portfolio_metrics(self._curve(bench_drift=0.001), rf=0.037)
        self.assertIsNotNone(m["beta_vs_bench"])
        self.assertGreater(m["beta_vs_bench"], 0)

    def test_short_curve_empty(self):
        from tracker.performance import portfolio_metrics
        self.assertEqual(portfolio_metrics([], rf=None), {})
        self.assertEqual(portfolio_metrics([{"date": "d", "portfolio": 1,
                                             "benchmark": 1}], rf=None), {})

    def test_inception_cost_applied(self):
        from tracker.portfolio import apply_inception_cost, TOTAL_BUY_COST_RATE
        curve = [{"date": "d", "portfolio": 100.0, "benchmark": 5000.0}]
        out = apply_inception_cost(curve)
        self.assertAlmostEqual(out[0]["portfolio"],
                               100.0 * (1 - TOTAL_BUY_COST_RATE), places=6)
        self.assertEqual(out[0]["benchmark"], 5000.0)  # bench untouched


class WeightsTableTests(unittest.TestCase):
    """£100k weights table: weights sum, positions, disclosed costs."""

    def test_table_rows_and_costs(self):
        from tracker.portfolio import (build_weights_table, NOTIONAL_GBP,
                                       TOTAL_BUY_COST_RATE, SECTOR_MAP)
        wt = build_weights_table({"AZN.L": {"price_gbp": 118.7}})
        rows = wt["rows"]
        self.assertEqual(len(rows), 8)
        self.assertAlmostEqual(sum(r["weight_pct"] for r in rows), 100.0,
                               places=6)
        for r in rows:
            self.assertAlmostEqual(
                r["position_gbp"],
                round(r["weight_pct"] / 100 * NOTIONAL_GBP, 2), places=2)
            self.assertAlmostEqual(
                r["buy_cost_gbp"],
                round(r["position_gbp"] * TOTAL_BUY_COST_RATE, 2), places=2)
            self.assertEqual(r["sector"], SECTOR_MAP[r["ticker"]])
        azn = next(r for r in rows if r["ticker"] == "AZN.L")
        self.assertEqual(azn["approx_shares"],
                         int(0.20 * NOTIONAL_GBP / 118.7))


class TrackingStartTests(unittest.TestCase):
    """Live record starts at FIRST publication, not the latest revision."""

    def _hist(self, days):
        return pd.DataFrame([
            {"Ticker": "TEST.L", "Date": d, "Close_gbp": 100.0 + 10 * i,
             "Volume": 1} for i, d in enumerate(days)
        ])

    def test_first_published_at_wins(self):
        first = datetime(2025, 6, 2)
        revision = datetime(2025, 8, 1)
        days = [first + timedelta(days=7 * i) for i in range(9)]
        hist = self._hist(days)
        bench = pd.DataFrame([
            {"Ticker": "^FTSE", "Date": d, "Close_gbp": 100.0, "Volume": 1}
            for d in days
        ])
        note = {"ticker": "TEST.L",
                "first_published_at": first.isoformat(),
                "published_at": revision.isoformat(),
                "price_target_gbp": 110.0, "recommendation": "BUY"}
        res = performance.note_performance(note, hist, bench)
        self.assertEqual(res["thesis_date"], str(days[0].date()))
        self.assertEqual(res["end_date"], str(days[-1].date()))
        self.assertEqual(res["base_price"], 100.0)

    def test_summarize_window_bounds(self):
        rows = [
            {"ticker": "A", "alpha_pct": 1.0, "return_pct": 2.0, "rec": "BUY",
             "pt": None, "last_price": 1.0, "ann_vol_pct": None,
             "max_drawdown_pct": None, "trading_days": 5,
             "thesis_date": "2026-09-21", "end_date": "2026-10-02"},
            {"ticker": "B", "alpha_pct": -1.0, "return_pct": -2.0,
             "rec": "SELL", "pt": None, "last_price": 1.0,
             "ann_vol_pct": None, "max_drawdown_pct": None, "trading_days": 3,
             "thesis_date": "2026-09-19", "end_date": "2026-09-30"},
        ]
        s = performance.summarize(rows)
        self.assertEqual(s["window_start"], "2026-09-19")
        self.assertEqual(s["window_end"], "2026-10-02")
        self.assertEqual(s["total_trading_days"], 8)


class PublishPreservationTests(unittest.TestCase):
    """Republishing inherits the first-publication anchor and addenda."""

    def test_publish_keeps_first_publication_and_addenda(self):
        import json as _json
        import tempfile
        from pathlib import Path as _Path
        from unittest import mock as _mock

        from tracker import research

        with tempfile.TemporaryDirectory() as td:
            notes_dir = _Path(td) / "notes"
            notes_dir.mkdir()
            prior = {
                "schema": "uk-equity-note/2", "ticker": "TEST.L",
                "name": "Test", "status": "published",
                "created_at": "2026-09-19T08:00:00+00:00",
                "published_at": "2026-09-19T08:00:00+00:00",
                "first_published_at": "2026-09-19T08:00:00+00:00",
                "headline": "h",
                "thesis": {"summary": "s", "catalysts": [], "risks": [],
                           "wrong_if": []},
                "recommendation": "HOLD", "price_target_gbp": 10.0,
                "target_weights": {}, "upside_pct": 0.0,
                "valuation_inputs": {
                    "is_bank": False, "beta_raw": None, "beta_adjusted": None,
                    "dcf": {"base_fcf_m": None, "base_fcf_used_m": None,
                            "base_fcf_source": "", "fcf_growth_path": [],
                            "terminal_growth": None, "wacc": None,
                            "wacc_source": "", "net_debt_m": None,
                            "shares_m": None, "result": {}, "derivation": []},
                    "ddm": {"value_per_share": None, "derivation": []},
                    "comps": {"implied_price_pe": None,
                              "implied_price_ev_ebitda": None,
                              "derivation": []}},
                "market_context": {"price_gbp_at_publication": 9.5},
                "next_events": None, "esg": None,
                "provenance": {}, "audit_refs": [], "benchmark": "^FTSE",
                "review_period_months": 3, "review_due_at": None,
                "addenda": [{"kind": "learning", "ts": "2026-09-20",
                             "text": "prior note"}],
                "publication_audit_id": "x",
            }
            (notes_dir / "test-l.json").write_text(
                _json.dumps(prior), encoding="utf-8")

            draft = dict(prior)
            draft["status"] = "draft"
            draft["addenda"] = []
            draft["recommendation"] = "BUY"
            fake_log = _Path(td) / "audit_log.jsonl"
            with _mock.patch.object(research.config, "NOTES_DIR",
                                    str(notes_dir)), \
                 _mock.patch.object(research.audit, "_log_path",
                                    return_value=fake_log), \
                 _mock.patch.object(research.data, "fetch_quotes",
                                    return_value={"TEST.L":
                                                  {"price_gbp": 9.5}}), \
                 _mock.patch.object(research, "_fetch_next_events",
                                    return_value=None), \
                 _mock.patch.object(research, "_fetch_esg",
                                    return_value=None):
                pub = research.publish(
                    draft, headline="h2", summary="s2",
                    catalysts=[], risks=[], correction="correction text",
                    wrong_if=["w1"],
                )
            self.assertEqual(pub["first_published_at"],
                             "2026-09-19T08:00:00+00:00")
            texts = [a["text"] for a in pub["addenda"]]
            self.assertTrue(any(t == "prior note" for t in texts))
            self.assertTrue(any(t == "correction text" for t in texts))
            self.assertEqual(pub["thesis"]["wrong_if"], ["w1"])
            self.assertNotEqual(pub["published_at"],
                                "2026-09-19T08:00:00+00:00")
