# RE: qubes-gui-daemon — dom0 side of the seamless GUI

**Depth:** medium · **Evidence:** `evidence/qubes-gui-daemon.txt`; tree of `gui-daemon/`, `shmoverride/`.
**Maps to MiniQubes:** ticket 07's cheap ancestor (our SPICE window title = trust label).

## What it is
Per-VM daemon in dom0 (12.3k LOC, C, GPL) that receives the GUI protocol and renders each
remote window as a real local X window — with the **frame and title drawn by dom0**, so a
compromised VM cannot fake another VM's window decoration. That unforgeable border is the
user-visible root of Qubes' security story.

## Layout (evidence)
- `gui-daemon/xside.c` — the X11 side: window creation/mapping, input forwarding, damage
  repaint from granted pages; `trayicon.c` (per-VM tray), `png.c` (window icons),
  `guid.conf`, `qubes.ClipboardPaste.policy` (clipboard is an RPC-policy decision too).
- `shmoverride/` — interposition library for MIT-SHM edge cases; `screen-layout-handler/`
  and `window-icon-updater/` — Python helpers (`qubesguidaemon/` package).
- `pulse/` — dom0-side audio configuration glue (audio rides its own path, see gui-agent).

## Reuse vs write
The one idea we take for v1, already in ticket 07: **the host, never the guest, labels the
window** — SPICE/VNC window titled `[<qube>]` by our launcher is the $5 version of dom0's
colored borders. Full protocol implementation: post-v1, only if ever. GPL → ideas only.

## Limitations
Component roles from layout; `xside.c` event handling and the shm grant/ungrant lifecycle
not line-traced.
