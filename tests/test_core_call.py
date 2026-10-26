"""Core.call through FakeBackend to a real loopback agent (ticket 03)."""
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from guest.agent import HANDLERS
from miniqubes import backends
from miniqubes.backends import FakeBackend
from miniqubes.channel import serve
from miniqubes.core import QubesCore, QubesError


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class CoreCallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old_base = backends.AGENT_BASE_PORT
        backends.AGENT_BASE_PORT = free_port()
        self.backend = FakeBackend(Path(self.tmp.name) / "fake.json")
        # Hermetic policy (ticket 06): nonexistent file → bootstrap defaults.
        self._env = mock.patch.dict(os.environ, {
            "MINIQUIBES_POLICY": str(Path(self.tmp.name) / "absent-policy.json")})
        self._env.start()
        self.core = QubesCore(self.backend)
        self.core.create_qube("personal")
        _, host, port = self.backend.agent_endpoint("personal")
        self.listener = socket.create_server((host, port))
        self.stop = threading.Event()
        self.thread = threading.Thread(
            target=serve, args=(self.listener, HANDLERS, self.stop.is_set), daemon=True)
        self.thread.start()

    def tearDown(self):
        self.stop.set()
        self.listener.close()
        self.thread.join(timeout=2)
        backends.AGENT_BASE_PORT = self._old_base
        self._env.stop()
        self.tmp.cleanup()

    def test_call_requires_running(self):
        with self.assertRaises(QubesError):
            self.core.call("personal", "ping")

    def test_call_ping_info(self):
        self.core.start_qube("personal")
        self.assertEqual(self.core.call("personal", "ping"), "pong")
        self.assertIn("hostname", self.core.call("personal", "info"))

    def test_unknown_service(self):
        self.core.start_qube("personal")
        with self.assertRaises(QubesError):
            self.core.call("personal", "bogus")

    def test_missing_qube(self):
        with self.assertRaises(QubesError):
            self.core.call("ghost", "ping")


class UnreachableTest(unittest.TestCase):
    def test_agent_not_listening(self):
        with tempfile.TemporaryDirectory() as d:
            old = backends.AGENT_BASE_PORT
            backends.AGENT_BASE_PORT = free_port()
            try:
                core = QubesCore(FakeBackend(Path(d) / "f.json"))
                core.create_qube("vault")
                core.start_qube("vault")
                with self.assertRaises(QubesError):
                    core.call("vault", "ping")
            finally:
                backends.AGENT_BASE_PORT = old


if __name__ == "__main__":
    unittest.main()
