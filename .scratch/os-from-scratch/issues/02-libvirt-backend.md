# 02 — LibvirtBackend: real KVM qubes

Blocked by: 01 · Status: doing (code + unit tests in sandbox 2026-10-26; closes only after owner-machine verification) · **Closes only on the owner's machine (KVM + libvirt).**
Step-by-step runbook (Hinglish): `docs/guides/02-libvirt-backend-guide.md`

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
- [x] Implement backend + XML template (sandbox, 2026-10-26 — fake-libvirt unit tests)
- [ ] Lifecycle test-suite shape re-run against libvirt (manual checklist below)
- [ ] Owner-machine verify transcript → Result

## Verify (owner machine)
`virsh list --all` shows `mq-personal`; `start` boots it (serial/SSH reachable per image);
`stop` is graceful-then-force; `remove` undefines + deletes disk. Sandbox: unit tests still green (fake).

## Result
**Interim (2026-10-26, sandbox) — code done, ticket NOT done.** Guide Step 4 implemented
TDD-style (red: `ImportError: cannot import name 'AGENT_VSOCK_PORT'`; green below):

- `LibvirtBackend` in `miniqubes/backends.py`: lazy libvirt import (clean `QubesError` if
  bindings missing), domain XML `mq-<name>` (1 vCPU/1 GiB, virtio qcow2, `<vsock><cid
  auto='yes'/>`, template in `<metadata>`), graceful-then-force `stop` (shutdown → poll →
  destroy), `remove` = undefine + disk delete, libvirt as source of truth (no state file),
  `agent_endpoint` reads the auto-assigned CID back from domain XML → `("vsock", cid, 27000)`.
- `default_backend()`: `MINIQUIBES_BACKEND=libvirt|fake`, default **fake** until this ticket
  closes. CLI now builds the core via `default_backend()` inside its error handler.
- Evidence: `tests/test_libvirt_backend.py` — 14 tests against a fake `libvirt` module
  (XML content, disk copy incl. `.img` templates, state mapping, foreign domains ignored,
  CID 3/4 assigned per qube, graceful vs forced stop, selection + error paths).
  Full suite: **50 tests OK**. Sandbox sanity: libvirt mode exits 1 with a clean
  "needs python3-libvirt" error (no traceback); fake demo unaffected.
- Code review (self): XML attribute quote-escaping fixed; `start/stop` assume Core's
  existence guard (same contract as FakeBackend).

**Labelled shortcuts:** unit tests use a fake libvirt module — they prove XML/mapping/calls,
not a boot. Disks are plain file copies (CoW = ticket 04). Fixed 1 vCPU/1 GiB. State by
polling, not libvirt events.

**Still required to close (owner's machine):** guide Steps 1–3 + 5–6 — KVM/libvirt ready,
repo synced, one guest disk, agent installed in the image, then the Step 6 checklist
(`virsh` shows `mq-personal`, real boot, `mq call personal ping` → `pong` over vsock,
graceful stop, remove). That transcript replaces this interim note and flips Status to done.
