# RE: cfenollosa/os-tutorial — "How to create an OS from scratch" (30.8K ⭐)

**Depth:** survey · **Evidence:** `evidence/os-tutorial.txt`; lesson directory listing.
**Maps to MiniQubes:** none currently — reference if the classic-kernel project ever starts.

## What it is
The most popular OS-from-scratch tutorial on GitHub: 25 self-contained lessons, 11k LOC,
BSD-3-Clause. Each directory is one concept, code + README, x86 32-bit, NASM + C, QEMU.

## Curriculum = architecture ramp (evidence: lesson names)
`01–07` BIOS boot sector in assembly (printing, memory, stack, segmentation, CHS disk
loading) → `08–10` 32-bit protected mode + GDT → `11–13` cross-compiler and first C kernel
linked at 0x1000 → `15–17` VGA text driver via ports 0x3D4/5 + scrolling → `18–20` IDT,
ISR/IRQ stubs, PIC remap, PIT timer, keyboard → `21` string-command shell → `22` kmalloc
(bump allocator with page alignment) → `23–24` fixes + minimal libc. The final kernel is
~1,500 lines: boot → protected mode → interrupts → interactive shell, no paging-based
process isolation, no filesystem, no multitasking.

## Verdict for us
Pedagogically excellent and license-permissive, but it teaches the *opposite* end of the
stack from MiniQubes (bare metal vs hypervisor control plane). Keep as the reference for
a possible future classic-kernel project (proposal.md candidate A). Lesson contents were
sampled by structure, not rebuilt/booted here.
