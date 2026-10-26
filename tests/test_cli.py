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


class CliOpenTest(CliTest):
    """`mq open` (ticket 07): the SPICE window launcher."""

    def test_open_launches_remote_viewer_with_titled_window(self):
        self.run_cli("create", "personal", "--template", "fedora-40")
        self.run_cli("start", "personal")
        with mock.patch("miniqubes.cli.subprocess.run") as run:
            rc, _ = self.run_cli("open", "personal")
        self.assertEqual(rc, 0)
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], "remote-viewer")
        self.assertIn("--title=[personal]", argv)      # host-drawn trust anchor
        spice = next(a for a in argv if a.startswith("spice://"))
        self.assertGreaterEqual(int(spice.rsplit(":", 1)[1]), 5900)

    def test_open_stopped_qube_never_launches_anything(self):
        self.run_cli("create", "personal")
        with mock.patch("miniqubes.cli.subprocess.run") as run, \
                contextlib.redirect_stderr(io.StringIO()):
            rc, _ = self.run_cli("open", "personal")
        self.assertEqual(rc, 1)
        run.assert_not_called()

    def test_open_without_remote_viewer_is_a_clean_error(self):
        self.run_cli("create", "personal", "--template", "fedora-40")
        self.run_cli("start", "personal")

        def boom(argv, **kw):
            raise FileNotFoundError("remote-viewer")

        with mock.patch("miniqubes.cli.subprocess.run", boom), \
                contextlib.redirect_stderr(io.StringIO()):
            rc, _ = self.run_cli("open", "personal")
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
