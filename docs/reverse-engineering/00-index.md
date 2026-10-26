# Reverse-engineering index — all main targets (2026-10-26)

Owner instruction: *"step by step first do all reverse-engineer then docs."* This is the docs
step. 25 targets were cloned and analyzed: the **22 Tier B "main" QubesOS repos** plus the 3
classic candidates. Raw per-repo evidence: [`evidence/`](evidence/) (generator:
[`collect_evidence.py`](collect_evidence.py)). Nothing was built or executed — static analysis
only; each report states its depth and limitations.

## Method & the REA question (answered with evidence)
REA's own routing (skill v49) says: *for a complete source repository, use normal repository
tools; REA engines are for shipped binaries/runtime behavior.* Verified empirically here:
`rea-agents capabilities` shows no usable native provider in this sandbox (Ghidra/Hopper/IDA
absent — `rea doctor`), and `rea analyze <qubesdb source tree>` only runs its JavaScript-app
inventory (0 files) — it is not a C/Python source analyzer. So this pass applies REA's
**Evidence discipline** (every claim traces to `evidence/*.txt` or a named file read) with
repository tools, exactly as REA prescribes. Binary-level REA (e.g., against a Qubes ISO)
remains available later on the owner's machine after `npx rea-agents setup` + Ghidra.

**Licensing stance:** Qubes core is GPL/LGPL (several repos lack a top-level LICENSE;
headers confirm GPL). Therefore: **architecture and ideas only — zero code copied.**
Classics are permissive (BSD-3 / MIT / MIT+Apache).

## All 25 targets
| Target | Depth | One-line verdict | MiniQubes link |
|---|---|---|---|
| [qubes-core-qrexec](qubes-core-qrexec.md) | deep | RPC over vchan; policy is a small first-match language (allow/deny/**ask**), services = stdio programs | tickets 03, 06 |
| [qubes-core-admin](qubes-core-admin.md) | medium | qubesd: property+event framework, VM class tree, storage pool drivers (file/LVM/reflink/ZFS) | `core.py` (01–02) |
| [qubes-core-admin-client](qubes-core-admin-client.md) | medium | library-first client; ~30 thin `qvm-*` tools; event subscription over polling | `cli.py` |
| [qubes-core-agent-linux](qubes-core-agent-linux.md) | medium | in-VM services; filecopy receiver *validates every path* (sender = hostile) | guest agent (03, 06) |
| [qubes-core-qubesdb](qubes-core-qubesdb.md) | medium | per-VM config DB; doubly-linked list store + watches — tiny on purpose | config push (03, deferred) |
| [qubes-core-vchan-xen](qubes-core-vchan-xen.md) | medium | socket-like stream over Xen grant rings; poll-able fd | vsock channel (03) |
| [qubes-core-vchan-socket](qubes-core-vchan-socket.md) | survey | same API over Unix sockets → dev/tests without Xen | validates ADR-0003 |
| [qubes-gui-daemon](qubes-gui-daemon.md) | medium | dom0 draws the window frames: unforgeable trust labels | ticket 07 (cheap version) |
| [qubes-gui-agent-linux](qubes-gui-agent-linux.md) | medium | real agent is 153KB; repo bulk = vendored PulseAudio + dummy X driver | post-v1 |
| [qubes-gui-common](qubes-gui-common.md) | survey+ | one header: metadata msgs + pixels via granted shared-memory pages | post-v1 |
| [qubes-builderv2](qubes-builderv2.md) | medium | plugin pipeline; dep-ordered builds inside disposable environments | future packaging |
| [qubes-core-admin-linux](qubes-core-admin-linux.md) | survey | dom0 odd jobs; gem: dom0 updates fetched *by an untrusted VM*, verified at home | future hardening |
| [qubes-linux-template-builder](qubes-linux-template-builder.md) | survey | assemble→inject agent→scrub identity→ship template as RPM | ticket 04 |
| [qubes-installer-qubes-os](qubes-installer-qubes-os.md) | survey | Anaconda data/kickstarts — plumbing, not invention | non-goal |
| [qubes-mgmt-salt ×8](qubes-mgmt-salt.md) | survey | Salt config-as-code; default qube set declared as pillar data | post-v1 `apply` |
| [os-tutorial](os-tutorial.md) | survey | 25 lessons BIOS→shell; the classic ramp | reference |
| [xv6-riscv](xv6-riscv.md) | survey+ | complete Unix in ~13k LOC; simplicity as a discipline | reference |
| [blog_os](blog_os.md) | survey | the blog, not the kernel; staged-allocator teaching pattern | reference |

## Cross-cutting findings (what "this algo, using this, using that" adds up to)
1. **Three-layer inter-VM stack, cleanly separated:** transport (vchan streams) → RPC +
   policy (qrexec) → services (executables fed via stdio). Our spec already mirrors this
   (vsock → channel → agent services) — upstream validates the shape.
2. **Policy is a language, not a list:** typed tokens (@anyvm/@type:/@tag:), an `ask`
   action with user prompt, redirects. Our ticket-06 JSON allow/deny is a correct v0 subset;
   `ask` is the natural v1.1 once a trusted prompt exists.
3. **Configuration is its own channel** (QubesDB with watches), separate from RPC. We merged
   it into the agent channel — fine until live config changes exist; revisit trigger is clear.
4. **Every VM-facing parser is fuzzed** (`fuzz/` in qrexec and qubesdb) and written to be
   boring. Adopt for ticket 03: frame-size caps + a fuzz-ish malformed-input test.
5. **Trust is rendered by the host:** dom0-drawn window borders. Our `[qube]` SPICE title
   (ticket 07) is the deliberate $5 version — same invariant, less pretty.
6. **Upstream also develops without the hypervisor** (vchan-socket; socket-based qrexec
   protocol tests). ADR-0003's FakeBackend-first is their pattern, not our hack.
7. **Small data structures win:** linked-list config DB, fixed proc table (xv6), bump
   allocator first (blog_os + os-tutorial). Ponytail is, empirically, how these systems started.
8. **Repo size ≠ importance** (again): gui-agent's 320k LOC is vendored PulseAudio; the
   security-critical agent code across Qubes fits in a few C files + one Python policy engine.

## Recommended folds into our docs (NOT applied yet — awaiting your yes)
- Ticket 03: add explicit verify items — length-capped frames, malformed-frame fuzz test,
  one service = one handler function named like upstream (`ping`, `info` → later `filecopy`).
- Ticket 06: policy rule shape confirmed; add path-component validation step (from
  qfile-unpacker) to Design; record `ask` + `@anyvm` as named post-v1 extensions.
- Ticket 04: add the "scrub identity" checklist (machine-id, ssh keys, logs) from template-builder.
- Spec: add a "post-v1 candidates" line: config-watch service (QubesDB idea), `mq apply`
  default-qube set (mgmt-salt idea), seamless GUI (gui protocol) — as named non-goals with triggers.

## ✅ Develop using this? — YES (owner, 2026-10-26)
Answered: *"ok start but with using ask-matt flow docs then implement using rea."*
The 4 deltas above are folded into `docs/spec.md` (milestones + post-v1 candidates) and
tickets 03/04/06; implementation proceeds ticket-by-ticket per the ask-matt flow
(docs → implement with TDD → code-review), starting with ticket 03.
