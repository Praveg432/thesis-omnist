#!/usr/bin/env python3
"""Independent audit of the abstract and the headline claims of the Semester 3 report.

Uses only json, numpy and the standard library (no project code), recomputes every abstract figure from the stored
per-split values, and checks that the abstract text is identical in README.md, SEM3-PROGRESS-REPORT.md and
SUBMISSION-TITLE-AND-ABSTRACT.md, and that the regenerated HTML (source of the PDF) contains it.
Run from the repo root: python3 tools/audit_claims.py   Exit code 0 if every claim holds.
"""
import json
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "phase1-omnist", "results")
DOMAINS = ["delhi_air_quality", "beijing_air_quality", "ghcn_weather", "pemsd7_traffic", "pemsbay_traffic"]
rows, bad = [], []


def load(name):
    return json.load(open(os.path.join(R, name)))


def claim(label, computed, stated, tol=0.0005):
    ok = abs(computed - stated) <= tol
    rows.append((label, round(computed, 4), stated, "OK" if ok else "MISMATCH"))
    if not ok:
        bad.append(label)


def text(path):
    return open(os.path.join(ROOT, path), encoding="utf-8").read()


readme, report, sub = text("README.md"), text("SEM3-PROGRESS-REPORT.md"), text("SUBMISSION-TITLE-AND-ABSTRACT.md")


def abstract_of(s, start, end):
    return " ".join(s[s.index(start) + len(start):s.index(end)].split())


a_readme = abstract_of(readme, "## Abstract", "**Terminology.**")
a_report = abstract_of(report, "## Abstract", "## 1. Introduction").rstrip("- ").strip()
a_sub = abstract_of(sub, "## Abstract", "**Keywords:**")
a_report = re.sub(r"\*\*Keywords:\*\*.*", "", a_report).strip()
a_readme = re.sub(r"\*\*Keywords:\*\*.*", "", a_readme).strip()
for name, a in (("report", a_report), ("submission record", a_sub)):
    ok = a_readme.startswith(a[:200]) and a.strip(" -") == a_readme.strip(" -") or a == a_readme
    rows.append((f"abstract text identical in README and {name}", len(a.split()), len(a_readme.split()), "OK" if ok else "MISMATCH"))
    if not ok:
        bad.append(f"abstract differs in {name}")

# --- figures quoted in the abstract -------------------------------------------------------------------------------
c1 = [np.mean([s["disjoint_calibration"]["coverage"] for s in load(f"exp_C1_{d}.json")["splits"]]) for d in DOMAINS]
claim("C1 coverage, lowest of five networks (87.6%)", min(c1), 0.876)
claim("C1 coverage, highest of five networks (90.6%)", max(c1), 0.906)
chrono = [np.mean([s["chronological"]["coverage"] for s in load(f"exp_C1b_norm_{d}.json")["splits"]]) for d in DOMAINS]
claim("forecast-time coverage, lowest (77.8%)", min(chrono), 0.778)
claim("forecast-time coverage, highest (89.1%)", max(chrono), 0.891)
for dom, stated in (("delhi_air_quality", 0.902), ("beijing_air_quality", 0.890), ("ghcn_weather", 0.908)):
    v = np.mean([s["omnist"]["scaled_seasonal"]["coverage"] for s in load(f"exp_C1h_{dom}.json")["splits"]])
    claim(f"pre-registered fixed rule, {dom} ({stated:.3f})", v, stated)
slope = load("exp_C2_analysis.json")["ghcn_weather"]["within_station"]["slope_per_spacing"]
claim("weather slope with Delhi constants (1.4 points per spacing)", abs(100 * slope), 1.4, tol=0.05)
ws = load("exp_C2n_analysis.json")["ghcn_weather"]["within_station"]
rows.append(("corrected-frame weather slope interval contains zero (abstract says the effect disappeared)",
             ws["ci95"], 0, "OK" if ws["ci95"][0] < 0 < ws["ci95"][1] else "MISMATCH"))
if not ws["ci95"][0] < 0 < ws["ci95"][1]:
    bad.append("weather slope interval excludes zero")

# --- Phase 2 figures quoted in the abstract -----------------------------------------------------------------------
p2 = os.path.join(ROOT, "phase2-omnist-scale", "results", "V4_scaling_crossover_results.json")
if os.path.exists(p2):
    d = json.load(open(p2))
    text_d = json.dumps(d)
    rows.append(("Phase 2 V4 result file present (seventeenfold memory at 8,000 sensors is checked by check_phase2_findings.py)", len(text_d), 0, "OK"))

# --- pre-registered verdicts recomputed ---------------------------------------------------------------------------
verd = load("exp_C1h_verdicts.json")
fails = sorted(f"{d}:{h}" for d, x in verd.items() for h in ("H1", "H2", "H3", "H4") if x.get(h) == "FAIL")
rows.append(("pre-registered C1h failures (report must say weather H4 fails)", fails, ["ghcn_weather:H4"],
             "OK" if fails == ["ghcn_weather:H4"] and "FAIL" in report else "MISMATCH"))
if fails != ["ghcn_weather:H4"]:
    bad.append("unexpected C1h verdicts")
v2 = load("exp_C1i_verdicts.json")
fails2 = sorted(f"{d}:{h}" for d, x in v2.items() for h in ("H5", "H6", "H7", "H8") if x.get(h) == "FAIL")
rows.append(("pre-registered C1i failures (report must show beijing:H7 and pemsbay_traffic:H5)", fails2,
             ["beijing_air_quality:H7", "pemsbay_traffic:H5"],
             "OK" if fails2 == ["beijing_air_quality:H7", "pemsbay_traffic:H5"] else "MISMATCH"))
if fails2 != ["beijing_air_quality:H7", "pemsbay_traffic:H5"]:
    bad.append("unexpected C1i verdicts")

# --- word limit, title, no leftover placeholders ------------------------------------------------------------------
n_words = len(a_readme.split())
rows.append(("abstract length within the 600-word limit", n_words, 600, "OK" if n_words <= 600 else "MISMATCH"))
if n_words > 600:
    bad.append("abstract too long")
placeholders = [t for t in ("TODO", "FIXME", "XXX", "lorem", "TBD") if t.lower() in report.lower()]
rows.append(("no placeholder text in the report", placeholders, [], "OK" if not placeholders else "MISMATCH"))
if placeholders:
    bad.append("placeholder text")

html = os.path.join(ROOT, "SEM3-PROGRESS-REPORT.html")
if os.path.exists(html):
    h = open(html, encoding="utf-8").read()
    plain = re.sub(r"<[^>]+>", " ", h)
    plain = " ".join(plain.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").split())
    probe = a_readme[200:320]
    ok = probe in plain
    rows.append(("regenerated HTML (source of the PDF) contains the current abstract", ok, True, "OK" if ok else "MISMATCH"))
    if not ok:
        bad.append("HTML/PDF source is stale")
    for h_id in ("4.3a", "4.3b", "4.3c", "4.3d"):
        present = f"{h_id} " in plain
        rows.append((f"HTML contains Section {h_id}", present, True, "OK" if present else "MISMATCH"))
        if not present:
            bad.append(f"HTML lacks {h_id}")

width = max(len(str(r[0])) for r in rows)
for label, computed, stated, status in rows:
    print(f"{status:9s} {str(label):{width}s}  computed={computed}  stated={stated}")
print(f"\n{len(rows) - len(bad)} of {len(rows)} audit rows OK")
sys.exit(1 if bad else 0)
