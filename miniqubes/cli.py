"""CLI — `python3 -m miniqubes <command>` (think upstream's qvm-* tools).

shortcut: FakeBackend only, LibvirtBackend selection lands in ticket 02.
"""
from __future__ import annotations

import argparse
import json
import sys

from .backends import FakeBackend
from .core import QubesCore, QubesError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="miniqubes", description="MiniQubes control CLI")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("create", help="create a qube")
    c.add_argument("name")
    c.add_argument("--template", default=None, help="template name (CoW cloning: ticket 04)")

    for cmd, helptext in [
        ("start", "start a qube"),
        ("stop", "stop a qube"),
        ("remove", "remove a stopped qube"),
    ]:
        sp = sub.add_parser(cmd, help=helptext)
        sp.add_argument("name")

    sub.add_parser("list", help="list qubes")

    cl = sub.add_parser("call", help="call an RPC service on a running qube's guest agent")
    cl.add_argument("name")
    cl.add_argument("service")
    cl.add_argument("args", nargs="?", default=None, help="optional JSON object, e.g. '{\"k\": 1}'")

    fc = sub.add_parser(
        "filecopy",
        help="copy a file between qubes into ~/QubesIncoming/<src>/ (policy-checked)")
    fc.add_argument("src", help="SRCQUBE:/absolute/path")
    fc.add_argument("dst", help="destination qube")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    core = QubesCore(FakeBackend())
    try:
        if args.command == "create":
            q = core.create_qube(args.name, template=args.template)
            tmpl = f" (template: {q.template})" if q.template else ""
            print(f"created qube {q.name!r}{tmpl}")
        elif args.command == "start":
            core.start_qube(args.name)
            print(f"started qube {args.name!r}")
        elif args.command == "stop":
            core.stop_qube(args.name)
            print(f"stopped qube {args.name!r}")
        elif args.command == "remove":
            core.remove_qube(args.name)
            print(f"removed qube {args.name!r}")
        elif args.command == "list":
            qubes = core.list_qubes()
            if not qubes:
                print("(no qubes)")
            else:
                print(f"{'NAME':<20} {'TEMPLATE':<20} STATE")
                for q in qubes:
                    print(f"{q.name:<20} {(q.template or '-'):<20} {q.state}")
        elif args.command == "call":
            rpc_args = None
            if args.args:
                try:
                    rpc_args = json.loads(args.args)
                except json.JSONDecodeError as exc:
                    print(f"error: args must be a JSON object: {exc}", file=sys.stderr)
                    return 1
            result = core.call(args.name, args.service, rpc_args)
            print(result if isinstance(result, str) else json.dumps(result, indent=1))
        elif args.command == "filecopy":
            src_qube, sep, src_path = args.src.partition(":")
            if not sep or not src_path.startswith("/"):
                print("error: source must look like SRCQUBE:/absolute/path",
                      file=sys.stderr)
                return 1
            res = core.filecopy(src_qube, src_path, args.dst)
            print(f"copied {res['name']} ({res['size']} bytes, "
                  f"sha256 {res['sha256'][:12]}…) {src_qube} -> {args.dst}:{res['path']}")
    except QubesError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
