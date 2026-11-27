#!/usr/bin/env python3
"""F5: peak memory of the v2 relative-bias k-NN attention against dense attention, N = 2,000 to 8,000.

Each configuration runs in a fresh subprocess; peak resident memory is read from getrusage, minus the same process's
memory after creating the inputs, so only the layer's own allocations count. CPU, float32, inference, batch 1, d = 64.
Writes results/memory.json.
"""
import json
import resource
import subprocess
import sys
from pathlib import Path

CHILD = r'''
import sys, resource, json
sys.dont_write_bytecode = True
sys.path.insert(0, {here!r})
import numpy as np, torch
torch.set_num_threads(1)
from v2lib import OmniSTv2, Variant, neighbours
N, mode, d, k = {N}, {mode!r}, 64, 8
rng = np.random.default_rng(0)
xy = rng.uniform(0, np.sqrt(N), size=(N, 2))
h = torch.randn(1, N, d)
if mode == "knn":
    idx, feat = neighbours(xy, np.arange(N), np.arange(N), 1.0, k=k)
    idx, feat = torch.as_tensor(idx)[None], torch.as_tensor(feat)[None]
    model = OmniSTv2(Variant("v2", spatial=True), horizon=12)
def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r if sys.platform == "darwin" else r * 1024
base = rss()
with torch.no_grad():
    if mode == "knn":
        out = model.spatial_context(h, idx, feat)
    else:
        q = k_ = v = h.view(1, N, 2, 32).transpose(1, 2)
        att = torch.softmax(q @ k_.transpose(-1, -2) / 32 ** 0.5, dim=-1)
        out = att @ v
print(json.dumps({{"N": N, "mode": mode, "layer_peak_mb": (rss() - base) / 2**20}}))
'''


def main():
    here = str(Path(__file__).resolve().parent)
    rows = []
    for N in (2000, 4000, 8000):
        for mode in ("knn", "dense"):
            r = subprocess.run([sys.executable, "-c", CHILD.format(here=here, N=N, mode=mode)], capture_output=True, text=True)
            if r.returncode != 0:
                rows.append({"N": N, "mode": mode, "error": r.stderr.strip().splitlines()[-1]})
            else:
                rows.append(json.loads(r.stdout.strip().splitlines()[-1]))
            print(rows[-1], flush=True)
    out = Path(here) / "results" / "memory.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
