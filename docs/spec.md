# SPEC — MiniQubes v1

Build, from scratch, a **Qubes-like compartmentalized OS**: one physical machine, many isolated
**qubes** (VMs), one small trusted **host** control plane. Terms: `GLOSSARY.md`.
Decisions: `docs/adr/0001–0003`. Informed by the public-architecture survey in
`docs/research/qubesos-*.md` (no upstream code copied; REA deep-dives remain opt-in per repo).

## Problem statement
On a normal single-OS machine, everything the user values — banking, work, browsing, keys —
lives in one security domain, so one compromise takes everything. Real Qubes OS solves this by
compartmentalizing work into isolated VMs, but it is 215 upstream repos: far too large for one
person to own, learn from, or customize. The owner wants the same compartment discipline in the
smallest system one developer can fully understand and reshape.

## Goal
From a host CLI, a user can create qubes from a template, start/stop them, copy a file between
two qubes through a policy-checked RPC, and open a window into a qube — with every qube isolated
from the others by the hypervisor, and all cross-qube communication denied unless policy allows it.

## User stories
1. As the owner, I want to create a qube from a template with one command, so that a new
   compartment (e.g. `work`, `vault`) costs seconds, not an OS install.
2. As the owner, I want to start, stop, and remove qubes from the CLI, so that compartments
   exist only while I need them.
3. As the owner, I want to list all qubes with their state, so that I always know what is running.
4. As the owner, I want each qube isolated by the hypervisor, so that a compromised `untrusted`
   qube cannot reach `vault` or the host.
5. As the owner, I want qubes to share nothing by default, so that no qube can read another's
   files or even talk to it unless I allow it.
6. As the owner, I want to ask a running qube simple questions (`ping`, `info`) and get answers,
   so that I can tell a live qube from a hung one.
7. As the owner, I want to copy a file from one qube to another only when policy explicitly
   allows that (source, service, target), so that moving data between compartments is a
   deliberate act I control.
8. As the owner, I want a denied copy to fail loudly and leave nothing behind in the target
   qube, so that a mistake or attack cannot smuggle files across.
9. As the owner, I want copied files to land in a fixed incoming area of the target qube, so
   that incoming data never overwrites anything I already trust.
10. As the owner, I want new qubes to boot as copy-on-write clones of one template, so that
    ten qubes share one OS install and a fresh qube starts from a known-clean state.
11. As the owner, I want each qube to reach the internet through host NAT while remaining
    unable to see the other qubes, so that browsing works without weakening isolation.
12. As the owner, I want to open a window into a running qube, so that I can actually use the
    applications inside it.
13. As the developer, I want the whole control plane to run and be tested on a machine with no
    KVM (fake backend), so that development is not blocked on special hardware.
14. As the developer, I want every cross-qube operation to be a named, policy-checked RPC
    service, so that the attack surface is a short list I can audit.

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
| vchan/QubesDB + qrexec | channel + RPC v0 (loopback TCP in dev, vsock in guests) | 03 |
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

## Testing decisions (verification bar, every ticket)
- Test **external behaviour at the highest seam**, not internals. There is deliberately one
  main seam: the **Backend interface** (ADR-0003). Tests run the real Core/CLI/policy code
  against `FakeBackend`; ticket 02 must re-run the same lifecycle suite shape against libvirt.
- The channel is tested over **real loopback sockets** (guest agent included), not mocks of
  our own framing code — framing, oversized frames, and bad JSON are exercised on the wire.
- Prior art: stdlib `unittest` suites in `tests/` (one file per area, hermetically env-scoped).
- The bar for every ticket: `python3 -m unittest discover -s tests` green · CLI demo transcript
  in the ticket's Result · no new dependency without an ADR · shortcuts labelled
  `shortcut: <limit>, <upgrade when>`.

## Post-v1 candidates (from reverse-engineering; each with its trigger)
Named non-goals today (evidence: `docs/reverse-engineering/00-index.md`); each lists the
condition that would promote it into a ticket:
- **Config-watch service** (QubesDB idea) — when a qube's config must change *while it runs*.
- **`mq apply` default qube set** (mgmt-salt idea) — when manual setup has been repeated ~3 times.
- **Policy `ask` action + `@anyvm`/tag tokens** (qrexec) — when a trusted prompt UI exists.
- **Seamless GUI** (gui-protocol: metadata channel + shared-memory pixels) — a research project of its own.

## Open questions (future grilling, non-blocking)
Guest distro for the golden template (Debian vs Fedora) · SPICE vs VNC default ·
when (if ever) Core graduates from library+CLI to a long-running socket daemon — trigger:
a second client (e.g. a GUI) needing concurrent access.
