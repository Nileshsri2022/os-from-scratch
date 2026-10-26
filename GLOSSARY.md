# GLOSSARY — MiniQubes (working name for our OS)

One shared vocabulary. Every doc, ticket, and commit uses these words with these meanings.

| Term | Meaning | Upstream Qubes equivalent |
|---|---|---|
| **Qube** | One VM compartment dedicated to a single security domain/purpose (e.g. `personal`, `vault`, `untrusted`). The unit of isolation and of daily use. | qube / VM |
| **Host** | The trusted Linux machine/domain running the admin daemon and the desktop. The trusted computing base together with the hypervisor. | dom0 |
| **Admin daemon** | Trusted control-plane process on the host. Owns the qube registry and all lifecycle decisions. The only component allowed to create/start/stop qubes. | qubesd (`qubes-core-admin`) |
| **Core** | The admin daemon's brain: lifecycle rules + validation, written against a Backend, never against a concrete hypervisor. | core-admin logic |
| **Backend** | Hypervisor driver behind a tiny interface (`create/start/stop/remove/get/list`). `LibvirtBackend` = real KVM VMs. `FakeBackend` = JSON-file simulation for development and tests on machines without KVM. | libvirt/Xen layer |
| **Template** | A read-only root filesystem image. AppQubes boot from it via copy-on-write, so 10 qubes share one OS install. | TemplateVM |
| **AppQube** | A qube whose root comes from a Template (CoW clone). Only its private data (home) persists across reboots. | AppVM |
| **Guest agent** | Small daemon running *inside* a qube. Serves RPCs from the host/other qubes (file copy, info, …). | `qubes-core-agent-linux` |
| **Channel** | The host↔guest transport the agent speaks over. Designed for virtio-vsock; in development it runs over plain sockets. | vchan + QubesDB |
| **RPC service** | A named operation one qube may request of another over the channel (e.g. `filecopy`, `open-url`). Every call is checked against Policy. | qrexec service |
| **Policy** | Rules deciding, per (source qube, RPC service, target qube): allow or deny. Deny by default. | qrexec policy |

**Not our words (yet):** NetQube/sys-net, Disposable, seamless GUI — deliberately deferred (see `docs/spec.md` non-goals); the glossary grows when tickets adopt them.
