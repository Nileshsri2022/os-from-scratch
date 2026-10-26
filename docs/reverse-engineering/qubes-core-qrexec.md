# RE: qubes-core-qrexec — inter-VM RPC protocol + policy engine

**Depth:** deep · **Evidence:** `evidence/qubes-core-qrexec.txt`, clone @e35f59e; files read:
`qrexec/policy/parser.py` (class inventory + `Rule`), `daemon/qrexec-daemon.c` (greps), tree.
**Maps to MiniQubes:** channel + RPC (ticket 03), `filecopy` + policy (ticket 06).

## What it is
qrexec is how any two Qubes domains talk: a client asks to run a named **service** in another
VM; a **policy** decides allow/deny/ask-the-user; bytes then flow over vchan. It is the
security heart of Qubes — the controlled hole through the isolation wall. 38.7k LOC, 195 files.

## Layout (evidence)
- `daemon/qrexec-daemon.c` (1,814 lines, C) — dom0 side, **one daemon instance per VM**;
  local clients reach it via Unix socket `/var/run/qubes/qrexec.<domid>`; it holds a
  `libvchan_t` to the VM. `daemon/qrexec-client.c` is the dom0 CLI client.
- `agent/` (C) — VM side: `qrexec-agent.c`, `qrexec-client-vm.c`, and `qrexec-fork-server.c`
  (pre-forking helper so service processes spawn fast). PAM files: services run in a real user session.
- `libqrexec/` — shared C plumbing: `ioall.c` (read/write-exactly helpers), `exec.c`, `buffer.c`, logging.
- `qrexec/policy/` (Python) — the policy engine; `parser.py` alone is 2,395 lines, plus
  `admin.py`/`admin_client.py`: policy files are editable *only* through a token-checked admin API.
- `policy.d/` + `policy.d/include/` — shipped default policies. `qubes-rpc-dom0/` — dom0's own services.
- `fuzz/`, `selinux/`, `qrexec/tests/` (incl. socket-based daemon/agent protocol tests) — every
  VM-facing parser is fuzzed.

## How it works — algorithms & data structures
- **Call path:** client → dom0 `qrexec-daemon` (per target VM) → **policy decision** (Python
  policy service) → if allowed, daemon opens vchan stream to `qrexec-agent` in the target →
  agent executes the service program (by convention `/etc/qubes-rpc/<Service>`, from
  core-agent-linux) with the stream as its stdin/stdout. Service = any executable; arguments
  after `+` in the service name are part of policy matching.
- **Policy = a small language, first-match evaluation.** A `Rule` (parser.py:1359) is
  `(service, argument, source, target, action, params)`. Sources/targets are typed tokens:
  literal VM, `AnyVM` (@anyvm), `AdminVM` (@adminvm), `TypeVM` (@type:AppVM…), `TagVM`
  (@tag:…), `DispVM`, wildcards. Actions are classes (`Allow`, `Deny`, `Ask`) each with
  `evaluate(request) -> Resolution`; `AskResolution` triggers a user prompt that may also
  redirect/remember. `AbstractPolicy.evaluate` (1838) walks rules from all loaded files
  (directory loader over `policy.d/`); unmatched ⇒ deny. Redirects (`Redirect` token) let
  dom0 silently retarget e.g. update traffic to a proxy VM.
- **Defense in depth:** C daemons do byte-moving with fixed, fuzz-tested parsing; all
  policy *judgement* is centralized in one Python evaluator; policy *edits* need the admin
  API (above), so a compromised VM cannot rewrite rules.

## Connections
Rides on **vchan-xen/vchan-socket**; serves **core-agent-linux** services; **core-admin's**
Admin API is itself exposed as qrexec services (`admin.*`) — even management goes through policy.

## Reuse vs write (MiniQubes)
Borrow as ideas: rule shape `(service, source, target, action)` + first-match + default-deny;
services as programs fed over stdio; a separate policy decision point; per-target daemon
accountability. Write ourselves (already specced): JSON RPC over vsock, ~100-line allow/deny
evaluator (tickets 03/06). Defer: `ask` (needs a trusted prompt UI), tags/types, redirects.
License: GPL (file headers; no top-level LICENSE) → **ideas only, no code reuse.**

## Limitations
Static read of policy classes + daemon greps; the binary wire format inside `libqrexec`
and the agent's full handshake were not traced line-by-line; nothing built or run.
