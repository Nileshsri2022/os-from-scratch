# 03 — Guest agent + channel v0 (ping / info RPC)

Blocked by: 01 (logic), 02 (real-guest end-to-end) · Status: todo

## Goal
Host can call `ping` and `info` RPCs on a running qube's guest agent over the channel;
in the sandbox the same code runs host↔agent over loopback for tests.

## Concepts
Why a narrow channel (vchan/vsock), not SSH; RPC framing; the agent as untrusted-input surface
(parse defensively: length-capped, JSON only).

## Design
- `miniqubes/channel.py`: length-prefixed JSON frames (`{id, service, args}` → `{id, ok, result|error}`),
  transport = a connected socket. Dev transport: TCP loopback / Unix socket.
  Real transport: virtio-vsock (`socket.AF_VSOCK`) — same frame code.
- `guest/agent.py`: stdlib-only server; services `ping`, `info` (hostname, uptime).
- `Core.call(qube, service, args)`: resolves channel address from backend
  (fake: loopback port recorded at `start`; libvirt: vsock CID from ticket 02 metadata).

## Steps
- [ ] channel.py + agent.py + Core.call
- [ ] unittest: start agent on loopback, call ping/info, malformed frame → clean error
- [ ] (with 02) real guest: agent in template, host calls over vsock

## Verify
Tests green incl. bad-frame case; CLI `mq call vault ping` → `pong`. Real-guest transcript appended when 02 lands.

## Result
(filled on completion)
