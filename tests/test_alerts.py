"""Shared alert convention tests: the-commons."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from alerts import make_alert
from grid import Grid
from spectrum import Spectrum

class TestAlerts(unittest.TestCase):

    def assert_shape(self, a, core):
        self.assertEqual(set(a), {"alert_id","source_core","kind","subject_id","severity","detail","action","status","recorded_at"})
        self.assertEqual(a["source_core"], core)
        self.assertEqual(a["action"], "record-not-operate")
        self.assertEqual(a["status"], "flagged")
        self.assertTrue(a["alert_id"].startswith("ALRT-"))

    def test_make_alert_shape(self):
        a = make_alert("the-commons", "k", "S-1", "high", "d", recorded_at="2026-01-01T00:00:00+00:00")
        self.assert_shape(a, "the-commons")
    def test_grid_shortfall_alerts_and_ok_grid_does_not(self):
        g = Grid(tempfile.mkdtemp())
        g.add_generator("G1", "solar", 100)
        g.record_load(50)
        self.assertEqual(g.alerts(), [])
        g.record_load(150)
        alerts = g.alerts()
        self.assertEqual(len(alerts), 1)
        self.assert_shape(alerts[0], "the-commons")
        self.assertEqual(alerts[0]["severity"], "critical")
    def test_spectrum_overlap_alerts(self):
        sp = Spectrum(tempfile.mkdtemp())
        sp.allocate("700MHz", "Alice", "public safety", "north")
        sp.allocate("700MHz", "Bob", "commercial", "north")
        alerts = sp.alerts()
        self.assertEqual(len(alerts), 1)
        self.assert_shape(alerts[0], "the-commons")
if __name__ == "__main__": unittest.main()
