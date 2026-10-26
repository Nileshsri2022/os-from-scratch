# RE: qubes-core-admin-client — Admin API library + qvm-* tools

**Depth:** medium · **Evidence:** `evidence/qubes-core-admin-client.txt`; `qubesadmin/` +
`qubesadmin/tools/` listings. **Maps to MiniQubes:** our `cli.py` over `core.py`.

## What it is
The client half of the Admin API: a Python library (`qubesadmin`, 55k LOC incl tests/docs,
LGPL) plus ~30 thin command line tools on top of it.

## Layout (evidence)
- `qubesadmin/app.py` — the `Qubes` client (connects to qubesd via qrexec Admin API from
  dom0 or a management VM); mirrored object model in `vm/`, `firewall.py` (rule objects),
  `devices.py` + shared `device_protocol.py`, `label.py`, `features.py`.
- `qubesadmin/events/` — subscribes to qubesd's event stream (property changes, VM
  start/stop) — how GUI widgets stay live without polling.
- `qubesadmin/tools/` — one module per command: `qvm_create, qvm_clone, qvm_start,
  qvm_shutdown, qvm_kill, qvm_pause/unpause, qvm_remove, qvm_ls, qvm_run, qvm_prefs,
  qvm_pool, qvm_tags, qvm_template, qvm_backup(_restore), qvm_device, qvm_firewall,
  qvm_features, qvm_service, qvm_check…`
- `backup/` — client side of the backup/restore protocol.

## Ideas that matter for us
**Library first, tools thin** — each `qvm-*` is argparse + one library call (exactly our
`cli.py` shape, just split into many binaries instead of subcommands). **Events over
polling** for any future GUI/watch mode. Client can run *outside* dom0 (mgmt VM) because
the API is policy-checked RPC — the same trust story as qrexec.

## Reuse vs write
Borrow: library-first CLI design (already ours), event subscription as a later ticket if a
watcher is ever needed. One-binary subcommands vs qvm-*: keep ours (single entry point,
less packaging). LGPL → ideas only.

## Limitations
File/class inventory level; wire encoding of Admin API calls (in `app.py`/`base.py`) not traced.
