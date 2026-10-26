# os-from-scratch

**MiniQubes** — a Qubes-like compartmentalized OS built from scratch for learning:
isolated VM "qubes" on Linux + KVM, a small trusted control plane, deny-by-default
policy-checked RPC between qubes. Spec: [docs/spec.md](docs/spec.md) ·
Words: [GLOSSARY.md](GLOSSARY.md) · Decisions: [docs/adr/](docs/adr/)

**Status:** 🧠 **M1 "Brain" reached + policy-checked filecopy** — tickets 01, 03, 06 done
(control plane, guest-agent RPC channel, deny-by-default policy + secure file copy);
ticket 02's LibvirtBackend code is written and unit-tested, awaiting real-VM verification
on a KVM machine. 50 tests green. Milestones: [docs/spec.md](docs/spec.md). M2 "Initial OS"
(real VMs) needs tickets 02 (verify) + 04. Tracker: `.scratch/os-from-scratch/issues/`

```bash
python3 -m miniqubes create personal --template fedora-40
python3 -m miniqubes start personal
python3 -m guest.agent --tcp 127.0.0.1:27000 &   # the qube's guest agent (dev transport)
python3 -m miniqubes call personal ping          # → pong
python3 -m miniqubes call personal info
python3 -m miniqubes filecopy personal:/etc/hostname vault   # needs a policy rule — see ticket 06
python3 -m unittest discover -s tests            # verify (50 tests)
```

How we work here: [AGENTS.md](AGENTS.md) (ask-matt flow · docs-first per ticket ·
ponytail smallest-change rule). Background research: [docs/research/](docs/research/)
(all 215 QubesOS repos graphed + the 22 "main" repos that matter).
