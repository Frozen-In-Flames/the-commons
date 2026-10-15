"""Tests for the-commons Post class. No network access."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from post import Post, SOURCE_LABEL


class TestPost(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.post = Post(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_register_and_list(self):
        self.post.register_address("A-1", "Springfield", "residential")
        self.post.register_address("A-2", "Springfield", "business")
        self.post.register_address("B-1", "Shelbyville", "po_box")
        self.assertEqual(len(self.post.addresses()), 3)
        self.assertEqual(len(self.post.addresses("Springfield")), 2)

    def test_register_rejects_bad_point_type(self):
        with self.assertRaises(ValueError):
            self.post.register_address("A-1", "Springfield", "igloo")

    def test_register_rejects_duplicate(self):
        self.post.register_address("A-1", "Springfield", "residential")
        with self.assertRaises(ValueError):
            self.post.register_address("A-1", "Shelbyville", "business")

    def test_build_routes_groups_by_locality(self):
        self.post.register_address("A-1", "Springfield", "residential")
        self.post.register_address("A-2", "Springfield", "business")
        self.post.register_address("B-1", "Shelbyville", "po_box")
        routes = self.post.build_routes()
        self.assertEqual(len(routes), 2)
        springfield = [r for r in routes if r["locality"] == "Springfield"][0]
        self.assertEqual(sorted(springfield["addresses"]), ["A-1", "A-2"])
        self.assertTrue(springfield["active"])

    def test_coverage_full_then_partial(self):
        self.post.register_address("A-1", "Springfield", "residential")
        self.post.register_address("B-1", "Shelbyville", "po_box")
        self.post.build_routes()
        c = self.post.coverage()
        self.assertEqual(c["total_addresses"], 2)
        self.assertEqual(c["routed_addresses"], 2)
        self.assertAlmostEqual(c["coverage"], 1.0)
        routes = self.post.routes()
        shelby = [r for r in routes if r["locality"] == "Shelbyville"][0]
        self.post.set_route_active(shelby["id"], False)
        c = self.post.coverage()
        self.assertAlmostEqual(c["coverage"], 0.5)

    def test_coverage_empty_registry(self):
        c = self.post.coverage()
        self.assertIsNone(c["coverage"])
        self.assertEqual(c["total_addresses"], 0)

    def test_deactivate_unknown_route(self):
        with self.assertRaises(ValueError):
            self.post.set_route_active("R-nowhere", False)

    def test_source_label_persisted(self):
        self.post.register_address("A-1", "Springfield", "residential")
        import json
        with open(os.path.join(self.tmp.name, "addresses.json")) as f:
            doc = json.load(f)
        self.assertEqual(doc["source"], SOURCE_LABEL)


if __name__ == "__main__":
    unittest.main()
