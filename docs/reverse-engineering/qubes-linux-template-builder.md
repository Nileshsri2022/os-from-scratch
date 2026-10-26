# RE: qubes-linux-template-builder — building template root filesystems

**Depth:** survey · **Evidence:** `evidence/qubes-linux-template-builder.txt`; script listing.
**Maps to MiniQubes:** ticket 04 (`tools/make-template.sh`).

## What it is
A shell pipeline (61 files, 3.7k LOC) that manufactures template images: per-distribution
build scripts assemble a root filesystem, install the Qubes agent packages into it,
`cleanup_image` strips logs/keys/machine-ids, and `build_template_rpm` packages the result
**as an RPM** — so templates are installed, updated, and distributed through the normal
package manager, versioned like software.

## Reuse vs write
Borrow: the pipeline shape (assemble → inject agent → scrub identity → publish) and the
scrub step as an explicit checklist. Difference kept deliberately: upstream ships
templates as packages built by builderv2; ours (ticket 04) produces a golden qcow2
directly — packaging is distribution machinery we don't need for a single-user dev OS.
Script names read; script bodies not line-traced. No LICENSE file found.
