# RE: qubes-core-admin — qubesd, the brain

**Depth:** medium · **Evidence:** `evidence/qubes-core-admin.txt`; class inventory of
`qubes/*.py`, `qubes/vm/*.py`; dir tree. **Maps to MiniQubes:** our `core.py` (tickets 01–02).

## What it is
The trusted control plane in dom0: owns every VM's definition and lifecycle, storage,
firewall rules, device assignment, backup — and exposes it all as the Admin API.
130.9k LOC of Python incl. a large test suite (`qubes/tests/`), LGPL.

## Layout & architecture (evidence)
- **Property + event framework first:** `qubes/__init__.py` defines a custom `property`
  descriptor and `PropertyHolder(qubes.events.Emitter)`. Every VM attribute (memory,
  netvm, template…) is a declared property; writes fire events that extensions and the
  libvirt sync subscribe to. This is the organizing idea of the whole codebase.
- **Application object:** `qubes/app.py` — `Qubes(PropertyHolder)` (the system), `VMCollection`
  (registry), `VMMConnection` + `VirConnectWrapper`/`VirDomainWrapper` (libvirt handles with
  reconnect/retry), `QubesHost` (host CPU/mem accounting).
- **VM hierarchy:** `BaseVM → LocalVM → QubesVM(+NetVMMixin)`, then `AppVM`, `TemplateVM`,
  `DispVM`, `StandaloneVM`, `AdminVM` (dom0 itself as a VM object), plus `RemoteVM`.
- **Storage pools:** `qubes/storage/` drivers — `file.py`, `lvm.py` (thin pools), `reflink.py`
  (CoW via FICLONE), `zfs.py`, `callback.py` (external driver protocol). Volumes per VM
  (root/private/kernel) — the template/AppVM split is implemented here.
- **Admin API:** `qubes/api/admin.py` (handlers called over qrexec) + `internal.py`
  (event forwarding between domains) + `misc.py`.
- **Rest:** `backup.py` (streaming backup format with send workers), `device_protocol.py`
  (a full model for USB/PCI/block assignment: `Port`, `VirtualDevice`, `DeviceAssignment`),
  `qmemman/` (memory balancing across VMs), `ext/` (event-hooked extensions), `tools/`
  (dom0-only utilities like qubesd itself).

## Algorithms worth naming
Event-driven property propagation (change → validate → persist → sync libvirt);
copy-on-write storage via three different mechanisms behind one pool API (file images,
LVM-thin snapshots, reflink clones); VM-start as a choreographed sequence across events
(storage prepare → libvirt define → qrexec/qubesdb daemons → gui/agent wiring).

## Reuse vs write
Borrow: the *seams* — registry vs hypervisor sync, storage-driver abstraction (= our Backend
idea, upstream-validated), "dom0 is also a VM object". Our v1 `QubesCore` dataclass stays
deliberately naïve (ADR-0003); properties/events are the known upgrade path if attribute
sprawl starts. LGPL → ideas only.

## Limitations
Structure- and class-level; method bodies, XML persistence format, and event ordering
guarantees not read. Nothing run (needs dom0+libvirt+Xen).
