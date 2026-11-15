#!/usr/bin/env python3
"""Check the draft title and abstract in SUBMISSION-TITLE-AND-ABSTRACT.md against the same rules as
tools/check_submission_text.py, and tie every number in it to a committed result file.
Run from the repo root: python3 tools/check_draft_abstract.py   (exit 1 on any failure)
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P1 = os.path.join(ROOT, "phase1-omnist", "results")
P2 = os.path.join(ROOT, "phase2-omnist-scale", "results")
FILLER = ("an investigation", "a study", "theory of", "some ", "an experimental investigation", "toward")
doc = open(os.path.join(ROOT, "SUBMISSION-TITLE-AND-ABSTRACT.md"), encoding="utf-8").read()
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


title = re.search(r"^## Title\s+\*\*(.+?)\*\*", doc, re.M | re.S).group(1).strip()
abstract = doc[doc.index("## Abstract") + len("## Abstract"):doc.index("**Keywords:**")].strip()
words = title.split()
check(10 <= len(words) <= 15, f"title has {len(words)} words; the manual prefers 10 to 15")
check(not re.search(r"\d", title), "title contains a digit")
check(not re.search(r"[()\[\]=+*/<>%$#@]|[\u0370-\u03ff]", title), "title contains a symbol or Greek letter")
check(not [w for w in re.findall(r"[A-Za-z]+", title) if len(w) > 1 and w.isupper()], "title contains an acronym")
check(not any(title.lower().startswith(f) for f in FILLER), "title starts with a filler phrase")
for w in ("certif", "calibrated", "scal", "topology"):
    check(w not in title.lower(), f"title commits to '{w}'")
n = len(abstract.split())
check(n <= 600, f"abstract has {n} words (limit 600)")
check("\u2014" not in abstract, "abstract contains an em dash")
for w in ("certif", "guarantee that", "will be packaged", "will be localised"):
    check(w not in abstract.lower(), f"abstract contains '{w}'")

doms = ["delhi_air_quality", "beijing_air_quality", "ghcn_weather", "pemsd7_traffic", "pemsbay_traffic"]
means = [json.load(open(os.path.join(P1, f"exp_C1_{d}.json")))["aggregate"]["disjoint_calibration"][
    "coverage_over_splits"]["mean"] for d in doms]
check(f"between {100 * min(means):.1f}% and {100 * max(means):.1f}%" in abstract, "coverage range does not match C1")
slope = json.load(open(os.path.join(P1, "exp_C2_analysis.json")))["ghcn_weather"]["within_station"]["slope_per_spacing"]
check(f"about {abs(100 * slope):.1f} points" in abstract, "weather slope does not match C2")
check("five real networks" in abstract, "should say 'five real networks'")

v4 = {r["N"]: r for r in json.load(open(os.path.join(P2, "V4_scaling_crossover_results.json")))["spatial"]}
r8 = v4[8000]["exact_mem_mb"] / v4[8000]["fast_mem_mb"]
check(16.0 <= r8 < 18.0 and "seventeenfold at 8,000 sensors" in abstract, f"memory ratio at 8000 is {r8:.1f}")
check(all(v4[N]["exact_mem_mb"] / v4[N]["fast_mem_mb"] <= 1.05 for N in (100, 500, 1000))
      and "no gain below about a thousand" in abstract, "claimed no gain below 1000 does not hold")
v3 = json.load(open(os.path.join(P2, "V3_coverage_at_scale_real.json")))["real_pemsbay"]
order_ok = all(v["persist"]["deployable"]["width"]["mean"] > v["model"]["deployable"]["width"]["mean"]
               > v["seasonal"]["deployable"]["width"]["mean"] for v in v3.values())
check(order_ok and "narrower than those of a persistence forecast but wider than those of a seasonal one" in abstract,
      "traffic width ordering does not hold")

if fails:
    print("\n".join(fails)); sys.exit(1)
print(f"draft OK: title {len(words)} words, abstract {n} words; all figures tie to the result files")
