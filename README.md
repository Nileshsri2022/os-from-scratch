# os-from-scratch

**MiniQubes** — a Qubes-like compartmentalized OS built from scratch for learning:
isolated VM "qubes" on Linux + KVM, a small trusted control plane, deny-by-default
policy-checked RPC between qubes. Spec: [docs/spec.md](docs/spec.md) ·
Words: [GLOSSARY.md](GLOSSARY.md) · Decisions: [docs/adr/](docs/adr/)

**Status:** 🚧 ticket 01 done — control-plane skeleton (Core lifecycle + FakeBackend + CLI),
9 tests green. Real KVM backend is ticket 02. Tracker: `.scratch/os-from-scratch/issues/`

```bash
python3 -m miniqubes create personal --template fedora-40
python3 -m miniqubes start personal
python3 -m miniqubes list
python3 -m unittest discover -s tests     # verify
```

How we work here: [AGENTS.md](AGENTS.md) (ask-matt flow · docs-first per ticket ·
ponytail smallest-change rule). Background research: [docs/research/](docs/research/)
(all 215 QubesOS repos graphed + the 22 "main" repos that matter).
