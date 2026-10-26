"""Lifecycle rules, tested against FakeBackend on a temp state file."""
import tempfile
import unittest
from pathlib import Path

from miniqubes.backends import FakeBackend
from miniqubes.core import QubesCore, QubesError, RUNNING, STOPPED


class CoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "fake.json"
        self.core = QubesCore(FakeBackend(self.state))

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_list_sorted(self):
        self.core.create_qube("vault")
        self.core.create_qube("personal", template="fedora-40")
        names = [q.name for q in self.core.list_qubes()]
        self.assertEqual(names, ["personal", "vault"])
        self.assertEqual(self.core.get_qube("personal").template, "fedora-40")
        self.assertEqual(self.core.get_qube("vault").state, STOPPED)

    def test_duplicate_rejected(self):
        self.core.create_qube("personal")
        with self.assertRaises(QubesError):
            self.core.create_qube("personal")

    def test_invalid_names_rejected(self):
        for bad in ["", "a b", "-x", "a/b", "x" * 40, "qube!"]:
            with self.assertRaises(QubesError, msg=bad):
                self.core.create_qube(bad)

    def test_start_stop_transitions(self):
        self.core.create_qube("personal")
        self.assertEqual(self.core.start_qube("personal").state, RUNNING)
        with self.assertRaises(QubesError):
            self.core.start_qube("personal")  # already running
        self.assertEqual(self.core.stop_qube("personal").state, STOPPED)
        with self.assertRaises(QubesError):
            self.core.stop_qube("personal")  # already stopped

    def test_missing_qube(self):
        for op in [self.core.start_qube, self.core.stop_qube,
                   self.core.remove_qube, self.core.get_qube]:
            with self.assertRaises(QubesError):
                op("ghost")

    def test_remove_running_rejected_then_ok(self):
        self.core.create_qube("personal")
        self.core.start_qube("personal")
        with self.assertRaises(QubesError):
            self.core.remove_qube("personal")
        self.core.stop_qube("personal")
        self.core.remove_qube("personal")
        self.assertEqual(self.core.list_qubes(), [])

    def test_persistence_across_backend_instances(self):
        self.core.create_qube("personal")
        self.core.start_qube("personal")
        # A fresh backend on the same file sees the same world (separate CLI runs).
        core2 = QubesCore(FakeBackend(self.state))
        self.assertEqual(core2.get_qube("personal").state, RUNNING)


if __name__ == "__main__":
    unittest.main()
