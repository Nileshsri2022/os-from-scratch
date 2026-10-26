# AGENTS.md — how we work in this repo

**Project:** an operating system built from scratch — one project from the
[Build Your Own X](https://github.com/codecrafters-io/build-your-own-x#build-your-own-operating-system) list,
developed here in `os-from-scratch` (kept as a single self-contained directory so it can later be
dropped into [`somecoolprojects`](https://github.com/Nileshsri2022/somecoolprojects) next to the other projects).

## The flow (ask-matt main flow: idea → ship)

Installed skills live in `.agents/skills/` (`ask-matt`, `ponytail`). Per ask-matt, work travels:

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
doc is closed out with what actually happened (boot evidence, shortcuts taken).

Ticket doc template: Goal → Concepts → Design → Steps → Verify → Result & shortcuts.

## Ponytail rule (lazy senior dev mode)

The smallest change that fully solves the ticket. Before writing anything, walk the ladder:
does it need to exist → already here → platform/stdlib → installed dependency → one line →
minimum code that works. No abstractions or "for later" code nobody asked for. A shortcut with
a known limit gets a comment: `shortcut: <limit>, <when to upgrade>`. Every change leaves one
check behind (for an OS: it builds warning-free and boots in QEMU to the expected screen).

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

- Code must build with `-Wall -Wextra` clean (or Rust equivalent) before a ticket closes.
- Boot evidence (QEMU screenshot/serial log) is attached to the ticket doc.
- Known sandbox gap: no QEMU/NASM/Rust preinstalled here; P0 (scaffold) resolves the toolchain
  or states exactly which commands the owner runs locally.

## Layout

```
.
├── AGENTS.md                 ← this file
├── GLOSSARY.md               ← created by the grilling session
├── docs/
│   ├── proposal.md           ← the plan being agreed right now
│   ├── spec.md               ← after grilling
│   ├── adr/                  ← architecture decision records
│   └── reverse-engineering/  ← REA-style reports (permitted targets only)
├── .scratch/os-from-scratch/issues/   ← tickets, blockers-first
├── .agents/skills/           ← ask-matt, ponytail (installed via `npx skills add`)
├── miniqubes/                ← the OS control plane (core, backends, channel, policy, cli)
├── guest/                    ← code that runs inside qubes (guest agent)
└── tests/                    ← stdlib unittest suite (must stay green)
```
