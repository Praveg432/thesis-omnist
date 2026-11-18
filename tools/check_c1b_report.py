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

# ---- Section 4.3b: multi-year rules (C1f), HCP (C1g), residual head --------------------------------------
sec_b = report_lines[report_lines.index("### 4.3b"):report_lines.index("### 4.4")]
rows = {"Same test year only": "expanding_within", "All earlier windows, across years": "expanding_all",
        "Earlier years, same season (within 45 days)": "seasonal",
        "All earlier windows, errors scaled by forecast magnitude": "scaled_predmag_all",
        "Earlier years, same season, scaled by forecast magnitude": "scaled_predmag_seasonal"}
fd = load("exp_C1f_delhi_air_quality.json")["aggregate"]
fb = load("exp_C1f_beijing_air_quality.json")["aggregate"]
for label, rule in rows.items():
    line = next(l for l in sec_b.splitlines() if l.startswith(f"| {label}"))
    want = [f"{fd[rule]['coverage_mean']:.3f}", f"{fd[rule]['width_mean']:.1f}",
            f"{fb[rule]['coverage_mean']:.3f}", f"{fb[rule]['width_mean']:.1f}"]
    for w in want:
        n_checked += 1
        if f"| {w} " not in line:
            failures.append(f"C1f row {label!r} lacks {w}: {line}")
for dom, before, after in (("delhi_air_quality", "0.809", "0.924"), ("ghcn_weather", "0.873", "0.985")):
    g = load(f"exp_C1g_hcp_{dom}.json")["aggregate"]
    got = (f"{g['pooled_expanding']['coverage_mean']:.3f}", f"{g['hcp_expanding']['coverage_mean']:.3f}")
    n_checked += 1
    if got != (before, after):
        failures.append(f"C1g {dom}: report says {before} to {after}, files give {got}")
for dom, old, new in (("pemsd7_traffic", "3.79", "3.69"), ("ghcn_weather", "4.73", "4.76"), ("pemsbay_traffic", "4.73", "5.04")):
    got = (f"{load(f'exp_C1b_norm_{dom}.json')['aggregate']['test_mae_over_splits']['mean']:.2f}",
           f"{load(f'exp_C1b_resid_{dom}.json')['aggregate']['test_mae_over_splits']['mean']:.2f}")
    n_checked += 1
    if got != (old, new):
        failures.append(f"residual head {dom}: report says {old} to {new}, files give {got}")

# ---- Section 4.3c: pre-registered confirmation (C1h) -----------------------------------------------------
sec_c = report_lines[report_lines.index("### 4.3c"):report_lines.index("### 4.4")]
verd = load("exp_C1h_verdicts.json")
for dom, label in (("delhi_air_quality", "Delhi"), ("beijing_air_quality", "Beijing"), ("ghcn_weather", "Weather")):
    x = verd[dom]
    line = next(l for l in sec_c.splitlines() if l.startswith(f"| {label}"))
    want = [f"{x['coverage_same_year']['mean']:.3f}", f"{x['coverage_scaled_seasonal']['mean']:.3f}",
            f"{x['width_same_year']:.1f} / {x['width_scaled_seasonal']:.1f}",
            f"{x['interval_score']['omnist']:.1f} / {x['interval_score']['persistence']:.1f}",
            x["H2" if dom == "ghcn_weather" else "H1"], x["H3"], x["H4"]]
    for w in want:
        n_checked += 1
        if w not in line:
            failures.append(f"C1h row {label} lacks {w}: {line}")

# ---- Section 4.3d: second pre-registered round (C1i/C1j) ---------------------------------------------------
sec_d = report_lines[report_lines.index("### 4.3d"):report_lines.index("### 4.4")]
vi = load("exp_C1i_verdicts.json")
for dom, label in (("delhi_air_quality", "Delhi"), ("beijing_air_quality", "Beijing"), ("ghcn_weather", "Weather")):
    x = vi[dom]
    line = next(l for l in sec_d.splitlines() if l.startswith(f"| {label} |"))
    want = [f"{x[r]['coverage']['mean']:.3f}" for r in ("same_year", "c1h_seasonal_scaled", "online_selection")]
    want += [f"{x['c1h_seasonal_scaled']['width']:.1f} / {x['online_selection']['width']:.1f}", x["H6"], x["H7"]]
    for w in want:
        n_checked += 1
        if w not in line:
            failures.append(f"C1i row {label} lacks {w}: {line}")
for dom, label in (("pemsd7_traffic", "PeMSD7-M"), ("pemsbay_traffic", "PeMS-BAY")):
    x = vi[dom]
    line = next(l for l in sec_d.splitlines() if l.startswith(f"| {label} |"))
    for w in (f"{x['expanding']['coverage']['mean']:.3f}", f"{x['time_of_day_scaled']['coverage']['mean']:.3f}", x["H5"]):
        n_checked += 1
        if w not in line:
            failures.append(f"C1j row {label} lacks {w}: {line}")
n_checked += 1
if f"{vi['pemsbay_hcp']['hcp']['coverage_mean']:.3f}" not in sec_d:
    failures.append("4.3d lacks the PeMS-BAY station-level coverage")

if failures:
    print("\n".join(failures))
    sys.exit(1)
print(f"all {n_checked} C1b to C1j report figures match the committed result files")
