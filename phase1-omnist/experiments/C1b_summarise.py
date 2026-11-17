#!/usr/bin/env python3
"""Print the C1b summary table and apply the pre-registered decision rules (see C1b_chronological_eval.py).
Reads results/exp_C1b_<domain>.json and results/exp_C1_<domain>.json. Run: python experiments/C1b_summarise.py
"""
import json
import os

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
DOMAINS = ["delhi_air_quality", "beijing_air_quality", "ghcn_weather", "pemsd7_traffic", "pemsbay_traffic"]
TARGET = 0.90


def fmt(ci: dict) -> str:
    lo, hi = ci["ci95"]
    return f"{ci['mean']:.3f} [{lo:.3f}, {hi:.3f}]" if lo is not None else f"{ci['mean']:.3f}"


def verdicts(chrono_mean: float, c1_mean: float) -> list:
    out = []
    if abs(chrono_mean - TARGET) <= 0.02:
        out.append("(a) within 0.02 of 0.90")
    if abs(chrono_mean - c1_mean) > 0.01:
        out.append("(b) differs from C1 by more than 0.01")
    if chrono_mean < 0.85:
        out.append("(c) below 0.85: under-coverage")
    return out or ["no rule triggered"]


def main() -> None:
    print("| Dataset | Splits | Chronological | Same-window (C1 protocol) | Pooled over time | C1 mean (full period) | Chronological per-station: mean / 10th pct / min | Rules |")
    print("|---|:---:|---|---|---|:---:|---|---|")
    for dom in DOMAINS:
        path = os.path.join(RESULTS, f"exp_C1b_{dom}.json")
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        a = d["aggregate"]
        c1_mean = json.load(open(os.path.join(RESULTS, f"exp_C1_{dom}.json")))["aggregate"][
            "disjoint_calibration"]["coverage_over_splits"]["mean"]
        ps = a["chronological"]["per_station_coverage"]
        chrono = a["chronological"]["coverage_over_splits"]["mean"]
        print(f"| {dom} | {len(d['splits'])} | {fmt(a['chronological']['coverage_over_splits'])} | "
              f"{fmt(a['same_window']['coverage_over_splits'])} | {fmt(a['pooled']['coverage_over_splits'])} | "
              f"{c1_mean:.3f} | {ps['mean']:.3f} / {ps['p10']:.3f} / {ps['min']:.3f} | "
              f"{'; '.join(verdicts(chrono, c1_mean))} |")


if __name__ == "__main__":
    main()
