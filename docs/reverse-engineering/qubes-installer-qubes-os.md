# RE: qubes-installer-qubes-os — installer definition (data, not code)

**Depth:** survey · **Evidence:** `evidence/qubes-installer-qubes-os.txt`; tree.
**Maps to MiniQubes:** non-goal in v1 (no ISO).

## What it is
3.5k LOC of mostly *data* consumed by builderv2's installer plugin: `conf/` (Anaconda
configuration), `live/` (kickstarts `.ks` + livecd tools), `meta-packages/` (package sets
that define what a Qubes install contains), `qubes-release/` (branding/release files),
`build-deps*.list`. The "installer" behavior itself lives in Fedora's Anaconda (+ Qubes'
addon in sibling packaging repos); this repo parameterizes it, including post-install
first-boot creation of the default qubes (executed by mgmt-salt states).

## Takeaway
Confirms our tiering: an "OS installer" at this level is distribution plumbing, not
invention. Our install story stays "run the CLI on your Linux host" until/unless an ISO
goal appears. Tree-level analysis; no LICENSE file found.
