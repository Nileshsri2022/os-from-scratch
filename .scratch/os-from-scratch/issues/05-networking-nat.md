# 05 — Networking v1: host NAT, qubes isolated from each other

Blocked by: 02 (only for real-packet verification; sandbox slice independent — same
pattern as 03/06/04) · Status: doing (sandbox slice in progress 2026-10-26; closes only
after owner-machine verification)

## Goal
Qubes can reach the internet via host NAT; qubes **cannot** reach each other directly
(the only cross-qube path is RPC — ticket 03/06).

## Concepts
libvirt virtual networks + NAT; why upstream uses sys-net/sys-firewall qubes instead
(deferred: `shortcut: host does NAT/firewall, upgrade to a net qube when host TCB must shrink`).

## Design
- One libvirt network `mq-net` (NAT, e.g. 10.137.0.0/24); qube NICs attach at create (ticket 02 XML gains `<interface>`).
- Host firewall rule (nftables via libvirt nwfilter or documented host rules): drop qube↔qube forwarding on mq-net, allow qube→internet.
- Fake backend: records `net: true/false` only (no simulation of packets).

### Sandbox-slice decisions (2026-10-26, before code — docs-first)
- **Network XML** ships as `tools/mq-net.xml`: `<network>` name `mq-net`, `forward
  mode='nat'`, subnet 10.137.0.1/24 (Qubes' homage), DHCP range **10.137.0.2–254**.
- **Isolation via nwfilter, not iptables** (`tools/mq-isolate.nwfilter`): guest↔guest on
  one bridge is L2 traffic the iptables FORWARD chain never sees (unless br_netfilter is
  loaded — a host-wide behavioural change we won't make). nwfilter rules attach per-tap
  (ebtables), which is exactly the right scope. One rule drops IPv4 with dst
  **10.137.0.2–254** (`inout`), then accept-all. Dropping precisely the DHCP range keeps
  the gateway (.1: DHCP/DNS via libvirt's dnsmasq) and the internet (dst outside the
  subnet) reachable — no per-service exceptions needed.
- **Domain XML gains** `<interface type='network'><source network='mq-net'/><filterref
  filter='mq-isolate'/></interface>` — unconditional for every qube (v1: no netless qubes).
- **Create-time guard:** libvirt refuses to define a domain referencing an undefined
  network with a raw error; `LibvirtBackend.create` pre-checks
  `networkLookupByName('mq-net')` and raises a clean QubesError pointing at the README
  one-time setup. Guard runs **before** the qemu-img clone so a failed create leaves
  nothing on disk.
- **One-time host setup lives in README** (ticket step says so): `virsh
  nwfilter-define tools/mq-isolate.nwfilter` → `virsh net-define tools/mq-net.xml` →
  `virsh net-autostart mq-net`. Guide gets a short Step 8 pointing there + the verify.
- **FakeBackend** stores `"net": true` in the state row at create (mirrors "NIC attached");
  the `Qube` dataclass and `mq list` output stay untouched — network is backend detail.
- **No new env vars / CLI flags** (ponytail): network name is a class constant.

## Steps
- [x] Network XML + create-time attach + README host setup (one-time `virsh net-define`)
      — sandbox 2026-10-26: `tools/mq-net.xml`, interface attach + create-guard in
      `backends.py`, README section; the `virsh` commands themselves are the owner's
      one-time run
- [x] Inter-qube drop rule — `tools/mq-isolate.nwfilter` written in sandbox (TDD shape
      tests); effect verified on owner machine (Step 8 of the guide)
- [ ] Owner verify: `personal` pings 1.1.1.1 ✅, pings `vault`'s IP ❌

## Verify
The two pings above; `mq list` unchanged (network is backend detail).
Sandbox: XML-shape tests + create-guard + fake net flag (same shortcut as 02/04 —
shapes and calls, not packets).

## Result
**Interim (2026-10-26, sandbox) — sandbox slice done, ticket NOT done.** Docs-first
decisions above, then TDD (red: 2 failures + 3 errors; green after):

- `tools/mq-net.xml` — NAT network `mq-net`, 10.137.0.0/24, DHCP 10.137.0.2–254.
- `tools/mq-isolate.nwfilter` — drop IPv4 dst 10.137.0.2–254 `inout`, accept-all
  after; gateway + internet stay reachable without per-service exceptions (nwfilter
  chosen because same-bridge guest↔guest is L2, invisible to iptables FORWARD).
- `LibvirtBackend`: domain XML gains the `mq-net` interface + `mq-isolate` filterref
  (every qube, unconditional); `create` pre-checks `networkLookupByName('mq-net')`
  **before** the qemu-img clone — missing network = clean QubesError with the README
  setup commands, nothing left on disk (regression-tested: no domain, no clone, no
  qemu call).
- `FakeBackend.create` records `"net": true`; `Qube`/`mq list` unchanged (asserted by
  test — network must not leak into the model).
- README gained the one-time host setup; guide gained Step 8 (the two-pings verify).

**Labelled shortcuts:** sandbox tests prove XML shapes, the guard, and recorded state —
not packets (same shortcut as 02/04). Per-qube net on/off does not exist (v1: all qubes
on `mq-net`). Filter drops the whole DHCP range statically — if the subnet ever changes,
both XML files change together (they are the single source, no code holds the IPs).

**Still required to close (owner's machine):** README one-time setup, then guide Step 8:
`personal` pings 1.1.1.1 ✅, pings `vault`'s IP ❌, `virsh nwfilter-list` shows
`mq-isolate`. That transcript replaces this interim note.
