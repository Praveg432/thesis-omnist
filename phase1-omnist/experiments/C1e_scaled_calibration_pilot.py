#!/usr/bin/env python3
"""C1e - pilot: can forecast-time calibration be made reliable when error grows over time? (exploratory)

C1b/C1d showed that expanding-window chronological calibration under-covers when forecast error grows over
the test period (Delhi, Beijing). This pilot compares calibration rules on the SAME trained models (corrected
coordinate frame) and the same splits, all using only forecast-time information:
  expanding        quantile of all earlier calibration errors (the C1b rule)
  rolling_2/4      quantile of the last 2 or 4 windows of calibration errors
  scaled_<s>       errors divided by a scale s computed from the forecast inputs of the same station and
                   window, interval half-width q_t * s, q_t the expanding quantile of the scaled errors
                   s = level (mean of the input window), vol (std of the input window), predmag (mean |forecast|)
  scaled_level_rolling4  level-scaled, rolling quantile
Each scale is floored at 10% of the training mean so it stays positive.
Selection protocol: rules are compared on splits 0-4 and confirmed on splits 5-9 (never chosen on the
half they are reported on). Exploratory: nothing here is a thesis claim until it is re-run under the
final protocol.

Run:  python experiments/C1e_scaled_calibration_pilot.py <domain> [n_splits]
Output: results/exp_C1e_pilot_<domain>.json
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
from torch.utils.data import DataLoader

torch.set_num_threads(2)

import C1_rigorous_inductive_eval as c1
from src.cc_hash import training_coordinate_frame
from src.chronological_conformal import (chronological_quantiles, coverage_with_quantiles, rolling_quantiles,
                                         scaled_coverage, warmup_windows)
from src.data import DataConfig, collate_variable_nodes
from src.omnist_model import ModelConfig, OmniST
from src.trainer import TrainConfig, train_model

WARMUP_FRACTION = 0.25
RULES = ["expanding", "rolling_2", "rolling_4", "scaled_level", "scaled_vol", "scaled_predmag",
         "scaled_level_rolling4"]


def scores_and_scales(model, meta, dataset) -> dict:
    """Absolute errors (windows, stations, horizon) and forecast-time scales (windows, stations, 1)."""
    mu = float(np.asarray(meta["means"]).squeeze())
    sd = float(np.asarray(meta["stds"]).squeeze())
    loader = DataLoader(dataset, batch_size=4, shuffle=False, collate_fn=collate_variable_nodes)
    err, level, vol, predmag = [], [], [], []
    model.eval()
    with torch.no_grad():
        for feats, coords, stamps, targets in loader:
            pred = model(feats, coords, stamps)
            err.append(((pred * sd + mu) - (targets * sd + mu)).abs()[..., 0].numpy())
            inputs = (feats * sd + mu)[..., 0].numpy()  # (B, T, N)
            level.append(inputs.mean(axis=1)[..., None])
            vol.append(inputs.std(axis=1)[..., None])
            predmag.append(np.abs((pred * sd + mu)[..., 0].numpy()).mean(axis=-1, keepdims=True))
    floor = 0.1 * abs(mu) + 1e-6
    return {"err": np.concatenate(err), "level": np.maximum(np.concatenate(level), floor),
            "vol": np.maximum(np.concatenate(vol), floor), "predmag": np.maximum(np.concatenate(predmag), floor)}


def evaluate_rules(cal: dict, test: dict) -> dict:
    first = warmup_windows(cal["err"].shape[0], WARMUP_FRACTION)
    a = c1.ALPHA
    out = {}
    out["expanding"] = coverage_with_quantiles(test["err"], chronological_quantiles(cal["err"], first, a), first)
    for w in (2, 4):
        out[f"rolling_{w}"] = coverage_with_quantiles(test["err"], rolling_quantiles(cal["err"], first, a, w), first)
    for s in ("level", "vol", "predmag"):
        out[f"scaled_{s}"] = scaled_coverage(cal["err"], cal[s], test["err"], test[s], first, a)
    out["scaled_level_rolling4"] = scaled_coverage(cal["err"], cal["level"], test["err"], test["level"], first, a, 4)
    return {k: {"coverage": round(v["coverage"], 4), "width": round(v["width"], 3),
                "per_station_coverage": [round(x, 4) for x in v["per_station_coverage"]]} for k, v in out.items()}


def run_split(name, spec, split, n_stations) -> dict:
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
    cal = scores_and_scales(model, meta, c1.station_dataset(meta, cal_idx, window, horizon))
    test = scores_and_scales(model, meta, c1.station_dataset(meta, test_idx, window, horizon))
    return {"split": split, "rules": evaluate_rules(cal, test)}


def aggregate(splits: list) -> dict:
    def agg(sub):
        out = {}
        for rule in RULES:
            cov = [s["rules"][rule]["coverage"] for s in sub]
            wid = [s["rules"][rule]["width"] for s in sub]
            station = np.concatenate([s["rules"][rule]["per_station_coverage"] for s in sub])
            out[rule] = {"coverage_mean": round(float(np.mean(cov)), 4), "width_mean": round(float(np.mean(wid)), 3),
                         "fraction_of_stations_below_0.80": round(float((station < 0.80).mean()), 3)}
        return out
    half = [s for s in splits if s["split"] < 5]
    rest = [s for s in splits if s["split"] >= 5]
    return {"all_splits": agg(splits), "selection_half_splits_0_4": agg(half) if half else None,
            "confirmation_half_splits_5_9": agg(rest) if rest else None}


def main(name: str, n_splits: int) -> None:
    spec = c1.DOMAINS[name]
    n_stations = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"], n_features=1),
                                 hold_out_stations=[])[3]["coords_all"].shape[0]
    splits = []
    for split in range(n_splits):
        splits.append(run_split(name, spec, split, n_stations))
        r = splits[-1]["rules"]
        print(f"[{name}] split {split}: " + " ".join(f"{k}={r[k]['coverage']}" for k in RULES), flush=True)
    result = {"experiment": "C1e exploratory pilot of forecast-time calibration rules", "domain": name,
              "warmup_fraction": WARMUP_FRACTION, "splits": splits, "aggregate": aggregate(splits)}
    json.dump(result, open(os.path.join(c1.RESULTS, f"exp_C1e_pilot_{name}.json"), "w"), indent=2)
    for key, table in result["aggregate"].items():
        if table:
            print(f"[{name}] {key}")
            for rule, v in table.items():
                print(f"   {rule:24s} coverage {v['coverage_mean']}  width {v['width_mean']}  stations<0.80 {v['fraction_of_stations_below_0.80']}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10)
