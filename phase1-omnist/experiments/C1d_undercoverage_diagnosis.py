#!/usr/bin/env python3
"""C1d - why does chronological calibration under-cover on Delhi and Beijing? (diagnosis, not a fix)

Three candidate causes are measured on the same C1 splits with the training-station coordinate frame:
  H1  error scale changes over the test period  -> late-third mean error / early-third mean error
  H2  calibration stations are not representative of test stations -> test mean error / calibration
      mean error (over the scored windows), and its spread over splits
  H3  too few independent calibration windows early on -> chronological coverage by third of the scored
      windows (early, middle, late), and the number of windows
Per-window scores are saved so that other calibration rules can be tested without retraining.

Run:  python experiments/C1d_undercoverage_diagnosis.py <domain> [n_splits]
Output: results/exp_C1d_diagnosis_<domain>.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
os.environ.setdefault("OMP_NUM_THREADS", "2")

import numpy as np
import torch

torch.set_num_threads(2)

import C1_rigorous_inductive_eval as c1
from src.cc_hash import training_coordinate_frame
from src.chronological_conformal import chronological_quantiles, warmup_windows
from src.data import DataConfig
from src.omnist_model import ModelConfig, OmniST
from src.trainer import TrainConfig, train_model

WARMUP_FRACTION = 0.25


def thirds(n: int) -> list:
    edges = np.linspace(0, n, 4).round().astype(int)
    return [(int(edges[i]), int(edges[i + 1])) for i in range(3)]


def diagnose(cal_scores: np.ndarray, test_scores: np.ndarray) -> dict:
    first = warmup_windows(cal_scores.shape[0], WARMUP_FRACTION)
    q = chronological_quantiles(cal_scores, first, c1.ALPHA)
    covered = test_scores[first:] <= q[:, None, None]  # (scored windows, stations, horizon)
    per_window = covered.mean(axis=(1, 2))
    cal_w = cal_scores.mean(axis=(1, 2))
    test_w = test_scores.mean(axis=(1, 2))
    parts = thirds(cal_scores.shape[0])
    ts = thirds(len(per_window))
    return {
        "n_windows": int(cal_scores.shape[0]), "first_scored": int(first),
        "coverage_by_third_of_scored_windows": [round(float(per_window[a:b].mean()), 4) for a, b in ts],
        "late_over_early_error_cal": round(float(cal_w[parts[2][0]:].mean() / cal_w[:parts[0][1]].mean()), 4),
        "late_over_early_error_test": round(float(test_w[parts[2][0]:].mean() / test_w[:parts[0][1]].mean()), 4),
        "test_over_cal_error_scored": round(float(test_w[first:].mean() / cal_w[first:].mean()), 4),
        "mean_chronological_quantile_over_late_mean_cal_error": round(float(q.mean() / cal_w[parts[2][0]:].mean()), 4),
        "per_window_cal_mean_error": [round(float(x), 3) for x in cal_w],
        "per_window_test_mean_error": [round(float(x), 3) for x in test_w],
    }


def run_split(name: str, spec: dict, split: int, n_stations: int) -> dict:
    rng = np.random.default_rng(1000 + split)
    perm = rng.permutation(n_stations)
    test_idx = np.sort(perm[:spec["n_test"]])
    cal_idx = np.sort(perm[spec["n_test"]:spec["n_test"] + spec["n_cal"]])
    held = sorted(int(i) for i in np.concatenate([cal_idx, test_idx]))
    torch.manual_seed(split)
    np.random.seed(split)
    window, horizon = spec["window"], spec["horizon"]
    cfg = DataConfig(window_size=window, horizon=horizon, n_features=1)
    tcfg = TrainConfig(lr=1e-3, n_epochs=spec["epochs"], patience=spec["patience"], batch_size=spec["batch"],
                       loss_type="pot")
    train_ds, val_ds, _, meta = spec["prepare"](cfg, hold_out_stations=held)
    center, scale = training_coordinate_frame(np.asarray(meta["coords_all"])[meta["train_stations"]])
    model = OmniST(ModelConfig(n_features=1, horizon=horizon, d_model=64, k_neighbors=8,
                               knn_mode=spec.get("knn_mode", "exact"), coord_center=center, coord_scale=scale))
    train_model(model, train_ds, val_ds, tcfg, meta)
    cal = c1.score_array(model, meta, c1.station_dataset(meta, cal_idx, window, horizon))
    test = c1.score_array(model, meta, c1.station_dataset(meta, test_idx, window, horizon))
    return {"split": split, **diagnose(cal, test)}


def main(name: str, n_splits: int) -> None:
    spec = c1.DOMAINS[name]
    n_stations = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"], n_features=1),
                                 hold_out_stations=[])[3]["coords_all"].shape[0]
    splits = []
    for split in range(n_splits):
        splits.append(run_split(name, spec, split, n_stations))
        print(f"[{name}] split {split}: by-third {splits[-1]['coverage_by_third_of_scored_windows']} "
              f"late/early cal {splits[-1]['late_over_early_error_cal']} test/cal {splits[-1]['test_over_cal_error_scored']}",
              flush=True)

    def mean(key, i=None):
        vals = [s[key] if i is None else s[key][i] for s in splits]
        return round(float(np.mean(vals)), 4)

    agg = {"coverage_by_third_mean": [mean("coverage_by_third_of_scored_windows", i) for i in range(3)],
           "late_over_early_error_cal_mean": mean("late_over_early_error_cal"),
           "late_over_early_error_test_mean": mean("late_over_early_error_test"),
           "test_over_cal_error_mean": mean("test_over_cal_error_scored"),
           "test_over_cal_error_sd": round(float(np.std([s["test_over_cal_error_scored"] for s in splits], ddof=1)), 4)}
    json.dump({"experiment": "C1d under-coverage diagnosis (training-station frame)", "domain": name,
               "splits": splits, "aggregate": agg},
              open(os.path.join(c1.RESULTS, f"exp_C1d_diagnosis_{name}.json"), "w"), indent=2)
    print(f"[{name}] aggregate {agg}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10)
