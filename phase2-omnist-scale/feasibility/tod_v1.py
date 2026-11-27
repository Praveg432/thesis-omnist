#!/usr/bin/env python3
"""L2 (PREREG-2.md): the thesis model (OmniST v1) with the constant year input replaced by the time of day.

Runs the thesis's own C1b pipeline read-only from the sandbox. `run_split` is a copy of
thesis-omnist/phase1-omnist/experiments/C1b_chronological_eval.py:run_split with norm=True, plus one optional change:
the 4th timestamp column (year fraction, constant within these single-year series) is overwritten with the time of day
as a fraction of the day, in the training, validation and evaluation datasets. Before overwriting, the script checks
that its reconstructed dates reproduce the dataset's existing timestamp encoding exactly.

Usage: python3 tod_v1.py <pemsbay_traffic|pemsd7_traffic> control      # split 0 without the change, vs committed result
       python3 tod_v1.py <pemsbay_traffic|pemsd7_traffic> run <splits..>  # with time of day
       python3 tod_v1.py <pemsbay_traffic|pemsd7_traffic> stride <stride> <splits..>
           EXPLORATORY, not pre-registered: no time of day; only the training-window stride changes (the thesis traffic
           loaders use stride = window = 48, so at PeMS-BAY's 30-minute cadence every training window starts at the
           same clock time). Output results/l2x_stride<stride>_<domain>.json.
"""
import sys

sys.dont_write_bytecode = True

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

THESIS = Path(__file__).resolve().parents[2] / "phase1-omnist"  # thesis-omnist/phase1-omnist
sys.path.insert(0, str(THESIS))
sys.path.insert(0, str(THESIS / "experiments"))
os.environ.setdefault("OMP_NUM_THREADS", "2")

import C1_rigorous_inductive_eval as c1  # noqa: E402  (sets torch threads to 2, as in the thesis runs)
from src.cc_hash import training_coordinate_frame  # noqa: E402
from src.chronological_conformal import compare_protocols  # noqa: E402
from src.data import DataConfig  # noqa: E402
from src.data_pemsbay import load_real_pemsbay  # noqa: E402
from src.data import SpatiotemporalDataset  # noqa: E402
from src.data_traffic_real import load_real_traffic  # noqa: E402
from src.omnist_model import ModelConfig, OmniST  # noqa: E402
from src.trainer import TrainConfig, train_model  # noqa: E402

WARMUP_FRACTION = 0.25
PROTOCOLS = ("chronological", "same_window", "pooled")
OUT = Path(__file__).resolve().parent / "results"


def split_dates(name):
    dates = pd.DatetimeIndex((load_real_pemsbay() if name == "pemsbay_traffic" else load_real_traffic())[2])
    n = len(dates)
    test_len, val_len = int(n * 0.20), int(n * 0.10)
    train_val = dates[:-test_len]
    return {"train": train_val[:-val_len], "val": train_val[-val_len:], "test": dates[-test_len:]}


def set_time_of_day(ds, dates):
    """Overwrite the constant year column with the time of day, after checking the dates line up exactly."""
    if len(ds.timestamps) != len(dates):
        raise ValueError(f"dataset has {len(ds.timestamps)} timestamps, reconstructed dates {len(dates)}")
    if not torch.allclose(ds._encode_timestamps(dates.values), ds.timestamps):
        raise ValueError("reconstructed dates do not reproduce the dataset's timestamp encoding")
    if float(ds.timestamps[:, 3].std()) != 0.0:
        raise ValueError("the year column is not constant; replacing it would lose information")
    tod = (dates.hour.values * 60 + dates.minute.values) / 1440.0
    ds.timestamps[:, 3] = torch.as_tensor(tod, dtype=torch.float32)


