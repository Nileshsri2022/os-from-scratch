# 07 — GUI v1: SPICE/VNC window per qube (deliberate shortcut)

Blocked by: 02 · Status: todo

## Goal
`mq open <qube>` pops a window into the qube's desktop. Not Qubes' seamless GUI protocol —
the whole guest desktop in one window, via SPICE (fallback VNC).

## Concepts
Why upstream's GUI protocol exists (per-window trust borders) and why it's the hardest part;
what we give up (a compromised guest can draw fake windows *inside its own window only* —
title bar must always show the qube name; that host-side label is the trust anchor).

## Design
- Domain XML (ticket 02 amendment): `<graphics type='spice'>` (or vnc), listen on Unix socket / localhost only.
- `mq open`: query backend for the graphics endpoint, exec `remote-viewer spice://… --title "[<qube>]"`.
- Document the shortcut in README:
  `shortcut: whole-desktop window, no per-window isolation — upgrade to gui-agent protocol post-v1`.

## Steps
- [ ] XML graphics + `mq open` (backend method `graphics_uri(qube)`)
- [ ] Owner verify: window opens, title shows `[personal]`, desktop usable

## Verify
Screenshot/transcript on owner machine; fake backend returns a placeholder URI (unit-tested formatting only).

## Result
(filled on completion)
