# RE: phil-opp/blog_os — "Writing an OS in Rust" (17.8K ⭐)

**Depth:** survey · **Evidence:** `evidence/blog_os.txt`; `blog/content/` (edition-1, edition-2).
**Maps to MiniQubes:** reference only (Rust classic direction).

## What this repo actually is
Not a kernel repo — the **blog itself** (Markdown posts, translations, site tooling;
414 files, LOC dominated by prose/SVG). The compilable per-post code lives on separate
git branches per post, **not in this shallow default-branch clone** (stated limitation).
Code license MIT/Apache; text CC-BY-NC (seen in `blog/content/`).

## Curriculum (edition-2 post series)
Freestanding Rust binary → VGA text mode output → CPU exceptions (incl. double-fault with
IST) → hardware interrupts (PIC, timer, keyboard) → paging (4-level, frame allocation) →
heap allocation in three escalating designs (bump → linked-list → fixed-size-block) →
cooperative multitasking via an `async/await` executor with wakers. Tooling: `bootloader`
crate, `cargo xbuild`-era custom target, QEMU.

## Verdict for us
Best-in-class if a future project goes Rust/x86_64; its staged allocator progression is a
great teaching pattern (ship the dumb version, name its limit, upgrade). Irrelevant to the
KVM control-plane we're building. Post-level evidence only; code branches not cloned/read
in this pass.
