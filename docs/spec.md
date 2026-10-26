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

## Milestones — when is there an OS to show?
Stages = tickets 01–07. Three demoable milestones:

| Milestone | Stages done | What you can show | Where it runs |
|---|---|---|---|
| **M1 "Brain"** | 01 + 03 | Create/start/stop qubes from the CLI; host calls RPC services (ping/info) on guest agents | this sandbox (FakeBackend + loopback) |
| **M2 "Initial OS" ⭐** | 01–04 | **Real VMs boot from one golden template as instant copy-on-write clones**; lifecycle + agent RPC for real over vsock | owner's KVM machine (02, 04) |
| **M3 "Usable"** | 01–07 | + NAT networking with qube↔qube isolation, policy-checked file copy, a desktop window per qube | owner's KVM machine |

**The initial OS is showable at M2 — after 4 of 7 stages.** M1 already proves the control
architecture end-to-end in simulation; M3 is when it feels like a daily-driver demo.

## Environment facts (checked 2026-10-26)
Sandbox: Python 3.11, **no KVM/QEMU/libvirt** → tickets 01/03/06 logic is verified here via
FakeBackend + loopback channel + unit tests. Tickets 02/04/05/07 close only with a run on the
owner's machine (any Linux with KVM + libvirt + qemu) using each ticket's verify checklist.

## Verification bar (every ticket)
`python3 -m unittest discover -s tests` green · CLI demo transcript in the ticket's Result ·
no new dependency without an ADR · shortcuts labelled `shortcut: <limit>, <upgrade when>`.

## Post-v1 candidates (from reverse-engineering; each with its trigger)
Named non-goals today (evidence: `docs/reverse-engineering/00-index.md`); each lists the
condition that would promote it into a ticket:
- **Config-watch service** (QubesDB idea) — when a qube's config must change *while it runs*.
- **`mq apply` default qube set** (mgmt-salt idea) — when manual setup has been repeated ~3 times.
- **Policy `ask` action + `@anyvm`/tag tokens** (qrexec) — when a trusted prompt UI exists.
- **Seamless GUI** (gui-protocol: metadata channel + shared-memory pixels) — a research project of its own.

## Open questions (future grilling, non-blocking)
Guest distro for the golden template (Debian vs Fedora) · SPICE vs VNC default ·
whether the daemon becomes a real socket service or stays a library+CLI until ticket 03.
