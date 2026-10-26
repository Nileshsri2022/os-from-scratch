# 01 — Project skeleton: Core lifecycle + FakeBackend + CLI

Blocked by: — · Status: **done** (2026-10-26)

## Goal
`python3 -m miniqubes create/list/start/stop/remove` works end-to-end against a simulated
hypervisor, with all lifecycle rules unit-tested. This is the tracer bullet: CLI → Core → Backend.

## Concepts
Control plane vs hypervisor; why upstream separates qubesd from Xen/libvirt; state machine
(`stopped → running → stopped`, remove only when stopped); deny-by-default naming/validation.

## Design
- `miniqubes/core.py`: `Qube` dataclass (`name`, `template`, `state`), `QubesError`,
  `QubesCore` with all rules (name regex, duplicate check, transition check). No hypervisor imports.
- `miniqubes/backends.py`: `Backend` ABC (create/start/stop/remove/get/list);
  `FakeBackend` persists to a JSON state file (`MINIQUIBES_STATE` env, else
  `~/.local/state/miniqubes/fake.json`) so separate CLI runs share one world.
- `miniqubes/cli.py` + `__main__.py`: argparse subcommands; human table for `list`;
  errors → stderr + exit 1.
- `tests/`: stdlib `unittest` — Core rules via FakeBackend on a temp file; one CLI smoke test.

## Steps
- [x] Write code + tests
- [x] `python3 -m unittest discover -s tests -v` green
- [x] CLI demo transcript → paste into Result

## Verify
Tests pass; demo shows: create `personal` (template `fedora-40`) + `vault`, start `personal`,
`list` shows one running/one stopped; duplicate create and stop-of-stopped fail cleanly.

## Result (2026-10-26)
Shipped as designed: `miniqubes/{__init__,__main__,core,backends,cli}.py` + `tests/` (9 tests).

Evidence — `python3 -m unittest discover -s tests -v` → **9 tests OK** (lifecycle rules,
invalid names, persistence across backend instances, CLI transcript). Demo:
```
$ python3 -m miniqubes create personal --template fedora-40
created qube 'personal' (template: fedora-40)
$ python3 -m miniqubes create vault && python3 -m miniqubes start personal
created qube 'vault' / started qube 'personal'
$ python3 -m miniqubes list
NAME                 TEMPLATE             STATE
personal             fedora-40            running
vault                -                    stopped
$ python3 -m miniqubes create vault        # stderr: error: qube already exists: 'vault'  (exit 1)
$ python3 -m miniqubes remove personal     # stderr: error: stop qube before removing it (exit 1)
```

Shortcuts taken:
- `shortcut: FakeBackend only in CLI, LibvirtBackend + selection lands in ticket 02`
- `shortcut: whole-file JSON state, no locking — fine for single-user CLI; revisit if a daemon owns state (ticket 03+)`
