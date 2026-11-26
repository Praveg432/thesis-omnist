#!/usr/bin/env python3
"""C1i / C1j - second pre-registered confirmation round (PRE-REGISTRATION-C1I.md).

C1i (Delhi, Beijing, weather; fresh splits; several test years): weekly forecast origins with known-at-origin
history; compares the same-year rule, the fixed C1h rule and online rule selection.
C1j (PeMSD7-M, PeMS-BAY; one test period): the phase-matched rule (same time of day on earlier days, scaled)
against the plain expanding rule.

Run:  python experiments/C1i_origin_rules.py <domain>
Output: results/exp_C1i_<domain>.json (resumable)
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
from C1h_confirmation import FOLDS as YEAR_FOLDS
from src.cc_hash import training_coordinate_frame
from src.data import DataConfig, SpatiotemporalDataset, collate_variable_nodes
from src.interval_metrics import interval_score
from src.omnist_model import ModelConfig, OmniST
from src.origin_calibration import Rule, half_widths, online_selection
from src.trainer import TrainConfig, train_model

WARMUP_FRACTION = 0.25
ALPHA = c1.ALPHA
C1H_RULE = Rule("c1h_seasonal_scaled", "prior_folds_phase", True, tolerance=45, period=366)
CANDIDATES = [Rule("same_year", "same_fold", False), Rule("all", "all", False), Rule("all_scaled", "all", True),
              C1H_RULE, Rule("same_year_scaled", "same_fold", True)]
TRAFFIC_RULE = Rule("time_of_day_scaled", "phase", True, tolerance=60, period=1440)
CONFIG = {
    "delhi_air_quality": {"folds": YEAR_FOLDS["delhi_air_quality"], "splits": range(30, 50), "stride": 7, "kind": "years"},
    "beijing_air_quality": {"folds": YEAR_FOLDS["beijing_air_quality"], "splits": range(30, 50), "stride": 7, "kind": "years"},
    "ghcn_weather": {"folds": YEAR_FOLDS["ghcn_weather"], "splits": range(20, 40), "stride": 7, "kind": "years"},
    "pemsd7_traffic": {"folds": [{}], "splits": range(0, 20), "stride": None, "kind": "day"},  # 0-5 pre-registered; 6-19 extension
    "pemsbay_traffic": {"folds": [{}], "splits": range(0, 20), "stride": None, "kind": "day"},  # 0-5 pre-registered; 6-19 extension
}


def score_fold(model, meta, idx, window, horizon, stride, kind):
    """Errors, mean |forecast| scale, and per-window origin, end, phase for one test period."""
    mu, sd = float(np.asarray(meta["means"]).squeeze()), float(np.asarray(meta["stds"]).squeeze())
    data = meta["test_data_all_normalized"][:, idx, :]
    w = min(window, len(data) - horizon - 1)
    ds = SpatiotemporalDataset(data, meta["coords_all"][idx], meta["test_dates"], window_size=w, horizon=horizon,
                               stride=stride or horizon)
    loader = DataLoader(ds, batch_size=4, shuffle=False, collate_fn=collate_variable_nodes)
    err, mag = [], []
    model.eval()
    with torch.no_grad():
        for feats, coords, stamps, targets in loader:
            pred = model(feats, coords, stamps)
            err.append(((pred * sd + mu) - (targets * sd + mu)).abs()[..., 0].numpy())
            mag.append(np.abs((pred * sd + mu)[..., 0].numpy()).mean(axis=-1, keepdims=True))
    dates = pd.DatetimeIndex(meta["test_dates"])
    first_target = dates[[s + w for s in ds.indices]]
    last_target = dates[[s + w + horizon - 1 for s in ds.indices]]
    if kind == "years":
        origin = np.array([d.toordinal() for d in first_target], dtype=float)
        end = np.array([d.toordinal() + 1 for d in last_target], dtype=float)
        phase = np.array([d.dayofyear for d in first_target], dtype=float)
    else:
        step = (dates[1] - dates[0]).total_seconds() / 60.0
        epoch, minute = pd.Timestamp("1970-01-01"), pd.Timedelta(minutes=1)
        origin = ((first_target - epoch) / minute).to_numpy().astype(float)  # unit-independent
        end = ((last_target - epoch) / minute).to_numpy().astype(float) + step
        phase = np.array([d.hour * 60 + d.minute for d in first_target], dtype=float)
    floor = 0.1 * abs(mu) + 1e-6
    return np.concatenate(err), np.maximum(np.concatenate(mag), floor), origin, end, phase


def scored_windows(fold, kind):
    folds = sorted(set(fold)) if kind == "day" else [f for f in sorted(set(fold)) if f > 0]
    return np.array([t for f in folds for t in np.nonzero(fold == f)[0][int(np.ceil(WARMUP_FRACTION * (fold == f).sum())):]])


def summarise(test_err, half, scored):
    e = test_err[scored]
    h = np.broadcast_to(half, e.shape)
    if not np.isfinite(h).all():
        raise ValueError("an interval has infinite width: a scored window has no usable calibration history")
    covered = e <= h
    return {"coverage": round(float(covered.mean()), 4), "width": round(float(2 * h.mean()), 3),
            "interval_score": round(interval_score(e, h, ALPHA), 3),
            "per_station_coverage": [round(float(x), 4) for x in covered.mean(axis=(0, 2))]}


def run_split(name, spec, cfg, split, n_stations):
    rng = np.random.default_rng(1000 + split)
    perm = rng.permutation(n_stations)
    test_idx = np.sort(perm[:spec["n_test"]])
    cal_idx = np.sort(perm[spec["n_test"]:spec["n_test"] + spec["n_cal"]])
    held = sorted(int(i) for i in np.concatenate([cal_idx, test_idx]))
    window, horizon = spec["window"], spec["horizon"]
    parts = {k: [] for k in ("ce", "cs", "te", "ts", "origin", "end", "phase", "fold")}
    for f, kwargs in enumerate(cfg["folds"]):
        torch.manual_seed(split)
        np.random.seed(split)
        dcfg = DataConfig(window_size=window, horizon=horizon, n_features=1)
        tcfg = TrainConfig(lr=1e-3, n_epochs=spec["epochs"], patience=spec["patience"], batch_size=spec["batch"],
                           loss_type="pot")
        train_ds, val_ds, _, meta = spec["prepare"](dcfg, hold_out_stations=held, **kwargs)
        center, scale = training_coordinate_frame(np.asarray(meta["coords_all"])[meta["train_stations"]])
        model = OmniST(ModelConfig(n_features=1, horizon=horizon, d_model=64, k_neighbors=8,
                                   knn_mode=spec.get("knn_mode", "exact"), coord_center=center, coord_scale=scale))
        train_model(model, train_ds, val_ds, tcfg, meta)
        ce, cs, origin, end, phase = score_fold(model, meta, cal_idx, window, horizon, cfg["stride"], cfg["kind"])
        te, ts, _, _, _ = score_fold(model, meta, test_idx, window, horizon, cfg["stride"], cfg["kind"])
        for k, v in (("ce", ce), ("cs", cs), ("te", te), ("ts", ts), ("origin", origin), ("end", end), ("phase", phase),
                     ("fold", np.full(len(ce), f))):
            parts[k].append(v)
    a = {k: np.concatenate(v) for k, v in parts.items()}
    scored = scored_windows(a["fold"], cfg["kind"])
    geo = (a["origin"], a["end"], a["fold"], a["phase"])
    out = {"split": split, "n_scored_windows": int(len(scored))}
    if cfg["kind"] == "years":
        for rule in (CANDIDATES[0], C1H_RULE):
            out[rule.name] = summarise(a["te"], half_widths(rule, a["ce"], a["cs"], a["ts"], scored, *geo, ALPHA), scored)
        half, chosen = online_selection(CANDIDATES, C1H_RULE.name, a["ce"], a["cs"], a["ts"], scored, *geo, ALPHA)
        out["online_selection"] = summarise(a["te"], half, scored)
        out["online_selection"]["chosen_counts"] = {n: chosen.count(n) for n in sorted(set(chosen))}
    else:
        base = Rule("expanding", "all", False)
        for rule in (base, TRAFFIC_RULE):
            out[rule.name] = summarise(a["te"], half_widths(rule, a["ce"], a["cs"], a["ts"], scored, *geo, ALPHA), scored)
    return out


def main(name):
    spec, cfg = c1.DOMAINS[name], CONFIG[name]
    path = os.path.join(c1.RESULTS, f"exp_C1i_{name}.json")
    n_stations = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"], n_features=1),
                                 hold_out_stations=[])[3]["coords_all"].shape[0]
    state = {"experiment": "C1i/C1j second confirmation round (PRE-REGISTRATION-C1I.md)", "domain": name,
             "stride_days": cfg["stride"], "splits": []}
    if os.path.exists(path):
        state = json.load(open(path))
    done = {s["split"] for s in state["splits"]}
    for split in cfg["splits"]:
        if split in done:
            continue
        r = run_split(name, spec, cfg, split, n_stations)
        state["splits"].append(r)
        json.dump(state, open(path, "w"), indent=2)
        print(f"[{name}] split {split} scored {r['n_scored_windows']}: " +
              " ".join(f"{k}={v['coverage']}" for k, v in r.items() if isinstance(v, dict)), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
