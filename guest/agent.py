"""Guest agent — the small daemon inside each qube (ticket 03).

Stdlib only (a guest image may be minimal). One service = one handler function,
the qrexec "services as programs" idea scaled down. Run `python3 -m guest.agent
--tcp 127.0.0.1:27000` in dev, `--vsock <port>` inside a real guest.
Ticket 04 copies the `miniqubes/` + `guest/` packages into the template.
"""
from __future__ import annotations

import argparse
import socket
import sys
import time

from miniqubes.channel import serve

_started = time.monotonic()


def _ping(args: dict) -> str:
    return "pong"


def _info(args: dict) -> dict:
    return {
        "hostname": socket.gethostname(),
        "agent_uptime_s": round(time.monotonic() - _started, 1),
        "python": sys.version.split()[0],
    }


HANDLERS = {"ping": _ping, "info": _info}


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
