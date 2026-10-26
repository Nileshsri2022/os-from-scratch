# ADR-0002: Python (stdlib-first) for the control plane and guest agent

Status: accepted (2026-10-26)

## Context
The admin daemon and guest agent are I/O-bound control-plane code: process/VM lifecycle,
socket RPC, config files. Upstream `qubes-core-admin` is Python for the same reason.
This sandbox has Python 3.11 and no Rust/C cross-toolchain requirements to satisfy.

## Decision
Python 3.11+, **standard library only** until a ticket proves a dependency is needed
(libvirt's Python bindings in ticket 02 are the first sanctioned exception, isolated
inside `LibvirtBackend`). Tests use stdlib `unittest`.

## Consequences
- Fast iteration, zero install step: `python3 -m miniqubes …` works anywhere.
- Guest images must ship python3 for the agent — true for Fedora/Debian templates.
- If a hot path ever appears (it shouldn't in a control plane), isolate and revisit then.
