#!/usr/bin/env python3
"""Exploratory: thesis model with training stride 12 against the committed stride-48 runs, same splits and seeds."""
import json
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
T = HERE.parents[1] / "phase1-omnist" / "results"
out = {}
for dom in ("pemsbay_traffic", "pemsd7_traffic"):
    x = sorted(json.loads((HERE / "results" / f"l2x_stride12_{dom}.json").read_text())["splits"], key=lambda s: s["split"])
    ref = {s["split"]: s for s in json.load(open(T / f"exp_C1b_norm_{dom}.json"))["splits"]}
    a = np.array([s["test_mae"] for s in x])
    b = np.array([ref[s["split"]]["test_mae"] for s in x])
    d = a - b
    h = stats.t.ppf(.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
    out[dom] = {"splits": [s["split"] for s in x], "mae_stride12": a.round(4).tolist(), "mae_stride48_committed": b.round(4).tolist(),
                "mean_stride12": round(float(a.mean()), 4), "mean_stride48": round(float(b.mean()), 4),
                "ratio": round(float(a.mean() / b.mean()), 4),
                "diff_mean": round(float(d.mean()), 4), "diff_ci95": [round(float(d.mean() - h), 4), round(float(d.mean() + h), 4)],
                "chrono_cov_stride12": round(float(np.mean([s["chronological"]["coverage"] for s in x])), 4),
                "chrono_cov_stride48": round(float(np.mean([ref[s["split"]]["chronological"]["coverage"] for s in x])), 4),
                "chrono_width_stride12": round(float(np.mean([s["chronological"]["width"] for s in x])), 4),
                "chrono_width_stride48": round(float(np.mean([ref[s["split"]]["chronological"]["width"] for s in x])), 4)}
(HERE / "results" / "l2x_stride_summary.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
