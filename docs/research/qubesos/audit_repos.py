"""Coverage audit: QubesOS org (live GitHub API) vs our classification.

Proves "no repo left behind" for the REA pass: re-runs build_graph.py's tier
rules on the LIVE org listing, verifies the published tier counts reproduce,
and cross-checks every Tier B repo against evidence/ + reports.

Usage:
  curl -sfL "https://api.github.com/orgs/QubesOS/repos?per_page=100&page=N" \
       -o live-N.json   (N = 1..3 while pages return items)
  python audit_repos.py /path/to/dir-with-live-N.json [--manifest]

Read-only: prints the audit summary; --manifest prints the per-repo CSV
(repo, tier, fork, archived, language, evidence, report) on stdout, so the
caller redirects it to a file. Exits 1 unless every invariant holds.
"""
import collections
import glob
import json
import os
import sys

# ---- tier rules: verbatim from build_graph.py (the published classification) ----
TIER_B = {"qubes-core-admin", "qubes-core-admin-client", "qubes-core-admin-linux",
          "qubes-core-qrexec", "qubes-core-qubesdb", "qubes-core-vchan-xen",
          "qubes-core-vchan-socket", "qubes-core-agent-linux", "qubes-gui-daemon",
          "qubes-gui-agent-linux", "qubes-gui-common", "qubes-builderv2",
          "qubes-installer-qubes-os", "qubes-linux-template-builder"}
EXTRA_A = {"qubes-linux-kernel", "qubes-grub2", "qubes-vmm-xen", "qubes-lorax",
           "qubes-blivet"}
DOCS = {".github", "qubes-doc", "qubes-offline-doc", "qubes-issues",
        "qubesos.github.io", "qubes-posts", "qubes-hcl", "qubes-attachment",
        "qubes-roadmap", "qubes-diagrams", "qubes-architecture", "qubes-artwork",
        "qubes-translated", "training-materials"}
MGMT_SALT = {f"qubes-mgmt-salt{sfx}" for sfx in (
    "", "-base", "-base-config", "-base-overrides", "-base-topd",
    "-dom0-qvm", "-dom0-update", "-dom0-virtual-machines")}
EXPECTED = {"A": 95, "B": 22, "C": 71, "D": 27}


def tier(r):
    n = r["name"]
    if n in TIER_B or n.startswith("qubes-mgmt-"):
        return "B"
    if n in DOCS or n.startswith(("build-logs", "build-commands", "build-issues",
                                  "updates-status")) \
       or n in {"openqa-tests-qubesos", "tests-hw-setup",
                "qubes-continuous-integration"}:
        return "D"
    if r["fork"] or r["language"] in (None, "Makefile") or n in EXTRA_A:
        return "A"
    return "C"


def main():
    live_dir = sys.argv[1]
    live = {}
    for f in sorted(glob.glob(os.path.join(glob.escape(live_dir), "live-*.json"))):
        with open(f, encoding="utf-8") as fh:
            for r in json.load(fh):
                live[r["name"]] = r
    if len(live) < 100:
        sys.exit(f"FAIL: only {len(live)} live repos fetched — incomplete pages?")

    counts = collections.Counter(tier(r) for r in live.values())
    print(f"live repos: {len(live)}  tiers: {dict(sorted(counts.items()))}")
    print(f"published counts reproduce: {counts == EXPECTED} (expected {EXPECTED})")

    # climb to the repo root via dirname only (no literal .. — Mimosa path rule)
    qubesos_dir = os.path.dirname(os.path.abspath(__file__))      # docs/research/qubesos
    re_dir = os.path.join(os.path.dirname(os.path.dirname(qubesos_dir)),
                          "reverse-engineering")
    ev_dir = os.path.join(re_dir, "evidence")
    evidence = {f[:-4] for f in os.listdir(ev_dir) if f.endswith(".txt")}
    reports = {f[:-3] for f in os.listdir(re_dir) if f.endswith(".md")}

    def report_for(name):
        if name in MGMT_SALT and "qubes-mgmt-salt" in reports:
            return "qubes-mgmt-salt.md"
        return f"{name}.md" if name in reports else ""

    tier_b = sorted(n for n in live if tier(live[n]) == "B")
    missing_ev = [n for n in tier_b if n not in evidence]
    missing_rep = [n for n in tier_b if not report_for(n)]
    print(f"Tier B: {len(tier_b)}  evidence files: {len(evidence)}  "
          f"Tier B without evidence: {missing_ev or 'none'}")
    print(f"Tier B without a report: {missing_rep or 'none'}")

    if "--manifest" in sys.argv:
        print("repo,tier,fork,archived,language,evidence_txt,report_md")
        for n in sorted(live):
            r = live[n]
            print(",".join([n, tier(r), str(r["fork"]), str(r["archived"]),
                            r["language"] or "", "yes" if n in evidence else "",
                            report_for(n)]))

    if counts != EXPECTED or missing_ev or missing_rep:
        sys.exit("FAIL: audit invariants violated — see above")
    print("AUDIT OK")


if __name__ == "__main__":
    main()
