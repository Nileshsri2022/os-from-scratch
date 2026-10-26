# RE: qubes-gui-common — the GUI protocol definition (one header)

**Depth:** survey+ · **Evidence:** `evidence/qubes-gui-common.txt`; `include/qubes-gui-protocol.h` (structs, defines).
**Maps to MiniQubes:** post-v1 only (ticket 07 uses SPICE instead).

## What it is
The whole seamless-GUI wire protocol as a single shared C header (repo total: 765 LOC,
mostly packaging). Both gui-daemon (dom0) and gui-agent (VM) compile against it.

## Protocol shape (evidence: header)
- Every message: `struct msg_hdr` + typed payload — `msg_create`, `msg_configure`,
  `msg_resize`, `msg_map_info`, `msg_keypress`, `msg_button`, `msg_motion`, `msg_crossing`,
  `msg_focus`, `msg_shmimage`, `msg_window_dump_hdr`.
- **Pixels don't travel through the pipe:** window contents move via shared memory pages
  (`QUBES_MAX_MSG_WINDOW_DUMP_LEN` computed from `MAX_GRANT_REFS_COUNT` grant references);
  messages carry geometry/events/metadata only.
- **Versioned by feature gates:** `QUBES_GUID_MIN_*` constants (bidirectional negotiation,
  window-dump ACK, clipboard format v4…) — old agents keep working with new daemons.

## Reuse vs write
If seamless GUI ever happens post-v1, the transferable ideas are: metadata-channel +
shared-memory pixels, damage-region updates only, per-feature version negotiation.
Until then: reference only. No LICENSE file; treat as GPL.

## Limitations
Header-level; input-event semantics and clipboard sub-protocols not traced.
