# RE: qubes-core-vchan-socket — the same vchan API over Unix sockets

**Depth:** survey · **Evidence:** `evidence/qubes-core-vchan-socket.txt`; tree (`vchan/`, `vchan-simple/`, `tests/`).
**Maps to MiniQubes:** precedent for ADR-0003 (FakeBackend/loopback-first development).

## What it is
~3k LOC implementing the libvchan API on top of plain Unix sockets, so qrexec daemons and
agents can be developed, unit-tested, and run **without Xen** (one host, sockets named
per domain/port). Ships `run-tests` and a `tests/` suite.

## Why we care
This is upstream's own answer to "how do you test VM-interconnect code without VMs?" —
exactly the role our FakeBackend + loopback channel play in tickets 01/03. It validates
the seam: code written against a *stream pair* API, transport swapped underneath.
Borrow the pattern (already ours); no code reuse (no LICENSE file; treat as GPL).

## Limitations
Tree level only; socket naming/handshake details not read.
