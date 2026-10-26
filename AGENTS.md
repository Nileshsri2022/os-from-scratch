# AGENTS.md — how we work in this repo

**Project:** an operating system built from scratch — one project from the
[Build Your Own X](https://github.com/codecrafters-io/build-your-own-x#build-your-own-operating-system) list,
developed here in `os-from-scratch` (kept as a single self-contained directory so it can later be
dropped into [`somecoolprojects`](https://github.com/Nileshsri2022/somecoolprojects) next to the other projects).

## The flow (ask-matt main flow: idea → ship)

Installed skills live in `.agents/skills/` (`ask-matt`, `ponytail`, `reverse-engineer-anything`).
Per ask-matt, work travels:

1. **Research first** — facts are the agent's job. Findings go in `docs/` as cited Markdown
   (e.g. popularity survey, reverse-engineering reports).
2. **Grill** — the agent interviews the user on every open decision before building.
   Output: `GLOSSARY.md` (shared vocabulary) + `docs/adr/` (one file per hard-to-reverse decision).
3. **Spec** — `docs/spec.md`: what we are building, in the glossary's words.
4. **Tickets** — spec split into tracer-bullet tickets in `.scratch/os-from-scratch/issues/`,
   one file per ticket, each naming its blocking tickets. Smallest end-to-end slice that boots.
5. **Implement per ticket** — see the docs-first rule below.

## Docs-first rule (project owner requirement)

Every ticket gets its document **before** code: goal, concepts, design (algorithms & data
structures), steps, how we verify. The doc is written/updated first, then the code, then the
doc is closed out with what actually happened (demo evidence, shortcuts taken).

Ticket doc template: Goal → Concepts → Design → Steps → Verify → Result & shortcuts.

## Ponytail rule (lazy senior dev mode)

The smallest change that fully solves the ticket. Before writing anything, walk the ladder:
does it need to exist → already here → platform/stdlib → installed dependency → one line →
minimum code that works. No abstractions or "for later" code nobody asked for. A shortcut with
a known limit gets a comment: `shortcut: <limit>, <when to upgrade>`. Every change leaves one
check behind (here: the unit suite stays green and the ticket's CLI demo works).

## Reverse-engineering rule (REA)

Reverse engineering happens **only** on a project the owner names, **only** after explicit
permission, following the [REA](https://github.com/morluto/rea) discipline: inspect → explain
how it works **with evidence** → state limitations. Report lands in
`docs/reverse-engineering/<target>.md` covering: architecture, algorithms, data structures,
build system, and "what we would reuse vs. write ourselves". After the report, the agent asks
"develop using this?" and waits for a yes before any implementation borrows from it.

REA status (2026-10-26): `reverse-engineer-anything` skill installed in `.agents/skills/`;
the `rea-agents` CLI runs in the sandbox, but `rea doctor` reports **not ready for native
binaries** (no Ghidra/Hopper/IDA here — those install on the owner's machine via
`npx rea-agents setup`). REA's own guidance applies: for complete **source** repositories use
normal repository analysis (our evidence-backed reports); reserve REA engines for shipped
binaries/artifacts (installer ISOs, kernel ELFs) and runtime behavior.

## Verification

- `python3 -m unittest discover -s tests` must be green before a ticket closes (Python,
  stdlib-only — ADR-0002; new dependency needs an ADR).
- Each ticket's **Result** carries its evidence: TDD red→green, a CLI demo transcript,
  self code-review notes, and any `shortcut:` taken.
- Known sandbox gap: no `/dev/kvm`, QEMU, or libvirt here → tickets needing real VMs
  (02/04/05/07) close only on the owner's KVM machine, following the ticket's verify
  checklist and its runbook under `docs/guides/`.

## Layout

```
.
├── AGENTS.md                 ← this file
├── GLOSSARY.md               ← shared vocabulary (grill-with-docs output)
├── docs/
│   ├── proposal.md           ← the original agreed plan
│   ├── spec.md               ← MiniQubes v1 spec (to-spec output)
│   ├── STATUS.md             ← step-by-step tracker (what's done / what's next)
│   ├── adr/                  ← architecture decision records
│   ├── agents/               ← skill config: issue tracker + domain doc rules
│   ├── guides/               ← runbooks (e.g. ticket 02 on the owner's machine)
│   ├── research/             ← surveys + the 215-repo graph
│   └── reverse-engineering/  ← REA-style reports (permitted targets only)
├── .scratch/os-from-scratch/issues/   ← tickets, blockers-first
├── .agents/skills/           ← ask-matt, ponytail, REA (via `npx skills add`)
├── miniqubes/                ← the OS control plane (core, backends, channel, policy, cli)
├── guest/                    ← code that runs inside qubes (guest agent)
└── tests/                    ← stdlib unittest suite (must stay green)
```

## Agent skills

### Issue tracker

Local markdown: one file per ticket under `.scratch/os-from-scratch/issues/`; the spec
lives at `docs/spec.md`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `GLOSSARY.md` at the repo root + `docs/adr/`. See `docs/agents/domain.md`.
