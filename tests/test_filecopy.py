"""filecopy end-to-end over loopback: two agents, one policy (ticket 06).

Includes the hostile-sender cases from the RE (qfile-unpacker): path escapes,
oversize files, and a tampered transfer that must leave no partial file.
"""
import base64
import contextlib
import hashlib
import io
import json
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from guest.agent import make_filecopy_handlers
from miniqubes import backends
from miniqubes.backends import FakeBackend
from miniqubes.channel import FILECOPY_MAX, serve
from miniqubes.cli import main as cli_main
from miniqubes.core import QubesCore, QubesError
from miniqubes.policy import Policy, Rule


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_agent(handlers, endpoint):
    _, host, port = endpoint
    listener = socket.create_server((host, port))
    stop = threading.Event()
    thread = threading.Thread(
        target=serve, args=(listener, handlers, stop.is_set), daemon=True)
    thread.start()
    return listener, stop, thread


class FilecopyWorld(unittest.TestCase):
    """FakeBackend + two loopback agents with separate guest homes."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.src_home = root / "work-home"
        self.dst_home = root / "vault-home"
        self.src_home.mkdir()
        self.dst_home.mkdir()
        self._old_base = backends.AGENT_BASE_PORT
        backends.AGENT_BASE_PORT = free_port()
        self.backend = FakeBackend(root / "fake.json")
        self.agents = []

    def tearDown(self):
        for listener, stop, thread in self.agents:
            stop.set()
            listener.close()
            thread.join(timeout=2)
        backends.AGENT_BASE_PORT = self._old_base
        self.tmp.cleanup()

    def boot(self, policy, tamper=False):
        core = QubesCore(self.backend, policy=policy)
        core.create_qube("work")
        core.create_qube("vault")
        dst_handlers = make_filecopy_handlers(self.dst_home)
        if tamper:
            real_write = dst_handlers["filecopy.write"]

            def corrupt(args):
                if args.get("data_b64"):
                    raw = bytearray(base64.b64decode(args["data_b64"]))
                    raw[0] ^= 0xFF
                    args = dict(args, data_b64=base64.b64encode(bytes(raw)).decode())
                return real_write(args)

            dst_handlers["filecopy.write"] = corrupt
        self.agents = [
            start_agent(make_filecopy_handlers(self.src_home),
                        self.backend.agent_endpoint("work")),
            start_agent(dst_handlers, self.backend.agent_endpoint("vault")),
        ]
        core.start_qube("work")
        core.start_qube("vault")
        return core

    def incoming_files(self):
        base = self.dst_home / "QubesIncoming"
        return sorted(p for p in base.rglob("*") if p.is_file()) if base.exists() else []


class FilecopyTest(FilecopyWorld):
    ALLOW = Policy([Rule("work", "filecopy", "vault", allow=True)])

    def test_copy_allowed(self):
        core = self.boot(self.ALLOW)
        src = self.src_home / "notes.txt"
        payload = b"hello compartments\n" * 10
        src.write_bytes(payload)
        res = core.filecopy("work", str(src), "vault")
        self.assertEqual(res["name"], "notes.txt")
        self.assertEqual(res["size"], len(payload))
        self.assertEqual(res["sha256"], hashlib.sha256(payload).hexdigest())
        landed = self.dst_home / "QubesIncoming" / "work" / "notes.txt"
        self.assertEqual(landed.read_bytes(), payload)

    def test_copy_multi_chunk(self):
        core = self.boot(self.ALLOW)
        payload = os.urandom(600_000)  # > 2 chunks of 256 KiB
        src = self.src_home / "blob.bin"
        src.write_bytes(payload)
        core.filecopy("work", str(src), "vault")
        landed = self.dst_home / "QubesIncoming" / "work" / "blob.bin"
        self.assertEqual(hashlib.sha256(landed.read_bytes()).hexdigest(),
                         hashlib.sha256(payload).hexdigest())

    def test_copy_denied_without_rule(self):
        core = self.boot(Policy([]))
        src = self.src_home / "notes.txt"
        src.write_bytes(b"secret")
        with self.assertRaises(QubesError):
            core.filecopy("work", str(src), "vault")
        self.assertEqual(self.incoming_files(), [])

    def test_tampered_transfer_leaves_no_partial_file(self):
        core = self.boot(self.ALLOW, tamper=True)
        src = self.src_home / "data.bin"
        src.write_bytes(b"x" * 1000)
        with self.assertRaises(QubesError):
            core.filecopy("work", str(src), "vault")
        self.assertEqual(self.incoming_files(), [])  # no final, no .part

    def test_copy_requires_both_running(self):
        core = self.boot(self.ALLOW)
        core.stop_qube("vault")
        src = self.src_home / "n.txt"
        src.write_bytes(b"n")
        with self.assertRaises(QubesError):
            core.filecopy("work", str(src), "vault")


class HandlerAttackTest(unittest.TestCase):
    """Direct handler calls: the receiver must refuse path escapes (RE finding)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.handlers = make_filecopy_handlers(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_rejects_escaping_names_and_sources(self):
        write = self.handlers["filecopy.write"]
        base = {"src": "work", "name": "ok.txt", "offset": 0,
                "data_b64": "", "sha256": "0" * 64, "final": True}
        for bad in ["../evil", "/etc/passwd", "a/b", "..", "", "a\\b"]:
            with self.assertRaises(ValueError, msg=bad):
                write(dict(base, name=bad))
        with self.assertRaises(ValueError):
            write(dict(base, src="../work"))

    def test_read_rejects_oversize_and_relative(self):
        read = self.handlers["filecopy.read"]
        big = self.home / "big.bin"
        with open(big, "wb") as f:
            f.truncate(FILECOPY_MAX + 1)
        with self.assertRaises(ValueError):
            read({"path": str(big), "offset": 0, "length": 10})
        with self.assertRaises(ValueError):
            read({"path": "relative.txt", "offset": 0, "length": 10})


class CliFilecopyTest(unittest.TestCase):
    def test_cli_end_to_end_and_bad_syntax(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state, policy_f = root / "s.json", root / "policy.json"
            policy_f.write_text(json.dumps([
                {"src": "host", "service": "ping", "dst": "*", "allow": True},
                {"src": "host", "service": "info", "dst": "*", "allow": True},
                {"src": "work", "service": "filecopy", "dst": "vault", "allow": True}]))
            old = backends.AGENT_BASE_PORT
            backends.AGENT_BASE_PORT = free_port()
            agents = []
            try:
                with mock.patch.dict(os.environ, {
                        "MINIQUIBES_STATE": str(state),
                        "MINIQUIBES_POLICY": str(policy_f)}):
                    for argv in (["create", "work"], ["create", "vault"],
                                 ["start", "work"], ["start", "vault"]):
                        with contextlib.redirect_stdout(io.StringIO()):
                            self.assertEqual(cli_main(argv), 0)
                    backend = FakeBackend(state)
                    dst_home = root / "vault-home"
                    dst_home.mkdir()
                    agents = [
                        start_agent(make_filecopy_handlers(root),
                                    backend.agent_endpoint("work")),
                        start_agent(make_filecopy_handlers(dst_home),
                                    backend.agent_endpoint("vault")),
                    ]
                    src = root / "hello.txt"
                    src.write_text("via cli")
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        rc = cli_main(["filecopy", f"work:{src}", "vault"])
                    self.assertEqual(rc, 0)
                    self.assertIn("copied hello.txt", out.getvalue())
                    landed = dst_home / "QubesIncoming" / "work" / "hello.txt"
                    self.assertEqual(landed.read_text(), "via cli")
                    with contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(
                            cli_main(["filecopy", "work:relative/path", "vault"]), 1)
            finally:
                for listener, stop, thread in agents:
                    stop.set()
                    listener.close()
                    thread.join(timeout=2)
                backends.AGENT_BASE_PORT = old


if __name__ == "__main__":
    unittest.main()
