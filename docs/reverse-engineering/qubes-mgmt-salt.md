# RE: qubes-mgmt-salt-* (8 repos) — configuration-as-code for the whole system

**Depth:** survey · **Evidence:** `evidence/qubes-mgmt-salt*.txt`; `dom0-virtual-machines` pillar listing.
**Maps to MiniQubes:** post-v1 ("default qubes as data"); v1 creates qubes manually via CLI.

## What the 8 repos are
One logical system split by packaging: `qubes-mgmt-salt` (Salt itself + transport config),
`-base` (core formulas + custom Salt modules), `-base-config` / `-base-overrides` /
`-base-topd` (config layering: which states apply where), `-dom0-qvm` (Salt modules that
create/configure VMs via the Admin API), `-dom0-update` (update orchestration states),
`-dom0-virtual-machines` (**the default qube set declared as data**: `pillar/qvm/*.sls`
defines sys-net, sys-firewall, sys-usb — notably as *disposable*-based service qubes —
sys-gui variants, whonix gateways, and per-feature toggles like usb-keyboard).

## How it works
`qubesctl` (dom0) runs Salt states; VM creation states call the Admin API so the *desired*
set of qubes (pillar data) converges to reality; in-VM states run over the qrexec-backed
Salt transport. First-boot setup and later reconfiguration are the same idempotent apply.

## Reuse vs write
Borrow the concept at our scale: a `defaults.json` + `mq apply` that creates the standard
qubes (net/personal/vault) idempotently — *if* setup toil ever justifies it; Salt itself
would be absurd overhead for v1. GPL-family licensing (copyright headers) → ideas only.
State files sampled, not exhaustively read.
