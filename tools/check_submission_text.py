#!/usr/bin/env python3
"""Check the submission text: title rules, title identity, abstract limits and abstract numbers.

Run from the repo root: python3 tools/check_submission_text.py
Exit code 0 if every check passes, 1 otherwise.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "phase1-omnist", "results")
FILLER = ("an investigation", "a study", "theory of", "some ", "an experimental investigation", "toward")
failures = []


def read(rel):
    return open(os.path.join(ROOT, rel), encoding="utf-8").read()


def norm(text):
    return " ".join(text.split())


def check(condition, message):
    if not condition:
        failures.append(message)


readme, proposal, report = read("README.md"), read("MTECH-THESIS-PROPOSAL.md"), read("SEM3-PROGRESS-REPORT.md")

# ---- title: identical everywhere ---------------------------------------------------------------
readme_title = re.search(r"^# (.+)$", readme, re.M).group(1).strip()
proposal_title = re.search(r"^## (.+)$", proposal, re.M).group(1).strip()
report_title = re.search(r"\| \*\*Project Title\*\* \| (.+?) \|$", report, re.M).group(1).strip()
check(readme_title == proposal_title == report_title,
      f"title differs between documents:\n  README:   {readme_title}\n  proposal: {proposal_title}\n  report:   {report_title}")
title = readme_title

# ---- title: IIT Patna manual rules (section 1.2) -------------------------------------------------
words = title.split()
check(len(words) <= 20, f"title has {len(words)} words; the manual allows at most 20")
check(10 <= len(words) <= 15, f"title has {len(words)} words; the manual prefers 10 to 15")
check(not re.search(r"\d", title), "title contains a digit")
check(not re.search(r"[()\[\]=+*/<>%$#@]|[\u0370-\u03ff]", title), "title contains a symbol or Greek letter")
check(not [w for w in re.findall(r"[A-Za-z]+", title) if len(w) > 1 and w.isupper()], "title contains an acronym")
check(not any(title.lower().startswith(f) for f in FILLER), "title starts with a discouraged filler phrase")
check("certif" not in title.lower(), "title still contains the word 'certified'")

# ---- abstract: README and report identical, within the 600-word limit ----------------------------
readme_abs = readme[readme.index("## Abstract") + len("## Abstract"):readme.index("**Terminology.**")].strip()
report_abs = report[report.index("## Abstract") + len("## Abstract"):report.index("## 1. Introduction")]
report_abs = report_abs.strip().rstrip("-").strip()
check(norm(readme_abs) == norm(report_abs), "the README abstract and the report abstract differ")
n_words = len(readme_abs.split())
check(n_words <= 600, f"abstract has {n_words} words; Annexure-I allows at most 600")
check("certif" not in readme_abs.lower(), "abstract still uses the word 'certified'")
check("em dash" not in readme_abs and "\u2014" not in readme_abs, "abstract contains an em dash")

# ---- abstract numbers tie back to the result files -----------------------------------------------
domains = ["delhi_air_quality", "beijing_air_quality", "ghcn_weather", "pemsd7_traffic", "pemsbay_traffic"]
means = [json.load(open(os.path.join(RESULTS, f"exp_C1_{d}.json")))["aggregate"]["disjoint_calibration"][
    "coverage_over_splits"]["mean"] for d in domains]
low, high = f"{100 * min(means):.1f}%", f"{100 * max(means):.1f}%"
check(f"between {low} and {high}" in readme_abs, f"abstract coverage range should read 'between {low} and {high}'")
chrono = [json.load(open(os.path.join(RESULTS, f"exp_C1b_norm_{d}.json")))["aggregate"]["chronological"][
    "coverage_over_splits"]["mean"] for d in domains]
clow, chigh = f"{100 * min(chrono):.1f}%", f"{100 * max(chrono):.1f}%"
check(f"between {clow} and {chigh}" in readme_abs,
      f"abstract forecast-time coverage range should read 'between {clow} and {chigh}' (C1b, training-station frame)")
slope = json.load(open(os.path.join(RESULTS, "exp_C2_analysis.json")))["ghcn_weather"]["within_station"]["slope_per_spacing"]
check(f"about {abs(100 * slope):.1f} points" in readme_abs, f"abstract slope should read 'about {abs(100 * slope):.1f} points'")
check(len(domains) == 5 and "five real networks" in readme_abs, "abstract should say 'five real networks'")

if failures:
    print("\n".join(failures))
    sys.exit(1)
print(f"submission text OK: title {len(words)} words, abstract {n_words} words, "
      f"coverage range {low} to {high}, weather slope {abs(100 * slope):.1f} points")