def run_split(name, spec, split, n_stations, with_tod, dates, train_stride=None):
    t0 = time.time()
    perm = np.random.default_rng(1000 + split).permutation(n_stations)
    test_idx = np.sort(perm[:spec["n_test"]])
    cal_idx = np.sort(perm[spec["n_test"]:spec["n_test"] + spec["n_cal"]])
    held = sorted(int(i) for i in np.concatenate([cal_idx, test_idx]))
    torch.manual_seed(split)
    np.random.seed(split)
    window, horizon = spec["window"], spec["horizon"]
    cfg = DataConfig(window_size=window, horizon=horizon, n_features=1)
    tcfg = TrainConfig(lr=1e-3, n_epochs=spec["epochs"], patience=spec["patience"], batch_size=spec["batch"], loss_type="pot")
    train_ds, val_ds, _, meta = spec["prepare"](cfg, hold_out_stations=held)
    if train_stride is not None:
        old = train_ds
        train_ds = SpatiotemporalDataset(old.features.numpy(), old.coords.numpy(), dates["train"].values,
                                         window_size=old.window_size, horizon=old.horizon, stride=train_stride)
        if not torch.allclose(train_ds.timestamps, old.timestamps):
            raise ValueError("re-strided training set does not reproduce the original timestamps")
    if with_tod:
        set_time_of_day(train_ds, dates["train"])
        set_time_of_day(val_ds, dates["val"])
    center, scale = training_coordinate_frame(np.asarray(meta["coords_all"])[meta["train_stations"]])
    model = OmniST(ModelConfig(n_features=1, horizon=horizon, d_model=64, k_neighbors=8,
                               knn_mode=spec.get("knn_mode", "exact"), coord_center=center, coord_scale=scale,
                               residual_to_last=False))
    train_model(model, train_ds, val_ds, tcfg, meta)
    cal_ds, test_ds = c1.station_dataset(meta, cal_idx, window, horizon), c1.station_dataset(meta, test_idx, window, horizon)
    if with_tod:
        set_time_of_day(cal_ds, dates["test"])
        set_time_of_day(test_ds, dates["test"])
    cal_scores, test_scores = c1.score_array(model, meta, cal_ds), c1.score_array(model, meta, test_ds)
    res = {"split": split, "with_time_of_day": with_tod, "test_mae": round(float(test_scores.mean()), 4)}
    compared = compare_protocols(cal_scores, test_scores, c1.ALPHA, WARMUP_FRACTION)
    for p in PROTOCOLS:
        res[p] = {k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v]) for k, v in compared[p].items()}
    res["seconds"] = round(time.time() - t0, 1)
    return res


def main():
    name, mode = sys.argv[1], sys.argv[2]
    spec = c1.DOMAINS[name]
    n_stations = spec["prepare"](DataConfig(window_size=spec["window"], horizon=spec["horizon"], n_features=1),
                                 hold_out_stations=[])[3]["coords_all"].shape[0]
    dates = split_dates(name)
    OUT.mkdir(exist_ok=True)
    if mode == "control":
        mine = run_split(name, spec, 0, n_stations, False, dates)
        stored = next(s for s in json.load(open(THESIS / "results" / f"exp_C1b_norm_{name}.json"))["splits"] if s["split"] == 0)
        pairs = {"test_mae": (mine["test_mae"], stored["test_mae"]),
                 **{p: (mine[p]["coverage"], stored[p]["coverage"]) for p in PROTOCOLS}}
        ok = all(a == b for a, b in pairs.values())
        (OUT / f"l2_control_{name}.json").write_text(json.dumps({"pairs": pairs, "reproduced_exactly": ok}, indent=1))
        print(name, "control", pairs, "REPRODUCED" if ok else "MISMATCH", flush=True)
        return
    if mode == "stride":
        stride = int(sys.argv[3])
        path = OUT / f"l2x_stride{stride}_{name}.json"
        state = json.loads(path.read_text()) if path.exists() else {"domain": name, "train_stride": stride, "exploratory": True, "splits": []}
        done = {s["split"] for s in state["splits"]}
        for split in map(int, sys.argv[4:]):
            if split in done:
                continue
            r = run_split(name, spec, split, n_stations, False, dates, train_stride=stride)
            r["train_stride"] = stride
            state["splits"].append(r)
            path.write_text(json.dumps(state, indent=1))
            print(f"[{name}] split {split} stride {stride}: mae {r['test_mae']} chrono cov {r['chronological']['coverage']} "
                  f"width {r['chronological']['width']} | {r['seconds']} s", flush=True)
        return
    path = OUT / f"l2_{name}.json"
    state = json.loads(path.read_text()) if path.exists() else {"domain": name, "splits": []}
    done = {s["split"] for s in state["splits"]}
    for split in map(int, sys.argv[3:]):
        if split in done:
            continue
        state["splits"].append(run_split(name, spec, split, n_stations, True, dates))
        path.write_text(json.dumps(state, indent=1))
        r = state["splits"][-1]
        print(f"[{name}] split {split} with time of day: mae {r['test_mae']} chrono cov {r['chronological']['coverage']} "
              f"width {r['chronological']['width']} | {r['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
