# RE: mit-pdos/xv6-riscv — MIT's teaching Unix (RISC-V)

**Depth:** survey+ · **Evidence:** `evidence/xv6-riscv.txt`; `kernel/` file inventory.
**Maps to MiniQubes:** reference only (classic direction); conceptually our registry/scheduler cousin.

## What it is
A compact, complete Unix v6 reimplementation for 64-bit RISC-V SMP (QEMU virt), MIT-licensed,
82 files / ~13k LOC including user programs (shell, ls, grep, …). Used by MIT's 6.S081 course.

## Architecture from the file inventory (evidence: kernel/)
- **Processes/scheduling:** `proc.c` — fixed-size process table, round-robin scheduler,
  `swtch.S` context switch, sleep/wakeup on channels; `spinlock.c`/`sleeplock.c`.
- **Memory:** `kalloc.c` free-list physical page allocator; Sv39 three-level page tables
  (`vm.c`, `memlayout.h`, `riscv.h`); per-process address spaces, `trampoline.S` for the
  user↔kernel boundary page.
- **Traps/syscalls:** `trap.c` + `kernelvec.S`, syscall table in `syscall.c` dispatching to
  `sysfile.c`/`sysproc.c`; `plic.c` platform interrupt controller; `exec.c` ELF loader.
- **Filesystem:** `fs.c` inode-based FS, `log.c` write-ahead logging (begin/commit/end-op
  transactions for crash consistency), `bio.c` LRU buffer cache, `file.c` file/pipe layer,
  `pipe.c` ring buffer. `console.c`+UART for I/O.

## Verdict for us
The cleanest existence proof that "a real OS" fits in ~10k lines — because it *chooses*
simplicity everywhere (fixed tables, linear scans, big locks where safe). That philosophy
validates our MiniQubes minimalism; the code itself is for the classic direction.
Structure-level analysis; not built or run in this pass.
