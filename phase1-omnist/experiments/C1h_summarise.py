#!/usr/bin/env python3
"""Evaluate the pre-registered hypotheses H1 to H4 of PRE-REGISTRATION-C1H.md from results/exp_C1h_<domain>.json.
Writes results/exp_C1h_verdicts.json and prints a Markdown table. Exit code 0 always (verdicts are data)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np

from src.interval_metrics import paired_difference

RESULTS = os.path.join(os.path.dirname(HERE), "results")
DOMAINS = {"delhi_air_quality": "Delhi", "beijing_air_quality": "Beijing", "ghcn_weather": "Weather"}
TARGET, TOL = 0.90, 0.02


def ci(values):
    from scipy import stats
    v = np.asarray(values, dtype=float)
    m, s = float(v.mean()), float(v.std(ddof=1))
    h = float(stats.t.ppf(0.975, len(v) - 1)) * s / np.sqrt(len(v))
    return {"mean": round(m, 4), "ci95": [round(m - h, 4), round(m + h, 4)], "n": int(len(v))}


def main():
    verdicts, rows = {}, []
    for dom, label in DOMAINS.items():
        path = os.path.join(RESULTS, f"exp_C1h_{dom}.json")
        if not os.path.exists(path):
            continue
        sp = json.load(open(path))["splits"]
        get = lambda m, r, k: [s[m][r][k] for s in sp]
        cov = ci(get("omnist", "scaled_seasonal", "coverage"))
        same = ci(get("omnist", "same_year", "coverage"))
        station = np.concatenate(get("omnist", "scaled_seasonal", "per_station_coverage"))
        is_model = get("omnist", "scaled_seasonal", "interval_score")
        d_pers = paired_difference(is_model, get("persistence", "scaled_seasonal", "interval_score"))
        d_sn = paired_difference(is_model, get("seasonal_naive", "scaled_seasonal", "interval_score"))
        d_rule = paired_difference(is_model, get("omnist", "same_year", "interval_score"))
        coverage_hyp = "H2" if dom == "ghcn_weather" else "H1"
        v = {"n_splits": len(sp), "coverage_scaled_seasonal": cov, "coverage_same_year": same,
             "width_scaled_seasonal": round(float(np.mean(get("omnist", "scaled_seasonal", "width"))), 3),
             "width_same_year": round(float(np.mean(get("omnist", "same_year", "width"))), 3),
             "fraction_stations_below_0.80": round(float((station < 0.80).mean()), 3),
             "baseline_coverage_scaled_seasonal": {m: round(float(np.mean(get(m, "scaled_seasonal", "coverage"))), 4)
                                                   for m in ("persistence", "seasonal_naive")},
             "interval_score": {"omnist": round(float(np.mean(is_model)), 3),
                                "persistence": round(float(np.mean(get("persistence", "scaled_seasonal", "interval_score"))), 3),
                                "seasonal_naive": round(float(np.mean(get("seasonal_naive", "scaled_seasonal", "interval_score"))), 3),
                                "omnist_same_year": round(float(np.mean(get("omnist", "same_year", "interval_score"))), 3)},
             "diff_vs_persistence": d_pers, "diff_vs_seasonal_naive": d_sn, "diff_vs_same_year_rule": d_rule,
             coverage_hyp: "PASS" if abs(cov["mean"] - TARGET) <= TOL else "FAIL",
             "H3": "PASS" if d_pers["ci95"][1] < 0 and d_sn["ci95"][1] < 0 else "FAIL",
             "H4": "PASS" if d_rule["ci95"][1] < 0 else "FAIL"}
        verdicts[dom] = v
        rows.append(f"| {label} | {len(sp)} | {same['mean']:.3f} | {cov['mean']:.3f} [{cov['ci95'][0]:.3f}, {cov['ci95'][1]:.3f}] "
                    f"| {v['fraction_stations_below_0.80']:.3f} | {v['interval_score']['omnist']:.1f} / {v['interval_score']['persistence']:.1f} / "
                    f"{v['interval_score']['seasonal_naive']:.1f} / {v['interval_score']['omnist_same_year']:.1f} "
                    f"| {v[coverage_hyp]} ({coverage_hyp}) | {v['H3']} | {v['H4']} |")
    json.dump(verdicts, open(os.path.join(RESULTS, "exp_C1h_verdicts.json"), "w"), indent=2)
    print("| Network | Splits | Coverage, same-year rule | Coverage, scaled seasonal [95% CI] | Stations below 0.80 | "
          "Interval score: OmniST / persistence / seasonal-naive / OmniST same-year | Coverage hypothesis | H3 | H4 |")
    print("|---|:---:|:---:|:---:|:---:|---|:---:|:---:|:---:|")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
