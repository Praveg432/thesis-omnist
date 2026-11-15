"""Render the Phase 2 V3/V3b/V4 result files as Markdown tables, so the numbers in
phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md come straight from the committed JSON.

Usage: python3 tools/summarise_phase2.py
"""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1] / "phase2-omnist-scale" / "results"


def load(name):
    p = R / name
    return json.loads(p.read_text()) if p.exists() else None


def f(x, n=3):
    return "n/a" if x is None else ("%.*f" % (n, x))


def ci(d, n=3):
    if not d or d.get("mean") is None:
        return "n/a"
    lo, hi = d["ci95"]
    return "%s [%s, %s]" % (f(d["mean"], n), f(lo, n), f(hi, n)) if lo is not None else f(d["mean"], n)


def v4():
    d = load("V4_scaling_crossover_results.json")
    if not d:
        return
    print("### V4 spatial (inference, CPU peak RSS delta; time on MPS)\n")
    print("| N | exact ms | exact MB | fast ms | fast MB | memory ratio |\n|---|---|---|---|---|---|")
    for r in d["spatial"]:
        ratio = r["exact_mem_mb"] / r["fast_mem_mb"] if r.get("exact_mem_mb") and r.get("fast_mem_mb") else None
        print("| %d | %s | %s | %s | %s | %s |" % (r["N"], f(r["exact_ms"], 1), f(r["exact_mem_mb"], 0),
                                                  f(r["fast_ms"], 1), f(r["fast_mem_mb"], 0), f(ratio, 1)))
    print("\n### V4 spatial (training: 8 per-timestep applications + backward, CPU peak RSS delta)\n")
    print("| N | exact MB | fast MB | ratio |\n|---|---|---|---|")
    for r in d["training_memory"]:
        ratio = r["exact_train_mb"] / r["fast_train_mb"] if r.get("exact_train_mb") and r.get("fast_train_mb") else None
        print("| %d | %s | %s | %s |" % (r["N"], f(r["exact_train_mb"], 0), f(r["fast_train_mb"], 0), f(ratio, 1)))
    print("\n### V4 temporal (forward+backward, N=100 nodes, d=64, 2 layers, MPS)\n")
    print("| T | GRU ms | SSM sequential ms | SSM chunked ms | chunked / GRU |\n|---|---|---|---|---|")
    for r in d["temporal"]:
        g, c = r["gru_fwdbwd_ms"], r["ssm_chunked_fwdbwd_ms"]
        print("| %d | %s | %s | %s | %s |" % (r["T"], f(g, 1), f(r["ssm_sequential_fwdbwd_ms"], 1), f(c, 1),
                                              f(c / g if g and c else None, 2)))


def v3():
    d = load("V3_coverage_at_scale_synthetic.json")
    if d:
        print("\n### V3 synthetic ladder (3 seeds; SYNTHETIC)\n")
        print("| N | n_cal | band | coverage same-window (oracle timing) | coverage deployable | width model (dep.) | width persistence | width seasonal-naive | worst-group global | worst-group Mondrian | infer s/window |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for N, r in d["synthetic_ladder"].items():
            m, b = r["model"], r["meta"]["band"]
            print("| %s | %d | [%s, %s] | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                N, r["meta"]["n_cal"], f(b[0]), f(b[1]), ci(m["same_window"]["coverage"]), ci(m["deployable"]["coverage"]),
                f(m["deployable"]["width"]["mean"], 2), f(r["persist"]["deployable"]["width"]["mean"], 2),
                f(r["seasonal"]["deployable"]["width"]["mean"], 2), f(m["deployable"]["worst_group_global"]["mean"]),
                f(m["deployable"]["worst_group_mondrian"]["mean"]), f(r["infer_s_per_window"]["mean"])))
    d = load("V3_coverage_at_scale_real.json")
    if d:
        print("\n### V3 real PeMS-BAY, N=325 (3 seeds, real coordinates)\n")
        print("| variant | steps | band | coverage same-window | coverage deployable | width model (dep.) | persistence | seasonal-naive | MAE model | MAE seasonal | worst-group global | worst-group Mondrian |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for k, r in d["real_pemsbay"].items():
            m, b = r["model"], r["meta"]["band"]
            print("| %s | %d | [%s, %s] | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                k, r["meta"]["steps"], f(b[0]), f(b[1]), ci(m["same_window"]["coverage"]), ci(m["deployable"]["coverage"]),
                f(m["deployable"]["width"]["mean"], 2), f(r["persist"]["deployable"]["width"]["mean"], 2),
                f(r["seasonal"]["deployable"]["width"]["mean"], 2), f(m["mae_test"]["mean"], 2),
                f(r["seasonal"]["mae_test"]["mean"], 2), f(m["deployable"]["worst_group_global"]["mean"]),
                f(m["deployable"]["worst_group_mondrian"]["mean"])))


def v3b():
    d = load("V3b_training_budget.json")
    if not d:
        return
    print("\n### V3b training budget (PeMS-BAY, seed 0, deployable protocol)\n")
    print("| steps | train s | coverage dep. | width model | width seasonal | width persistence | MAE model | MAE seasonal |\n|---|---|---|---|---|---|---|---|")
    for r in d["rows"]:
        print("| %d | %.0f | %s | %s | %s | %s | %s | %s |" % (
            r["steps"], r["train_s"], f(r["coverage_deployable"]), f(r["width_model_deployable"], 2),
            f(r["width_seasonal_deployable"], 2), f(r["width_persist_deployable"], 2), f(r["mae_model"], 2), f(r["mae_seasonal"], 2)))
    print("\nVerdict string in file: " + d["verdict"])


if __name__ == "__main__":
    v4(); v3(); v3b()
