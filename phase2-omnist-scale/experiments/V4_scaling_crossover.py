"""V4 - does the scalable stack actually scale? (H4, the MambaOut-analog kill-gate)

Measures, honestly and separately:
  A. SPATIAL: exact O(N^2) vs fast O(N.k) attention, vs node count N
       - peak memory (peak RSS delta in a fresh subprocess, CPU; one config per process)
       - steady-state forward time on MPS (fast = cached k-NN) and the one-off k-NN build time
  B. TEMPORAL: BiGRU vs BiSSM (sequential loop) vs BiSSM (chunked scan), vs sequence length T
       - forward+backward time on MPS (training cost), N=100 nodes, d=64

Verdicts it can produce:
  * fast attention: memory growth exponent (log-log slope) ~1 vs ~2 for exact -> scales
  * SSM: GO only if chunked-SSM fwd+bwd beats the GRU at some T (crossover reported). If the GRU is
    faster everywhere, the SSM does NOT earn its keep on this hardware at these sizes: say so.

Accuracy parity at T=60 is established in V1; this experiment is about cost only.
Run: python experiments/V4_scaling_crossover.py  [quick]
"""
import sys, os, json, time, subprocess, resource
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve()


def worker_attn(kind, N, train=False, steps=8):
    """Fresh-process peak-RSS delta for attention on CPU. train=True runs `steps` per-timestep
    forwards WITH autograd + backward (how OmniST applies the GAT per timestep), i.e. real training
    activation memory."""
    import torch
    from omnist_scale.omnist.inductive_gat import InductiveGAT
    from omnist_scale.fast_attention import FastInductiveGAT
    torch.manual_seed(0)
    d = 64
    m = (InductiveGAT(d, 4, 8) if kind == "exact" else FastInductiveGAT(d, 4, 8)).eval()
    coords = torch.rand(1, N, 2) * torch.tensor([0.4, 0.6]) + torch.tensor([28.4, 76.8])
    tokens = torch.randn(1, N, d)
    base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if train:
        m.train()
        toks = [torch.randn(1, N, d, requires_grad=True) for _ in range(steps)]
        sum(m(t, coords).sum() for t in toks).backward()
    else:
        with torch.no_grad():
            m(tokens, coords)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({"delta_mb": (peak - base) / (1024 * 1024)}))  # macOS ru_maxrss is bytes


def attn_memory(kind, N, train=False):
    r = subprocess.run([sys.executable, str(HERE), "--worker", kind, str(N), "train" if train else "infer"],
                       capture_output=True, text=True, timeout=1500)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])["delta_mb"]
    except Exception:
        return None


def slope(xs, ys):
    pts = [(np.log(x), np.log(max(y, 1e-3))) for x, y in zip(xs, ys) if y is not None]
    if len(pts) < 3:
        return None
    a = np.array(pts)
    return float(np.polyfit(a[:, 0], a[:, 1], 1)[0])


