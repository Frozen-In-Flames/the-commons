"""Tests for the-commons Grid class. No network access."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grid import Grid, SOURCE_LABEL


class TestGrid(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.grid = Grid(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_list_generators(self):
        self.grid.add_generator("Sunfield Solar", "solar", 120)
        self.grid.add_generator("Riverbend Hydro", "hydro", 300,
                                status="maintenance")
        self.assertEqual(len(self.grid.generators()), 2)
        self.assertEqual(len(self.grid.generators("online")), 1)

    def test_add_rejects_bad_fuel_and_status(self):
        with self.assertRaises(ValueError):
            self.grid.add_generator("X", "phlogiston", 10)
        with self.assertRaises(ValueError):
            self.grid.add_generator("X", "solar", 10, status="flying")

    def test_add_rejects_nonpositive_capacity(self):
        with self.assertRaises(ValueError):
            self.grid.add_generator("X", "solar", 0)

    def test_add_rejects_duplicate_name(self):
        self.grid.add_generator("Sunfield Solar", "solar", 120)
        with self.assertRaises(ValueError):
            self.grid.add_generator("Sunfield Solar", "wind", 50)

    def test_set_status(self):
        self.grid.add_generator("Sunfield Solar", "solar", 120)
        g = self.grid.set_generator_status("Sunfield Solar", "offline")
        self.assertEqual(g["status"], "offline")
        with self.assertRaises(ValueError):
            self.grid.set_generator_status("Nope", "online")

    def test_committed_capacity_counts_only_online(self):
        self.grid.add_generator("A", "solar", 100)
        self.grid.add_generator("B", "wind", 200, status="offline")
        self.assertAlmostEqual(self.grid.committed_capacity_mw(), 100.0)

    def test_record_load_rejects_negative(self):
        with self.assertRaises(ValueError):
            self.grid.record_load(-5)

    def test_readout_ok(self):
        self.grid.add_generator("A", "solar", 100)
        self.grid.record_load(50, timestamp="2026-10-15T12:00:00+00:00")
        r = self.grid.readout()
        self.assertEqual(r["status"], "OK")
        self.assertAlmostEqual(r["margin_mw"], 50.0)

    def test_readout_at_risk(self):
        self.grid.add_generator("A", "solar", 100)
        self.grid.record_load(92)
        self.assertEqual(self.grid.readout()["status"], "AT RISK")

    def test_readout_shortfall(self):
        self.grid.add_generator("A", "solar", 100)
        self.grid.record_load(110)
        r = self.grid.readout()
        self.assertEqual(r["status"], "SHORTFALL")
        self.assertAlmostEqual(r["margin_mw"], -10.0)

    def test_readout_no_data(self):
        self.grid.add_generator("A", "solar", 100)
        r = self.grid.readout()
        self.assertEqual(r["status"], "NO DATA")
        self.assertIsNone(r["demand_mw"])

    def test_source_label_persisted(self):
        self.grid.add_generator("A", "solar", 100)
        import json
        with open(os.path.join(self.tmp.name, "generators.json")) as f:
            doc = json.load(f)
        self.assertEqual(doc["source"], SOURCE_LABEL)


if __name__ == "__main__":
    unittest.main()
