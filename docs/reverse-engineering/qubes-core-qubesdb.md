# RE: qubes-core-qubesdb — tiny config database between dom0 and VMs

**Depth:** medium · **Evidence:** `evidence/qubes-core-qubesdb.txt`; `daemon/qubesdb_internal.h`
structs; tree. **Maps to MiniQubes:** config push on the channel (ticket 03; deferred as its own service).

## What it is
Qubes' replacement for XenStore: a minimal path→value database (`/name`, `/qubes-vm-type`,
`/qubes-ip`…) holding per-VM configuration, with **watches** (notify me when a key changes).
Each VM gets its own daemon instance, so a VM can only ever see its own subtree.
7k LOC of C + client lib + Python bindings; systemd units `qubes-db.service` (in VM) and
`qubes-db-dom0.service`.

## Layout & data structures (evidence)
- `daemon/db-core.c` (store), `db-cmds.c` (protocol commands), `db-daemon.c` (vchan server),
  `buffer.c`; `client/qdb-client.c` + `qubesdb-cmd.c` CLI; `python/` bindings; `fuzz/` harnesses.
- **Deliberately primitive storage** (`qubesdb_internal.h`): entries are a *doubly-linked
  list* (`qubesdb_entry {prev,next}`), watches a linked list, clients a linked list.
  Lookups are linear scans — the correct algorithm when N is a few dozen keys and the code
  must be auditably tiny. (Ponytail-grade engineering, upstream.)
- Watch notification is a callback type (`send_watch_notify_t`) so dom0-side and VM-side
  transports share the core.

## Connections
core-admin writes config at VM start; agents, GUI daemon, and tools inside the VM read/watch
it. qrexec carries *commands*; QubesDB carries *configuration/state* — clean split.

## Reuse vs write
Our spec currently folds config into the agent channel (`shortcut` noted at design time).
Borrow later, verbatim as an idea only: a 100-line `config` RPC with watch semantics **if**
live config changes ever appear (they don't in v1). No code reuse (no top-level LICENSE;
treat as GPL like the rest of Qubes core).

## Limitations
Structs and file roles read; exact command opcodes (`include/qubesdb.h`) and the
multiread/rm semantics not line-traced.
