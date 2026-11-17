#!/usr/bin/env python3
"""C1c - persistence and seasonal-naive baselines under the C1b protocol (same stations, same splits).

No training. For each C1 split the calibration and test stations are the ones C1 and C1b used. Each
baseline gets split-conformal intervals with chronological calibration (expanding window over the
calibration stations' earlier errors, first 25% of windows as warm-up), exactly as the model does in C1b.
Seasonal period: 7 days for the daily air-quality data, 288 steps (one day) for PeMSD7-M, 48 steps (one
day) for PeMS-BAY. Weather has no seasonal baseline (daily data, test period under a year).
Seasonal-naive drops windows without a full period of history, so it is scored on a later subset of
windows than persistence and the model; this is stated wherever the numbers are used.

Run:  python experiments/C1c_naive_baselines.py <domain|all>
Output: results/exp_C1c_baselines_<domain>.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import numpy as np

import C1_rigorous_inductive_eval as c1
from src.chronological_conformal import compare_protocols
from src.data import DataConfig
from src.naive_baselines import persistence_errors, seasonal_naive_errors, window_starts

SEASONAL_PERIOD = {"delhi_air_quality": 7, "beijing_air_quality": 7, "pemsd7_traffic": 288, "pemsbay_traffic": 48}
WARMUP_FRACTION = 0.25


def baseline_split(series_cal, series_test, window, horizon, period):
    n = len(series_cal)
    w = min(window, n - horizon - 1)
    starts = window_starts(n, w, horizon, horizon)
    out = {}
    methods = {"persistence": lambda s: (persistence_errors(s, starts, w, horizon), starts)}
    if period is not None:
        methods["seasonal_naive"] = lambda s: seasonal_naive_errors(s, starts, w, horizon, period)
    for name, fn in methods.items():
        cal_err, kept = fn(series_cal)
        test_err, _ = fn(series_test)
        if np.isnan(cal_err).any() or np.isnan(test_err).any():
            raise ValueError(f"{name}: NaN errors; the series has missing values the baseline cannot use")
        compared = compare_protocols(cal_err, test_err, c1.ALPHA, WARMUP_FRACTION)
        chrono = compared["chronological"]
        out[name] = {"coverage": round(chrono["coverage"], 4), "width": round(chrono["width"], 3),
                     "per_station_coverage": [round(c, 4) for c in chrono["per_station_coverage"]],
                     "mae": round(float(test_err.mean()), 4), "n_windows": int(len(kept)),
                     "first_kept_window_start": int(kept[0]),
                     "n_scored_windows": compared["n_scored_windows"]}
    return out


def run_domain(name: str) -> None:
    spec = c1.DOMAINS[name]
    meta = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"], n_features=1),
                           hold_out_stations=[])[3]
    mu = float(np.asarray(meta["means"]).squeeze())
    sd = float(np.asarray(meta["stds"]).squeeze())
    full = np.asarray(meta["test_data_all_normalized"])[:, :, 0] * sd + mu
    n_stations = full.shape[1]
    period = SEASONAL_PERIOD.get(name)
    splits = []
    for split in range(spec["splits"]):
        rng = np.random.default_rng(1000 + split)
        perm = rng.permutation(n_stations)
        test_idx = np.sort(perm[:spec["n_test"]])
        cal_idx = np.sort(perm[spec["n_test"]:spec["n_test"] + spec["n_cal"]])
        res = baseline_split(full[:, cal_idx], full[:, test_idx], spec["window"], spec["horizon"], period)
        splits.append({"split": split, **res})
    aggregate = {}
    for method in splits[0]:
        if method == "split":
            continue
        covs = [s[method]["coverage"] for s in splits]
        aggregate[method] = {
            "coverage_over_splits": c1.mean_ci(covs),
            "width_over_splits": c1.mean_ci([s[method]["width"] for s in splits]),
            "mae_over_splits": c1.mean_ci([s[method]["mae"] for s in splits]),
            "per_station_fraction_below_0.80": round(float(np.mean(
                np.concatenate([s[method]["per_station_coverage"] for s in splits]) < 0.80)), 3)}
    path = os.path.join(c1.RESULTS, f"exp_C1c_baselines_{name}.json")
    json.dump({"experiment": "C1c naive baselines, chronological calibration, same splits as C1",
               "domain": name, "seasonal_period": period, "warmup_fraction": WARMUP_FRACTION,
               "splits": splits, "aggregate": aggregate}, open(path, "w"), indent=2, default=float)
    for method, a in aggregate.items():
        print(f"[{name}] {method}: coverage {a['coverage_over_splits']['mean']} "
              f"width {a['width_over_splits']['mean']} mae {a['mae_over_splits']['mean']}", flush=True)


if __name__ == "__main__":
    which = list(c1.DOMAINS) if (len(sys.argv) < 2 or sys.argv[1] == "all") else [sys.argv[1]]
    for dom in which:
        run_domain(dom)
