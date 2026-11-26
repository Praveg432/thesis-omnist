#!/usr/bin/env python3
"""Audit tracked Markdown files for broken relative links and missing backticked paths.

Run from the repo root: python3 tools/audit_links.py
Exit code 0 if nothing is broken, 1 otherwise.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
TICK_RE = re.compile(r"`([A-Za-z0-9_./\-]+\.(?:py|json|md|csv|npz|toml|txt|tex|pdf|png))`")
EXTERNAL = ("http://", "https://", "mailto:")


def tracked_markdown() -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "*.md"], text=True)
    return [line for line in out.splitlines() if line]


def tracked_basenames() -> set[str]:
    out = subprocess.check_output(["git", "ls-files"], text=True)
    return {os.path.basename(line) for line in out.splitlines() if line}


TRACKED_BASENAMES = tracked_basenames()

# Paths that name files inside an upstream *external* repository (the download source for the
# gitignored traffic speed series), not files in this repo. See phase1-omnist/data/README.md.
EXTERNAL_SOURCE_PATHS = {"data/pems-bay/vel.csv", "vel.csv"}
# Files that phase1-omnist/data/README.md tells the reader to download; they are deliberately not committed, so
# they are absent on a clean checkout. Only that README may name them.
DOWNLOADED_BY_README = {"data/real_pems/pemsd7_vel.csv", "data/real_pems/pemsbay_vel.csv"}
README_WITH_DOWNLOADS = "phase1-omnist/data/README.md"


def main() -> int:
    files = tracked_markdown()
    broken_links: list[tuple[str, str]] = []
    broken_ticks: set[tuple[str, str]] = set()

    for path in files:
        base = os.path.dirname(path)
        with open(path, encoding="utf-8", errors="ignore") as handle:
            text = handle.read()

        for match in LINK_RE.finditer(text):
            target = match.group(1).split("#")[0]
            if not target or target.startswith(EXTERNAL):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(base, target))):
                broken_links.append((path, target))

        phase_root = path.split("/")[0] if path.startswith("phase") else ""
        for match in TICK_RE.finditer(text):
            target = match.group(1)
            if target in EXTERNAL_SOURCE_PATHS or (path == README_WITH_DOWNLOADS and target in DOWNLOADED_BY_README):
                continue
            candidates = [
                os.path.normpath(os.path.join(base, target)),  # relative to the doc
                target,                                        # relative to repo root
                os.path.join(phase_root, target) if phase_root else target,  # phase root
            ]
            if any(os.path.exists(c) for c in candidates):
                continue
            # A bare reference such as `exp_calibration.json` is accepted if exactly
            # that file exists somewhere in the repo (results/ and figures/ are flat).
            if os.path.basename(target) in TRACKED_BASENAMES and "/" not in target:
                continue
            broken_ticks.add((path, target))

    print(f"markdown files scanned: {len(files)}")
    print(f"broken markdown links: {len(broken_links)}")
    for item in broken_links:
        print("  LINK", item)
    print(f"missing backticked paths: {len(broken_ticks)}")
    for item in sorted(broken_ticks):
        print("  PATH", item)
    return 1 if (broken_links or broken_ticks) else 0


if __name__ == "__main__":
    sys.exit(main())
