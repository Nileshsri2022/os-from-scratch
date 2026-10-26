# MiniQubes

Our Qubes-like OS built from scratch: one trusted Linux **Host**, many isolated
**qubes** for separate areas of life, and the smallest control plane that can
keep them apart. One shared vocabulary — every doc, ticket, and commit uses
these words with these meanings. (Upstream Qubes equivalents are mapped in
`docs/spec.md` → Components.)

## Language

**Qube**:
One VM compartment dedicated to a single security domain/purpose (e.g.
`personal`, `vault`, `untrusted`). The unit of isolation and of daily use.
_Avoid_: VM, container, sandbox

**Host**:
The trusted Linux machine running the control plane and the desktop; together
with the hypervisor it is the trusted computing base.
_Avoid_: dom0, hypervisor host

**Admin daemon**:
The trusted authority on the Host that owns the qube registry and every
lifecycle decision. The only thing allowed to create, start, or stop qubes.
_Avoid_: manager, orchestrator, server

**Core**:
The Admin daemon's decision-making part: lifecycle rules and validation,
expressed against a Backend, never against a concrete hypervisor.
_Avoid_: controller, engine

**Backend**:
The hypervisor-facing part beneath Core that actually creates, starts, and
stops qubes. Two exist: the real one (libvirt/KVM) and a fake for development
on machines without KVM.
_Avoid_: driver, hypervisor layer

**Template**:
A read-only root filesystem image that AppQubes boot from, so many qubes share
one OS install.
_Avoid_: base image, master image

**AppQube**:
A qube whose root filesystem comes from a Template via copy-on-write. Only its
private data (home) persists across reboots.
_Avoid_: AppVM, clone

**Guest agent**:
The small program running inside a qube that answers RPC requests on that
qube's behalf.
_Avoid_: in-guest daemon, helper

**Channel**:
The single communication path between the Host and a qube's Guest agent,
carrying RPC requests and replies.
_Avoid_: socket, pipe, vchan

**RPC service**:
A named operation one qube may request of another (or the Host of a qube) over
the Channel, e.g. `filecopy`. Every call is checked against Policy.
_Avoid_: command, endpoint

**Policy**:
The set of rules that decides, for each (source qube, RPC service, target
qube), allow or deny. Anything not allowed is denied.
_Avoid_: ACL, firewall rules

Words deliberately **not** ours yet (NetQube, Disposable, seamless GUI) live in
`docs/spec.md` non-goals; terms enter this glossary when a ticket adopts them.
