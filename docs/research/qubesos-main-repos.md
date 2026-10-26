# Building a Qubes-style OS: do you need all 215 repos?

**No.** Of the 215 QubesOS repos, only **22 are the actual invention** (Tier B below) — and even the Qubes team did not write the rest from scratch: the hypervisor is Xen, the kernel is Linux, the userland is Fedora/Debian. Qubes = a small set of core components + reuse + packaging glue. Data: GitHub API 2026-10-26 (sizes are repo sizes incl. history — a proxy, not LOC).

| Tier | Meaning | Repos |
|---|---|---:|
| **B — MAIN: the invention** (develop your equivalent) | qubesd, qrexec, QubesDB, vchan, in-VM agent, GUI protocol, builder/installer/template glue, Salt config | 22 |
| **A — reuse upstream** (develop nothing) | forks/mirrors + packaging recipes for Xen, Linux kernel, libvirt, GRUB, X11, dnf stack, Python libs… | 95 |
| **C — real products, deferrable** | Qubes Manager GUI, desktop integrations, Windows tools, convenience apps | 71 |
| **D — meta** | docs, website, issue tracker, CI build logs (yes, ~3.3 GB of logs), artwork, HCL | 27 |

In the [interactive graph](qubesos/index.html) tick **“⭐ main repos only (Tier B)”** — Tier B repos carry a gold ring.

## ⭐ The main repos (Tier B) — this is the list you asked for

