# RE: qubes-gui-agent-linux — VM side of the seamless GUI (and a vendoring lesson)

**Depth:** medium · **Evidence:** `evidence/qubes-gui-agent-linux.txt`; per-dir sizes.
**Maps to MiniQubes:** post-v1 reference.

## What it is — and what it mostly isn't
The stats lie at first glance: 3,628 files / 320k LOC. `du` shows the truth — `pulse/` is
**19 MB of vendored PulseAudio source** (built to produce Qubes' audio module), plus a
patched `xf86-video-dummy/` Xorg driver and `pipewire/` bits. The actual agent is small:
`gui-agent/` ≈ 153 KB of C.

## How it works (structure-level)
The guest runs a real X server on the **patched dummy driver**: applications render to a
fake screen; the agent watches X window lifecycle/damage events, translates them into
gui-protocol messages, and grants the framebuffer pages to dom0 (`msg_shmimage` /
window_dump). Input flows backward as `msg_keypress/button/motion`, injected into the
guest X server. Audio is a separate, parallel hack: PulseAudio/PipeWire module streaming
to dom0 — hence the vendored trees.

## Reuse vs write
Nothing for v1 (SPICE gives whole-desktop windows for free). The transferable insight is
cost accounting: Qubes' prettiest feature rides on ~2 vendored subsystems and a fake X
driver — confirming our decision to shortcut GUI in v1 and treat seamless mode as a
research project of its own. GPL (+ vendored licenses) → ideas only.

## Limitations
Agent C code not line-read; damage-tracking algorithm inferred from protocol + structure.
