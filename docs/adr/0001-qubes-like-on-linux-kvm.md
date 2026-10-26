# ADR-0001: Build a Qubes-like compartment OS on Linux + KVM

Status: accepted (2026-10-26, owner said "start") · Reversibility: cheap until ticket 02 lands.

## Context
Three directions were on the table (see `docs/proposal.md`, `docs/research/qubesos-main-repos.md`):
(a) classic kernel-from-scratch (bootloader → C kernel → shell), (b) compile real Qubes OS with
builderv2, (c) build our own Qubes-like OS — equivalents of only the 22 Tier B "invention" repos.
The owner's latest stated goal ("i want to build this os from scratch" about QubesOS) points to (c).

## Decision
Build **MiniQubes**: a compartmentalized OS in Qubes' architecture —
reuse Linux + KVM/QEMU + a distro userland (Tier A), and develop only equivalents of the core
ideas: admin daemon, guest agent + channel, template CoW clones, policy-checked RPC.
KVM, not Xen: simpler dev loop (libvirt, vsock, SPICE are all first-class), one less system to learn.

## Consequences
- We write a *control plane and guest agent*, not a kernel or hypervisor. The learning target is
  Qubes' architecture: compartmentalize, treat guests as untrusted, keep the trusted core tiny.
- Sandbox limit becomes manageable: core logic is developed against a FakeBackend (ADR-0003);
  real VMs run on the owner's machine from ticket 02.
- The classic-kernel path stays available as a future separate project; nothing here blocks it.
