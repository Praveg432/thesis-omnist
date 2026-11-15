"""V3b - is the model's width gap vs seasonal-naive on real PeMS-BAY just undertraining?

An early 300-step run gave valid coverage but an interval WIDTH above seasonal-naive on real traffic.
This sweeps the training budget on one seed (gru+fast) and reports, under the DEPLOYABLE (chronological)
calibration protocol, coverage, width and MAE against persistence and seasonal-naive. If width falls
below seasonal-naive with more training the gap was undertraining; if it plateaus above, the
patch-trained model is not competitive with a trivial seasonal predictor on this data.

Run: python experiments/V3b_training_budget.py [quick]
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from V3_coverage_at_scale import load_pemsbay, run_one, ROOT

quick = "quick" in sys.argv
y, coords, ts, per_day = load_pemsbay()
budgets = [60, 200] if quick else [300, 1200, 3000]
rows = []
for steps in budgets:
    r = run_one(y, coords, ts, per_day, 0, ("gru", "fast"), W=48, H=6, steps=steps, patch=128, n_eval_windows=60)
    m, sn, pr = r["model"], r["seasonal"], r["persist"]
    row = {"steps": steps, "train_s": r["meta"]["train_s"],
           "coverage_deployable": m["deployable"]["coverage"], "coverage_same_window": m["same_window"]["coverage"],
           "width_model_deployable": m["deployable"]["width"], "width_seasonal_deployable": sn["deployable"]["width"],
           "width_persist_deployable": pr["deployable"]["width"],
           "mae_model": m["mae_test"], "mae_seasonal": sn["mae_test"], "mae_persist": pr["mae_test"],
           "band": r["meta"]["band"]}
    rows.append(row)
    print("  steps=%5d train=%5.0fs cov dep=%.3f sw=%.3f | width dep: model=%.2f seasonal=%.2f persist=%.2f | MAE model=%.2f seasonal=%.2f"
          % (steps, row["train_s"], row["coverage_deployable"], row["coverage_same_window"],
             row["width_model_deployable"], row["width_seasonal_deployable"], row["width_persist_deployable"],
             row["mae_model"], row["mae_seasonal"]), flush=True)
beats = rows[-1]["width_model_deployable"] < rows[-1]["width_seasonal_deployable"]
out = {"experiment": "V3b training-budget sweep on real PeMS-BAY (seed 0, gru+fast), deployable protocol",
       "rows": rows, "model_beats_seasonal_naive_at_max_budget": bool(beats),
       "verdict": ("Width falls below seasonal-naive with more training -> the earlier gap was undertraining."
                   if beats else
                   "Width stays above seasonal-naive at the largest budget -> the patch-trained model is not "
                   "competitive with a trivial seasonal predictor on this real traffic data.")}
(ROOT / "results" / ("V3b_training_budget%s.json" % ("_quick" if quick else ""))).write_text(json.dumps(out, indent=2, default=float))
print(out["verdict"])
