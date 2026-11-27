#!/usr/bin/env python3
"""Run the pre-registered feasibility tests F1 to F4 (PREREG.md) for one network and a list of splits.

Usage: python3 run_feasibility.py <delhi|pemsbay> <split> [<split> ...] [quick]
Writes results/<network>_split<k>.json (skips splits already written; quick runs go to results/quick/).
"""
import sys

sys.dont_write_bytecode = True

import json
import time
from pathlib import Path

import numpy as np
import torch

import v2lib as L
from src.chronological_conformal import chronological_quantiles, warmup_windows  # thesis helpers, read-only
from src.interval_metrics import interval_score

torch.set_num_threads(3)
ALPHA = 0.10
VARIANTS = {
    "delhi": [L.Variant("gru", False), L.Variant("v2_nomask", True), L.Variant("v2_mask", True, mask_ratio=0.2)],
    "pemsbay": [L.Variant("gru", False), L.Variant("v2_nomask", True), L.Variant("v2_mask", True, mask_ratio=0.2),
                L.Variant("gru_res_scale", False, residual=True, scale_head=True),
                L.Variant("v2_res_scale", True, residual=True, scale_head=True)],
}
BATCH = {"delhi": 16, "pemsbay": 8}


def mae(pred, y):
    return float(np.abs(pred - y).mean())


def intervals(cal_pred, cal_y, test_pred, test_y, cal_scale=None, test_scale=None):
    """Forecast-time expanding split conformal at the calibration stations; metrics on the test stations."""
    cal_err, test_err = np.abs(cal_pred - cal_y), np.abs(test_pred - test_y)
    first = warmup_windows(cal_err.shape[0], 0.25)
    if cal_scale is None:
        q = chronological_quantiles(cal_err, first, ALPHA)
        half = np.broadcast_to(q[:, None, None], test_err[first:].shape)
    else:
        q = chronological_quantiles(cal_err / cal_scale, first, ALPHA)
        half = q[:, None, None] * test_scale[first:]
    e = test_err[first:]
    covered = e <= half
    return {"coverage": round(float(covered.mean()), 4), "width": round(float(2 * half.mean()), 4),
            "interval_score": round(interval_score(e, half, ALPHA), 4),
            "per_station_coverage": [round(float(c), 4) for c in covered.mean(axis=(0, 2))]}


def run_split(net, split, steps):
    t0 = time.time()
    train, cal, test = L.station_split(net.series.shape[1], split, net.n_cal, net.n_test)
    y_tr = net.series[:net.train_end, train]
    norm = (float(y_tr.mean()), float(y_tr.std() + 1e-8))
    y_test, y_cal = L.truth(net, test), L.truth(net, cal)
    out = {"split": split, "n_train": len(train), "n_windows": int(len(L.eval_starts(net))), "variants": {}, "baselines": {}}

    # warm baselines at the test stations
    pers_t, pers_c = L.persistence(net, test), L.persistence(net, cal)
    sn_t, sn_c = L.seasonal_naive(net, test), L.seasonal_naive(net, cal)
    out["baselines"]["warm_persistence_mae"] = mae(pers_t, y_test)
    out["baselines"]["warm_seasonal_naive_mae"] = mae(sn_t, y_test)
    # cold neighbour baselines: forecasts made at the training stations, interpolated to the test stations
    pers_tr, sn_tr = L.persistence(net, train), L.seasonal_naive(net, train)
    out["baselines"]["cold_nn_persistence_mae"] = mae(L.idw(pers_tr, net, train, test, nearest_only=True), y_test)
    out["baselines"]["cold_idw_persistence_mae"] = mae(L.idw(pers_tr, net, train, test), y_test)
    out["baselines"]["cold_idw_seasonal_naive_mae"] = mae(L.idw(sn_tr, net, train, test), y_test)
    if net.name == "pemsbay":
        out["intervals"] = {"persistence": intervals(pers_c, y_cal, pers_t, y_test),
                            "seasonal_naive": intervals(sn_c, y_cal, sn_t, y_test)}

    for v in VARIANTS[net.name]:
        model = L.train_variant(net, v, train, norm, seed=split, steps=steps, batch=BATCH[net.name])
        rec = {}
        warm_t, sc_t = L.predict(model, net, train, test, norm, cold=False)
        rec["warm_mae"] = mae(warm_t, y_test)
        if v.spatial:
            rec["gate_mean_abs"] = round(float(model.gate.detach().abs().mean()), 5)
            if not v.residual:
                cold_t, _ = L.predict(model, net, train, test, norm, cold=True)
                rec["cold_mae"] = mae(cold_t, y_test)
        if v.name == "gru":
            gru_at_train, _ = L.predict(model, net, train, train, norm, cold=False)
            out["baselines"]["cold_idw_gru_mae"] = mae(L.idw(gru_at_train, net, train, test), y_test)
        if net.name == "pemsbay" and not (v.spatial and not v.residual and v.mask_ratio == 0):
            warm_c, sc_c = L.predict(model, net, train, cal, norm, cold=False)
            rec["intervals"] = intervals(warm_c, y_cal, warm_t, y_test, sc_c, sc_t)
        out["variants"][v.name] = rec
        print(f"[{net.name} split {split}] {v.name}: " + ", ".join(f"{k}={val}" for k, val in rec.items() if k != "intervals"), flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    return out


def main():
    args = [a for a in sys.argv[1:] if a != "quick"]
    quick = "quick" in sys.argv[1:]
    net = L.load_network(args[0])
    outdir = Path(__file__).resolve().parent / "results" / ("quick" if quick else "")
    outdir.mkdir(parents=True, exist_ok=True)
    for split in map(int, args[1:]):
        path = outdir / f"{net.name}_split{split}.json"
        if path.exists() and not quick:
            continue
        res = run_split(net, split, steps=60 if quick else 1500)
        path.write_text(json.dumps(res, indent=1))
        print(f"wrote {path.name} in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
