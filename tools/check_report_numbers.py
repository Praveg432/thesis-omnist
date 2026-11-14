#!/usr/bin/env python3
"""Check that the numbers quoted in the Semester-3 report and the proposal match the result files.

Builds the expected strings from the committed result JSON files and fails if any is missing from the
documents. Run from the repo root: python3 tools/check_report_numbers.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P1 = os.path.join(ROOT, "phase1-omnist", "results")
P2 = os.path.join(ROOT, "phase2-omnist-scale", "results")
DOCS = {name: open(os.path.join(ROOT, name), encoding="utf-8").read()
        for name in ("SEM3-PROGRESS-REPORT.md", "MTECH-THESIS-PROPOSAL.md")}

DOMAIN_LABEL = {"delhi_air_quality": "Delhi PM2.5", "beijing_air_quality": "Beijing PM2.5",
                "ghcn_weather": "NOAA weather", "pemsd7_traffic": "PeMSD7-M traffic",
                "pemsbay_traffic": "PeMS-BAY traffic"}
failures = []
checked = 0


def need(doc: str, text: str, why: str) -> None:
    global checked
    checked += 1
    if text not in DOCS[doc]:
        failures.append(f"{doc}: missing '{text}' ({why})")


for dom, label in DOMAIN_LABEL.items():
    d = json.load(open(os.path.join(P1, f"exp_C1_{dom}.json")))
    a, s0 = d["aggregate"], d["splits"][0]
    dis, leg = a["disjoint_calibration"], a["legacy_train_station_calibration"]
    ci = dis["coverage_over_splits"]
    stations = f"{s0['n_train']} / {s0['n_cal']} / {s0['n_test']}"
    cells = [label, stations, str(len(d["splits"])),
             f"{ci['mean']:.3f} [{ci['ci95'][0]:.3f}, {ci['ci95'][1]:.3f}]",
             f"{leg['coverage_over_splits']['mean']:.3f}",
             f"{dis['per_station_coverage']['mean']:.3f} / {dis['per_station_coverage']['p10']:.3f} / "
             f"{dis['per_station_coverage']['min']:.3f}"]
    row = "| " + " | ".join(cells) + " |"
    for doc in DOCS:
        need(doc, row, f"C1 table row for {dom}")

v1 = json.load(open(os.path.join(P2, "V1_ssm_matches_omnist_results.json")))["variants"]
need("SEM3-PROGRESS-REPORT.md", f"{v1['ssm+fast']['mae']['mean']:.2f} against {v1['gru+exact']['mae']['mean']:.2f}",
     "V1 MAE")
need("SEM3-PROGRESS-REPORT.md", f"{v1['ssm+fast']['coverage']['mean']:.3f} against {v1['gru+exact']['coverage']['mean']:.3f}",
     "V1 coverage")

t1 = json.load(open(os.path.join(P2, "T1_ssm_vs_gru_timing.json")))["rows"]
need("SEM3-PROGRESS-REPORT.md",
     " / ".join(f"{r['ssm_ms']}" for r in t1), "T1 SSM times")
need("SEM3-PROGRESS-REPORT.md",
     " / ".join(f"{r['gru_ms']}" for r in t1), "T1 GRU times")

v2 = json.load(open(os.path.join(P2, "V2_attention_equivalence_results.json")))
need("SEM3-PROGRESS-REPORT.md", f"{v2['min_cosine_vs_exact']:.5f}", "V2 minimum cosine")

ig = json.load(open(os.path.join(P1, "exp_ignnk_inductive.json")))["results_by_domain"]["delhi_air_quality"]
need("SEM3-PROGRESS-REPORT.md", f"{ig['omnist_inductive_mae'][0]:.1f} for OmniST against {ig['ignnk_inductive_mae'][0]:.1f}",
     "IGNNK MAE")

# ---- C2 (distance experiment) rows in the report -------------------------------------------------
import numpy as np  # noqa: E402

c2_analysis = json.load(open(os.path.join(P1, "exp_C2_analysis.json")))
for dom, label in DOMAIN_LABEL.items():
    splits = json.load(open(os.path.join(P1, f"exp_C2_{dom}.json")))["splits"]
    cov = np.array([s["coverage"] for s in splits])
    test_d = np.mean([np.mean(s["test_d1"]) for s in splits])
    cal_d = np.mean([np.mean(s["cal_d1"]) for s in splits])
    scattered = json.load(open(os.path.join(P1, f"exp_C1_{dom}.json")))["aggregate"]["disjoint_calibration"][
        "coverage_over_splits"]["mean"]
    ws = c2_analysis[dom]["within_station"]
    row = (f"| {label} | {cov.mean():.3f} ({cov.std(ddof=1):.3f}) | {scattered:.3f} | "
           f"{test_d:.2f} vs {cal_d:.2f} | {ws['slope_per_spacing']:+.4f} [{ws['ci95'][0]:+.4f}, {ws['ci95'][1]:+.4f}] |")
    need("SEM3-PROGRESS-REPORT.md", row, f"C2 table row for {dom}")

# ---- C3 (total-variation feasibility) figures ----------------------------------------------------
c3 = {d: json.load(open(os.path.join(P1, f"exp_C3_{d}.json"))) for d in ("delhi_air_quality", "ghcn_weather")}
for dom, label in (("delhi_air_quality", "Delhi PM2.5"), ("ghcn_weather", "NOAA weather")):
    d = c3[dom]
    row = (f"| {label} | {d['tv_pairs']['median']:.3f} | {d['noise_floor_random_halves_median']:.3f} | "
           f"{d['tv_pairs']['nearest_quartile_median']:.3f} vs {d['tv_pairs']['farthest_quartile_median']:.3f} | "
           f"{d['bound_loss_3_nearest_median']:.3f} |")
    need("SEM3-PROGRESS-REPORT.md", row, f"C3 table row for {dom}")
need("SEM3-PROGRESS-REPORT.md", f"{c3['delhi_air_quality']['tv_pairs']['median']:.2f} in Delhi and "
     f"{c3['ghcn_weather']['tv_pairs']['median']:.2f} in the weather data", "C3 medians in the text")
need("SEM3-PROGRESS-REPORT.md", f"(Spearman correlation {c3['ghcn_weather']['tv_pairs']['spearman_rho_distance']:.2f})",
     "C3 weather correlation")

if failures:
    print("\n".join(failures))
    sys.exit(1)
print(f"all {checked} quoted figures match the committed result files")
