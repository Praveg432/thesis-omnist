#!/usr/bin/env python3
"""L1 (PREREG-2.md): Day-0 replication, component ablations, Day-0 intervals and mask-ratio sensitivity.

Usage: python3 run_leads.py <pemsbay|pemsd7> <split> [<split> ...]
Writes results/leads_<network>_split<k>.json (skips splits already written).
"""
import sys

sys.dont_write_bytecode = True

import json
import time
from pathlib import Path

import numpy as np
import torch

import v2lib as L
from run_feasibility import intervals, mae

torch.set_num_threads(3)
CORE = [L.Variant("gru", False), L.Variant("v2_mask", True, mask_ratio=0.2),
        L.Variant("v2_mask_nobias", True, mask_ratio=0.2, attention="nobias"),
        L.Variant("v2_mask_mean", True, mask_ratio=0.2, attention="mean")]
RATIOS = [L.Variant("v2_mask_r01", True, mask_ratio=0.1), L.Variant("v2_mask_r04", True, mask_ratio=0.4)]


def run_split(net, split):
    t0 = time.time()
    train, cal, test = L.station_split(net.series.shape[1], split, net.n_cal, net.n_test)
    y_tr = net.series[:net.train_end, train]
    norm = (float(y_tr.mean()), float(y_tr.std() + 1e-8))
    y_test, y_cal = L.truth(net, test), L.truth(net, cal)
    out = {"split": split, "n_windows": int(len(L.eval_starts(net))), "variants": {}, "cold_baselines": {}, "day0_intervals": {}}

    # Day-0 neighbour baselines: forecasts at the training stations, interpolated to calibration and test stations
    at_train = {"persistence": L.persistence(net, train)}
    if net.window >= net.period:
        at_train["seasonal_naive"] = L.seasonal_naive(net, train)
    variants = CORE + (RATIOS if net.name == "pemsbay" and split < 5 else [])
    for v in variants:
        model = L.train_variant(net, v, train, norm, seed=split, steps=1500, batch=8)
        warm_t, _ = L.predict(model, net, train, test, norm, cold=False)
        rec = {"warm_mae": mae(warm_t, y_test)}
        if v.spatial:
            cold_t, _ = L.predict(model, net, train, test, norm, cold=True)
            rec["cold_mae"] = mae(cold_t, y_test)
            rec["gate_mean_abs"] = round(float(model.gate.detach().abs().mean()), 5)
            if v.name == "v2_mask":
                cold_c, _ = L.predict(model, net, train, cal, norm, cold=True)
                out["day0_intervals"]["v2_mask"] = intervals(cold_c, y_cal, cold_t, y_test)
        else:
            at_train["gru"], _ = L.predict(model, net, train, train, norm, cold=False)
        out["variants"][v.name] = rec
        print(f"[{net.name} split {split}] {v.name}: " + ", ".join(f"{k}={val:.4f}" for k, val in rec.items()), flush=True)

    for base, vals in at_train.items():
        for how, nearest in (("idw", False), ("nn", True)):
            key = f"{how}_{base}"
            pred_t = L.idw(vals, net, train, test, nearest_only=nearest)
            out["cold_baselines"][key] = mae(pred_t, y_test)
            pred_c = L.idw(vals, net, train, cal, nearest_only=nearest)
            out["day0_intervals"][key] = intervals(pred_c, y_cal, pred_t, y_test)
    out["seconds"] = round(time.time() - t0, 1)
    return out


def main():
    net = L.load_network(sys.argv[1])
    outdir = Path(__file__).resolve().parent / "results"
    outdir.mkdir(exist_ok=True)
    for split in map(int, sys.argv[2:]):
        path = outdir / f"leads_{net.name}_split{split}.json"
        if path.exists():
            continue
        res = run_split(net, split)
        path.write_text(json.dumps(res, indent=1))
        print(f"wrote {path.name} in {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
