#!/usr/bin/env python3
"""Evaluate H5 to H8 of PRE-REGISTRATION-C1I.md. Writes results/exp_C1i_verdicts.json, prints Markdown tables."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np

from src.interval_metrics import paired_difference

RESULTS = os.path.join(os.path.dirname(HERE), "results")
TARGET, TOL = 0.90, 0.02
C1H_DELHI_CI_WIDTH = 0.018


def ci(values):
    from scipy import stats
    v = np.asarray(values, dtype=float)
    m, s = float(v.mean()), float(v.std(ddof=1))
    h = float(stats.t.ppf(0.975, len(v) - 1)) * s / np.sqrt(len(v))
    return {"mean": round(m, 4), "ci95": [round(m - h, 4), round(m + h, 4)], "n": int(len(v))}


def load(dom):
    p = os.path.join(RESULTS, f"exp_C1i_{dom}.json")
    return json.load(open(p))["splits"] if os.path.exists(p) else None


def rule_stats(sp, rule):
    station = np.concatenate([s[rule]["per_station_coverage"] for s in sp])
    return {"coverage": ci([s[rule]["coverage"] for s in sp]),
            "width": round(float(np.mean([s[rule]["width"] for s in sp])), 3),
            "interval_score": round(float(np.mean([s[rule]["interval_score"] for s in sp])), 3),
            "fraction_stations_below_0.80": round(float((station < 0.80).mean()), 3)}


def main():
    v = {}
    print("| Network | Splits | Rule | Coverage [95% CI] | Width | Interval score | Stations below 0.80 |")
    print("|---|:---:|---|:---:|:---:|:---:|:---:|")
    for dom in ("delhi_air_quality", "beijing_air_quality", "ghcn_weather"):
        sp = load(dom)
        if not sp:
            continue
        d = {r: rule_stats(sp, r) for r in ("same_year", "c1h_seasonal_scaled", "online_selection")}
        d["n_splits"] = len(sp)
        d["is_diff_online_minus_c1h"] = paired_difference([s["online_selection"]["interval_score"] for s in sp],
                                                          [s["c1h_seasonal_scaled"]["interval_score"] for s in sp])
        d["online_relative_is"] = round(d["online_selection"]["interval_score"] / d["c1h_seasonal_scaled"]["interval_score"], 4)
        counts = {}
        for s in sp:
            for k, n in s["online_selection"]["chosen_counts"].items():
                counts[k] = counts.get(k, 0) + n
        d["online_chosen_counts"] = counts
        c = d["c1h_seasonal_scaled"]["coverage"]
        d["H6"] = "PASS" if abs(c["mean"] - TARGET) <= TOL and (
            dom != "delhi_air_quality" or c["ci95"][1] - c["ci95"][0] < C1H_DELHI_CI_WIDTH) else "FAIL"
        oc = d["online_selection"]["coverage"]["mean"]
        if dom == "ghcn_weather":
            eff = d["is_diff_online_minus_c1h"]["ci95"][1] < 0
        else:
            eff = d["online_relative_is"] <= 1.02
        d["H7"] = "PASS" if abs(oc - TARGET) <= TOL and eff else "FAIL"
        v[dom] = d
        for r in ("same_year", "c1h_seasonal_scaled", "online_selection"):
            x = d[r]
            print(f"| {dom} | {len(sp)} | {r} | {x['coverage']['mean']:.3f} [{x['coverage']['ci95'][0]:.3f}, {x['coverage']['ci95'][1]:.3f}] "
                  f"| {x['width']:.1f} | {x['interval_score']:.1f} | {x['fraction_stations_below_0.80']:.3f} |")
    for dom in ("pemsd7_traffic", "pemsbay_traffic"):
        sp = load(dom)
        if not sp:
            continue
        d = {r: rule_stats(sp, r) for r in ("expanding", "time_of_day_scaled")}
        d["n_splits"] = len(sp)
        d["is_diff_tod_minus_expanding"] = paired_difference([s["time_of_day_scaled"]["interval_score"] for s in sp],
                                                             [s["expanding"]["interval_score"] for s in sp])
        d["H5"] = "PASS" if abs(d["time_of_day_scaled"]["coverage"]["mean"] - TARGET) <= TOL else "FAIL"
        v[dom] = d
        for r in ("expanding", "time_of_day_scaled"):
            x = d[r]
            print(f"| {dom} | {len(sp)} | {r} | {x['coverage']['mean']:.3f} [{x['coverage']['ci95'][0]:.3f}, {x['coverage']['ci95'][1]:.3f}] "
                  f"| {x['width']:.2f} | {x['interval_score']:.2f} | {x['fraction_stations_below_0.80']:.3f} |")
    g = os.path.join(RESULTS, "exp_C1g_hcp_pemsbay_traffic.json")
    if os.path.exists(g):
        a = json.load(open(g))["aggregate"]
        v["pemsbay_hcp"] = {"pooled": a["pooled_expanding"], "hcp": a["hcp_expanding"],
                            "H8": "PASS" if a["hcp_expanding"]["coverage_mean"] >= 0.90 and
                            a["hcp_expanding"]["fraction_of_stations_below_0.80"] < a["pooled_expanding"]["fraction_of_stations_below_0.80"]
                            else "FAIL"}
    json.dump(v, open(os.path.join(RESULTS, "exp_C1i_verdicts.json"), "w"), indent=2)
    print({k: {h: x[h] for h in ("H5", "H6", "H7", "H8") if h in x} for k, x in v.items()})


if __name__ == "__main__":
    main()
