#!/usr/bin/env python3
"""C1b - C1 re-run with chronological (forecast-time-only) calibration.

Why. C1 computes the conformal quantile from the calibration stations' errors over the same test
period it then scores, so the interval for window t uses errors from windows after t. That is not
available at forecast time. C1b keeps C1's splits, seeds, models and data, and compares three
protocols on exactly the same scored windows (see src/chronological_conformal.py):
  chronological  quantile for window t from calibration-station errors of windows before t only
  same_window    C1's protocol (needs targets not yet known)
  pooled         one quantile over all windows
The first 25% of test-period windows are warm-up history and are not scored.

Decision rules, fixed before the full run (THESIS-COMPLETION-PLAN.md, Section 0, step S2):
  (a) chronological mean coverage within 0.02 of 0.90 on a dataset: "consistent with nominal" stays;
  (b) any dataset's chronological mean differs from its C1 mean by more than 0.01, or the 87.6% to
      90.6% range of the submitted abstract changes: file an abstract revision request;
  (c) chronological mean below 0.85 on a dataset: report as under-coverage.

Run:  python experiments/C1b_chronological_eval.py <domain|all> [quick]
Output: results/exp_C1b_<domain>.json (quick runs write results/C1b_quick_<domain>.json instead and
never touch committed result files). Resumable: completed splits are skipped on restart.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import numpy as np
import torch

torch.set_num_threads(2)

import C1_rigorous_inductive_eval as c1
from src.chronological_conformal import compare_protocols
from src.data import DataConfig
from src.omnist_model import ModelConfig, OmniST
from src.trainer import TrainConfig, train_model

WARMUP_FRACTION = 0.25
PROTOCOLS = ("chronological", "same_window", "pooled")


def run_split(name: str, spec: dict, split: int, n_stations: int, quick: bool) -> dict:
    """Same split, seeds and training as C1.run_split; only the calibration protocol differs."""
    t0 = time.time()
    split_rng = np.random.default_rng(1000 + split)
    perm = split_rng.permutation(n_stations)
    test_idx = np.sort(perm[:spec["n_test"]])
    cal_idx = np.sort(perm[spec["n_test"]:spec["n_test"] + spec["n_cal"]])
    held = sorted(int(i) for i in np.concatenate([cal_idx, test_idx]))
    torch.manual_seed(split)
    np.random.seed(split)
    window, horizon = spec["window"], spec["horizon"]
    cfg = DataConfig(window_size=window, horizon=horizon, n_features=1)
    tcfg = TrainConfig(lr=1e-3, n_epochs=2 if quick else spec["epochs"], patience=spec["patience"],
                       batch_size=spec["batch"], loss_type="pot")
    train_ds, val_ds, _, meta = spec["prepare"](cfg, hold_out_stations=held)
    model = OmniST(ModelConfig(n_features=1, horizon=horizon, d_model=64, k_neighbors=8,
                               knn_mode=spec.get("knn_mode", "exact")))
    train_model(model, train_ds, val_ds, tcfg, meta)
    cal_scores = c1.score_array(model, meta, c1.station_dataset(meta, cal_idx, window, horizon))
    test_scores = c1.score_array(model, meta, c1.station_dataset(meta, test_idx, window, horizon))
    result = {"split": split, "n_cal": len(cal_idx), "n_test": len(test_idx),
              "test_stations": [int(i) for i in test_idx], "cal_stations": [int(i) for i in cal_idx],
              "n_windows": int(cal_scores.shape[0]), "test_mae": round(float(test_scores.mean()), 4)}
    compared = compare_protocols(cal_scores, test_scores, c1.ALPHA, WARMUP_FRACTION)
    result["first_scored_window"] = compared["first_scored_window"]
    result["n_scored_windows"] = compared["n_scored_windows"]
    for protocol in PROTOCOLS:
        result[protocol] = {k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v])
                            for k, v in compared[protocol].items()}
    result["seconds"] = round(time.time() - t0, 1)
    return result


def aggregate(splits: list) -> dict:
    out = {}
    for protocol in PROTOCOLS:
        station_cov = np.concatenate([s[protocol]["per_station_coverage"] for s in splits])
        covs = [s[protocol]["coverage"] for s in splits]
        out[protocol] = {
            "coverage_over_splits": c1.mean_ci(covs),
            "width_over_splits": c1.mean_ci([s[protocol]["width"] for s in splits]),
            "per_station_coverage": {
                "mean": round(float(station_cov.mean()), 4),
                "p10": round(float(np.percentile(station_cov, 10)), 4),
                "min": round(float(station_cov.min()), 4),
                "fraction_below_0.80": round(float((station_cov < 0.80).mean()), 3)}}
    out["test_mae_over_splits"] = c1.mean_ci([s["test_mae"] for s in splits])
    return out


def run_domain(name: str, quick: bool) -> None:
    spec = c1.DOMAINS[name]
    path = os.path.join(c1.RESULTS, f"C1b_quick_{name}.json" if quick else f"exp_C1b_{name}.json")
    n_stations = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"],
                                            n_features=1), hold_out_stations=[])[3]["coords_all"].shape[0]
    n_splits = 1 if quick else spec["splits"]
    state = {"experiment": "C1b chronological (forecast-time-only) calibration, same splits as C1",
             "domain": name, "n_stations": int(n_stations), "target_coverage": c1.TARGET,
             "warmup_fraction": WARMUP_FRACTION, "splits": []}
    if os.path.exists(path):
        state = json.load(open(path))
    done = {s["split"] for s in state["splits"]}
    print(f"[{name}] N={n_stations}, target {n_splits} splits, done {sorted(done)}", flush=True)
    for split in range(n_splits):
        if split in done:
            continue
        res = run_split(name, spec, split, n_stations, quick)
        state["splits"].append(res)
        print(f"  split {split}: chrono={res['chronological']['coverage']} "
              f"same_window={res['same_window']['coverage']} pooled={res['pooled']['coverage']} "
              f"| {res['seconds']}s", flush=True)
        state["aggregate"] = aggregate(state["splits"])
        json.dump(state, open(path, "w"), indent=2, default=float)
    print(f"[{name}] saved -> {path}", flush=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "quick"]
    quick_mode = "quick" in sys.argv[1:]
    which = list(c1.DOMAINS) if (not args or args[0] == "all") else [args[0]]
    for dom in which:
        run_domain(dom, quick_mode)
