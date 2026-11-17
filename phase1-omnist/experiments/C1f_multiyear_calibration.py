#!/usr/bin/env python3
"""C1f - rolling-origin evaluation over several test years, and calibration rules that use earlier years.

C1b/C1d/C1e used one test year per network (10 windows on Delhi, 22 on Beijing). Error grows through that
year, so a rule restricted to the same year has little to learn from. Here the model is retrained for each
test year (trained only on earlier years), the calibration stations' errors from earlier years are kept, and
rules may use them. Everything a rule uses was observable before the forecast origin.
  Delhi: test years 2021, 2022, 2023 (three folds, models trained on years before the test year)
  Beijing: two test years (the last 365 days, and the 365 days before them)
Only windows in folds after the first are scored (the first fold is history), skipping the first 25% of each
fold's windows so every rule is compared on the same windows.

Rules: expanding_within (the C1b rule), expanding_all (all earlier windows, across years), rolling (last 4
windows), seasonal (earlier-year windows within 45 days of the same day of year), scaled_predmag_all and
scaled_predmag_seasonal (errors divided by mean absolute forecast, interval q * that scale).
Also reported: hierarchical conformal (HCP) threshold availability, which needs at least 9 calibration stations
at 90%.

Run:  python experiments/C1f_multiyear_calibration.py <delhi_air_quality|beijing_air_quality> [n_splits]
Output: results/exp_C1f_<domain>.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
os.environ.setdefault("OMP_NUM_THREADS", "2")

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

torch.set_num_threads(2)

import C1_rigorous_inductive_eval as c1
from src.cc_hash import training_coordinate_frame
from src.data import DataConfig, collate_variable_nodes
from src.multiyear_calibration import hcp_threshold, rule_quantiles
from src.omnist_model import ModelConfig, OmniST
from src.trainer import TrainConfig, train_model

FOLDS = {"delhi_air_quality": [{"train_end_year": 2020}, {"train_end_year": 2021}, {"train_end_year": 2022}],
         "beijing_air_quality": [{"test_offset_days": 365}, {"test_offset_days": 0}]}
WARMUP_FRACTION = 0.25
RULES = ["expanding_within", "expanding_all", "rolling_4", "seasonal", "scaled_predmag_all", "scaled_predmag_seasonal"]


def fold_scores(model, meta, idx, window, horizon):
    """Errors (windows, stations, horizon), mean |forecast| (windows, stations, 1) and origin day of year."""
    mu, sd = float(np.asarray(meta["means"]).squeeze()), float(np.asarray(meta["stds"]).squeeze())
    ds = c1.station_dataset(meta, idx, window, horizon)
    loader = DataLoader(ds, batch_size=4, shuffle=False, collate_fn=collate_variable_nodes)
    err, predmag = [], []
    model.eval()
    with torch.no_grad():
        for feats, coords, stamps, targets in loader:
            pred = model(feats, coords, stamps)
            err.append(((pred * sd + mu) - (targets * sd + mu)).abs()[..., 0].numpy())
            predmag.append(np.abs((pred * sd + mu)[..., 0].numpy()).mean(axis=-1, keepdims=True))
    dates = pd.DatetimeIndex(meta["test_dates"])
    origins = [ds.indices[i] + ds.window_size for i in range(len(ds))]
    doy = np.array([dates[o].dayofyear for o in origins])
    floor = 0.1 * abs(mu) + 1e-6
    return np.concatenate(err), np.maximum(np.concatenate(predmag), floor), doy


def evaluate(cal, test, fold_ids, doy, cal_scale, test_scale):
    scored = np.array([t for f in sorted(set(fold_ids)) if f > 0
                       for t in np.nonzero(fold_ids == f)[0][int(np.ceil(WARMUP_FRACTION * (fold_ids == f).sum())):]])
    a = c1.ALPHA
    out = {}

    def add(name, q, scale=None):
        half = q[:, None, None] * (test_scale[scored] if scale else 1.0)
        covered = test[scored] <= half
        out[name] = {"coverage": float(covered.mean()),
                     "width": float(2.0 * np.broadcast_to(half, test[scored].shape).mean()),
                     "per_station_coverage": [float(x) for x in covered.mean(axis=(0, 2))]}

    add("expanding_within", rule_quantiles(cal, fold_ids, doy, scored, a, "expanding_within"))
    add("expanding_all", rule_quantiles(cal, fold_ids, doy, scored, a, "expanding_all"))
    add("rolling_4", rule_quantiles(cal, fold_ids, doy, scored, a, "rolling", n_recent=4))
    add("seasonal", rule_quantiles(cal, fold_ids, doy, scored, a, "seasonal", half_width_days=45))
    norm = cal / cal_scale
    add("scaled_predmag_all", rule_quantiles(norm, fold_ids, doy, scored, a, "expanding_all"), scale=True)
    add("scaled_predmag_seasonal", rule_quantiles(norm, fold_ids, doy, scored, a, "seasonal", half_width_days=45),
        scale=True)
    last = int(scored[-1])
    hcp = hcp_threshold([cal[:last, s, :].reshape(-1) for s in range(cal.shape[1])], a)
    return out, int(len(scored)), bool(np.isfinite(hcp))


def run_split(name, spec, split, n_stations):
    rng = np.random.default_rng(1000 + split)
    perm = rng.permutation(n_stations)
    test_idx = np.sort(perm[:spec["n_test"]])
    cal_idx = np.sort(perm[spec["n_test"]:spec["n_test"] + spec["n_cal"]])
    held = sorted(int(i) for i in np.concatenate([cal_idx, test_idx]))
    window, horizon = spec["window"], spec["horizon"]
    cal_all, test_all, scale_cal, scale_test, folds, doys = [], [], [], [], [], []
    for fold, kwargs in enumerate(FOLDS[name]):
        torch.manual_seed(split)
        np.random.seed(split)
        cfg = DataConfig(window_size=window, horizon=horizon, n_features=1)
        tcfg = TrainConfig(lr=1e-3, n_epochs=spec["epochs"], patience=spec["patience"], batch_size=spec["batch"],
                           loss_type="pot")
        train_ds, val_ds, _, meta = spec["prepare"](cfg, hold_out_stations=held, **kwargs)
        center, scale = training_coordinate_frame(np.asarray(meta["coords_all"])[meta["train_stations"]])
        model = OmniST(ModelConfig(n_features=1, horizon=horizon, d_model=64, k_neighbors=8, coord_center=center,
                                   coord_scale=scale))
        train_model(model, train_ds, val_ds, tcfg, meta)
        ce, cp, doy = fold_scores(model, meta, cal_idx, window, horizon)
        te, tp, _ = fold_scores(model, meta, test_idx, window, horizon)
        cal_all.append(ce), test_all.append(te), scale_cal.append(cp), scale_test.append(tp)
        folds += [fold] * len(ce)
        doys.append(doy)
    cal, test = np.concatenate(cal_all), np.concatenate(test_all)
    rules, n_scored, hcp_finite = evaluate(cal, test, np.array(folds), np.concatenate(doys),
                                           np.concatenate(scale_cal), np.concatenate(scale_test))
    return {"split": split, "n_windows_per_fold": [len(x) for x in cal_all], "n_scored": n_scored,
            "hcp_threshold_finite": hcp_finite,
            "rules": {k: {"coverage": round(v["coverage"], 4), "width": round(v["width"], 3),
                          "per_station_coverage": [round(x, 4) for x in v["per_station_coverage"]]}
                      for k, v in rules.items()}}


def main(name, n_splits):
    spec = c1.DOMAINS[name]
    n_stations = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"], n_features=1),
                                 hold_out_stations=[])[3]["coords_all"].shape[0]
    splits = []
    for split in range(n_splits):
        splits.append(run_split(name, spec, split, n_stations))
        r = splits[-1]["rules"]
        print(f"[{name}] split {split} scored {splits[-1]['n_scored']}: " + " ".join(f"{k}={r[k]['coverage']}" for k in RULES),
              flush=True)
    agg = {}
    for rule in RULES:
        station = np.concatenate([s["rules"][rule]["per_station_coverage"] for s in splits])
        agg[rule] = {"coverage_mean": round(float(np.mean([s["rules"][rule]["coverage"] for s in splits])), 4),
                     "width_mean": round(float(np.mean([s["rules"][rule]["width"] for s in splits])), 3),
                     "fraction_of_stations_below_0.80": round(float((station < 0.80).mean()), 3)}
    result = {"experiment": "C1f rolling-origin calibration over several test years", "domain": name,
              "folds": FOLDS[name], "warmup_fraction": WARMUP_FRACTION, "n_calibration_stations": spec["n_cal"],
              "hcp_finite_in_all_splits": all(s["hcp_threshold_finite"] for s in splits),
              "splits": splits, "aggregate": agg}
    json.dump(result, open(os.path.join(c1.RESULTS, f"exp_C1f_{name}.json"), "w"), indent=2)
    for rule, v in agg.items():
        print(f"[{name}] {rule:26s} coverage {v['coverage_mean']} width {v['width_mean']} stations<0.80 {v['fraction_of_stations_below_0.80']}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10)
