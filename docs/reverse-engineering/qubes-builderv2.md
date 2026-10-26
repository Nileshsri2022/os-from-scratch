# RE: qubes-builderv2 — the assembly line that builds all ~200 components

**Depth:** medium · **Evidence:** `evidence/qubes-builderv2.txt`; `qubesbuilder/plugins/` listing; tree.
**Maps to MiniQubes:** our deferred "shell scripts + setup doc" shortcut (spec); future packaging reference.

## What it is
Python build orchestrator (51.6k LOC) that turns ~200 component repos into signed
packages, templates, and the installer ISO, reproducibly, inside disposable build
environments. Forked into the org from fepitre's repo (see survey).

## Architecture (evidence)
- **Plugin pipeline** in `qubesbuilder/plugins/`: `fetch` (clone sources; `keys/` holds
  maintainer GPG keys for signature verification), `list_deps{,_archlinux}` (compute the
  component **build-dependency order** — the true build graph our survey deliberately did
  not reconstruct), `chroot_{rpm,deb,archlinux,windows}` (prepare build roots),
  `build_{rpm,deb,archlinux,windows}` (per-distro package builds), `installer` (ISO assembly),
  publish/sign stages.
- **Executors:** builds run isolated — `dockerfiles/` for container executors, or inside
  a disposable Qubes VM via qrexec (`rpc/`, `ansible/`): the build machine itself assumes
  components are untrusted.
- **Config:** one `builder.yml` (samples in `example-configs/`) selects components,
  distributions, templates; `qb` is the CLI entry point.

## Reuse vs write
For v1: nothing (no ISO goal). If packaging ever matters, borrow: component list as data,
dependency-order computation, "build inside a throwaway VM" stance. Our version of this
for the foreseeable future is a Makefile + README. No LICENSE file found; treat as GPL.

## Limitations
Plugin inventory level; dependency extraction from `.qubesbuilder`/spec files not traced.
