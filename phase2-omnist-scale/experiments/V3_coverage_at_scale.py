"""V3 - does calibrated coverage at unseen stations survive scale? (supports WP3)

Protocol. Nodes are split at random into TRAIN 55% / CALIBRATION 20% / TEST 25%. The model trains only
on TRAIN nodes, on random spatial PATCHES (<= `patch` nearest train nodes; topology invariance allows
training on subgraphs), and infers on the FULL graph. Two calibration protocols are reported:

  same_window  (oracle timing, NOT deployable): at each window the quantile comes from the calibration
               nodes' residuals AT THAT SAME WINDOW. It needs the cal nodes' targets for the very
               window being forecast, which are unknown at forecast time. Kept because it isolates
               node-exchangeability from temporal effects, and to be comparable with the first run.
  deployable   (chronological): the quantile comes from calibration-node residuals pooled over the
               EARLIER half of the evaluation windows and is applied to test nodes in the LATER half.
               This is what could actually be run in operation. It is the headline.

Baselines (conformalised in the same way): persistence and seasonal-naive (same time one period ago).
Valid coverage is trivial with wide intervals, so width against these baselines is reported.

Parts: real = PeMS-BAY (325 sensors, REAL coordinates; gru+fast and gru+exact);
       synthetic = smooth field with regional AR factors at constant node density, N up to 4000.
SYNTHETIC results say whether the pipeline and exchangeability hold as N grows; they are not evidence
about real thousand-sensor networks.

Run: python experiments/V3_coverage_at_scale.py [real|synthetic|all] [quick]
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from scipy import stats as ss
from scipy.spatial import cKDTree

from omnist_scale.omnist.omnist_model import ModelConfig
from omnist_scale.scalable_model import OmniSTScale
from omnist_scale.conformal import window_conformal, beta_band, group_ids, split_qhat

ALPHA = 0.10
DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
ROOT = Path(__file__).resolve().parents[1]
PEMS = ROOT.parent / "phase1-omnist" / "data" / "real_pems"


def mean_ci(xs):
    v = np.asarray([x for x in xs if x is not None and x == x], float); n = len(v)
    if n < 2:
        return {"mean": round(float(v[0]), 4) if n else None, "ci95": [None, None], "n": n}
    m = float(v.mean()); h = float(ss.t.ppf(0.975, n - 1)) * float(v.std(ddof=1)) / np.sqrt(n)
    return {"mean": round(m, 4), "ci95": [round(m - h, 4), round(m + h, 4)], "n": n}


def synth_field(N, T, seed):
    """Smooth spatiotemporal field at constant density; coords in the Delhi frame (the coordinate
    normaliser is Delhi-specific). Returns y (T,N), coords (N,2), timestamps (T,4), period."""
    rng = np.random.default_rng(1000 + seed)
    side = 0.12 * np.sqrt(N / 100.0)
    xy = rng.uniform(-side / 2, side / 2, size=(N, 2))
    coords = np.stack([28.6 + xy[:, 0], 77.1 + xy[:, 1]], 1).astype(np.float32)

    def rff(ell, M=64):
        w = rng.normal(0, 1, size=(M, 2)); b = rng.uniform(0, 2 * np.pi, M)
        return np.sqrt(2.0 / M) * np.cos(2 * np.pi * (xy / ell) @ w.T + b) @ rng.normal(0, 1, M)

    t = np.arange(T)
    a = 1 + 0.5 * rff(0.10); phi = 0.5 * rff(0.10); bw = 0.5 * rff(0.10); c = rff(0.06)
    y = (a[None] * np.sin(2 * np.pi * t[:, None] / 24 + phi[None])
         + bw[None] * np.sin(2 * np.pi * t[:, None] / 168) + c[None])
    for _ in range(6):                                   # regional AR factors -> neighbours informative
        load = rff(0.08); f = np.zeros(T); e = rng.normal(0, 1, T)
        for i in range(1, T):
            f[i] = 0.97 * f[i - 1] + 0.25 * e[i]
        y += 0.8 * load[None] * f[:, None]
    n = np.zeros((T, N)); e = rng.normal(0, 0.25, (T, N))  # per-node AR(1) noise
    for i in range(1, T):
        n[i] = 0.7 * n[i - 1] + e[i]
    y = (y + n).astype(np.float32)
    ts = np.stack([(t % 24) / 24, ((t // 24) % 7) / 7, ((t // 24) % 365) / 365, t / T], 1).astype(np.float32)
    return y, coords, ts, 24


def load_pemsbay(subsample=6):
    """PeMS-BAY speeds (30-min cadence) with the REAL sensor coordinates (pems_bay_coords.csv), whose
    order was verified against the released adjacency (Spearman -1.000 between adjacency weight and
    haversine distance; shuffled-order control -0.010). Coordinates are re-centred into the Delhi frame
    because the coordinate embedding uses Delhi constants."""
    vel = pd.read_csv(PEMS / "pemsbay_vel.csv", header=None).values.astype(np.float32)[::subsample]
    vel[vel <= 0] = np.nan
    y = pd.DataFrame(vel).ffill().bfill().fillna(float(np.nanmedian(vel))).values.astype(np.float32)
    cc = pd.read_csv(PEMS / "pems_bay_coords.csv", header=None).values[:, 1:3].astype(np.float32)
    coords = cc - cc.mean(0) + np.array([28.6, 77.1], np.float32)
    T = len(y); step = np.arange(T)
    per_day = int(24 * 60 / (5 * subsample))
    ts = np.stack([(step % per_day) / per_day, ((step // per_day) % 7) / 7,
                   ((step // per_day) % 365) / 365, step / T], 1).astype(np.float32)
    return y, coords, ts, per_day


def deployable_conformal(Rcal, Rte, alpha, gc, gt, n_groups=3, min_group=10):
    """Quantile from cal-node residuals pooled over the EARLIER half of windows, applied to test nodes
    in the LATER half. Rcal: (nW, n_cal), Rte: (nW, n_te)."""
    h = Rcal.shape[0] // 2
    pool = Rcal[:h].reshape(-1); grp_pool = np.tile(gc, h)
    q = split_qhat(pool, alpha)
    covered = (Rte[h:] <= q)
    out = {"cov": float(covered.mean()), "width": 2 * q, "windows": int(Rte.shape[0] - h)}
    gg, gm = [], []
    for g in range(n_groups):
        mt = gt == g
        if mt.sum() == 0:
            continue
        gg.append(float(covered[:, mt].mean()))
        mp = grp_pool == g
        qg = split_qhat(pool[mp], alpha) if mp.sum() >= min_group else q
        gm.append(float((Rte[h:][:, mt] <= qg).mean()))
    out["worst_group_global"] = min(gg) if gg else None
    out["worst_group_mondrian"] = min(gm) if gm else None
    return out


def run_one(y, coords, ts, period, seed, variant, W, H, steps, patch, n_eval_windows, train_frac=0.55):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    T, N = y.shape
    perm = rng.permutation(N)
    n_tr, n_cal = int(N * train_frac), int(N * 0.20)
    tr, cal, te = np.sort(perm[:n_tr]), np.sort(perm[n_tr:n_tr + n_cal]), np.sort(perm[n_tr + n_cal:])
    t_train_end = int(T * 0.55); t_eval_start = int(T * 0.70)
    mu, sd = float(y[:t_train_end].mean()), float(y[:t_train_end].std() + 1e-6)
    yn = (y - mu) / sd

    cfg = ModelConfig(n_features=1, horizon=H, d_model=64, k_neighbors=8, n_gat_layers=1, n_temporal_layers=2)
    model = OmniSTScale(cfg, temporal=variant[0], attention=variant[1]).to(DEV)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)

    xy = np.stack([np.radians(coords[:, 1]) * np.cos(np.radians(coords[:, 0].mean())), np.radians(coords[:, 0])], 1)
    tree_tr = cKDTree(xy[tr])
    pn = min(patch, len(tr))
    t0 = time.time(); bs = 8
    for step in range(steps):
        model.train()
        fb, cb, tb, yb = [], [], [], []
        s = rng.integers(0, t_train_end - W - H)
        for _ in range(bs):
            c = rng.integers(len(tr)); _, nb = tree_tr.query(xy[tr][c], k=pn)
            idx = tr[np.atleast_1d(nb)]
            fb.append(yn[s:s + W][:, idx][:, :, None]); yb.append(yn[s + W:s + W + H][:, idx].T[:, :, None])
            cb.append(coords[idx]); tb.append(ts[s:s + W])
        f = torch.tensor(np.stack(fb), device=DEV); c_ = torch.tensor(np.stack(cb), device=DEV)
        t_ = torch.tensor(np.stack(tb), device=DEV); y_ = torch.tensor(np.stack(yb), device=DEV)
        opt.zero_grad(); torch.nn.functional.l1_loss(model(f, c_, t_), y_).backward(); opt.step()
    train_s = time.time() - t0

    model.eval()
    c_all = torch.tensor(coords, device=DEV).unsqueeze(0)
    span = T - W - H - 1 - t_eval_start
    starts = np.arange(t_eval_start, T - W - H - 1, max(1, span // n_eval_windows))[:n_eval_windows]
    R = {"model": [], "persist": [], "seasonal": []}
    t0 = time.time()
    with torch.no_grad():
        for s in starts:
            x = torch.tensor(yn[s:s + W][None, :, :, None], device=DEV)
            p = model(x, c_all, torch.tensor(ts[s:s + W][None], device=DEV)).cpu().numpy()[0, :, :, 0]
            tgt = yn[s + W:s + W + H].T
            R["model"].append(np.abs(p - tgt).mean(1) * sd)
            R["persist"].append(np.abs(yn[s + W - 1][:, None] - tgt).mean(1) * sd)
            lag = s + W - period
            sn = yn[lag:lag + H].T if lag >= 0 and period >= H else np.repeat(yn[s + W - 1][:, None], H, 1)
            R["seasonal"].append(np.abs(sn - tgt).mean(1) * sd)
    infer_s = (time.time() - t0) / len(starts)

    d_tr = tree_tr.query(xy)[0]
    edges = np.quantile(d_tr[cal], [1 / 3, 2 / 3]); gc, gt = group_ids(d_tr[cal], edges), group_ids(d_tr[te], edges)
    res = {}
    for name, M in R.items():
        M = np.array(M)
        sw = [window_conformal(r[cal], r[te], ALPHA, gc, gt) for r in M]
        dep = deployable_conformal(M[:, cal], M[:, te], ALPHA, gc, gt)
        res[name] = {
            "same_window": {"coverage": float(np.mean([w["cov"] for w in sw])),
                            "width": float(np.mean([w["width"] for w in sw])),
                            "worst_group_global": float(np.mean([min(w["group_global"].values()) for w in sw if w["group_global"]])),
                            "worst_group_mondrian": float(np.mean([min(w["group_mondrian"].values()) for w in sw if w["group_mondrian"]]))},
            "deployable": {"coverage": dep["cov"], "width": dep["width"],
                           "worst_group_global": dep["worst_group_global"], "worst_group_mondrian": dep["worst_group_mondrian"]},
            "mae_test": float(M[:, te].mean()),
        }
    res["meta"] = {"N": N, "n_train": len(tr), "n_cal": len(cal), "n_test": len(te),
                   "band": beta_band(len(cal), ALPHA), "train_s": round(train_s, 1),
                   "infer_s_per_window": round(infer_s, 3), "windows": len(starts), "steps": steps}
    return res


def aggregate(runs):
    out = {"meta": runs[0]["meta"]}
    for k in ("model", "persist", "seasonal"):
        out[k] = {"mae_test": mean_ci([r[k]["mae_test"] for r in runs])}
        for proto in ("same_window", "deployable"):
            out[k][proto] = {m: mean_ci([r[k][proto][m] for r in runs]) for m in runs[0][k][proto]}
    out["train_s"] = mean_ci([r["meta"]["train_s"] for r in runs])
    out["infer_s_per_window"] = mean_ci([r["meta"]["infer_s_per_window"] for r in runs])
    return out


def line(tag, r):
    m = r["model"]
    return ("  [%s] cov same-window=%.3f deployable=%.3f (band %s) | width dep: model=%.2f persist=%.2f seasonal=%.2f | "
            "worst-grp dep global/mondrian=%.3f/%.3f" % (
                tag, m["same_window"]["coverage"], m["deployable"]["coverage"], [round(b, 3) for b in r["meta"]["band"]],
                m["deployable"]["width"], r["persist"]["deployable"]["width"], r["seasonal"]["deployable"]["width"],
                m["deployable"]["worst_group_global"], m["deployable"]["worst_group_mondrian"]))


def part_real(quick, steps_override=None):
    y, coords, ts, per_day = load_pemsbay()
    seeds = 1 if quick else 3
    steps = steps_override or (60 if quick else 1200)
    out = {}
    for name, var in (("gru+fast", ("gru", "fast")), ("gru+exact", ("gru", "exact"))):
        runs = []
        for s in range(seeds):
            r = run_one(y, coords, ts, per_day, s, var, W=48, H=6, steps=steps, patch=128,
                        n_eval_windows=20 if quick else 60)
            runs.append(r); print(line("PeMS-BAY N=325 %s seed %d" % (name, s), r), flush=True)
        out[name] = aggregate(runs)
    return out


def part_synth(quick):
    Ns = [100, 500] if quick else [100, 500, 1000, 2000, 4000]
    seeds = 1 if quick else 3
    out = {}
    for N in Ns:
        runs = []
        for s in range(seeds):
            y, coords, ts, P = synth_field(N, 1800 if quick else 2400, s)
            r = run_one(y, coords, ts, P, s, ("gru", "fast"), W=24, H=6, steps=60 if quick else 300,
                        patch=200, n_eval_windows=20 if quick else 60)
            runs.append(r); print(line("synthetic N=%d seed %d" % (N, s), r), flush=True)
        out[str(N)] = aggregate(runs)
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("real", "synthetic", "all") else "all"
    quick = "quick" in sys.argv
    t0 = time.time(); res = {"device": str(DEV), "alpha": ALPHA, "quick": quick}
    if which in ("real", "all"):
        res["real_pemsbay"] = part_real(quick)
    if which in ("synthetic", "all"):
        res["synthetic_ladder"] = part_synth(quick)
    res["runtime_seconds"] = round(time.time() - t0, 1)
    (ROOT / "results").mkdir(exist_ok=True)
    fn = "V3_coverage_at_scale_%s%s.json" % (which, "_quick" if quick else "")
    (ROOT / "results" / fn).write_text(json.dumps(res, indent=2, default=float))
    print("wrote", fn, "runtime", res["runtime_seconds"], "s")
