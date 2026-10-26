# Proposal: Operating System From Scratch

**Status:** awaiting your approval — no OS code until you agree.
**Date:** 2026-10-26
**Workflow:** ask-matt (routing/grilling/spec/tickets) + ponytail (smallest complete change) +
REA (reverse engineering, on your permission only).

---

## 1. Your goal, as I understand it

- Work through [Build Your Own X](https://github.com/codecrafters-io/build-your-own-x) projects
  one by one; the current project is **Build your own Operating System**.
- Use two installed skills: **ask-matt** for process, **ponytail** for coding discipline.
- Find the **most popular** existing OS-from-scratch projects. For the one you pick, and only
  with your permission, **reverse-engineer** it (REA-style) and report: *this project uses this
  algorithm, this structure, this technique* — then ask you **"develop using this?"**
- **Docs first:** every task gets its document before any code is written.

## 2. What each of your links actually is

| Link | What it is | How we'll use it |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) `--skill ask-matt` | **Installed ✅** → `.agents/skills/ask-matt/`. ask-matt is a *router* over Matt Pocock's engineering skills. For a greenfield multi-session build in a repo it prescribes: `/grill-with-docs` (interview → `GLOSSARY.md` + ADRs) → `/to-spec` → `/to-tickets` (tracer-bullet tickets w/ blockers) → `/implement` per ticket (TDD + code-review). Precondition: `/setup-matt-pocock-skills` (tracker + doc layout — this proposal covers it). | Our project process, §5. |
| [ponytail](https://www.skills.sh/dietrichgebert/ponytail) | **Installed ✅** → `.agents/skills/ponytail/` (334K installs on skills.sh). "Lazy senior dev mode": best code is code never written. Ladder: need it? → already exists? → stdlib/platform? → installed dep? → one line? → minimum code. Shortcuts get `shortcut: <limit>, <when to upgrade>` comments; non-trivial logic leaves a check. Sibling skills exist (ponytail-review/audit/debt/gain) — not installed yet (YAGNI). | Coding discipline for every ticket. |
| [morluto/rea](https://github.com/morluto/rea) | **REA — Reverse Engineer Anything**: an MCP server + CLI (`npx rea-agents setup`) that lets an agent inspect native binaries (via Hopper/Ghidra/IDA bridges), JS/Electron apps, .NET assemblies and websites *without source*, explain how a feature works **with evidence**, then rebuild it. Honest note: REA's binary tooling needs a local disassembler setup; our candidate targets are open-source, so the practical move is REA's *discipline* (inspect → evidence → limitations → rebuild) applied at source level, plus binary-level checks (`readelf`/`objdump`) on the compiled kernel image where useful. If you install REA on your machine later, we can go full binary-level too. | Only on the target you name + permit. Report → `docs/reverse-engineering/`. |
| [Nileshsri2022/somecoolprojects](https://github.com/Nileshsri2022/somecoolprojects) | Your mono-repo: **~105 project directories** (redis-server, docker, shell, tetris…). No OS project yet — this would be the first. | We build in this dedicated `os-from-scratch` repo (this session's branch), structured as one self-contained directory so you can copy it into `somecoolprojects` whenever you like. Say the word if you want it developed directly there instead. |
| [build-your-own-x#…operating-system](https://github.com/codecrafters-io/build-your-own-x#build-your-own-operating-system) | The index (556K ⭐). Its OS section lists **19 tutorials**: 2× Assembly (x86 bootloader, Baking Pi), 13× C (os-tutorial, Little OS Book, James Molloy, OS 0→1, mini-arm-os, raspberry-pi-os…), 2× C++, 2× Rust (Phil Opp, Stephen Marz RISC-V), 1× Linux From Scratch. | Our source list; §3 ranks them. |

## 3. Popularity research (evidence)

GitHub API, 2026-10-26. Stars = popularity; forks = people actually building it.

| Project | ⭐ Stars | Forks | Lang / Arch | Type |
|---|---:|---:|---|---|
| [SerenityOS/serenity](https://github.com/SerenityOS/serenity) | 33,905 | 3,489 | C++ / x86_64 | Full hobby OS (huge, not a tutorial) |
| **[cfenollosa/os-tutorial](https://github.com/cfenollosa/os-tutorial)** | **30,777** | 3,552 | C+ASM / x86-32 | **Tutorial — "How to create an OS from scratch"** |
| [reactos/reactos](https://github.com/reactos/reactos) | 18,362 | — | C / x86 | Windows-compatible OS (not from-scratch learning) |
| **[phil-opp/blog_os](https://github.com/phil-opp/blog_os)** | **17,788** | 1,204 | Rust / x86_64 | **Tutorial — "Writing an OS in Rust"** |
| [redox-os/redox](https://github.com/redox-os/redox) | 16,657 | 1,033 | Rust / x86_64 | Full microkernel OS |
| [s-matyukevich/raspberry-pi-os](https://github.com/s-matyukevich/raspberry-pi-os) | 13,959 | 1,341 | C+ASM / ARMv8 (RPi 3) | Tutorial |
| [tuhdo/os01](https://github.com/tuhdo/os01) | 13,755 | 796 | book / x86 | Book "Operating Systems: From 0 to 1" |
| **[mit-pdos/xv6-riscv](https://github.com/mit-pdos/xv6-riscv)** | **10,692** | **4,494** | C / RISC-V 64 | **MIT teaching OS (Unix v6 reimplementation)** |
| [mit-pdos/xv6-public](https://github.com/mit-pdos/xv6-public) | 9,704 | 4,561 | C / x86-32 | xv6 original (superseded by RISC-V version) |
| [klange/toaruos](https://github.com/klange/toaruos) | 6,865 | 546 | C / x86 | Hobby OS with GUI |
| [littleosbook/littleosbook](https://github.com/littleosbook/littleosbook) | 2,673 | 289 | C / x86 | Book (GRUB-based) |
| [jserv/mini-arm-os](https://github.com/jserv/mini-arm-os) | 1,262 | 257 | C / ARM | Minimal multitasking kernel tutorial |

**Reading of the evidence:** the most popular *learn-by-building* OS project on Earth right now
is **cfenollosa/os-tutorial** (30.8K ⭐). The most popular Rust one is **phil-opp/blog_os**.
The most *forked* (most hands-on builders) is MIT's **xv6**. These three are the serious
reverse-engineering candidates.

## 4. Reverse-engineering candidates (preview — full evidence only after your permission)

> Below is the well-known public shape of each project. The real REA-style report (clone →
> inspect every subsystem → evidence-cited algorithm list) happens only for the one you pick.

**A. cfenollosa/os-tutorial** — C + NASM assembly, x86 32-bit, BIOS boot, QEMU.
Techniques it teaches/uses: 512-byte boot sector & BIOS disk loading (CHS), GDT & switch to
32-bit protected mode, VGA text-mode driver (port I/O `0x3D4/0x3D5`, memory at `0xB8000`),
IDT + ISR/IRQ stubs, PIC remapping, PIT timer @ IRQ0, PS/2 keyboard scancodes (set 1),
`kmalloc` (placement-address bump allocator), paging intro, and a tiny string-command shell
(`END`, `PAGE` commands). ~24 small lessons, each one new concept. **Best if:** you want the
classic, most-followed path, and our OS in C/x86-32.

**B. phil-opp/blog_os** — Rust (`#![no_std]`), x86_64, `bootloader` crate, QEMU.
Techniques: VGA buffer with spinlock, CPU exceptions (breakpoint, double fault w/ IST),
hardware interrupts (PIC → later APIC), 4-level paging (PML4), heap allocators built in
stages (**bump → linked-list → fixed-size-block**), cooperative multitasking via Rust
`async/await` executor with wakers. **Best if:** you want a modern language, 64-bit, and strong
memory-safety lessons. Needs a Rust toolchain (not present in this sandbox — you'd run it locally).

**C. mit-pdos/xv6-riscv** — C, RISC-V 64-bit, QEMU `virt` machine. A complete small Unix:
processes & round-robin scheduler, Sv39 page tables / copy-on-write fork (in labs), trap
handling & system calls, spinlocks/sleeplocks, a logging file system (write-ahead log, inodes,
buffer cache), pipes, `exec` of ELF binaries, plus user programs (`sh`, `ls`, `grep`…).
**Best if:** you want to end with a *real* multi-process OS with a filesystem and shell, and
the cleanest textbook architecture (it's MIT's 6.S081 course OS).

Whatever we pick, the RE report answers: architecture map · boot sequence · memory model ·
scheduler algorithm · interrupt/trap design · drivers · FS (if any) · build system · what we
reuse as *ideas* vs. write ourselves. Then I ask: **"develop using this?"**

## 5. Proposed process & doc layout (ask-matt, adapted)

```
Research (§2–4 done) ──► YOUR DECISIONS (§8) ──► Grill-with-docs ──► RE report (REA, if permitted)
                                                        │                       │
                                              GLOSSARY.md + docs/adr/           ▼
                                                        └────► docs/spec.md ◄── "develop using this?" = yes
                                                                    │
                                        .scratch/os-from-scratch/issues/NN-*.md  (tickets, blockers first)
                                                                    │
                              Per ticket:  DOC FIRST ──► ponytail-minimal code ──► build+boot check ──► close doc
```

- **Tracker:** local ticket files under `.scratch/` (ask-matt supports this; zero setup, all in-repo).
  GitHub Issues instead? Say so and I'll switch.
- **ADRs** (`docs/adr/`): one short file per hard-to-reverse choice (arch, language, BIOS vs UEFI,
  own bootloader vs GRUB, 32- vs 64-bit). Written during grilling, not up front.

## 6. Proposed OS phases (draft tickets — final list comes from the spec)

Phases assume the C/x86-32 classic path; if you pick Rust or RISC-V in §8, same shape, different
details. Each phase = 1+ tickets, each ticket boots in QEMU before it closes.

| # | Phase (tracer bullet) | Done means (boot evidence) |
|---|---|---|
| P0 | Scaffold + toolchain | `make` produces a bootable image; build is `-Wall -Wextra` clean |
| P1 | Boot sector | BIOS loads us; "Hello" on screen from pure assembly |
| P2 | Protected mode + C kernel | GDT loaded, 32-bit C `kernel_main()` running |
| P3 | Screen driver | `kprint()` with scrolling VGA text output |
| P4 | Interrupts | IDT + timer ticks counting on screen; keyboard IRQ live |
| P5 | Keyboard + shell | Type commands (`help`, `echo`, `clear`, `halt`) at a prompt |
| P6 | Memory | Paging on; `kmalloc/kfree` heap passing a self-test |
| P7 | Multitasking | Two+ kernel tasks switching on the timer tick |
| P8 | Filesystem | Read/write files on a simple on-disk FS from the shell |
| P9 | User mode (stretch) | Syscalls + running a separate user program |

Ponytail scoping: **v1 = P0–P5** (boot → interactive shell). P6–P9 are agreed one phase at a
time, after v1 boots.

## 7. Per-ticket doc template (docs-first, every task)

```md
# NN — <title>            Blocked by: <tickets>   Status: todo/doing/done
## Goal            — one sentence + boot evidence that proves it
## Concepts        — the OS theory this ticket teaches (short)
## Design          — algorithms, data structures, memory map, file changes
## Steps           — checklist
## Verify          — exact commands + expected screen/serial output
## Result          — what actually happened, shortcuts (shortcut: …, upgrade when …)
```

## 8. Decisions I need from you (the grilling starts here)

1. **Reverse-engineer which project?** (answering = your permission) os-tutorial / blog_os / xv6-riscv / none yet
2. **Our OS stack?** C on x86-32 / Rust on x86_64 / C on RISC-V 64 / C on ARM (Raspberry Pi)
3. **v1 scope?** Boot→shell (P0–P5) / +memory & multitasking (P6–P7) / +FS & user mode (P8–P9) / decide per phase
4. **Approve this docs workflow?** Then next step is grill-with-docs: `GLOSSARY.md` + ADRs →
   `docs/spec.md` → tickets → first ticket doc.

## 9. Risks & honest limitations

- **Sandbox tooling:** this environment has `gcc`/`ld`/`make` but **no QEMU, NASM, or Rust**,
  and package installs are network-restricted. P0 will either get the tools or state the exact
  commands for your machine; until then I can compile freestanding C and verify build-clean,
  but boot evidence may need your local QEMU. This decides nothing yet — flagged early, per ponytail.
- **REA scope:** REA's full power (Ghidra/Hopper binary bridges) runs on your machine via
  `npx rea-agents setup`. In this sandbox I'll run the same evidence discipline against the
  target's source and compiled artifacts.
- Skipped for now (deliberately): GLOSSARY/ADRs/spec/tickets — they are outputs of your §8
  answers, not something to invent before you decide.
