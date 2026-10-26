# os-from-scratch

**MiniQubes** — a Qubes-like compartmentalized OS built from scratch for learning:
isolated VM "qubes" on Linux + KVM, a small trusted control plane, deny-by-default
policy-checked RPC between qubes. Spec: [docs/spec.md](docs/spec.md) ·
Words: [GLOSSARY.md](GLOSSARY.md) · Decisions: [docs/adr/](docs/adr/)

**Status:** 🧠 **M1 "Brain" reached** — tickets 01+03 done (control plane + guest-agent RPC
channel), 21 tests green. Milestones: [docs/spec.md](docs/spec.md). M2 "Initial OS" (real VMs)
needs ticket 02+04 on a KVM machine. Tracker: `.scratch/os-from-scratch/issues/`

```bash
python3 -m miniqubes create personal --template fedora-40
python3 -m miniqubes start personal
python3 -m miniqubes list
python3 -m unittest discover -s tests     # verify
```

How we work here: [AGENTS.md](AGENTS.md) (ask-matt flow · docs-first per ticket ·
ponytail smallest-change rule). Background research: [docs/research/](docs/research/)
(all 215 QubesOS repos graphed + the 22 "main" repos that matter).
