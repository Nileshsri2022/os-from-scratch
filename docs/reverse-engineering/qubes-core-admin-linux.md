# RE: qubes-core-admin-linux — dom0's Linux-integration grab-bag

**Depth:** survey · **Evidence:** `evidence/qubes-core-admin-linux.txt`; tree + `vmupdate/` listing.
**Maps to MiniQubes:** scattered future features, no v1 ticket.

## What it is
9.4k LOC of dom0 (AdminVM) Linux-side integration that doesn't belong in qubesd proper:
- `vmupdate/` — the VM software-update framework (agent sources for apt/dnf; dom0 asks a
  VM "do you have updates?" without trusting its answer format-blindly);
- `dom0-updates/` — **dom0 never talks to the internet**: its packages are downloaded in
  an (untrusted) update VM and verified by signature in dom0;
- `qubes-rpc/` + `qubes-rpc-policy/` — RPC services *provided by dom0 itself* and their policies;
- `file-copy-vm/`, `cpu-microcode-info/`, `dracut/` (initramfs bits), `pm-utils/` (suspend hooks).

## Idea worth stealing later
`dom0-updates`: even the trusted host's network I/O is delegated to an untrusted VM, with
cryptographic verification on return. Our equivalent post-v1: template updates fetched by
a disposable qube. No LICENSE file; treat as GPL. Tree-level analysis only.
