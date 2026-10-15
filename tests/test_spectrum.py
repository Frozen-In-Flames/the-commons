"""Tests for the-commons Spectrum class. No network access."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spectrum import Spectrum, SOURCE_LABEL


class TestSpectrum(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Spectrum(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_allocate_and_list(self):
        a = self.spec.allocate("700 MHz", "Carrier One", "mobile", "North")
        self.assertTrue(a["id"].startswith("A-"))
        self.spec.allocate("3.5 GHz", "Carrier Two", "fixed", "South")
        self.assertEqual(len(self.spec.allocations()), 2)
        self.assertEqual(len(self.spec.allocations("North")), 1)

    def test_allocate_rejects_empty_fields(self):
        with self.assertRaises(ValueError):
            self.spec.allocate("", "Carrier One", "mobile", "North")
        with self.assertRaises(ValueError):
            self.spec.allocate("700 MHz", "  ", "mobile", "North")

    def test_overlap_detected(self):
        self.spec.allocate("700 MHz", "Carrier One", "mobile", "North")
        self.spec.allocate("700 MHz", "Carrier Two", "mobile", "North")
        hits = self.spec.overlaps()
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["band"], "700 MHz")
        self.assertEqual(sorted(hits[0]["licensees"]),
                         ["Carrier One", "Carrier Two"])

    def test_no_overlap_different_band(self):
        self.spec.allocate("700 MHz", "Carrier One", "mobile", "North")
        self.spec.allocate("3.5 GHz", "Carrier Two", "mobile", "North")
        self.assertEqual(self.spec.overlaps(), [])

    def test_no_overlap_different_region(self):
        self.spec.allocate("700 MHz", "Carrier One", "mobile", "North")
        self.spec.allocate("700 MHz", "Carrier Two", "mobile", "South")
        self.assertEqual(self.spec.overlaps(), [])

    def test_no_overlap_same_licensee(self):
        self.spec.allocate("700 MHz", "Carrier One", "mobile", "North")
        self.spec.allocate("700 MHz", "Carrier One", "broadcast", "North")
        self.assertEqual(self.spec.overlaps(), [])

    def test_overlap_case_insensitive(self):
        self.spec.allocate("700 MHz", "Carrier One", "mobile", "north")
        self.spec.allocate("700 MHZ", "Carrier Two", "mobile", "North")
        self.assertEqual(len(self.spec.overlaps()), 1)

    def test_revoke_clears_overlap(self):
        a1 = self.spec.allocate("700 MHz", "Carrier One", "mobile", "North")
        self.spec.allocate("700 MHz", "Carrier Two", "mobile", "North")
        self.assertEqual(len(self.spec.overlaps()), 1)
        self.assertTrue(self.spec.revoke(a1["id"]))
        self.assertEqual(self.spec.overlaps(), [])
        self.assertFalse(self.spec.revoke("A-999"))

    def test_source_label_persisted(self):
        self.spec.allocate("700 MHz", "Carrier One", "mobile", "North")
        import json
        with open(os.path.join(self.tmp.name, "allocations.json")) as f:
            doc = json.load(f)
        self.assertEqual(doc["source"], SOURCE_LABEL)


if __name__ == "__main__":
    unittest.main()
