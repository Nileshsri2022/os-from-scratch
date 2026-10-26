"""Channel — length-prefixed JSON RPC over a connected socket.

The host↔guest transport (ticket 03), shaped by the qrexec/vchan RE findings:
a dumb reliable stream underneath, named services on top, and a parser that
treats every byte from a guest as hostile (hard frame cap, JSON only, drop the
connection — never the server — on garbage). Dev transport is TCP loopback;
in a real guest the same frames ride AF_VSOCK.
"""
from __future__ import annotations

import json
import socket
import struct

MAX_FRAME = 1 << 20  # 1 MiB per frame, both directions

# filecopy conventions (ticket 06): both sides import these from here so
# chunking can never outgrow the frame cap (256 KiB raw ≈ 342 KiB base64).
FILECOPY_CHUNK = 256 * 1024
FILECOPY_MAX = 64 * 1024 * 1024  # largest file filecopy will move, v1
_HDR = struct.Struct(">I")


class ProtocolError(Exception):
    """Framing/JSON violation or an RPC-level error response."""


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("connection closed mid-frame")
        buf.extend(chunk)
    return bytes(buf)


def send_frame(sock: socket.socket, obj) -> None:
    data = json.dumps(obj).encode("utf-8")
    if len(data) > MAX_FRAME:
        raise ProtocolError(f"frame too large: {len(data)} > {MAX_FRAME}")
    sock.sendall(_HDR.pack(len(data)) + data)


def recv_frame(sock: socket.socket):
    (n,) = _HDR.unpack(_recv_exact(sock, _HDR.size))
    if n > MAX_FRAME:
        raise ProtocolError(f"frame too large: {n} > {MAX_FRAME}")
    data = _recv_exact(sock, n)
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"invalid JSON frame: {exc}") from exc


def connect(endpoint) -> socket.socket:
    """endpoint is ("tcp", host, port) or ("vsock", cid, port)."""
    kind, a, b = endpoint
    if kind == "tcp":
        return socket.create_connection((a, b), timeout=5)
    if kind == "vsock":
        sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((a, b))
        return sock
    raise ProtocolError(f"unknown endpoint kind: {kind!r}")


def rpc_call(endpoint, service: str, args: dict | None = None):
    """One connection, one request, one response. Returns the result or raises."""
    with connect(endpoint) as sock:
        send_frame(sock, {"id": 1, "service": service, "args": args or {}})
        resp = recv_frame(sock)
    if not isinstance(resp, dict) or "ok" not in resp:
        raise ProtocolError(f"malformed response: {resp!r}")
    if not resp["ok"]:
        raise ProtocolError(str(resp.get("error", "RPC failed")))
    return resp.get("result")


def handle_connection(conn: socket.socket, handlers: dict) -> None:
    """Serve requests until the peer hangs up or sends garbage. Never raises."""
    with conn:
        while True:
            try:
                req = recv_frame(conn)
            except (EOFError, ProtocolError, ConnectionError, OSError):
                return
            rid = req.get("id") if isinstance(req, dict) else None
            if not isinstance(req, dict) or "service" not in req:
                resp = {"id": rid, "ok": False, "error": "malformed request"}
            elif req["service"] not in handlers:
                resp = {"id": rid, "ok": False,
                        "error": f"unknown service: {req['service']!r}"}
            else:
                try:
                    result = handlers[req["service"]](req.get("args") or {})
                    json.dumps(result)  # handler results must stay JSON-shaped
                    resp = {"id": rid, "ok": True, "result": result}
                except Exception as exc:  # a handler bug must not kill the server
                    resp = {"id": rid, "ok": False,
                            "error": f"{type(exc).__name__}: {exc}"}
            try:
                send_frame(conn, resp)
            except (ProtocolError, ConnectionError, OSError):
                return


def serve(listener: socket.socket, handlers: dict, should_stop=lambda: False) -> None:
    # shortcut: sequential connections (one client at a time) — plenty for v0
    # control traffic; go thread-per-connection when concurrent calls exist.
    listener.settimeout(0.2)
    while not should_stop():
        try:
            conn, _ = listener.accept()
        except TimeoutError:
            continue
        except OSError:
            return
        conn.settimeout(None)  # accepted sockets inherit the listener's timeout
        handle_connection(conn, handlers)
