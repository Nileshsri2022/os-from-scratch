# 06 — `filecopy` RPC + policy v0 (deny by default)

Blocked by: 03 · Status: **done** (2026-10-26)

## Goal
`mq filecopy <src-qube>:/abs/path <dst-qube>` copies a file guest→guest **only if policy
allows** that (source, service, target) triple. The file always lands in
`~/QubesIncoming/<src>/` on the destination — the caller does **not** get to choose the
directory (that refusal is the upstream safety property, kept deliberately).
This is the qrexec moment: useful *and* safe.

## Concepts
Policy as data, not code; confused-deputy risks (agent must not let callers escape the
destination dir); streaming with size caps; audit line per decision.

## Design
- Policy file `~/.config/miniqubes/policy.json` (`MINIQUIBES_POLICY` overrides; used by tests):
  list of `{src, service, dst, allow}` rules, first match wins, **default deny**.
  `*` wildcards allowed per field. Host-originated `Core.call` uses source token `host`.
  **Bootstrap:** file missing → built-in defaults (`host` may `ping`/`info`, everything else
  denied — mirrors upstream shipped `policy.d`); file present → it is authoritative.
- `Core.call` gains a policy check before dialing (ticket 03's call path); denial → QubesError + log line.
- Transfer: **host-mediated chunked relay** — Core streams 256 KiB chunks (`filecopy.read`
  on src agent → `filecopy.write` on dst agent) over the ticket-03 channel, so the 64 MiB
  file cap survives the channel's 1 MiB frame cap. (Upstream qrexec data also transits dom0
  daemons.) Destination writes a temp file, verifies sha256, then atomically renames —
  failed transfers leave no partial file.
- `filecopy` service in agent: read file (source side) / write file (dest side, basename only,
  into `~/QubesIncoming/<src>/`), 64 MiB cap v1, sha256 verified end-to-end.
  **Path safety (RE: qubes-core-agent-linux `qfile-unpacker`/`qubes-fs-tree-check`):** the
  receiver validates *every* path component — reject `..`, absolute paths, and symlinks —
  and writes nothing outside the incoming dir. The sender is treated as fully hostile.

Named post-v1 extensions (RE: qrexec policy language): `ask` action (needs a trusted prompt
UI), `@anyvm`/`@type:`/`@tag:` tokens, target redirects. v1 policy = literal names + `*`,
allow/deny, first-match, default deny — recorded here so the upgrade seam is deliberate.

## Steps
- [x] Policy loader + check + tests (allow, deny-default, wildcard, first-match)
- [x] filecopy both sides + hash check + cap test
- [x] CLI `mq filecopy`; loopback end-to-end test (two agents, one policy)

## Verify
Policy tests green; loopback copy succeeds with allow-rule, fails closed without it;
tampered hash → error, no partial file.

## Result (2026-10-26)
Shipped as designed: `miniqubes/policy.py` (`Rule`/`Policy`/`Policy.load` + bootstrap
defaults), `guest/agent.py` (`make_filecopy_handlers(home)` → `filecopy.read/write`),
`QubesCore.filecopy` (+ `_policy_check`, used by `call` too with source `host`),
`FILECOPY_CHUNK`/`FILECOPY_MAX` in `channel.py`, CLI `filecopy SRC:/abs/path DST`.
Ticket 03's `test_core_call.py` made policy-hermetic (env-pointed nonexistent file).

Evidence — TDD red (2 import errors only) → green: **36 tests OK** (21 old + 15 new:
policy decide/load/malformed/bootstrap; copy allow/deny/multi-chunk/tamper/no-partial;
handler path attacks `../`, absolute, nested, bad src token; oversize read; CLI e2e).
Live demo (two agent processes, separate $HOMEs):
```
$ python3 -m miniqubes filecopy work:/tmp/mq6/work/notes.txt vault
policy denied: work --filecopy--> vault        # audit log line
error: policy denied: work --filecopy--> vault # exit 1, nothing created
$ # write policy.json (host ping/info + work--filecopy-->vault), retry:
copied notes.txt (26 bytes, sha256 6bc6260b5536…) work -> vault:/tmp/mq6/vault/QubesIncoming/work/notes.txt
$ sha256sum work/notes.txt vault/QubesIncoming/work/notes.txt   # identical
```

### Code review (self, ask-matt two-axis)
- **Standards:** stdlib only, no new deps; shortcuts labelled below; suite green; one
  deliberate semantics choice surfaced & documented (present policy file *replaces*
  bootstrap defaults — tested).
- **Spec:** every Verify item evidenced, incl. "no partial file" (tamper test asserts the
  incoming tree is empty, `.part` included).
- **Findings caught while writing/reviewing:**
  1. Base64 decode moved inside the write handler's try-block so a corrupt mid-transfer
     chunk aborts (temp deleted) instead of leaking transfer state.
  2. Final `os.replace` onto a pre-planted symlink replaces the link itself rather than
     following it; incoming dirs are additionally symlink-checked before use.
  3. Demo hygiene (not code): a stale ticket-03 demo agent still owned :27000, so the
     first demo attempt got "unknown service" — diagnosed via its bind-error log, re-ran
     with PID-managed agents. Sandbox `&` jobs outlive shells; recorded here for next time.

Shortcuts taken:
- `shortcut: host relay holds each chunk in Core memory (same topology as qrexec via dom0); direct streaming when a guest-initiated channel exists`
- `shortcut: one connection per chunk (rpc_call); keep-alive channel when copies get big/often`
- `shortcut: source-side read trusts the host CLI user's explicit path — per-file guest consent is the policy 'ask' extension (post-v1)`
- `shortcut: whole-file sha256 pass on first read (bounded by the 64 MiB cap); incremental hashing if the cap grows`
