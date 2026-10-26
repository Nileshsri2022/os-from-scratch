# 04 — Templates: golden image + copy-on-write AppQubes

Blocked by: 02 · Status: todo

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
- LibvirtBackend.create: `qemu-img create -f qcow2 -b <template> -F qcow2 <qube>.qcow2`.
- Guard: starting a qube whose template file is missing → clear QubesError.

## Steps
- [ ] Recipe + one golden image on owner machine (Debian or Fedora — spec open question)
- [ ] Backend CoW create + missing-template guard (+ fake records the relationship)
- [ ] Boot two AppQubes from one template; write in one, verify invisible in the other

## Verify
`qemu-img info` shows backing file chain; isolation check above passes; disk usage ≈ template + deltas.

## Result
(filled on completion)