def run(quick=False):
    import torch
    from omnist_scale.omnist.inductive_gat import InductiveGAT
    from omnist_scale.fast_attention import FastInductiveGAT, knn_indices_ckdtree
    from omnist_scale.omnist.temporal import BidirectionalGRU
    from omnist_scale.ssm_temporal import BidirectionalSSM
    DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    t0 = time.time()

    def sync():
        if DEV.type == "mps":
            torch.mps.synchronize()

    # ---------------- A. spatial ----------------
    Ns = [100, 500, 1000, 2000] if quick else [100, 500, 1000, 2000, 4000, 8000]
    spatial = []
    for N in Ns:
        d = 64
        coords = (torch.rand(1, N, 2) * torch.tensor([0.4, 0.6]) + torch.tensor([28.4, 76.8])).to(DEV)
        tokens = torch.randn(1, N, d, device=DEV)
        row = {"N": N}
        for kind in ("exact", "fast"):
            m = (InductiveGAT(d, 4, 8) if kind == "exact" else FastInductiveGAT(d, 4, 8)).to(DEV).eval()
            try:
                with torch.no_grad():
                    m(tokens, coords); sync()                       # warmup (also builds fast cache)
                    ts = []
                    for _ in range(5):
                        a = time.time(); m(tokens, coords); sync(); ts.append(time.time() - a)
                row[f"{kind}_ms"] = round(1000 * float(np.median(ts)), 2)
            except Exception as e:                                   # e.g. OOM at large N
                row[f"{kind}_ms"] = None; row[f"{kind}_error"] = str(e)[:80]
            row[f"{kind}_mem_mb"] = attn_memory(kind, N)
        a = time.time(); knn_indices_ckdtree(coords, 8); row["knn_build_ms"] = round(1000 * (time.time() - a), 1)
        spatial.append(row)
        print("  N=%5d exact: %s ms / %s MB | fast: %s ms / %s MB | knn build %s ms"
              % (N, row["exact_ms"], row["exact_mem_mb"] and round(row["exact_mem_mb"]),
                 row["fast_ms"], row["fast_mem_mb"] and round(row["fast_mem_mb"]), row["knn_build_ms"]), flush=True)
    # training activation memory (8 per-timestep GAT applications + backward), smaller N ladder
    train_Ns = [500, 1000, 2000] if quick else [500, 1000, 2000, 4000]
    train_mem = []
    for N in train_Ns:
        r = {"N": N, "exact_train_mb": attn_memory("exact", N, True), "fast_train_mb": attn_memory("fast", N, True)}
        train_mem.append(r)
        print("  TRAIN-MEM N=%5d exact=%s MB fast=%s MB" % (N, r["exact_train_mb"] and round(r["exact_train_mb"]),
              r["fast_train_mb"] and round(r["fast_train_mb"])), flush=True)
    t_exact = slope([r["N"] for r in train_mem], [r["exact_train_mb"] for r in train_mem])
    t_fast = slope([r["N"] for r in train_mem], [r["fast_train_mb"] for r in train_mem])
    s_exact = slope([r["N"] for r in spatial], [r["exact_mem_mb"] for r in spatial])
    s_fast = slope([r["N"] for r in spatial], [r["fast_mem_mb"] for r in spatial])
    mem_ratio = None
    big = [r for r in spatial if r["exact_mem_mb"] and r["fast_mem_mb"]]
    if big:
        mem_ratio = round(big[-1]["exact_mem_mb"] / max(big[-1]["fast_mem_mb"], 1e-3), 1)

    # ---------------- B. temporal ----------------
    Ts = [30, 60, 120, 240] if quick else [30, 60, 120, 240, 480, 960]
    Nn, d = 100, 64
    temporal = []
    for T in Ts:
        row = {"T": T}
        for name, mk in (("gru", lambda: BidirectionalGRU(d, 2, 0.0)),
                         ("ssm_sequential", lambda: BidirectionalSSM(d, 16, 2, 0.0, mode="sequential")),
                         ("ssm_chunked", lambda: BidirectionalSSM(d, 16, 2, 0.0, mode="chunked"))):
            m = mk().to(DEV).train()
            x = torch.randn(1, T, Nn, d, device=DEV, requires_grad=True)
            try:
                for _ in range(2):
                    m(x).sum().backward(); sync()
                ts = []
                for _ in range(4):
                    a = time.time(); m(x).sum().backward(); sync(); ts.append(time.time() - a)
                row[f"{name}_fwdbwd_ms"] = round(1000 * float(np.median(ts)), 1)
            except Exception as e:
                row[f"{name}_fwdbwd_ms"] = None; row[f"{name}_error"] = str(e)[:80]
        temporal.append(row)
        print("  T=%4d fwd+bwd  gru=%s  ssm_seq=%s  ssm_chunked=%s ms"
              % (T, row["gru_fwdbwd_ms"], row["ssm_sequential_fwdbwd_ms"], row["ssm_chunked_fwdbwd_ms"]), flush=True)

    wins = [r["T"] for r in temporal if r["ssm_chunked_fwdbwd_ms"] and r["gru_fwdbwd_ms"]
            and r["ssm_chunked_fwdbwd_ms"] < r["gru_fwdbwd_ms"]]
    last = temporal[-1]
    ratio_last = (round(last["ssm_chunked_fwdbwd_ms"] / last["gru_fwdbwd_ms"], 2)
                  if last["ssm_chunked_fwdbwd_ms"] and last["gru_fwdbwd_ms"] else None)

    # judged on TRAINING memory (where N^2 activations bite) at the largest N
    tr = [r for r in train_mem if r["exact_train_mb"] and r["fast_train_mb"]]
    train_ratio = round(tr[-1]["exact_train_mb"] / tr[-1]["fast_train_mb"], 1) if tr else None
    spatial_ok = bool(train_ratio and train_ratio >= 2.0 and t_exact is not None and t_fast is not None
                      and t_exact > t_fast + 0.4)
    ssm_earns = len(wins) > 0
    out = {
        "experiment": "V4 scaling/crossover: spatial (exact vs fast) and temporal (GRU vs SSM) cost",
        "device": str(DEV), "spatial": spatial, "temporal": temporal,
        "spatial_memory_loglog_slope": {"exact": s_exact, "fast": s_fast},
        "spatial_memory_ratio_exact_over_fast_at_max_N": mem_ratio,
        "training_memory": train_mem, "training_memory_loglog_slope": {"exact": t_exact, "fast": t_fast},
        "training_memory_ratio_exact_over_fast_at_max_N": train_ratio,
        "ssm_chunked_beats_gru_at_T": wins, "ssm_over_gru_time_ratio_at_max_T": ratio_last,
        "verdicts": {
            "fast_attention_scales": bool(spatial_ok),
            "ssm_earns_its_keep_on_speed": bool(ssm_earns),
        },
        "runtime_seconds": round(time.time() - t0, 1),
    }
    rd = HERE.parents[1] / "results"; rd.mkdir(exist_ok=True)
    (rd / "V4_scaling_crossover_results.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({"inference_mem_slopes": out["spatial_memory_loglog_slope"],
                      "train_mem_slopes": out["training_memory_loglog_slope"],
                      "train_mem_ratio_at_max_N": train_ratio,
                      "mem_ratio_at_max_N": mem_ratio, "ssm_chunked_beats_gru_at_T": wins,
                      "ssm_over_gru_ratio_max_T": ratio_last, "verdicts": out["verdicts"]}, indent=2, default=float))
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker_attn(sys.argv[2], int(sys.argv[3]), train=(len(sys.argv) > 4 and sys.argv[4] == "train"))
    else:
        run(quick=(len(sys.argv) > 1 and sys.argv[1] == "quick"))
