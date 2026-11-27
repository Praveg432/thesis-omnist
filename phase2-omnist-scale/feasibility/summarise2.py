#!/usr/bin/env python3
"""Apply the pass rules of PREREG-2.md. Writes results/verdicts2.json and prints it."""
import json
from pathlib import Path

import numpy as np
from scipy import stats

R = Path(__file__).resolve().parent / "results"
THESIS_RESULTS = Path(__file__).resolve().parents[2] / "phase1-omnist" / "results"
SN_PEMSBAY, PERS_PEMSD7 = 3.47, 3.63  # thesis C1c, quoted in PREREG-2.md


def paired(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    h = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
    return {"mean": round(float(d.mean()), 4), "ci95": [round(float(d.mean() - h), 4), round(float(d.mean() + h), 4)], "n": len(d)}


def m(x):
    return round(float(np.mean(x)), 4)


out = {}
for net in ("pemsbay", "pemsd7"):
    sp = sorted((json.loads(p.read_text()) for p in R.glob(f"leads_{net}_split*.json")), key=lambda s: s["split"])
    if not sp:
        continue
    cold = lambda v: [s["variants"][v]["cold_mae"] for s in sp]
    base = lambda k: [s["cold_baselines"][k] for s in sp]
    best = min(sp[0]["cold_baselines"], key=lambda k: np.mean(base(k)))
    d_best = paired(cold("v2_mask"), base(best))
    o = {"n_splits": len(sp), "best_neighbour_baseline": best,
         "cold_mae": {"v2_mask": m(cold("v2_mask")), "v2_mask_nobias": m(cold("v2_mask_nobias")), "v2_mask_mean": m(cold("v2_mask_mean")),
                      **{k: m(base(k)) for k in sp[0]["cold_baselines"]}},
         "warm_mae": {v: m([s["variants"][v]["warm_mae"] for s in sp]) for v in ("gru", "v2_mask", "v2_mask_nobias", "v2_mask_mean")},
         "L1a_diff_v2_minus_best": d_best, "L1a_ratio": round(np.mean(cold("v2_mask")) / np.mean(base(best)), 4)}
    o["L1a"] = "PASS" if d_best["ci95"][1] < 0 and o["L1a_ratio"] <= 0.95 else "FAIL"
    if net == "pemsbay":
        fresh = [s for s in sp if s["split"] >= 5]
        fb = [s["cold_baselines"][best] for s in fresh]
        fv = [s["variants"]["v2_mask"]["cold_mae"] for s in fresh]
        o["L1a_fresh_splits_5_9"] = {"diff": paired(fv, fb), "ratio": round(np.mean(fv) / np.mean(fb), 4)}
    d_mean, d_nob = paired(cold("v2_mask"), cold("v2_mask_mean")), paired(cold("v2_mask"), cold("v2_mask_nobias"))
    o["L1b_diff_v2_minus_mean_pool"], o["L1b_diff_v2_minus_nobias"] = d_mean, d_nob
    o["L1b_attention_needed"] = "PASS" if d_mean["ci95"][1] < 0 else "FAIL"
    o["L1b_distance_bias_needed"] = "PASS" if d_nob["ci95"][1] < 0 else "FAIL"
    iv = lambda k: [s["day0_intervals"][k] for s in sp]
    v2i, bi = iv("v2_mask"), iv(best)
    d_is = paired([r["interval_score"] for r in v2i], [r["interval_score"] for r in bi])
    o["day0_intervals"] = {k: {"coverage": m([r["coverage"] for r in iv(k)]), "width": m([r["width"] for r in iv(k)]),
                               "interval_score": m([r["interval_score"] for r in iv(k)])} for k in sp[0]["day0_intervals"]}
    o["L1c_diff_interval_score_v2_minus_best"] = d_is
    o["L1c"] = "PASS" if abs(o["day0_intervals"]["v2_mask"]["coverage"] - 0.90) <= 0.03 and d_is["ci95"][1] < 0 else "FAIL"
    if net == "pemsbay":
        rs = [s for s in sp if "v2_mask_r01" in s["variants"]]
        rr = {}
        for v in ("v2_mask_r01", "v2_mask", "v2_mask_r04"):
            ratio = np.mean([s["variants"][v]["cold_mae"] for s in rs]) / np.mean([s["cold_baselines"][best] for s in rs])
            rr[v] = round(float(ratio), 4)
        o["L1d_ratio_to_best_baseline_splits_0_4"] = rr
        o["L1d"] = "PASS" if rr["v2_mask_r01"] <= 0.95 and rr["v2_mask_r04"] <= 0.95 else "FAIL"
    out[net] = o

for dom, label in (("pemsbay_traffic", "pemsbay"), ("pemsd7_traffic", "pemsd7")):
    p = R / f"l2_{dom}.json"
    if not p.exists():
        continue
    tod = sorted(json.loads(p.read_text())["splits"], key=lambda s: s["split"])
    ref = {s["split"]: s for s in json.load(open(THESIS_RESULTS / f"exp_C1b_norm_{dom}.json"))["splits"]}
    ids = [s["split"] for s in tod]
    a, b = [s["test_mae"] for s in tod], [ref[i]["test_mae"] for i in ids]
    d = paired(a, b)
    ratio = np.mean(a) / np.mean(b)
    o = {"n_splits": len(tod), "mae_with_tod": m(a), "mae_without_tod": m(b), "ratio": round(float(ratio), 4), "diff": d,
         "chrono_coverage_with_tod": m([s["chronological"]["coverage"] for s in tod]),
         "chrono_coverage_without_tod": m([ref[i]["chronological"]["coverage"] for i in ids]),
         "chrono_width_with_tod": m([s["chronological"]["width"] for s in tod]),
         "chrono_width_without_tod": m([ref[i]["chronological"]["width"] for i in ids])}
    o["L2a"] = "PASS" if d["ci95"][1] < 0 and ratio <= 0.90 else "FAIL"
    bar = SN_PEMSBAY if label == "pemsbay" else PERS_PEMSD7
    o["L2b_bar"], o["L2b"] = bar, ("PASS" if o["mae_with_tod"] < bar else "FAIL")
    o["L2c"] = "PASS" if abs(o["chrono_coverage_with_tod"] - 0.90) <= 0.02 and o["chrono_width_with_tod"] < o["chrono_width_without_tod"] else "FAIL"
    out.setdefault("L2", {})[label] = o

(R / "verdicts2.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
