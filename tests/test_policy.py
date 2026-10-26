"""Policy loader + evaluator (ticket 06): first-match, wildcards, deny-by-default."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from miniqubes.policy import Policy, PolicyError, Rule


class DecideTest(unittest.TestCase):
    def test_empty_policy_denies_everything(self):
        p = Policy([])
        self.assertFalse(p.decide("host", "ping", "vault"))
        self.assertFalse(p.decide("work", "filecopy", "vault"))

    def test_first_match_wins(self):
        p = Policy([
            Rule("work", "filecopy", "vault", allow=False),
            Rule("*", "filecopy", "*", allow=True),
        ])
        self.assertFalse(p.decide("work", "filecopy", "vault"))  # explicit deny first
        self.assertTrue(p.decide("personal", "filecopy", "vault"))

    def test_wildcards_per_field(self):
        p = Policy([Rule("host", "*", "*", allow=True)])
        self.assertTrue(p.decide("host", "anything", "vault"))
        self.assertFalse(p.decide("work", "anything", "vault"))


class LoadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_file_uses_bootstrap_defaults(self):
        p = Policy.load(self.dir / "absent.json")
        self.assertTrue(p.decide("host", "ping", "vault"))
        self.assertTrue(p.decide("host", "info", "vault"))
        self.assertFalse(p.decide("host", "filecopy", "vault"))
        self.assertFalse(p.decide("work", "filecopy", "vault"))
        self.assertFalse(p.decide("work", "ping", "vault"))

    def test_present_file_is_authoritative(self):
        f = self.dir / "policy.json"
        f.write_text(json.dumps([
            {"src": "work", "service": "filecopy", "dst": "vault", "allow": True}]))
        p = Policy.load(f)
        self.assertTrue(p.decide("work", "filecopy", "vault"))
        self.assertFalse(p.decide("host", "ping", "vault"))  # defaults replaced, not merged

    def test_env_override(self):
        f = self.dir / "p.json"
        f.write_text("[]")
        with mock.patch.dict(os.environ, {"MINIQUIBES_POLICY": str(f)}):
            p = Policy.load()
        self.assertFalse(p.decide("host", "ping", "vault"))

    def test_malformed_files_rejected(self):
        cases = {
            "notalist.json": "{}",
            "missingfield.json": json.dumps([{"src": "a", "service": "s", "allow": True}]),
            "badallow.json": json.dumps(
                [{"src": "a", "service": "s", "dst": "b", "allow": "yes"}]),
            "notjson.json": "{oops",
        }
        for name, content in cases.items():
            f = self.dir / name
            f.write_text(content)
            with self.assertRaises(PolicyError, msg=name):
                Policy.load(f)


if __name__ == "__main__":
    unittest.main()
