#!/usr/bin/env python3
"""Check that the prose figures in phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md, THESIS-OVERVIEW.md,
PROGRESSION-DECISION-BRIEF.md and EXPERIMENTS-INDEX.md match the committed V3/V3b/V4 result files.
Exit code 1 on any mismatch. Run from the repo root: python3 tools/check_phase2_findings.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "phase2-omnist-scale", "results")
DOCS = {n: open(os.path.join(ROOT, n), encoding="utf-8").read() for n in (
    "phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md", "THESIS-OVERVIEW.md",
    "PROGRESSION-DECISION-BRIEF.md", "EXPERIMENTS-INDEX.md")}
F, OV, BR, IX = list(DOCS)
fails, n = [], 0


def _norm(s):
    return " ".join(s.split())          # prose wraps lines; compare with whitespace collapsed


NDOCS = {k: _norm(v) for k, v in DOCS.items()}


def need(doc, text, why):
    global n
    n += 1
    if _norm(text) not in NDOCS[doc]:
        fails.append(f"{doc}: missing '{text}' ({why})")


v4 = json.load(open(os.path.join(R, "V4_scaling_crossover_results.json")))
sp = {r["N"]: r for r in v4["spatial"]}
tm = {r["N"]: r for r in v4["training_memory"]}
ratio = lambda r: r["exact_mem_mb"] / r["fast_mem_mb"]
tratio = lambda r: r["exact_train_mb"] / r["fast_train_mb"]
for doc in (F, OV, IX):
    need(doc, f"{ratio(sp[4000]):.1f}x", "inference memory ratio N=4000")
    need(doc, f"{ratio(sp[8000]):.1f}x", "inference memory ratio N=8000")
need(F, f"{sp[8000]['exact_mem_mb']:.0f} vs {sp[8000]['fast_mem_mb']:.0f} MB", "N=8000 MB")
need(F, f"{sp[4000]['exact_ms']:.1f} vs {sp[4000]['fast_ms']:.1f} ms", "N=4000 ms")
need(F, f"{sp[8000]['exact_ms'] / sp[8000]['fast_ms']:.1f}x less time", "N=8000 time ratio")
need(F, f"{tratio(tm[2000]):.1f}x at N=2000", "training ratio 2000")
for doc in (F, OV):
    need(doc, f"{tratio(tm[4000]):.1f}x", "training ratio 4000")
need(F, f"Not met at N=2000 ({ratio(sp[2000]):.1f}x)", "WP3 criterion line")
ch = [r["ssm_chunked_fwdbwd_ms"] / r["gru_fwdbwd_ms"] for r in v4["temporal"]]
need(F, f"{min(ch):.1f} to {max(ch):.1f} times slower than the GRU", "chunked/GRU range")

v3r = json.load(open(os.path.join(R, "V3_coverage_at_scale_real.json")))["real_pemsbay"]
fa, ex = v3r["gru+fast"], v3r["gru+exact"]
cf, ce = fa["model"]["deployable"]["coverage"], ex["model"]["deployable"]["coverage"]
need(F, f"{cf['mean']:.3f} [{cf['ci95'][0]:.3f}, {cf['ci95'][1]:.3f}]", "real gru+fast deployable CI")
need(F, f"{ce['mean']:.3f} [{ce['ci95'][0]:.3f}, {ce['ci95'][1]:.3f}]", "real gru+exact deployable CI")
for doc in (OV,):
    need(doc, f"{cf['mean']:.3f} and {ce['mean']:.3f}", "real coverage pair")
wm = fa["model"]["deployable"]["width"]["mean"]; wp = fa["persist"]["deployable"]["width"]["mean"]
ws = fa["seasonal"]["deployable"]["width"]["mean"]
need(F, f"{100 * (1 - wm / wp):.1f}% tighter than persistence ({wm:.1f} vs {wp:.1f})", "persistence gap")
need(F, f"{100 * (wm / ws - 1):.1f}% wider than seasonal-naive** ({wm:.1f} vs {ws:.1f})", "seasonal gap")
need(F, f"MAE {fa['model']['mae_test']['mean']:.2f} vs {fa['seasonal']['mae_test']['mean']:.2f}", "real MAE")
need(F, f"{fa['model']['deployable']['worst_group_global']['mean']:.3f} (`gru+fast`)", "worst group fast")
need(F, f"{ex['model']['deployable']['worst_group_global']['mean']:.3f} (`gru+exact`)", "worst group exact")
need(OV, f"{fa['model']['deployable']['worst_group_global']['mean']:.3f}", "overview worst group")

v3s = json.load(open(os.path.join(R, "V3_coverage_at_scale_synthetic.json")))["synthetic_ladder"]
seq = ", ".join(f"{v3s[N]['model']['deployable']['coverage']['mean']:.3f}" for N in ("100", "500", "1000", "2000", "4000"))
need(F, seq, "synthetic deployable sequence")
b = v3s["4000"]["meta"]["band"]
need(F, f"[{b[0]:.3f}, {b[1]:.3f}]", "N=4000 band")

v3b = json.load(open(os.path.join(R, "V3b_training_budget.json")))["rows"][-1]
need(F, f"MAE is\n  {v3b['mae_model']:.2f} against {v3b['mae_seasonal']:.2f}", "V3b MAE")
need(F, f"{v3b['width_model_deployable']:.2f} against {v3b['width_seasonal_deployable']:.2f}", "V3b width")
need(F, f"({100 * (v3b['width_model_deployable'] / v3b['width_seasonal_deployable'] - 1):.0f}% wider)", "V3b width gap")

if fails:
    print("\n".join(fails)); print(f"FAILED: {len(fails)} of {n}"); sys.exit(1)
print(f"OK: {n} Phase 2 figures match the result files")
