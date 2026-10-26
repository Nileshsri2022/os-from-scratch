# 05 — Networking v1: host NAT, qubes isolated from each other

Blocked by: 02 · Status: todo

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

## Steps
- [ ] Network XML + create-time attach + README host setup (one-time `virsh net-define`)
- [ ] Inter-qube drop rule
- [ ] Owner verify: `personal` pings 1.1.1.1 ✅, pings `vault`'s IP ❌

## Verify
The two pings above; `mq list` unchanged (network is backend detail).

## Result
(filled on completion)
