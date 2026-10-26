"""CLI smoke test: the exact transcript ticket 01 promises."""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from miniqubes.cli import main


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(
            os.environ, {"MINIQUIBES_STATE": str(Path(self.tmp.name) / "s.json")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = main(list(argv))
        return rc, out.getvalue()

    def test_demo_transcript(self):
        rc, out = self.run_cli("create", "personal", "--template", "fedora-40")
        self.assertEqual(rc, 0)
        self.assertIn("created qube 'personal'", out)

        rc, _ = self.run_cli("create", "vault")
        self.assertEqual(rc, 0)

        rc, _ = self.run_cli("create", "vault")  # duplicate -> error path
        self.assertEqual(rc, 1)

        rc, _ = self.run_cli("start", "personal")
        self.assertEqual(rc, 0)

        rc, out = self.run_cli("list")
        self.assertEqual(rc, 0)
        self.assertIn("personal", out)
        self.assertIn("running", out)
        self.assertIn("vault", out)
        self.assertIn("stopped", out)

    def test_empty_list(self):
        rc, out = self.run_cli("list")
        self.assertEqual(rc, 0)
        self.assertIn("(no qubes)", out)


if __name__ == "__main__":
    unittest.main()
