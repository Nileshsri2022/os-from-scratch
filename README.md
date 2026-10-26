# os-from-scratch

**MiniQubes** — a Qubes-like compartmentalized OS built from scratch for learning:
isolated VM "qubes" on Linux + KVM, a small trusted control plane, deny-by-default
policy-checked RPC between qubes. Spec: [docs/spec.md](docs/spec.md) ·
Words: [GLOSSARY.md](GLOSSARY.md) · Decisions: [docs/adr/](docs/adr/)

**Status:** 🧠 **M1 "Brain" reached + policy-checked filecopy + networking** — tickets 01,
03, 06 done (control plane, guest-agent RPC channel, deny-by-default policy + secure file
copy); all seven tickets' code is written (01/03/06 done; 02 LibvirtBackend, 04 CoW
templates, 05 NAT networking, 07 SPICE window await real-KVM verification). 68 tests
green. Milestones: [docs/spec.md](docs/spec.md). M2 "Initial OS" = verify 02 + 04 on
KVM. Tracker: `.scratch/os-from-scratch/issues/`

```bash
python3 -m miniqubes create personal --template fedora-40
python3 -m miniqubes start personal
python3 -m guest.agent --tcp 127.0.0.1:27000 &   # the qube's guest agent (dev transport)
python3 -m miniqubes call personal ping          # → pong
python3 -m miniqubes call personal info
python3 -m miniqubes filecopy personal:/etc/hostname vault   # needs a policy rule — see ticket 06
python3 -m miniqubes open personal               # SPICE window, titled [personal] (ticket 07)
python3 -m unittest discover -s tests            # verify (68 tests)
```

> `shortcut:` ticket 07 is a whole-desktop SPICE window, not Qubes' seamless per-window
> GUI — no per-window isolation; the host-drawn `[qube]` title is the trust anchor.
> Upgrade to the gui-agent protocol post-v1 (see docs/spec.md).

### Real backend (libvirt) — one-time network setup (ticket 05)

With `MINIQUIBES_BACKEND=libvirt` (ticket 02, runbook:
`docs/guides/02-libvirt-backend-guide.md`), every qube attaches to the `mq-net` NAT
network and is firewalled by the `mq-isolate` filter: qubes reach the internet but
**cannot** reach each other — the only cross-qube path is policy-checked RPC. Define
both once (they persist in libvirt):

```bash
virsh nwfilter-define tools/mq-isolate.nwfilter
virsh net-define tools/mq-net.xml
virsh net-autostart mq-net && virsh net-start mq-net
```

How we work here: [AGENTS.md](AGENTS.md) (ask-matt flow · docs-first per ticket ·
ponytail smallest-change rule). Background research: [docs/research/](docs/research/)
(all 215 QubesOS repos graphed + the 22 "main" repos that matter).
