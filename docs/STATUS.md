# STATUS — MiniQubes, step by step (updated 2026-10-26)

One page that answers: *what has been done, in what order, what is completed, what is left.*
Workflow: ask-matt main flow (research → grill-with-docs → spec → tickets → implement per
ticket with TDD + code-review), ponytail for coding, REA discipline for reverse-engineering.

## The flow, step by step

| # | Step (ask-matt) | What happened | Status |
|---|---|---|---|
| 0 | Setup | Skills installed (`ask-matt`, `ponytail`); `AGENTS.md` workflow written | ✅ PR #1 |
| 1 | Research (`/research`) | Popularity survey of OS-from-scratch projects; all **215 QubesOS repos** classified into 16 families + interactive graph; tier analysis found the **22 "main" (Tier B) repos** | ✅ PR #1 |
| 2 | REA setup | `reverse-engineer-anything` skill installed; `rea-agents` CLI + `rea doctor` run (native engines absent in sandbox — expected) | ✅ PR #2 |
| 3 | Reverse-engineering | 25 targets (22 Tier B + os-tutorial/xv6/blog_os): evidence + 17 reports + index in `docs/reverse-engineering/` | ✅ PR #2 · **coverage re-audited 2026-10-26** (live org diff: 215=215, zero drift; all Tier B covered — [proof](research/coverage-audit-qubesos-org.md)) |
| 4 | Grill-with-docs | `GLOSSARY.md` + ADR-0001 (Qubes-like on Linux+KVM), ADR-0002 (Python), ADR-0003 (Backend/fake-first) | ✅ PR #2 |
| 5 | To-spec | `docs/spec.md` incl. milestones M1–M3 | ✅ |
| 6 | To-tickets | 7 tracer-bullet tickets with blockers (`.scratch/os-from-scratch/issues/`) | ✅ |
| 7 | Implement ticket 01 | Core lifecycle + FakeBackend + CLI (9 tests) | ✅ done |
| 8 | Implement ticket 03 | Guest agent + RPC channel (M1 "Brain") | ✅ done |
| 9 | Implement ticket 06 | Policy engine + secure filecopy (36 tests total) | ✅ done |
| 10 | Implement ticket 02 | LibvirtBackend — real KVM VMs | 🔶 **code done + 14 fake-libvirt unit tests (sandbox, 2026-10-26)**; real-VM verification still ⏳ **owner's machine** — guide: `docs/guides/02-libvirt-backend-guide.md` Steps 1–3 + 5–6 |
| 11 | Implement ticket 04 | Template CoW clones (`qemu-img` backing files + `tools/make-template.sh` recipe) | 🔶 **sandbox slice done (2026-10-26)** — code + 53 tests green; golden image + isolation check on **owner's machine** |
| 12 | Implement ticket 05 | Host NAT (`mq-net`) + qube↔qube isolation (`mq-isolate` nwfilter) | 🔶 **sandbox slice done (2026-10-26)** — XML files + backend attach + guard, 60 tests green; two-pings verify on **owner's machine** |
| 13 | Implement ticket 07 | SPICE window per qube (`mq open` + `graphics_uri`) | 🔶 **sandbox slice done (2026-10-26)** — XML + backend/CLI wired, 68 tests green; window verify on **owner's machine** (guide Step 9) |

## Which upstream repo did we start with, and its status

We do not modify upstream repos; we write original small **equivalents** (upstream is GPL —
ideas only). Reverse-engineering went deepest on `qubes-core-qrexec`. Development started
with the most important one — `qubes-core-admin` (the brain) — because nothing else has
meaning without it:

| Upstream main repo (of 215) | Our equivalent | Status |
|---|---|---|
| `qubes-core-admin` | `miniqubes/core.py` | ✅ v0 done (ticket 01) |
| `qubes-core-admin-client` | `miniqubes/cli.py` | ✅ v0 done (01) |
| `qubes-core-qrexec` | `miniqubes/channel.py` + `miniqubes/policy.py` | ✅ v0 done (03, 06) |
| `qubes-core-agent-linux` | `guest/agent.py` | ✅ v0 done (03, 06) |
| `qubes-core-vchan-xen` / `-socket` | kernel TCP/vsock sockets | ✅ concept (nothing to write) |
| `qubes-linux-template-builder` | `tools/make-template.sh` | 🔶 script + CoW backend done (sandbox, ticket 04); golden image = owner run |
| `qubes-core-qubesdb` | — | post-v1 (config-watch idea) |
| `qubes-gui-daemon` / `-agent-linux` / `-common` | SPICE window shortcut | ⏳ ticket 07 (seamless GUI post-v1) |
| `qubes-builderv2` | — (scripts instead) | not developing |
| `qubes-installer-qubes-os` | — | non-goal (no ISO in v1) |
| `qubes-core-admin-linux` | — (one idea taken: filecopy safety) | not developing |
| `qubes-mgmt-salt` ×8 | — | post-v1 (`mq apply` idea) |
| Remaining 193 repos | — | upstream reuse (Tier A) / deferrable (C) / meta (D) — never ours to develop |

## Milestones

- **M1 "Brain" (stages 01+03)** — ✅ reached; stage 06 also done in simulation.
- **M2 "Initial OS" (stages 01–04)** — all four stages' code now written (02 + 04 close
  only on the owner's KVM machine: real boot + CoW isolation evidence).
- **M3 "Usable" (stages 01–07)** — **all seven stages' sandbox slices now done** (05+07
  added 2026-10-26); every remaining work item is owner-machine verification.

## Numbers

Our OS code: **1020 lines of Python** (`miniqubes/` 854 + `guest/` 166); tests 1046 lines,
**68 passing**. Upstream Tier B equivalent scope: ~366k LOC. The difference is reuse
(KVM/QEMU, libvirt, Linux, distro userland) plus ponytail scope discipline.

## Is this the correct flow? — honest deviations list

Yes, with three recorded deviations:
1. **Grilling questions were skipped by the owner**, so the direction (Qubes-like, Python,
   v1 scope) was written into ADRs as a stated, reversible assumption; the owner's
   "ok start" confirmed it. Any ADR can be superseded on request.
2. **Ticket order 01 → 03 → 06** (02 skipped for now): valid per the blocker graph —
   03 and 06 do not depend on 02; 02 physically cannot run in this sandbox (no KVM),
   so it is scheduled on the owner's machine. Ticket 04's sandbox slice (2026-10-26)
   follows the same pattern: its CoW/guard logic needs no KVM to write and test —
   only to close.
3. **REA's binary engines (Ghidra/Hopper) were not run**: all targets are open-source, and
   REA's own routing prescribes evidence-backed source analysis for complete source repos.
   Binary-level REA remains available for shipped artifacts (e.g., a Qubes ISO) later.
4. **Ask-matt setup precondition was incomplete until the 2026-10-26 docs audit**:
   `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, and the `## Agent skills`
   block in `AGENTS.md` were missing, and GLOSSARY/spec predated the skill formats.
   All closed in that audit (spec gained Problem statement + User stories + Testing
   decisions; GLOSSARY moved to the prescribed format; our two deliberate convention
   deviations — spec at `docs/spec.md`, richer ticket template — are now recorded in
   `docs/agents/issue-tracker.md` instead of being silent).

Plus one process bug found & fixed 2026-10-26: ticket 01/03 `Status` fields and checkboxes
lagged their (correct) Result sections due to a parallel-edit race in the agent tooling;
both tickets now read correctly, and edits are made one file at a time.
