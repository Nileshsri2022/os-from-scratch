# 03 — Guest agent + channel v0 (ping / info RPC)

Blocked by: 01 (logic), 02 (real-guest end-to-end) · Status: **done** (2026-10-26; vsock item carried to 02)
RE folded in: [qubes-core-qrexec](../../../docs/reverse-engineering/qubes-core-qrexec.md),
[qubes-core-vchan-xen](../../../docs/reverse-engineering/qubes-core-vchan-xen.md) — delta from RE index #4.

## Goal
Host can call `ping` and `info` RPCs on a running qube's guest agent over the channel;
in the sandbox the same code runs host↔agent over loopback for tests.

## Concepts
Why a narrow channel (vchan/vsock), not SSH; RPC framing; the agent as untrusted-input
surface (parse defensively: capped frames, JSON only); one service = one handler function
(the qrexec services-as-programs idea, scaled down).

## Design
- `miniqubes/channel.py`: frame = 4-byte big-endian length + UTF-8 JSON
  (`{id, service, args}` → `{id, ok, result|error}`). **Hard cap: 1 MiB per frame, both
  directions** — oversized/invalid input raises `ProtocolError` and drops the connection,
  never the server (upstream fuzzes every VM-facing parser; we adopt the stance).
  Transport = any connected socket; dev: TCP loopback; real guest: `socket.AF_VSOCK`.
- `guest/agent.py`: stdlib-only server; services `ping`, `info` (hostname, agent uptime).
  Runs in the guest (ticket 04 copies `miniqubes/` + `guest/` into the template).
- Addressing: `Backend.agent_endpoint(name)` — new 7th backend method, default `None`
  (ADR-0003 addendum). FakeBackend assigns a loopback port per qube at create;
  LibvirtBackend (ticket 02) will return `("vsock", cid, port)`.
- `Core.call(name, service, args)`: requires running qube; resolves endpoint; one
  connection per call; transport/policy errors surface as `QubesError`.
  Policy check is **ticket 06** (marked seam in code).

## Steps (TDD: red → green)
- [x] Tests first: frame round-trip; oversized frame rejected; invalid JSON rejected;
      server survives random garbage then still answers `ping`; unknown service error
- [x] `channel.py` + `guest/agent.py` + `Core.call` + CLI `call` command
- [x] Full suite green (old 9 + new); loopback demo transcript → Result
- [ ] (with 02) real guest over vsock — carried as verify item into ticket 02

## Verify
Tests green incl. malformed/oversized/garbage cases; `python3 -m miniqubes call personal ping`
→ `pong` (agent on loopback); calling a stopped qube fails with a clean error.
Real-guest vsock transcript appended when 02 lands.

## Result (2026-10-26)
Shipped as designed: `miniqubes/channel.py` (framing + `rpc_call` + `serve`),
`guest/agent.py` (`ping`/`info`), `Backend.agent_endpoint` (+ ADR-0003 addendum),
`QubesCore.call`, CLI `call NAME SERVICE [JSON]`. **Milestone M1 "Brain" reached.**

Evidence — TDD: new tests written first (suite red: 2 import errors), then green:
`python3 -m unittest discover -s tests` → **21 tests OK** (9 old + 12 new: frame codec,
oversized/invalid rejection, garbage-survival, Core.call rules, unreachable agent).
Demo (agent on loopback :27000, FakeBackend):
```
$ python3 -m miniqubes call personal ping     # before start → error: qube is not running (exit 1)
$ python3 -m miniqubes start personal
$ python3 -m miniqubes call personal ping     → pong
$ python3 -m miniqubes call personal info     → {"hostname": …, "agent_uptime_s": …, "python": "3.11.2"}
$ python3 -m miniqubes call personal bogus    → error: RPC 'bogus' … unknown service (exit 1)
```

### Code review (self, ask-matt two-axis)
- **Standards:** stdlib only; no new deps; shortcuts labelled in code (sequential accept
  loop; one connection per call); tests left green.
- **Spec:** every Verify item evidenced above except real-guest vsock (blocked by 02, carried).
- **Findings caught & fixed while writing/reviewing:**
  1. Accepted sockets inherit the listener's 0.2s timeout → idle RPC connections would die;
     `conn.settimeout(None)` after accept.
  2. A handler returning a non-JSON-serializable result would raise `TypeError` inside
     `send_frame` and kill `serve` → result is serialization-checked; handler errors become
     `ok:false` responses instead.

Shortcuts taken:
- `shortcut: sequential connections in serve(), thread-per-connection when concurrent calls exist`
- `shortcut: vsock code paths (connect/agent --vsock) untested in sandbox — first real run is ticket 02`
- `shortcut: pre-ticket-03 FakeBackend state files have no agent_port → recreate those qubes`
