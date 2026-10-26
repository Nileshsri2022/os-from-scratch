# 07 — GUI v1: SPICE/VNC window per qube (deliberate shortcut)

Blocked by: 02 (only for real-window verification; sandbox slice independent — same
pattern as 03/06/04/05) · Status: doing (sandbox slice in progress 2026-10-26; closes
only after owner-machine verification)

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

### Sandbox-slice decisions (2026-10-26, before code — docs-first)
- **SPICE over TCP localhost, not a Unix socket** (v1 ponytail): domain XML gains
  `<graphics type='spice' autoport='yes' listen='127.0.0.1'/>` — `autoport` lets libvirt
  pick a free port; we read it back from `XMLDesc` with a bounded regex (same no-XML-parser
  rule as ticket 04's Mimosa fix: `_graphics_from_xml` extracts type/port/listen).
  VNC fallback is documented, not implemented — one attribute away if SPICE ever fails.
- **Endpoint shape mirrors `agent_endpoint`:** `Backend.graphics_uri(name)` →
  `("spice", "127.0.0.1", port)` or `None`. Default in the ABC returns `None` (like
  `agent_endpoint`), so the seam (ADR-0003) stays additive.
- **Port −1 case:** a *defined but not running* autoport domain reports `port='-1'` in
  XMLDesc — `graphics_uri` returns None then; the real guard is Core's
  `_require_running` (same as `call`/`filecopy`): you cannot open a stopped qube's screen.
- **Core gains `graphics_uri(name)`** = running-guard + backend query + QubesError when
  the backend offers nothing ("no graphics endpoint"). CLI stays thin.
- **CLI `mq open <name>`:** `subprocess.run(["remote-viewer", f"--title=[{name}]",
  f"spice://{host}:{port}"])`. `remote-viewer` missing → clean error ("install
  virt-viewer"). No config option for the viewer (ponytail; PATH is the config).
- **FakeBackend:** allocates a `graphics_port` per qube at create (upward from
  `GRAPHICS_BASE_PORT = 5900`, same allocator pattern as agent ports) so `mq open` is
  end-to-end testable in simulation; port is a placeholder — no display exists.
- **shortcut (recorded):** whole-desktop window, no per-window isolation; no SPICE
  password/SASL — single-user localhost host; upgrade to gui-agent protocol post-v1
  (spec post-v1 candidates already list it).

## Steps
- [x] XML graphics + `mq open` (backend method `graphics_uri(qube)`)
      — sandbox 2026-10-26, TDD (red: 1 failure + 5 errors → green)
- [ ] Owner verify: window opens, title shows `[personal]`, desktop usable

## Verify
Screenshot/transcript on owner machine; fake backend returns a placeholder URI (unit-tested formatting only).

## Result
**Interim (2026-10-26, sandbox) — sandbox slice done, ticket NOT done.** Per the
docs-first decisions above:

- `LibvirtBackend._domain_xml` gains `<graphics type='spice' autoport='yes'
  listen='127.0.0.1'/>` (loopback only). Port read back via `_GRAPHICS_RE` (no XML
  parser — Mimosa rule); stopped autoport domains report `port='-1'` → `graphics_uri`
  returns None (modelled exactly by the fake harness).
- `Backend.graphics_uri` added to the ABC (default None, like `agent_endpoint`);
  `FakeBackend` allocates placeholder `graphics_port`s upward from 5900.
- `QubesCore.graphics_uri(name)` = running-guard + None→QubesError translation;
  CLI `mq open <name>` execs `remote-viewer --title=[<name>] spice://host:port`
  (missing viewer → clean "install virt-viewer" error, rc 1).
- Fake harness now mimics libvirt's autoport lifecycle: define-time `port='-1'`,
  real port on start — so the None-when-stopped path is tested, not assumed.

**Labelled shortcuts:** whole-desktop window, no per-window isolation; no SPICE
password/SASL (single-user localhost host); viewer is hardcoded `remote-viewer`
(PATH is the config). Real window behaviour is the owner checklist — sandbox proves
shapes, guards, and the launched argv only.

**Still required to close (owner's machine):** guide Step 9 — `mq open personal`
opens a window titled `[personal]` showing the qube desktop; screenshot into this
Result replaces the interim note.
