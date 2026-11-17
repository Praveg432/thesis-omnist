#!/usr/bin/env python3
"""Check that the C1b, C1c and C1d figures quoted in SEM3-PROGRESS-REPORT.md Section 4.3a and 4.6 match the
committed result files. Run from the repo root. Exit code 0 if all match, 1 otherwise."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "phase1-omnist", "results")
report = " ".join(open(os.path.join(ROOT, "SEM3-PROGRESS-REPORT.md"), encoding="utf-8").read().split())
report_lines = open(os.path.join(ROOT, "SEM3-PROGRESS-REPORT.md"), encoding="utf-8").read()
LABEL = {"delhi_air_quality": "Delhi", "beijing_air_quality": "Beijing", "ghcn_weather": "NOAA weather",
         "pemsd7_traffic": "PeMSD7-M", "pemsbay_traffic": "PeMS-BAY"}
failures, n_checked = [], 0


def load(name):
    return json.load(open(os.path.join(R, name)))


def need(text, label):
    global n_checked
    n_checked += 1
    if text not in report:
        failures.append(f"missing {text!r} ({label})")


section = report_lines[report_lines.index("### 4.3a"):report_lines.index("### 4.4")]
for dom, label in LABEL.items():
    c1 = load(f"exp_C1_{dom}.json")["aggregate"]["disjoint_calibration"]["coverage_over_splits"]["mean"]
    b = load(f"exp_C1b_{dom}.json")["aggregate"]
    n = load(f"exp_C1b_norm_{dom}.json")["aggregate"]
    row = next(l for l in section.splitlines() if l.startswith(f"| {label} ") and "|:---:|" not in l and l.count("|") == 7)
    cells = [f"{c1:.3f}", f"{b['same_window']['coverage_over_splits']['mean']:.3f}",
             f"{b['chronological']['coverage_over_splits']['mean']:.3f}",
             f"{n['chronological']['coverage_over_splits']['mean']:.3f}"]
    for cell in cells:
        n_checked += 1
        if f"| {cell} " not in row and not row.rstrip().endswith(f"| {cell} |"):
            failures.append(f"{label}: C1b table row lacks {cell}: {row}")

    base = load(f"exp_C1c_baselines_{dom}.json")["aggregate"]
    model = (n["chronological"]["coverage_over_splits"]["mean"], n["chronological"]["width_over_splits"]["mean"],
             n["test_mae_over_splits"]["mean"])
    parts = [model] + [(m["coverage_over_splits"]["mean"], m["width_over_splits"]["mean"], m["mae_over_splits"]["mean"])
                       for m in base.values()]
    brow = next(l for l in section.splitlines() if l.startswith(f"| {label if label != 'NOAA weather' else 'Weather'} | OmniST"))
    for idx, fmts in enumerate((("{:.3f}",), ("{:.1f}",), ("{:.2f}", "{:.1f}"))):
        candidates = [" / ".join(f.format(p[idx]) for p in parts) for f in fmts]
        n_checked += 1
        if not any(c in brow for c in candidates):
            failures.append(f"{label}: baseline row lacks any of {candidates}: {brow}")

for dom, ratio_keys in {"delhi_air_quality": (1.90, 1.03), "beijing_air_quality": (2.11, 0.99), "ghcn_weather": (0.87, 1.08)}.items():
    agg = load(f"exp_C1d_diagnosis_{dom}.json")["aggregate"]
    got = (round(agg["late_over_early_error_cal_mean"], 2), round(agg["test_over_cal_error_mean"], 2))
    n_checked += 1
    if got != ratio_keys:
        failures.append(f"{dom}: C1d ratios in report {ratio_keys} but files give {got}")
    thirds = ", ".join(f"{x:.2f}" for x in agg["coverage_by_third_mean"])
    need(thirds, f"{dom} coverage by third")

if failures:
    print("\n".join(failures))
    sys.exit(1)
print(f"all {n_checked} C1b/C1c/C1d report figures match the committed result files")
