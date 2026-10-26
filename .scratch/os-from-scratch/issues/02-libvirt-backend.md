# 02 — LibvirtBackend: real KVM qubes

Blocked by: 01 · Status: todo · **Closes only on the owner's machine (KVM + libvirt).**

## Goal
Same CLI, real VMs: `create/start/stop/list` drive libvirt domains (QEMU/KVM).

## Concepts
libvirt domain XML; QEMU/KVM; why the Core must not learn any of it (Backend seam, ADR-0003).

## Design
- `LibvirtBackend` in `backends.py` — the **only** module importing `libvirt` (lazy import,
  so sandbox/tests never touch it). Domain XML template: name `mq-<qube>`, 1 vCPU/1 GiB v1,
  disk = file under `~/.local/share/miniqubes/disks/` (qcow2, ticket 04 makes it CoW).
- Backend selection: `MINIQUIBES_BACKEND=libvirt|fake` (default fake until this ticket lands).
- State mapping: libvirt domain state → our `running|stopped`; template stored in domain
  `<metadata>` so libvirt stays the source of truth.

## Steps
- [ ] Implement backend + XML template
- [ ] Lifecycle test-suite shape re-run against libvirt (manual checklist below)
- [ ] Owner-machine verify transcript → Result

## Verify (owner machine)
`virsh list --all` shows `mq-personal`; `start` boots it (serial/SSH reachable per image);
`stop` is graceful-then-force; `remove` undefines + deletes disk. Sandbox: unit tests still green (fake).

## Result
(filled on completion)
