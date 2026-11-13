"""V2 - equivalence bound: O(N·k) fast attention vs exact attention (H2).

No training needed. With SHARED weights (only neighbour SELECTION differs), measure the output
agreement of FastInductiveGAT vs the exact InductiveGAT across node counts, and the throughput
crossover. GO: cosine similarity >= 0.999 at the scales where exact is still affordable, and the fast
path stays sub-quadratic in memory/time as N grows.

Run: python experiments/V2_attention_equivalence.py  [quick]
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import numpy as np
import torch

from omnist_scale.omnist.inductive_gat import InductiveGAT
from omnist_scale.fast_attention import FastInductiveGAT

DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def make_pair(d=64, H=4, k=8, seed=0):
    torch.manual_seed(seed)
    exact = InductiveGAT(d, H, k).to(DEV).eval()
    fast = FastInductiveGAT(d, H, k).to(DEV).eval()
    for name in ("q_proj", "k_proj", "v_proj", "out_proj", "dist_bias", "norm"):
        getattr(fast, name).load_state_dict(getattr(exact, name).state_dict())
    return exact, fast


def run(quick=False):
    t0 = time.time()
    d = 64
    Ns = [37, 100, 325] if quick else [37, 100, 325, 1000, 2000]
    exact, fast = make_pair(d=d)
    rows = []
    for N in Ns:
        coords = (torch.rand(1, N, 2) * torch.tensor([0.4, 0.6]) + torch.tensor([28.4, 76.8])).to(DEV)
        tokens = torch.randn(1, N, d, device=DEV)
        with torch.no_grad():
            # time fast always; exact only where O(N^2) is affordable
            tf0 = time.time()
            of = fast(tokens, coords)
            tf = time.time() - tf0
            exact_ok = N <= 2000
            if exact_ok:
                te0 = time.time(); oe = exact(tokens, coords); te = time.time() - te0
                cos = torch.nn.functional.cosine_similarity(oe.flatten(), of.flatten(), dim=0).item()
                rel = (oe - of).norm().item() / (oe.norm().item() + 1e-9)
            else:
                te, cos, rel = None, None, None
        rows.append({"N": N, "cosine_vs_exact": round(cos, 6) if cos is not None else None,
                     "rel_l2_diff": round(rel, 6) if rel is not None else None,
                     "fast_time_s": round(tf, 4), "exact_time_s": round(te, 4) if te is not None else None})
        print(f"  N={N:>5}: cosine={cos if cos is None else round(cos,5)} "
              f"fast={tf*1000:.1f}ms exact={'n/a' if te is None else f'{te*1000:.1f}ms'}", flush=True)

    cos_vals = [r["cosine_vs_exact"] for r in rows if r["cosine_vs_exact"] is not None]
    min_cos = min(cos_vals) if cos_vals else None
    equivalent = min_cos is not None and min_cos >= 0.999
    verdict = ("GO - fast attention is numerically equivalent to exact (min cosine %.5f >= 0.999) "
               "across tested N; the O(N.k) path is a drop-in for exact with no coverage/accuracy "
               "cost." % min_cos) if equivalent else \
              ("CHECK - min cosine %.5f < 0.999; investigate neighbour-selection mismatch before "
               "claiming equivalence." % (min_cos if min_cos is not None else float("nan")))
    out = {"experiment": "V2 fast O(N.k) attention equivalence vs exact (shared weights)",
           "device": str(DEV), "d_model": d, "rows": rows,
           "min_cosine_vs_exact": min_cos, "equivalent": bool(equivalent),
           "verdict": verdict, "runtime_seconds": round(time.time() - t0, 2)}
    from pathlib import Path
    rd = Path(__file__).resolve().parents[1] / "results"; rd.mkdir(exist_ok=True)
    (rd / "V2_attention_equivalence_results.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({"min_cosine_vs_exact": min_cos, "verdict": verdict}, indent=2, default=float))
    return out


if __name__ == "__main__":
    run(quick=(len(sys.argv) > 1 and sys.argv[1] == "quick"))
