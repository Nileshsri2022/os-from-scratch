# QubesOS GitHub org — all 215 repos, and how they connect

**Answer: exactly 215 public repositories** (GitHub API, 2026-10-26) — 170 original, 45 forks, 11 archived. Interactive graph: [qubesos/index.html](qubesos/index.html). Which of the 215 actually matter if you want to build this OS: [qubesos-main-repos.md](qubesos-main-repos.md).

## The 215, by component family

| Family | Repos | Flagships (by ⭐) |
|---|---:|---|
| Core system (dom0, qrexec, VM agents) | 12 | [qubes-core-admin](https://github.com/QubesOS/qubes-core-admin), [qubes-core-agent-linux](https://github.com/QubesOS/qubes-core-agent-linux), [qubes-core-admin-client](https://github.com/QubesOS/qubes-core-admin-client) |
| GUI virtualization | 8 | [qubes-gui-agent-linux](https://github.com/QubesOS/qubes-gui-agent-linux), [qubes-gui-daemon](https://github.com/QubesOS/qubes-gui-daemon), [qubes-gui-agent-wayland](https://github.com/QubesOS/qubes-gui-agent-wayland) |
| Hypervisor / Xen / VMM | 12 | [qubes-vmm-xen](https://github.com/QubesOS/qubes-vmm-xen), [qubes-vmm-xen-windows-pvdrivers](https://github.com/QubesOS/qubes-vmm-xen-windows-pvdrivers), [qubes-vmm-xen-stubdom-linux](https://github.com/QubesOS/qubes-vmm-xen-stubdom-linux) |
| Linux kernel & support | 11 | [qubes-linux-kernel](https://github.com/QubesOS/qubes-linux-kernel), [qubes-linux-utils](https://github.com/QubesOS/qubes-linux-utils), [qubes-linux-template-builder](https://github.com/QubesOS/qubes-linux-template-builder) |
| VM templates | 3 | [qubes-template-configs](https://github.com/QubesOS/qubes-template-configs), [qubes-template-whonix](https://github.com/QubesOS/qubes-template-whonix), [qubes-template-kicksecure](https://github.com/QubesOS/qubes-template-kicksecure) |
| Desktop, X11 & audio | 25 | [qubes-desktop-linux-i3](https://github.com/QubesOS/qubes-desktop-linux-i3), [qubes-desktop-linux-kde](https://github.com/QubesOS/qubes-desktop-linux-kde), [qubes-desktop-linux-manager](https://github.com/QubesOS/qubes-desktop-linux-manager) |
| Applications | 21 | [qubes-app-linux-pdf-converter](https://github.com/QubesOS/qubes-app-linux-pdf-converter), [qubes-manager](https://github.com/QubesOS/qubes-manager), [qubes-video-companion](https://github.com/QubesOS/qubes-video-companion) |
| Windows support | 3 | [qvm-create-windows-qube](https://github.com/QubesOS/qvm-create-windows-qube), [qubes-windows-utils](https://github.com/QubesOS/qubes-windows-utils), [qubes-windows-tools-cross](https://github.com/QubesOS/qubes-windows-tools-cross) |
| Python libraries | 15 | [qubes-python-u2flib-host](https://github.com/QubesOS/qubes-python-u2flib-host), [qubes-python-objgraph](https://github.com/QubesOS/qubes-python-objgraph), [qubes-python-sphinx](https://github.com/QubesOS/qubes-python-sphinx) |
| Management (Salt / Ansible) | 11 | [qubes-ansible](https://github.com/QubesOS/qubes-ansible), [qubes-mgmt-salt-dom0-virtual-machines](https://github.com/QubesOS/qubes-mgmt-salt-dom0-virtual-machines), [qubes-mgmt-salt-dom0-qvm](https://github.com/QubesOS/qubes-mgmt-salt-dom0-qvm) |
| Builder, CI, testing & infra | 27 | [qubes-builder](https://github.com/QubesOS/qubes-builder), [updates-status](https://github.com/QubesOS/updates-status), [qubes-builder-archlinux](https://github.com/QubesOS/qubes-builder-archlinux) |
| Installer & boot | 15 | [qubes-installer-qubes-os](https://github.com/QubesOS/qubes-installer-qubes-os), [qubes-installer-qubes-os-windows-tools](https://github.com/QubesOS/qubes-installer-qubes-os-windows-tools), [qubes-anaconda-addon](https://github.com/QubesOS/qubes-anaconda-addon) |
| Firmware & hardware | 7 | [qubes-fwupd](https://github.com/QubesOS/qubes-fwupd), [qubes-seabios](https://github.com/QubesOS/qubes-seabios), [qubes-flashrom](https://github.com/QubesOS/qubes-flashrom) |
| Security components | 9 | [qubes-secpack](https://github.com/QubesOS/qubes-secpack), [qubes-antievilmaid](https://github.com/QubesOS/qubes-antievilmaid), [qubes-remote-support](https://github.com/QubesOS/qubes-remote-support) |
| Docs, website & community | 14 | [qubes-issues](https://github.com/QubesOS/qubes-issues), [qubes-doc](https://github.com/QubesOS/qubes-doc), [qubesos.github.io](https://github.com/QubesOS/qubesos.github.io) |
| System packages & packaging forks | 22 | [qubes-gentoo](https://github.com/QubesOS/qubes-gentoo), [qubes-qubes-release](https://github.com/QubesOS/qubes-qubes-release), [qubes-release-configs](https://github.com/QubesOS/qubes-release-configs) |

## Languages

| Language | Repos |
|---|---:|
| Makefile | 61 |
| Python | 44 |
| Shell | 35 |
| C | 28 |
| (none — mostly packaging/meta) | 25 |
| Ruby | 5 |
| Rust | 4 |
| Roff | 3 |
| JavaScript | 3 |
| Perl | 1 |
| Jinja | 1 |
| PowerShell | 1 |
| Salt | 1 |
| Brainfuck | 1 |
| HTML | 1 |
| SCSS | 1 |

(61 "Makefile" repos are packaging components — build recipes that fetch and package upstream software.)

## Most-starred repos

| ⭐ | Repo |
|---:|---|
| 622 | [qubes-issues](https://github.com/QubesOS/qubes-issues) |
| 554 | [qubes-secpack](https://github.com/QubesOS/qubes-secpack) |
| 408 | [qubes-doc](https://github.com/QubesOS/qubes-doc) |
| 399 | [qvm-create-windows-qube](https://github.com/QubesOS/qvm-create-windows-qube) |
| 374 | [qubesos.github.io](https://github.com/QubesOS/qubesos.github.io) |
| 163 | [qubes-antievilmaid](https://github.com/QubesOS/qubes-antievilmaid) |
| 148 | [qubes-core-admin](https://github.com/QubesOS/qubes-core-admin) |
| 103 | [qubes-linux-kernel](https://github.com/QubesOS/qubes-linux-kernel) |
| 90 | [qubes-builder](https://github.com/QubesOS/qubes-builder) |
| 69 | [qubes-app-linux-pdf-converter](https://github.com/QubesOS/qubes-app-linux-pdf-converter) |
| 68 | [qubes-core-agent-linux](https://github.com/QubesOS/qubes-core-agent-linux) |
| 56 | [qubes-manager](https://github.com/QubesOS/qubes-manager) |

## The 45 forks — where they come from

Fork parents by owner: `fepitre` ×19, `HW42` ×5, `marmarek` ×3, `kalkin` ×2, `jpouellet` ×2, `rust-vmm` ×2, `kdj0c` ×1, `kushaldas` ×1. Most are **maintainer working forks** mirrored into the org. Heavyweight true upstreams: **xen ← xen-project/xen**, **rust-vmm ← rust-vmm org**, **qubes-template-kicksecure ← Kicksecure**.

## How the 215 actually connect

**1. Build-time: one builder, ~200 components.** [qubes-builderv2](https://github.com/QubesOS/qubes-builderv2)
builds every component repo into packages/ISO (dotted "builder builds-all" links in the graph).

**2. Runtime: dom0 at the center.** [qubes-core-admin](https://github.com/QubesOS/qubes-core-admin) (`qubesd`, dom0)
manages Xen VMs; tools reach it via the Admin API ([qubes-core-admin-client](https://github.com/QubesOS/qubes-core-admin-client)).
VMs talk over **qrexec** ([qubes-core-qrexec](https://github.com/QubesOS/qubes-core-qrexec) ↔
[qubes-core-agent-linux](https://github.com/QubesOS/qubes-core-agent-linux) in each VM) on top of **vchan**
transport; **QubesDB** carries configuration. VM windows appear as local windows via the GUI protocol
([qubes-gui-daemon](https://github.com/QubesOS/qubes-gui-daemon) ↔ [qubes-gui-agent-linux](https://github.com/QubesOS/qubes-gui-agent-linux)).

**3. Templates & management.** AppVMs are copy-on-write clones of template roots (`qubes-template-*`,
built by qubes-linux-template-builder); Salt formulas (`qubes-mgmt-salt-*`) configure them.

**4. Lineage.** Dashed purple links = GitHub fork parentage: how code entered the org.

### Graph edge legend
| Edge | Meaning | Source |
|---|---|---|
| colored thin | repo → its component family hub | naming + role |
| purple dashed | GitHub fork-of | GitHub API |
| white solid | documented runtime relationship | curated (7) |
| gray dotted | builderv2 builds this family | Qubes build system |

**Honest limit:** family links are architectural grouping, not code-level dependencies.
