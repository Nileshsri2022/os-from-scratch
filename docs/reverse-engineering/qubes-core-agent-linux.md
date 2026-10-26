# RE: qubes-core-agent-linux — everything Qubes runs inside a Linux VM

**Depth:** medium · **Evidence:** `evidence/qubes-core-agent-linux.txt`; `qubes-rpc/` inventory; top-level tree.
**Maps to MiniQubes:** our guest agent (tickets 03, 06).

## What it is
The in-VM half of Qubes: RPC service programs, network setup, boot integration.
471 files / 22.8k LOC, but much is config (.conf, .desktop, systemd units); the security-
critical code is a handful of small C programs. GPL.

## Layout (evidence)
- `qubes-rpc/` — the services another VM may invoke (subject to qrexec policy):
  `qubes.Filecopy` → `qfile-agent.c` (sender) + `qfile-unpacker.c` (receiver) +
  `qubes-fs-tree-check.c`; `qubes.OpenInVM` → `qopen-in-vm.c` + `qubes-open`;
  `qubes.GetDate` (clock sync, `qubes-sync-clock`), `qubes.ConnectTCP`, `qubes.Backup`,
  `qubes.GetAppmenus`, `qubes.GetImageRGBA`, `qubes.DetachPciDevice`,
  `qubes.InstallUpdatesGUI`, file-manager integrations (nautilus/caja/kde).
- `network/` — vif/iptables setup for AppVM vs NetVM roles; `init/` + `boot/` — systemd
  units and early setup (private volume mount, hostname, IP from QubesDB);
  `filesystem/` — file overrides; `app-menu/` — desktop menu plumbing;
  `package-managers/` — update-check hooks; `passwordless-root/` — sudo/pam setup
  (VMs are single-user; root inside a qube is deliberately uninteresting).

## Algorithm that matters: paranoid file unpacking
Filecopy treats the sending VM as fully hostile: the stream lists a file tree, and the
receiver (`qfile-unpacker.c`, checked by `qubes-fs-tree-check.c`) validates every path
component before writing (no `..`, no absolute paths, no symlink escapes), landing files
in `~/QubesIncoming/<source>/`. The split into *separate* agent/unpacker/checker programs
is privilege separation inside the guest.

## Reuse vs write
Borrow: services as small single-purpose programs; incoming-dir convention; unpacker
paranoia (our ticket 06 already specs hash-verified, basename-only writes — add
path-component validation as an explicit step). Ours stays one Python agent for v1 —
simpler, with the split as the documented upgrade. GPL → ideas only.

## Limitations
Inventory + role level; qfile wire format (headers/checksums) and network scripts not line-read.
