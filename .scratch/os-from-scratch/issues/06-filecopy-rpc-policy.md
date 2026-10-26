# 06 — `filecopy` RPC + policy v0 (deny by default)

Blocked by: 03 · Status: todo

## Goal
`mq filecopy <src-qube>:<path> <dst-qube>:<dir>` copies a file guest→guest **only if policy
allows** that (source, service, target) triple. This is the qrexec moment: useful *and* safe.

## Concepts
Policy as data, not code; confused-deputy risks (agent must not let callers escape the
destination dir); streaming with size caps; audit line per decision.

## Design
- Policy file `~/.config/miniqubes/policy.json`: list of `{src, service, dst, allow}` rules,
  first match wins, **default deny**. `*` wildcards allowed per field.
- `Core.call` gains a policy check before dialing (ticket 03's call path); denial → QubesError + log line.
- `filecopy` service in agent: read file (source side) / write file (dest side, basename only,
  into `~/QubesIncoming/<src>/`), 64 MiB cap v1, sha256 verified end-to-end.

## Steps
- [ ] Policy loader + check + tests (allow, deny-default, wildcard, first-match)
- [ ] filecopy both sides + hash check + cap test
- [ ] CLI `mq filecopy`; loopback end-to-end test (two agents, one policy)

## Verify
Policy tests green; loopback copy succeeds with allow-rule, fails closed without it;
tampered hash → error, no partial file.

## Result
(filled on completion)
