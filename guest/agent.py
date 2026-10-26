"""Guest agent — the small daemon inside each qube (tickets 03, 06).

Stdlib only (a guest image may be minimal). One service = one handler function,
the qrexec "services as programs" idea scaled down. Run `python3 -m guest.agent
--tcp 127.0.0.1:27000` in dev, `--vsock <port>` inside a real guest.
Ticket 04 copies the `miniqubes/` + `guest/` packages into the template.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import re
import socket
import sys
import time
from pathlib import Path

from miniqubes.channel import FILECOPY_CHUNK, FILECOPY_MAX, serve

_started = time.monotonic()
_TOKEN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


def _ping(args: dict) -> str:
    return "pong"


def _info(args: dict) -> dict:
    return {
        "hostname": socket.gethostname(),
        "agent_uptime_s": round(time.monotonic() - _started, 1),
        "python": sys.version.split()[0],
    }


# -- filecopy (ticket 06) --------------------------------------------------
# The receiver treats the sender as fully hostile (RE: qfile-unpacker's path
# paranoia): basename-only names, writes confined to ~/QubesIncoming/<src>/,
# temp file + sha256 verify + atomic rename, size cap on both sides.

def _check_token(kind: str, value) -> str:
    if not isinstance(value, str) or not _TOKEN.match(value):
        raise ValueError(f"invalid {kind}: {value!r}")
    return value


def _check_name(name) -> str:
    if not isinstance(name, str) or name in ("", ".", "..") \
            or "/" in name or "\\" in name or "\x00" in name:
        raise ValueError(f"invalid file name: {name!r}")
    return name


def make_filecopy_handlers(home: Path) -> dict:
    """filecopy.read / filecopy.write bound to one guest home directory."""
    transfers: dict = {}  # (src, name) -> {tmp, dir, sha256, bytes}

    def read(args: dict) -> dict:
        path = Path(str(args.get("path", "")))
        if not path.is_absolute():
            raise ValueError(f"path must be absolute: {path}")
        if not path.is_file():
            raise ValueError(f"not a regular file: {path}")
        size = path.stat().st_size
        if size > FILECOPY_MAX:
            raise ValueError(f"file too large: {size} > {FILECOPY_MAX}")
        offset = int(args.get("offset", 0))
        length = min(int(args.get("length", FILECOPY_CHUNK)), FILECOPY_CHUNK)
        if offset < 0 or length < 0:
            raise ValueError("negative offset/length")
        with open(path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest() if offset == 0 else None
            f.seek(offset)
            data = f.read(length)
        return {"name": path.name, "size": size, "sha256": digest,
                "offset": offset,
                "data_b64": base64.b64encode(data).decode("ascii"),
                "eof": offset + len(data) >= size}

    def _abort(key) -> None:
        state = transfers.pop(key, None)
        if state:
            state["tmp"].unlink(missing_ok=True)

    def write(args: dict) -> dict:
        src = _check_token("source qube", args.get("src"))
        name = _check_name(args.get("name"))
        offset = int(args.get("offset", -1))
        final = bool(args.get("final"))
        key = (src, name)
        try:
            data = base64.b64decode(str(args.get("data_b64", "")), validate=True)
            if offset == 0:
                _abort(key)  # stale half-transfer from a dead attempt
                sha = str(args.get("sha256", ""))
                if len(sha) != 64:
                    raise ValueError("first chunk must carry the file sha256")
                incoming = home / "QubesIncoming" / src
                if (home / "QubesIncoming").is_symlink() or incoming.is_symlink():
                    raise ValueError("incoming dir is a symlink; refusing")
                incoming.mkdir(parents=True, exist_ok=True)
                tmp = incoming / f".{name}.part"
                transfers[key] = {"tmp": tmp, "dir": incoming,
                                  "sha256": sha, "bytes": 0}
                fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                             | getattr(os, "O_NOFOLLOW", 0), 0o600)
            else:
                state = transfers.get(key)
                if state is None or offset != state["bytes"]:
                    raise ValueError("out-of-order chunk")
                fd = os.open(state["tmp"], os.O_WRONLY | os.O_APPEND
                             | getattr(os, "O_NOFOLLOW", 0))
            state = transfers[key]
            if state["bytes"] + len(data) > FILECOPY_MAX:
                raise ValueError("file too large")
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            state["bytes"] += len(data)
            if not final:
                return {"received": state["bytes"]}
            digest = hashlib.sha256(state["tmp"].read_bytes()).hexdigest()
            if digest != state["sha256"]:
                raise ValueError("sha256 mismatch; transfer discarded")
            dest = state["dir"] / name
            os.replace(state["tmp"], dest)  # atomic; symlink at dest is replaced, not followed
            transfers.pop(key, None)
            return {"path": str(dest), "size": state["bytes"], "sha256": digest}
        except Exception:
            _abort(key)
            raise

    return {"filecopy.read": read, "filecopy.write": write}


HANDLERS = {"ping": _ping, "info": _info, **make_filecopy_handlers(Path.home())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="guest.agent", description="MiniQubes guest agent")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tcp", metavar="HOST:PORT", help="dev transport")
    group.add_argument("--vsock", metavar="PORT", type=int,
                       help="real-guest transport (AF_VSOCK)")
    args = parser.parse_args(argv)
    if args.tcp:
        host, _, port = args.tcp.rpartition(":")
        listener = socket.create_server((host, int(port)))
        where = f"tcp {args.tcp}"
    else:
        listener = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        listener.bind((socket.VMADDR_CID_ANY, args.vsock))
        listener.listen()
        where = f"vsock {args.vsock}"
    print(f"guest agent listening on {where}", flush=True)
    try:
        serve(listener, HANDLERS)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
