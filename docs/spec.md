# SPEC — MiniQubes v1

Build, from scratch, a **Qubes-like compartmentalized OS**: one physical machine, many isolated
**qubes** (VMs), one small trusted **host** control plane. Terms: `GLOSSARY.md`.
Decisions: `docs/adr/0001–0003`. Informed by the public-architecture survey in
`docs/research/qubesos-*.md` (no upstream code copied; REA deep-dives remain opt-in per repo).

## Goal
From a host CLI, a user can create qubes from a template, start/stop them, copy a file between
two qubes through a policy-checked RPC, and open a window into a qube — with every qube isolated
from the others by the hypervisor, and all cross-qube communication denied unless policy allows it.

## Non-goals (v1)
Custom kernel/bootloader · Xen · seamless colored-border GUI protocol (SPICE window instead) ·
Windows guests · separate net/firewall qubes (host NAT instead) · disposables · ISO installer.

## Security model (the actual point)
- Guests are **untrusted**; compromise of one qube must not imply compromise of others or host.
- Trusted base = host kernel + hypervisor + admin daemon. Keep the daemon small and boring.
- Cross-qube talk happens **only** as named RPC services over the channel, **deny by default**.

## Architecture
```
 host (trusted)                                   guests (untrusted)
 ┌─────────────┐   Admin API    ┌──────────────┐   backend    ┌─────────────┐
 │ CLI (mq)    │ ─────────────► │ Admin daemon │ ───────────► │ libvirt/KVM │
 └─────────────┘                │  = Core      │   (fake in   └──────┬──────┘
                                │  + Policy    │    dev)           │ domains
                                └──────┬───────┘            ┌──────▼──────┐
                                       │ channel (RPC)      │ qube        │
                                       └──────────────────► │ guest agent │
                                                            └─────────────┘
```

## Components (upstream Tier B → ours → ticket)
| Upstream idea | Our component | Ticket |
|---|---|---|
| qubesd (`core-admin`) | `miniqubes/core.py` — lifecycle + registry rules | 01 |
| libvirt/Xen layer | `miniqubes/backends.py` — FakeBackend → LibvirtBackend | 01 → 02 |
| Admin API + `qvm-*` tools | `miniqubes/cli.py` (`python3 -m miniqubes …`) | 01 |
| vchan/QubesDB + qrexec | channel + RPC v0 (socket now, vsock-ready) | 03 |
| `core-agent-linux` | `guest/agent.py` — RPC server inside the qube | 03 |
| template-builder + storage | golden qcow2 + backing-file CoW clones | 04 |
| sys-net (simplified) | libvirt NAT network per host | 05 |
| qrexec services + policy | `filecopy` RPC + policy file (deny-default) | 06 |
| gui-daemon/agent (shortcut) | SPICE/VNC window launcher | 07 |

## Environment facts (checked 2026-10-26)
Sandbox: Python 3.11, **no KVM/QEMU/libvirt** → tickets 01/03/06 logic is verified here via
FakeBackend + loopback channel + unit tests. Tickets 02/04/05/07 close only with a run on the
owner's machine (any Linux with KVM + libvirt + qemu) using each ticket's verify checklist.

## Verification bar (every ticket)
`python3 -m unittest discover -s tests` green · CLI demo transcript in the ticket's Result ·
no new dependency without an ADR · shortcuts labelled `shortcut: <limit>, <upgrade when>`.

## Open questions (future grilling, non-blocking)
Guest distro for the golden template (Debian vs Fedora) · SPICE vs VNC default ·
whether the daemon becomes a real socket service or stays a library+CLI until ticket 03.
