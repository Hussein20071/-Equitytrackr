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
