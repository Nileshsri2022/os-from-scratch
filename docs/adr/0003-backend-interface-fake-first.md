# ADR-0003: Hypervisor behind a tiny Backend interface; FakeBackend first

Status: accepted (2026-10-26)

## Context
Fact (checked 2026-10-26): this sandbox has **no `/dev/kvm`, no QEMU, no libvirt**.
The owner's machine is where real VMs can boot. Upstream Qubes itself keeps a non-Xen
development path (`qubes-core-vchan-socket`) for the same reason.

## Decision
All lifecycle logic lives in `Core`, written against a `Backend` interface with exactly six
operations: `create, start, stop, remove, get, list`.
- `FakeBackend` (ticket 01): simulates qubes in a JSON state file. Used by tests and demos.
- `LibvirtBackend` (ticket 02): real KVM domains via libvirt. The only file that imports libvirt.

## Consequences
- Every rule (name validation, state transitions, errors) is unit-tested here, today, for free.
- Known risk: the fake drifting from libvirt semantics. Mitigation: keep the interface tiny,
  and ticket 02 must pass the *same* lifecycle test-suite shape against libvirt on the owner's
  machine before it closes.
- The fake is a permanent dev tool, not throwaway code — labelled as such, not a mock of record.

## Addendum (ticket 03, 2026-10-26)
Backend grew a 7th method, `agent_endpoint(name)` — where a qube's guest agent listens —
with a default implementation returning `None` ("no channel"), so existing backends stay
valid. FakeBackend returns `("tcp", "127.0.0.1", port)` (port assigned at create);
LibvirtBackend (ticket 02) will return `("vsock", cid, port)`. Core stays transport-blind.
