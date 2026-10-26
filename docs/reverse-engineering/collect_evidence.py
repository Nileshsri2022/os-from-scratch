#!/usr/bin/env python3
"""Collect static-analysis evidence for reverse-engineering targets.

Usage: python3 collect_evidence.py [targets_dir]   (default ~/refs/targets)
Writes evidence/<repo>.txt next to this script + prints a one-line-per-repo table.
Evidence discipline per AGENTS.md/REA: every report claim must trace to these files
or to a file read recorded in the report.
"""
import collections, pathlib, subprocess, sys

TARGETS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.home() / "refs/targets"
OUT = pathlib.Path(__file__).parent / "evidence"
OUT.mkdir(exist_ok=True)
URL = {"os-tutorial": "cfenollosa/os-tutorial", "xv6-riscv": "mit-pdos/xv6-riscv",
       "blog_os": "phil-opp/blog_os"}
BUILD_MARKERS = [".qubesbuilder", "Makefile", "Makefile.builder", "setup.py", "pyproject.toml",
                 "Cargo.toml", "meson.build", "CMakeLists.txt", "debian", "archlinux"]


def sh(repo, *args):
    return subprocess.run(args, cwd=repo, capture_output=True, text=True).stdout.strip()


def license_line(repo):
    for pat in ("LICENSE*", "COPYING*", "LICENSE.*"):
        for f in sorted(repo.glob(pat)):
            if f.is_file():
                for line in f.read_text(errors="ignore").splitlines():
                    if line.strip():
                        return line.strip()[:80]
    return "(no LICENSE file found)"


rows = []
for repo in sorted(p for p in TARGETS.iterdir() if (p / ".git").exists()):
    name = repo.name
    files = sh(repo, "git", "ls-files").splitlines()
    ext = collections.Counter(
        (pathlib.Path(f).suffix.lower() or "(none)") for f in files)
    loc, sizes = 0, []
    for f in files:
        fp = repo / f
        try:
            if fp.is_file() and fp.stat().st_size < 2_000_000:
                n = len(fp.read_bytes().splitlines())
                loc += n
                sizes.append((n, f))
        except OSError:
            pass
    sizes.sort(reverse=True)
    markers = [m for m in BUILD_MARKERS if (repo / m).exists()]
    markers += [f for f in files if f.endswith(".spec")][:2]
    readme = "(none)"
    for cand in ("README.md", "README.rst", "README", "README.txt"):
        if (repo / cand).exists():
            readme = "\n".join((repo / cand).read_text(errors="ignore").splitlines()[:12])
            break
    lic = license_line(repo)
    top = sorted({f.split("/")[0] for f in files})
    txt = [
        f"repo: {name}",
        f"url: https://github.com/{URL.get(name, 'QubesOS/' + name)}",
        f"head: {sh(repo, 'git', 'rev-parse', '--short', 'HEAD')} (shallow clone, 2026-10-26)",
        f"license(first line): {lic}",
        f"tracked files: {len(files)} | total LOC (files<2MB): {loc}",
        "extensions by file count: " + ", ".join(f"{e}×{c}" for e, c in ext.most_common(8)),
        "build markers: " + (", ".join(markers) or "(none)"),
        "top-level entries: " + ", ".join(top[:25]),
        "largest files (lines path):",
        *[f"  {n:6} {f}" for n, f in sizes[:8]],
        "README head:", readme,
    ]
    (OUT / f"{name}.txt").write_text("\n".join(txt) + "\n")
    rows.append(f"{name:42} files={len(files):5} loc={loc:7} "
                f"top={','.join(e for e, _ in ext.most_common(3))} lic={lic[:38]}")

print("\n".join(rows))
print(f"evidence written: {OUT} ({len(rows)} repos)")
