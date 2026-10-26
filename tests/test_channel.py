"""Channel framing + dispatch + agent handlers (ticket 03).

Includes the malformed-input cases from the RE finding: upstream fuzzes every
VM-facing parser (qrexec/qubesdb), so ours must drop bad connections, never die.
"""
import os
import socket
import struct
import threading
import unittest

from guest.agent import HANDLERS
from miniqubes import channel
from miniqubes.channel import ProtocolError, recv_frame, rpc_call, send_frame, serve


class FrameTest(unittest.TestCase):
    def test_roundtrip(self):
        a, b = socket.socketpair()
        with a, b:
            send_frame(a, {"id": 1, "service": "ping", "args": {}})
            self.assertEqual(recv_frame(b), {"id": 1, "service": "ping", "args": {}})

    def test_oversized_header_rejected(self):
        a, b = socket.socketpair()
        with a, b:
            a.sendall(struct.pack(">I", channel.MAX_FRAME + 1))
            with self.assertRaises(ProtocolError):
                recv_frame(b)

    def test_invalid_json_rejected(self):
        a, b = socket.socketpair()
        with a, b:
            payload = b"{not json"
            a.sendall(struct.pack(">I", len(payload)) + payload)
            with self.assertRaises(ProtocolError):
                recv_frame(b)

    def test_send_oversized_payload_rejected(self):
        a, b = socket.socketpair()
        with a, b:
            with self.assertRaises(ProtocolError):
                send_frame(a, {"blob": "x" * (channel.MAX_FRAME + 1)})


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.listener = socket.create_server(("127.0.0.1", 0))
        self.port = self.listener.getsockname()[1]
        self.stop = threading.Event()
        self.thread = threading.Thread(
            target=serve, args=(self.listener, HANDLERS, self.stop.is_set), daemon=True)
        self.thread.start()
        self.endpoint = ("tcp", "127.0.0.1", self.port)

    def tearDown(self):
        self.stop.set()
        self.listener.close()
        self.thread.join(timeout=2)

    def test_ping_info_unknown(self):
        self.assertEqual(rpc_call(self.endpoint, "ping"), "pong")
        self.assertIn("hostname", rpc_call(self.endpoint, "info"))
        with self.assertRaises(ProtocolError):
            rpc_call(self.endpoint, "bogus")

    def test_server_survives_garbage(self):
        with socket.create_connection(("127.0.0.1", self.port)) as s:
            s.sendall(os.urandom(256))
        # The bad connection is dropped; the server must still answer correctly.
        self.assertEqual(rpc_call(self.endpoint, "ping"), "pong")


class HandlerTest(unittest.TestCase):
    def test_handlers(self):
        self.assertEqual(HANDLERS["ping"]({}), "pong")
        self.assertIn("agent_uptime_s", HANDLERS["info"]({}))


if __name__ == "__main__":
    unittest.main()
