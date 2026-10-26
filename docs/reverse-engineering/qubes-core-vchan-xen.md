# RE: qubes-core-vchan-xen — libvchan, the byte-stream under everything

**Depth:** medium · **Evidence:** `evidence/qubes-core-vchan-xen.txt`; API from `vchan/libvchan.h`.
**Maps to MiniQubes:** our channel over virtio-vsock (ticket 03) — same role, KVM transport.

## What it is
A socket-like, reliable, ordered byte stream between two Xen domains, addressed by
(domain, port) — port distinguishes services (qrexec, GUI, QubesDB each get one).
~3.1k LOC of C including a Windows port (`windows/src/`).

## API = the design (evidence: libvchan.h)
`libvchan_server_init(domain, port, read_min, write_min)` · `libvchan_client_init[_async]`
(async variant exposes an `EVTCHN` watch fd for event loops) · `libvchan_write/read`
(all-or-block) vs `libvchan_send/recv` (partial) · `libvchan_wait` (block until readable/
space) · `libvchan_data_ready` · `libvchan_fd_for_select` · `libvchan_is_open` · `close`.
Underneath: shared-memory ring pages (Xen grant references) + event-channel doorbells —
the standard Xen PV pattern; the API deliberately feels like a blocking fd so daemons can
poll() it alongside sockets.

## Why it matters architecturally
Everything above it (qrexec, GUI protocol, QubesDB) gets "a pipe to exactly one other
domain" with **no network stack in between** — nothing to sniff, spoof, or firewall.
Our vsock choice is the KVM-native equivalent (guest CID + port). Borrow: stream semantics,
"poll-able fd", separate ports per service family. Write: ours is `socket.AF_VSOCK` — the
kernel gives us what libvchan implements manually on Xen.

## Limitations
Header/API level; ring indexing and grant-mapping internals (`libvchan_private.h`, io.c)
not line-read. No LICENSE file; treat as GPL.
