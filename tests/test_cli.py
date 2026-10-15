"""CLI smoke tests for the-commons. No network access."""

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import commons_cli


def run_cli(tmpdir, *args):
    buf = io.StringIO()
    full = ["--data-dir", tmpdir] + list(args)
    with redirect_stdout(buf):
        commons_cli.main(full)
    return buf.getvalue()


class TestCommonsCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_post_flow(self):
        d = self.tmp.name
        out = run_cli(d, "post", "register", "--id", "A-1",
                      "--locality", "Springfield", "--type", "residential")
        self.assertIn("registered address A-1", out)
        run_cli(d, "post", "register", "--id", "B-1",
                "--locality", "Shelbyville", "--type", "business")
        out = run_cli(d, "post", "build-routes")
        self.assertIn("route R-springfield", out)
        out = run_cli(d, "post", "coverage")
        self.assertIn("100.0%", out)

    def test_post_bad_type_rejected_by_parser(self):
        with self.assertRaises(SystemExit):
            run_cli(self.tmp.name, "post", "register", "--id", "A-1",
                    "--locality", "X", "--type", "igloo")

    def test_grid_flow(self):
        d = self.tmp.name
        out = run_cli(d, "grid", "add-gen", "--name", "Sunfield",
                      "--fuel", "solar", "--capacity", "100")
        self.assertIn("Sunfield", out)
        run_cli(d, "grid", "load", "--demand", "95")
        out = run_cli(d, "grid", "readout")
        self.assertIn("AT RISK", out)
        run_cli(d, "grid", "load", "--demand", "120")
        out = run_cli(d, "grid", "readout")
        self.assertIn("SHORTFALL", out)

    def test_spectrum_flow(self):
        d = self.tmp.name
        run_cli(d, "spectrum", "allocate", "--band", "700 MHz",
                "--licensee", "Carrier One", "--purpose", "mobile",
                "--region", "North")
        run_cli(d, "spectrum", "allocate", "--band", "700 MHz",
                "--licensee", "Carrier Two", "--purpose", "mobile",
                "--region", "North")
        out = run_cli(d, "spectrum", "overlaps")
        self.assertIn("OVERLAP", out)
        out = run_cli(d, "spectrum", "allocations")
        self.assertIn("Carrier One", out)


if __name__ == "__main__":
    unittest.main()
