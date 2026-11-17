#!/usr/bin/env python3
"""C1h - pre-registered confirmation of the scaled seasonal calibration rule (see PRE-REGISTRATION-C1H.md).

Fresh station splits (10 to 29) on Delhi and Beijing, and a network not used for selection (weather, three test
years, splits 0 to 19). For OmniST, persistence and seasonal-naive (7-day), compares the same-year rule (C1b) with
the fixed scaled seasonal rule on identical windows: coverage, width and interval score. Hypotheses H1 to H4 are
evaluated by experiments/C1h_summarise.py.

Run:  python experiments/C1h_confirmation.py <delhi_air_quality|beijing_air_quality|ghcn_weather>
Output: results/exp_C1h_<domain>.json (resumable; completed splits are skipped)
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
from C1f_multiyear_calibration import fold_scores
from src.cc_hash import training_coordinate_frame
from src.data import DataConfig
from src.interval_metrics import interval_score
from src.multiyear_calibration import rule_quantiles
from src.naive_baselines import persistence_forecasts, seasonal_naive_forecasts, targets, window_starts
from src.omnist_model import ModelConfig, OmniST
from src.trainer import TrainConfig, train_model

FOLDS = {"delhi_air_quality": [{"train_end_year": 2020}, {"train_end_year": 2021}, {"train_end_year": 2022}],
         "beijing_air_quality": [{"test_offset_days": 365}, {"test_offset_days": 0}],
         "ghcn_weather": [{"test_offset_days": 730}, {"test_offset_days": 365}, {"test_offset_days": 0}]}
SPLITS = {"delhi_air_quality": range(10, 30), "beijing_air_quality": range(10, 30), "ghcn_weather": range(0, 20)}
WARMUP_FRACTION = 0.25
HALF_WIDTH_DAYS = 45
SEASON = 7
ALPHA = c1.ALPHA


def baseline_arrays(meta, idx, window, horizon):
    mu, sd = float(np.asarray(meta["means"]).squeeze()), float(np.asarray(meta["stds"]).squeeze())
    series = np.asarray(meta["test_data_all_normalized"])[:, idx, 0] * sd + mu
    w = min(window, len(series) - horizon - 1)
    starts = window_starts(len(series), w, horizon, horizon)
    y = targets(series, starts, w, horizon)
    floor = 0.1 * abs(mu) + 1e-6
    out = {}
    for name, pred in (("persistence", persistence_forecasts(series, starts, w, horizon)),
                       ("seasonal_naive", seasonal_naive_forecasts(series, starts, w, horizon, SEASON))):
        out[name] = (np.abs(y - pred), np.maximum(np.abs(pred).mean(axis=-1, keepdims=True), floor))
    return out


def scored_windows(fold_ids):
    return np.array([t for f in sorted(set(fold_ids)) if f > 0
                     for t in np.nonzero(fold_ids == f)[0][int(np.ceil(WARMUP_FRACTION * (fold_ids == f).sum())):]])


def evaluate(cal_err, cal_scale, test_err, test_scale, fold_ids, doy):
    scored = scored_windows(fold_ids)
    q_same = rule_quantiles(cal_err, fold_ids, doy, scored, ALPHA, "expanding_within")
    q_seas = rule_quantiles(cal_err / cal_scale, fold_ids, doy, scored, ALPHA, "seasonal", half_width_days=HALF_WIDTH_DAYS)
    out = {}
    for rule, half in (("same_year", np.broadcast_to(q_same[:, None, None], test_err[scored].shape)),
                       ("scaled_seasonal", np.broadcast_to(q_seas[:, None, None] * test_scale[scored], test_err[scored].shape))):
        e = test_err[scored]
        covered = e <= half
        out[rule] = {"coverage": round(float(covered.mean()), 4), "width": round(float(2 * half.mean()), 3),
                     "interval_score": round(interval_score(e, half, ALPHA), 3),
                     "per_station_coverage": [round(float(x), 4) for x in covered.mean(axis=(0, 2))]}
    out["mae"] = round(float(test_err[scored].mean()), 4)
    return out, int(len(scored))


def run_split(name, spec, split, n_stations):
    rng = np.random.default_rng(1000 + split)
    perm = rng.permutation(n_stations)
    test_idx = np.sort(perm[:spec["n_test"]])
    cal_idx = np.sort(perm[spec["n_test"]:spec["n_test"] + spec["n_cal"]])
    held = sorted(int(i) for i in np.concatenate([cal_idx, test_idx]))
    window, horizon = spec["window"], spec["horizon"]
    acc = {m: {"ce": [], "cs": [], "te": [], "ts": []} for m in ("omnist", "persistence", "seasonal_naive")}
    folds, doys = [], []
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
        ce, cs, doy = fold_scores(model, meta, cal_idx, window, horizon)
        te, ts, _ = fold_scores(model, meta, test_idx, window, horizon)
        for key, val in (("ce", ce), ("cs", cs), ("te", te), ("ts", ts)):
            acc["omnist"][key].append(val)
        bc, bt = baseline_arrays(meta, cal_idx, window, horizon), baseline_arrays(meta, test_idx, window, horizon)
        for m in ("persistence", "seasonal_naive"):
            if bc[m][0].shape != ce.shape:
                raise ValueError(f"{m} windows {bc[m][0].shape} do not match the model's {ce.shape}")
            acc[m]["ce"].append(bc[m][0]), acc[m]["cs"].append(bc[m][1])
            acc[m]["te"].append(bt[m][0]), acc[m]["ts"].append(bt[m][1])
        folds += [fold] * len(ce)
        doys.append(doy)
    fold_ids, doy = np.array(folds), np.concatenate(doys)
    result = {"split": split}
    for m, a in acc.items():
        result[m], n_scored = evaluate(*(np.concatenate(a[k]) for k in ("ce", "cs", "te", "ts")), fold_ids, doy)
    result["n_scored_windows"] = n_scored
    return result


def main(name):
    spec = c1.DOMAINS[name]
    path = os.path.join(c1.RESULTS, f"exp_C1h_{name}.json")
    n_stations = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"], n_features=1),
                                 hold_out_stations=[])[3]["coords_all"].shape[0]
    state = {"experiment": "C1h pre-registered confirmation (PRE-REGISTRATION-C1H.md)", "domain": name,
             "folds": FOLDS[name], "splits_planned": list(SPLITS[name]), "half_width_days": HALF_WIDTH_DAYS,
             "seasonal_period": SEASON, "splits": []}
    if os.path.exists(path):
        state = json.load(open(path))
    done = {s["split"] for s in state["splits"]}
    for split in SPLITS[name]:
        if split in done:
            continue
        r = run_split(name, spec, split, n_stations)
        state["splits"].append(r)
        json.dump(state, open(path, "w"), indent=2)
        print(f"[{name}] split {split}: omnist same {r['omnist']['same_year']['coverage']} "
              f"seasonal {r['omnist']['scaled_seasonal']['coverage']} | IS {r['omnist']['scaled_seasonal']['interval_score']} "
              f"pers {r['persistence']['scaled_seasonal']['interval_score']} sn {r['seasonal_naive']['scaled_seasonal']['interval_score']}",
              flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
