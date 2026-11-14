"""T1 - diagnostic: forward-pass time of the current BidirectionalSSM vs the BidirectionalGRU.

Not a vetting gate. It records a fact found during review: the SSM block is evaluated by a
sequential Python loop, so it has no time-parallel advantage, and it is slower than the GRU.
Run it on an otherwise idle machine; the result is a ratio, not an absolute speed.

Run: python experiments/T1_ssm_vs_gru_timing.py
Writes results/T1_ssm_vs_gru_timing.json
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import torch

from omnist_scale.omnist.temporal import BidirectionalGRU
from omnist_scale.ssm_temporal import BidirectionalSSM

DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
D_MODEL, BATCH, NODES, LAYERS, REPS = 64, 4, 37, 2, 5
LENGTHS = (60, 240, 960)


def sync() -> None:
    if DEV.type == "mps":
        torch.mps.synchronize()


def forward_ms(module, length: int) -> float:
    x = torch.randn(BATCH, length, NODES, D_MODEL, device=DEV)
    with torch.no_grad():
        module(x)
        sync()
        start = time.time()
        for _ in range(REPS):
            module(x)
        sync()
    return (time.time() - start) / REPS * 1000.0


def run() -> dict:
    ssm = BidirectionalSSM(D_MODEL, n_layers=LAYERS).to(DEV).eval()
    gru = BidirectionalGRU(D_MODEL, n_layers=LAYERS).to(DEV).eval()
    rows = []
    for length in LENGTHS:
        g, s = forward_ms(gru, length), forward_ms(ssm, length)
        rows.append({"T": length, "gru_ms": round(g, 1), "ssm_ms": round(s, 1),
                     "ssm_over_gru": round(s / g, 2)})
        print(f"T={length:>4}: GRU {g:7.1f} ms  SSM {s:7.1f} ms  ratio {s / g:.2f}", flush=True)
    out = {"experiment": "T1 diagnostic: SSM vs GRU forward time", "device": str(DEV),
           "batch": BATCH, "nodes": NODES, "d_model": D_MODEL, "layers": LAYERS, "reps": REPS,
           "rows": rows,
           "reading": "A ratio near 2 at every T, with both growing linearly in T, means the SSM "
                      "scan is sequential and has no time-parallel advantage over the GRU."}
    results = Path(__file__).resolve().parents[1] / "results"
    results.mkdir(exist_ok=True)
    (results / "T1_ssm_vs_gru_timing.json").write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    run()