| Repo | Size | Lang | Role |
|---|---:|---|---|
| [qubes-installer-qubes-os](https://github.com/QubesOS/qubes-installer-qubes-os) | 43.0 MB | Python | Installer definition (Anaconda config + kickstarts). Configuration, not new code. |
| [qubes-core-admin](https://github.com/QubesOS/qubes-core-admin) | 20.7 MB | Python | **qubesd — the brain.** VM lifecycle, storage pools, firewall rules, backup/restore, device assignment, events. Python (asyncio), runs in dom0. |
| [qubes-linux-template-builder](https://github.com/QubesOS/qubes-linux-template-builder) | 20.5 MB | Shell | Builds template root filesystems; AppVMs are copy-on-write clones of these. |
| [qubes-core-agent-linux](https://github.com/QubesOS/qubes-core-agent-linux) | 9.5 MB | Shell | **The in-VM agent.** qrexec services, networking setup, updates proxy, file copy, time sync — everything a Linux AppVM needs. |
| [qubes-builderv2](https://github.com/QubesOS/qubes-builderv2) | 4.3 MB | Python | The assembly line: builds every component into packages and the installer ISO. |
| [qubes-core-admin-client](https://github.com/QubesOS/qubes-core-admin-client) | 4.0 MB | Python | Admin API client — every CLI tool (`qvm-*`) and the GUI manager talk to qubesd through this. |
| [qubes-gui-agent-linux](https://github.com/QubesOS/qubes-gui-agent-linux) | 3.6 MB | C | **GUI protocol, VM side** (X11 agent feeding windows to the daemon). |
| [qubes-core-admin-linux](https://github.com/QubesOS/qubes-core-admin-linux) | 3.5 MB | Python | dom0 Linux-side pieces: storage driver glue, helper services. |
| [qubes-core-qrexec](https://github.com/QubesOS/qubes-core-qrexec) | 2.7 MB | Python | **qrexec — the RPC fabric.** Secure inter-VM calls + the policy engine deciding who may call what. |
| [qubes-gui-daemon](https://github.com/QubesOS/qubes-gui-daemon) | 2.5 MB | C | **GUI protocol, dom0 side** — renders each VM window as a (fake) local window with colored borders. |
| [qubes-core-qubesdb](https://github.com/QubesOS/qubes-core-qubesdb) | 811 KB | C | **QubesDB** — tiny key/value config database shared dom0↔VM (with watches). |
| [qubes-core-vchan-xen](https://github.com/QubesOS/qubes-core-vchan-xen) | 501 KB | C | vchan transport over Xen — reliable byte streams between domains; qrexec/GUI/QubesDB ride on it. |
| [qubes-gui-common](https://github.com/QubesOS/qubes-gui-common) | 144 KB | C | Shared GUI protocol definitions used by both sides. |
| [qubes-core-vchan-socket](https://github.com/QubesOS/qubes-core-vchan-socket) | 126 KB | C | Same vchan API over Unix sockets (testing / non-Xen setups). |
| `qubes-mgmt-salt-*` (8 repos) | small | Salt/YAML | Configuration-as-code: formulas that create & configure the default qubes (sys-net, sys-firewall, vault…). A v1 needs a minimal subset. |

Evidence for "the rest is not invented here": **86 repos are Makefile/no-language** (pure packaging recipes), **100 repos are under 200 KB**, **45 are forks** of someone else's code.

### Tier A examples — reuse, never develop
| Repo | Size | What it really is |
|---|---:|---|
| [qubes-linux-dom0-updates](https://github.com/QubesOS/qubes-linux-dom0-updates) | 260.4 MB | package metadata hosting |
| [xen](https://github.com/QubesOS/xen) | 121.2 MB | fork of xen-project/xen — the hypervisor |
| [qubes-linux-kernel](https://github.com/QubesOS/qubes-linux-kernel) | 91.8 MB | upstream Linux kernel + Qubes config/patches |
| [qubes-grub2](https://github.com/QubesOS/qubes-grub2) | 15.5 MB | upstream software, packaged |
| [rust-vmm](https://github.com/QubesOS/rust-vmm) | 12.0 MB | fork of rust-vmm crates |
| [qubes-lorax](https://github.com/QubesOS/qubes-lorax) | 11.0 MB | upstream software, packaged |
| [qubes-vmm-xen](https://github.com/QubesOS/qubes-vmm-xen) | 7.4 MB | upstream software, packaged |
| [qubes-anaconda](https://github.com/QubesOS/qubes-anaconda) | 5.8 MB | upstream software, packaged |

### Tier C examples — real, but a v1 skips them

[qubes-builder-rpm](https://github.com/QubesOS/qubes-builder-rpm), [qubes-vmm-xen-windows-pvdrivers](https://github.com/QubesOS/qubes-vmm-xen-windows-pvdrivers), [qubes-manager](https://github.com/QubesOS/qubes-manager), [qubes-builder](https://github.com/QubesOS/qubes-builder), [qubes-rpm](https://github.com/QubesOS/qubes-rpm), [qubes-secpack](https://github.com/QubesOS/qubes-secpack), [qubes-linux-utils](https://github.com/QubesOS/qubes-linux-utils), [qubes-desktop-linux-menu](https://github.com/QubesOS/qubes-desktop-linux-menu) …

### Tier D examples — meta weight

[build-logs](https://github.com/QubesOS/build-logs) (1996.5 MB), [build-logs42](https://github.com/QubesOS/build-logs42) (633.6 MB), [build-logs43](https://github.com/QubesOS/build-logs43) (450.6 MB), [openqa-tests-qubesos](https://github.com/QubesOS/openqa-tests-qubesos) (394.3 MB), [build-logs-devel](https://github.com/QubesOS/build-logs-devel) (288.0 MB), [build-logs-secondary](https://github.com/QubesOS/build-logs-secondary) (208.3 MB)

## So what does "build this OS from scratch" mean in practice?

### Path 1 — Compile the real Qubes OS from source (develop: 0 repos)
Clone [qubes-builderv2](https://github.com/QubesOS/qubes-builderv2), write a `builder.yml`
selecting components (≈ the whole org), build packages → template → ISO. You develop nothing;
the learning is the build system. Needs a beefy machine (hours, lots of disk/RAM) — not runnable
in this sandbox.

### Path 2 — Build your own Qubes-like OS (develop: equivalents of ~6 ideas)
Ponytail-minimal v1 mapping — reuse everything Tier A, write only:

| Qubes piece | Your v1 equivalent | Shortcut (upgrade when…) |
|---|---|---|
| Xen + Linux kernel + distro | **Reuse**: KVM/QEMU + a Linux distro | shortcut: KVM instead of Xen — simpler dev loop; revisit if you need Xen's driver domains |
| qubes-core-admin (qubesd) | Small Python admin daemon over **libvirt**: create/start/stop/clone VMs, attach disks | — |
| qrexec + vchan + QubesDB (4 repos) | **One** agent channel over **virtio-vsock**: simple RPC + config push | shortcut: merged protocol, permissive policy; split when you need granular inter-VM policy |
| qubes-core-agent-linux | Small guest agent: RPC server, file copy, IP/time setup | — |
| qubes-gui-daemon/agent | **Skip the protocol** — SPICE/VNC window per VM | shortcut: no seamless colored-border windows; that's the hardest part, deliberately last |
| template-builder + storage | One golden qcow2; AppVMs = qemu-img **backing-file clones** (free CoW) | — |
| builderv2 + installer + Salt | Shell scripts + a setup doc | shortcut: no ISO builder until the OS itself works |

That's **3 things to actually write** (admin daemon, guest agent, thin CLI) versus 215 repos.
Honest scale note: upstream Tier B is ~45 MB of repos built by a team over 15 years; a
learning-grade equivalent with the shortcuts above is a few thousand lines — the architecture
(compartmentalize everything, treat VMs as untrusted, one small trusted core) is the real lesson.
