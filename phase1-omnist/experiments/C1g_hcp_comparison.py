#!/usr/bin/env python3
"""C1g - station-level (hierarchical) conformal against pooled conformal, forecast-time calibration.

Pooled split conformal treats the many dependent errors of one station as independent calibration points.
Hierarchical conformal prediction (HCP, Lee, Barber, Willett, arXiv:2306.06342) gives each calibration station
equal total weight and puts 1/(K+1) of the mass at infinity, so its threshold is infinite unless there are at
least 9 calibration stations at a 90% target. This experiment uses at least 10 calibration stations and
compares, on the same trained models and splits (corrected coordinate frame, chronological history):
  pooled_expanding   the C1b rule (quantile of all earlier calibration errors)
  hcp_expanding      HCP threshold from earlier calibration errors, stations weighted equally
HCP's guarantee needs exchangeability of errors within a station; time series errors are not exchangeable
within a station, so its coverage here is an empirical question, not a theorem.

Run:  python experiments/C1g_hcp_comparison.py <domain> [n_splits] [n_cal]
Output: results/exp_C1g_hcp_<domain>.json
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
from src.multiyear_calibration import hcp_threshold
from src.omnist_model import ModelConfig, OmniST
from src.trainer import TrainConfig, train_model

WARMUP_FRACTION = 0.25


def evaluate(cal: np.ndarray, test: np.ndarray) -> dict:
    first = warmup_windows(cal.shape[0], WARMUP_FRACTION)
    q_pooled = chronological_quantiles(cal, first, c1.ALPHA)
    q_hcp = np.array([hcp_threshold([cal[:t, s, :].reshape(-1) for s in range(cal.shape[1])], c1.ALPHA)
                      for t in range(first, cal.shape[0])])
    out = {}
    for name, q in (("pooled_expanding", q_pooled), ("hcp_expanding", q_hcp)):
        covered = test[first:] <= q[:, None, None]
        finite = np.isfinite(q)
        out[name] = {"coverage": float(covered.mean()),
                     "width": float(2.0 * q[finite].mean()) if finite.any() else float("inf"),
                     "fraction_finite_windows": float(finite.mean()),
                     "per_station_coverage": [float(x) for x in covered.mean(axis=(0, 2))]}
    return out


def run_split(name, spec, split, n_stations, n_cal):
    rng = np.random.default_rng(1000 + split)
    perm = rng.permutation(n_stations)
    test_idx = np.sort(perm[:spec["n_test"]])
    cal_idx = np.sort(perm[spec["n_test"]:spec["n_test"] + n_cal])
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
    return {"split": split, "n_train": len(meta["train_stations"]), "n_cal": len(cal_idx),
            "rules": {k: {kk: (round(vv, 4) if isinstance(vv, float) else [round(x, 4) for x in vv])
                          for kk, vv in v.items()} for k, v in evaluate(cal, test).items()}}


def main(name, n_splits, n_cal):
    spec = c1.DOMAINS[name]
    n_stations = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"], n_features=1),
                                 hold_out_stations=[])[3]["coords_all"].shape[0]
    if n_cal < 9:
        raise SystemExit("HCP at a 90% target needs at least 9 calibration stations; pass n_cal >= 9")
    path = os.path.join(c1.RESULTS, f"exp_C1g_hcp_{name}.json")
    splits = []
    if os.path.exists(path):  # resumable: splits are deterministic given their index, so finished ones are kept
        prior = json.load(open(path))
        if prior.get("n_calibration_stations") == n_cal:
            splits = prior["splits"]
    done = {s["split"] for s in splits}
    for split in range(n_splits):
        if split in done:
            continue
        splits.append(run_split(name, spec, split, n_stations, n_cal))
        r = splits[-1]["rules"]
        print(f"[{name}] split {split}: pooled {r['pooled_expanding']['coverage']} hcp {r['hcp_expanding']['coverage']}",
              flush=True)
        json.dump({"experiment": "C1g HCP against pooled conformal, forecast-time calibration (partial)", "domain": name,
                   "n_calibration_stations": n_cal, "splits": splits, "aggregate": {}}, open(path, "w"), indent=2)
    splits = sorted(splits, key=lambda s: s["split"])
    agg = {}
    for rule in ("pooled_expanding", "hcp_expanding"):
        station = np.concatenate([s["rules"][rule]["per_station_coverage"] for s in splits])
        widths = [s["rules"][rule]["width"] for s in splits if np.isfinite(s["rules"][rule]["width"])]
        agg[rule] = {"coverage_mean": round(float(np.mean([s["rules"][rule]["coverage"] for s in splits])), 4),
                     "coverage_sd": round(float(np.std([s["rules"][rule]["coverage"] for s in splits], ddof=1)), 4),
                     "width_mean": round(float(np.mean(widths)), 3) if widths else None,
                     "fraction_finite": round(float(np.mean([s["rules"][rule]["fraction_finite_windows"] for s in splits])), 3),
                     "fraction_of_stations_below_0.80": round(float((station < 0.80).mean()), 3)}
    json.dump({"experiment": "C1g HCP against pooled conformal, forecast-time calibration", "domain": name,
               "n_calibration_stations": n_cal, "splits": splits, "aggregate": agg},
              open(os.path.join(c1.RESULTS, f"exp_C1g_hcp_{name}.json"), "w"), indent=2)
    for rule, v in agg.items():
        print(f"[{name}] {rule}: {v}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10,
         int(sys.argv[3]) if len(sys.argv) > 3 else c1.DOMAINS[sys.argv[1]]["n_cal"])
