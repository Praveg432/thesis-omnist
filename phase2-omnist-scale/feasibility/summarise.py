#!/usr/bin/env python3
"""Apply the pass rules of PREREG.md to results/*.json. Writes results/verdicts.json and prints a report."""
import json
from pathlib import Path

import numpy as np
from scipy import stats

R = Path(__file__).resolve().parent / "results"


def load(net):
    return [json.loads(p.read_text()) for p in sorted(R.glob(f"{net}_split*.json"))]


def paired(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    h = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
    return {"mean": round(float(d.mean()), 4), "ci95": [round(float(d.mean() - h), 4), round(float(d.mean() + h), 4)], "n": len(d)}


def mean(x):
    return round(float(np.mean(x)), 4)


V, out = {}, {}
for net in ("delhi", "pemsbay"):
    sp = load(net)
    if not sp:
        continue
    var = lambda name, key: [s["variants"][name][key] for s in sp]
    base = lambda key: [s["baselines"][key] for s in sp]
    gru, nomask, mask = var("gru", "warm_mae"), var("v2_nomask", "warm_mae"), var("v2_mask", "warm_mae")
    cold_keys = [k for k in sp[0]["baselines"] if k.startswith("cold_")]
    best_key = min(cold_keys, key=lambda k: np.mean(base(k)))
    cold_v2 = var("v2_mask", "cold_mae")
    o = {"n_splits": len(sp),
         "warm_mae": {"gru": mean(gru), "v2_nomask": mean(nomask), "v2_mask": mean(mask),
                      "persistence": mean(base("warm_persistence_mae")), "seasonal_naive": mean(base("warm_seasonal_naive_mae"))},
         "cold_mae": {"v2_mask": mean(cold_v2), "v2_nomask": mean(var("v2_nomask", "cold_mae")),
                      **{k.replace("cold_", ""): mean(base(k)) for k in cold_keys}},
         "gate_mean_abs": {"v2_nomask": mean(var("v2_nomask", "gate_mean_abs")), "v2_mask": mean(var("v2_mask", "gate_mean_abs"))},
         "F1_diff_v2_nomask_minus_gru": paired(nomask, gru),
         "F2_ratio_v2_mask_over_gru": round(np.mean(mask) / np.mean(gru), 4),
         "F3_best_neighbour_baseline": best_key.replace("cold_", ""),
         "F3_diff_v2_mask_cold_minus_best": paired(cold_v2, base(best_key)),
         "F3_ratio": round(np.mean(cold_v2) / np.mean(base(best_key)), 4)}
    f1 = o["F1_diff_v2_nomask_minus_gru"]
    o["F1"] = "PASS" if f1["ci95"][1] < 0 and np.mean(nomask) <= 0.98 * np.mean(gru) else "FAIL"
    o["F2"] = "PASS" if o["F2_ratio_v2_mask_over_gru"] <= 1.01 else "FAIL"
    o["F3"] = "PASS" if o["F3_diff_v2_mask_cold_minus_best"]["ci95"][1] < 0 and o["F3_ratio"] <= 0.95 else "FAIL"
    if net == "pemsbay":
        iv = lambda name: [s["variants"][name]["intervals"] for s in sp]
        isc = lambda rows: [r["interval_score"] for r in rows]
        sn = [s["intervals"]["seasonal_naive"] for s in sp]
        pers = [s["intervals"]["persistence"] for s in sp]
        o["intervals"] = {name: {"coverage": mean([r["coverage"] for r in rows]), "width": mean([r["width"] for r in rows]),
                                 "interval_score": mean(isc(rows))}
                          for name, rows in (("seasonal_naive", sn), ("persistence", pers), ("gru", iv("gru")), ("v2_mask", iv("v2_mask")),
                                             ("gru_res_scale", iv("gru_res_scale")), ("v2_res_scale", iv("v2_res_scale")))}
        d_sn = paired(isc(iv("v2_res_scale")), isc(sn))
        d_gru = paired(isc(iv("v2_res_scale")), isc(iv("gru_res_scale")))
        d_grusn = paired(isc(iv("gru_res_scale")), isc(sn))
        cov = o["intervals"]["v2_res_scale"]["coverage"]
        o["F4_diff_v2_res_scale_minus_seasonal_naive"] = d_sn
        o["F4_diff_v2_res_scale_minus_gru_res_scale"] = d_gru
        o["F4_diff_gru_res_scale_minus_seasonal_naive"] = d_grusn
        o["F4"] = "PASS" if d_sn["ci95"][1] < 0 and abs(cov - 0.90) <= 0.02 else "FAIL"
        o["F4_attribution_to_spatial"] = "PASS" if d_gru["ci95"][1] < 0 else "FAIL"
    out[net] = o

mem = json.loads((R / "memory.json").read_text()) if (R / "memory.json").exists() else []
if mem:
    g = {(r["N"], r["mode"]): r.get("layer_peak_mb") for r in mem}
    ratio = g[(8000, "dense")] / g[(8000, "knn")] if g.get((8000, "dense")) else float("inf")
    growth = g[(8000, "knn")] / g[(2000, "knn")]
    out["memory"] = {"knn_mb": {n: round(g[(n, "knn")], 1) for n in (2000, 4000, 8000)},
                     "dense_mb": {n: round(g[(n, "dense")], 1) for n in (2000, 4000, 8000) if g.get((n, "dense"))},
                     "dense_over_knn_at_8000": round(ratio, 2), "knn_growth_2000_to_8000": round(growth, 2),
                     "F5": "PASS" if ratio >= 5 and growth <= 5 else "FAIL"}
(R / "verdicts.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
