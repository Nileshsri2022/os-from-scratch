# 04 — Templates: golden image + copy-on-write AppQubes

Blocked by: 02 · Status: doing (sandbox slice in progress 2026-10-26 — same
simulation pattern as tickets 03/06; closes only after owner-machine verification)

## Goal
Build one golden template image; `create --template X` produces a qube whose disk is a qcow2
**backing-file clone** (instant, near-zero space until written), exactly Qubes' template trick.

## Concepts
qcow2 backing files (read from parent, write locally); why templates must be treated as
read-only while AppQubes run; private-vs-root volumes (v1: single CoW disk; persistence note).

## Design
- `tools/make-template.sh`: documented recipe (debootstrap/cloud image + agent from ticket 03
  + cloud-init off) → `templates/<name>.qcow2`. Manual but reproducible; automation later.
  **Identity scrub before sealing** (RE: qubes-linux-template-builder `cleanup_image`):
  remove `/etc/machine-id`, SSH host keys, shell histories, and logs — clones must not share
  one identity, or the compartments stop being distinguishable on the network.
- LibvirtBackend.create: `qemu-img create -f qcow2 -b <template> -F qcow2 <qube>.qcow2`
  (replaces ticket 02's plain `shutil.copyfile`). Backing format from template suffix:
  `.qcow2` → `qcow2`, `.img`/suffixless → `raw`. No `qemu-img` on PATH → clean QubesError
  ("install qemu-utils"); qemu-img failure → its stderr in the QubesError, no domain defined.
- Guard: starting a qube whose template file is missing → clear QubesError
  (`LibvirtBackend.start` checks template metadata before `dom.create()`).
  shortcut: cannot tell a plain-copy disk from a CoW clone without `qemu-img info`, so the
  guard treats every template'd qube as CoW; upgrade when a real mixed-disk fleet exists.
- FakeBackend: already records the template relationship in state (the `template` field,
  shown by `mq list`; covered by `tests/test_core.py`) — no code needed.
- Guest layout inside the golden image (fixes a latent guide-Step-5 bug): packages copied as
  `/usr/local/lib/miniqubes/` + `/usr/local/lib/guest/`, unit sets `PYTHONPATH=/usr/local/lib`
  and runs `python3 -m guest.agent --vsock 27000` — `agent.py` does
  `from miniqubes.channel import …`, which the guide's original flat copy + unit would not
  satisfy (script dir ≠ parent of the `miniqubes` package).

## Steps
- [x] Recipe + one golden image on owner machine (Debian or Fedora — spec open question)
      — script `tools/make-template.sh` + `tools/mq-agent.service` written in sandbox (2026-10-26);
      actually building/sealing the image is the owner's run
- [x] Backend CoW create + missing-template guard (+ fake records the relationship)
      — sandbox, 2026-10-26; fake already recorded the relationship (test_core) so no code there
- [ ] Boot two AppQubes from one template; write in one, verify invisible in the other

## Verify
`qemu-img info` shows backing file chain; isolation check above passes; disk usage ≈ template + deltas.
Sandbox: unit tests against a fake `qemu-img` prove the exact command shape, error paths,
and the start guard — not a real clone (same shortcut as ticket 02).

## Result
**Interim (2026-10-26, sandbox) — sandbox slice done, ticket NOT done.** TDD: red first
(4 errors + 1 failure on the new CoW/guard tests against the ticket-02 copy code), then green:

- `LibvirtBackend.create` now clones with `qemu-img create -f qcow2 -b <src> -F <fmt>
  <clone>` instead of `shutil.copyfile`; backing format from suffix (`.qcow2` → qcow2,
  `.img`/plain → raw). Clean errors: no `qemu-img` → "install qemu-utils"; qemu-img failure →
  its stderr surfaced, no domain defined, no leftover disk.
- `LibvirtBackend.start` guard: template metadata set but template disk missing → clear
  `QubesError`, `dom.create()` never runs (a vanished backing file must not be a cryptic
  qemu failure). shortcut: cannot distinguish plain-copy from CoW without `qemu-img info`;
  guard treats every template'd qube as CoW.
- `tools/make-template.sh` (bash-syntax-checked; runs on owner's Linux): base cloud image →
  `qemu-img convert` → `virt-customize`: agent packages (`miniqubes/` + `guest/`) +
  `mq-agent.service`, cloud-init masked, then the scrub (machine-id truncated, SSH host keys,
  histories, logs, journal) → sealed `templates/<name>.qcow2`.
- Guide Step 5 corrected: the manual unit's flat copy would break
  `from miniqubes.channel import …`; ready-made `tools/mq-agent.service` uses
  `PYTHONPATH=/usr/local/lib` + `-m guest.agent`. (Latent bug found while writing the script.)
- FakeBackend: already records the template relationship (`template` field, test_core
  line 21–24) — no code needed, per the docs-first design note.

**Labelled shortcuts:** fake `qemu-img` in tests proves command shape + error paths, not a
real backing-file clone; real evidence is `qemu-img info` showing the chain + the two-AppQube
isolation check on the owner's machine. Script depends on `virt-customize` (libguestfs) —
if that proves heavy on the owner machine, fallback is boot-once-and-scrub manually.

**Still required to close (owner's machine):** build the golden image
(`tools/make-template.sh debian [base.img]`), then the isolation checklist — create two
AppQubes from it, write a file in one, verify invisible in the other + `qemu-img info`
backing chain + disk usage ≈ template + deltas. That transcript replaces this interim note.
