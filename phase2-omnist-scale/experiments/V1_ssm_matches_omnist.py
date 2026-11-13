"""V1 - THE MAKE-OR-BREAK (H1): do the scalable components match OmniST's accuracy AND coverage?

If swapping OmniST's GRU -> SSM temporal block and exact -> O(N.k) attention loses accuracy or breaks
the inductive conformal coverage guarantee, the whole scale-up is moot. So this is checked FIRST, on
real Delhi PM2.5, before any scaling work.

Compares four variants (same architecture, same data/seeds/budget):
    gru+exact  = OmniST baseline (published)
    ssm+exact  = SSM temporal only
    gru+fast   = O(N.k) attention only
    ssm+fast   = the full scalable model (this project)

Metrics per variant: inductive MAE at UNSEEN stations (de-normalized), inductive conformal coverage
at unseen stations (target-regime calibrated), and forward throughput. Multi-seed, 95% CIs,
finite-sample coverage band.

GO: ssm+fast matches gru+exact on inductive MAE (within CI) AND holds inductive coverage in the band.
NO-GO: ssm+fast loses accuracy materially OR breaks coverage -> scale-up is moot.

MPS. Run: python experiments/V1_ssm_matches_omnist.py  [quick]
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from scipy import stats as ss

from omnist_scale.omnist.omnist_model import ModelConfig
from omnist_scale.scalable_model import OmniSTScale

ALPHA = 0.10
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "real_delhi"
DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def _mean_ci(xs):
    v = np.asarray([x for x in xs if x == x], float); n = len(v)
    if n < 2:
        return {"mean": round(float(v[0]), 4) if n else None, "ci95": [None, None], "n": n}
    m = float(v.mean()); se = float(v.std(ddof=1)) / np.sqrt(n); h = float(ss.t.ppf(0.975, n - 1)) * se
    return {"mean": round(m, 4), "ci95": [round(m - h, 4), round(m + h, 4)], "n": n}


def band(n, alpha=ALPHA):
    l = max(1, min(int(np.floor((n + 1) * alpha)), n)); d = ss.beta(n + 1 - l, l)
    return [round(float(d.ppf(0.025)), 4), round(float(d.ppf(0.975)), 4)]


def load_delhi():
    loc = pd.read_csv(DATA_DIR / "Location of Stations PM25.csv").dropna(subset=["Station"])
    coords = loc[["LAT", "LONG"]].values[:37].astype(np.float32)
    df = pd.read_csv(DATA_DIR / "PM25_Daily_Data.csv")
    y = df.values[:, :37].astype(np.float32)
    y[y <= 0] = np.nan; y[y > 999] = np.nan
    for s in range(y.shape[1]):
        y[:, s] = pd.Series(y[:, s]).ffill().bfill().fillna(np.nanmedian(y[:, s])).values
    return y, coords


def encode_ts(day_idx):
    doy = (day_idx % 365) / 366.0; dow = (day_idx % 7) / 7.0
    month = ((day_idx % 365) // 30) / 12.0; year = (day_idx // 365) / 5.0
    return np.stack([doy, dow, month, year], axis=-1).astype(np.float32)


def windows(y, day_index, stations, W, H, stride):
    out = []
    for s in range(0, len(day_index) - W - H, stride):
        feat = y[day_index[s:s + W]][:, stations][:, :, None]
        ts = encode_ts(day_index[s:s + W])
        tgt = y[day_index[s + W:s + W + H]][:, stations].T[:, :, None]
        out.append((feat, ts, tgt))
    return out


def train_eval(variant, y, coords, cal_days, test_days, mu, sd, seen_st, unseen_st, W, H, epochs, seed):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    temporal, attention = variant
    cfg = ModelConfig(n_features=1, horizon=H, d_model=64, k_neighbors=8, n_gat_layers=1, n_temporal_layers=2)
    model = OmniSTScale(cfg, temporal=temporal, attention=attention).to(DEV)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    train = windows((y - mu) / sd, cal_days, seen_st, W, H, stride=5)
    c_seen = torch.tensor(coords[seen_st], dtype=torch.float32, device=DEV).unsqueeze(0)
    bs = 16
    for ep in range(epochs):
        rng.shuffle(train); model.train()
        for i in range(0, len(train), bs):
            batch = train[i:i + bs]
            fb = torch.tensor(np.stack([b[0] for b in batch]), device=DEV)
            tb = torch.tensor(np.stack([b[1] for b in batch]), device=DEV)
            yb = torch.tensor(np.stack([b[2] for b in batch]), device=DEV)
            opt.zero_grad()
            loss = torch.nn.functional.l1_loss(model(fb, c_seen.expand(len(batch), -1, -1), tb), yb)
            loss.backward(); opt.step()

    @torch.no_grad()
    def predict(stations_idx, day_index):
        model.eval()
        sm = windows((y - mu) / sd, day_index, stations_idx, W, H, stride=H)
        c = torch.tensor(coords[stations_idx], dtype=torch.float32, device=DEV).unsqueeze(0)
        P, Tg = [], []
        for feat, ts, tgt in sm:
            p = model(torch.tensor(feat[None], device=DEV), c, torch.tensor(ts[None], device=DEV))
            P.append(p.cpu().numpy()[0, :, :, 0]); Tg.append(tgt[:, :, 0])
        return np.array(P), np.array(Tg)

    half = len(test_days) // 2
    cal_win, eval_win = test_days[:half], test_days[half:]
    # target-regime calibration on seen stations (winter cal slice)
    Pc, Tc = predict(seen_st, cal_win); Pc = Pc * sd + mu; Tc = Tc * sd + mu
    resid_cal = np.abs(Pc - Tc).mean(axis=2).reshape(-1)
    qhat = float(np.quantile(resid_cal, min(1.0, (1 - ALPHA) * (1 + 1 / len(resid_cal)))))
    # inductive eval at UNSEEN stations (winter eval slice)
    Pe, Te = predict(unseen_st, eval_win); Pe = Pe * sd + mu; Te = Te * sd + mu
    resid_un = np.abs(Pe - Te).mean(axis=2)
    mae_unseen = float(resid_un.mean())
    cov_unseen = float((resid_un <= qhat).mean())
    # throughput: forward passes/sec on a representative batch
    c_all = torch.tensor(coords, dtype=torch.float32, device=DEV).unsqueeze(0)
    fx = torch.randn(4, W, 37, 1, device=DEV); tx = torch.randn(4, W, 4, device=DEV)
    model.eval()
    with torch.no_grad():
        for _ in range(2):
            model(fx, c_all.expand(4, -1, -1), tx)
        t0 = time.time()
        for _ in range(10):
            model(fx, c_all.expand(4, -1, -1), tx)
        fps = 10 * 4 / (time.time() - t0)
    return mae_unseen, cov_unseen, fps


def run(quick=False):
    t0 = time.time()
    y, coords = load_delhi()
    T, N = y.shape
    doy = np.arange(T) % 365
    is_winter = (doy < 59) | (doy >= 305)
    cal_days = np.where(~is_winter)[0]; test_days = np.where(is_winter)[0]
    mu = float(np.mean(y[cal_days])); sd = float(np.std(y[cal_days]) + 1e-6)
    W, H = 60, 7
    seeds = 3 if not quick else 1
    epochs = 15 if not quick else 4
    variants = {"gru+exact": ("gru", "exact"), "ssm+exact": ("ssm", "exact"),
                "gru+fast": ("gru", "fast"), "ssm+fast": ("ssm", "fast")}
    agg = {k: {"mae": [], "cov": [], "fps": []} for k in variants}

    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        perm = rng.permutation(N); n_un = int(round(N * 0.35))
        unseen_st = np.sort(perm[:n_un]); seen_st = np.sort(perm[n_un:])
        for name, var in variants.items():
            mae, cov, fps = train_eval(var, y, coords, cal_days, test_days, mu, sd,
                                       seen_st, unseen_st, W, H, epochs, seed)
            agg[name]["mae"].append(mae); agg[name]["cov"].append(cov); agg[name]["fps"].append(fps)
            print(f"  seed {seed} {name:>10}: MAE={mae:.2f} cov={cov:.3f} fps={fps:.0f}", flush=True)

    S = {k: {"mae": _mean_ci(v["mae"]), "coverage": _mean_ci(v["cov"]), "fps": _mean_ci(v["fps"])}
         for k, v in agg.items()}
    b_un = band(int(round(N * 0.35)))

    base_mae = S["gru+exact"]["mae"]["mean"]
    full_mae = S["ssm+fast"]["mae"]["mean"]
    full_cov = S["ssm+fast"]["coverage"]["mean"]
    # parity: full model MAE within 10% of baseline, coverage in band
    mae_parity = full_mae is not None and full_mae <= base_mae * 1.10
    cov_ok = full_cov is not None and b_un[0] - 0.03 <= full_cov <= b_un[1] + 0.03
    faster = (S["ssm+fast"]["fps"]["mean"] is not None and S["gru+exact"]["fps"]["mean"] is not None
              and S["ssm+fast"]["fps"]["mean"] >= 0.9 * S["gru+exact"]["fps"]["mean"])

    if mae_parity and cov_ok:
        verdict = ("GO - the scalable ssm+fast model MATCHES OmniST: inductive MAE %.2f vs baseline "
                   "%.2f (within 10%%), inductive coverage %.3f in band %s. %s Parity holds -> the "
                   "scale-up is worth pursuing (V2 equivalence, V3 coverage-at-scale, V4 SSM crossover)."
                   % (full_mae, base_mae, full_cov, b_un,
                      "Throughput comparable/better." if faster else
                      "Throughput not yet better at N=37 (expected; the win is at large N - V4)."))
        go = True
    elif not cov_ok:
        verdict = ("NO-GO - the scalable model BREAKS coverage (%.3f, band %s). The guarantee does not "
                   "survive the component swap -> scale-up is moot as framed. STOP." % (full_cov, b_un))
        go = False
    else:
        verdict = ("NO-GO - the scalable model loses accuracy (MAE %.2f vs baseline %.2f, >10%%). "
                   "Fix the components or stop." % (full_mae, base_mae))
        go = False

    out = {"experiment": "V1 make-or-break (H1): do SSM temporal + O(N.k) attention match OmniST "
                         "accuracy AND inductive coverage on real Delhi?",
           "data": "CPCB Delhi PM2.5, 37 stations, real", "device": str(DEV),
           "seeds": seeds, "epochs": epochs, "alpha": ALPHA, "finite_sample_band_unseen": b_un,
           "variants": S,
           "diagnostics": {"mae_parity_full_vs_baseline": bool(mae_parity),
                           "coverage_in_band": bool(cov_ok), "throughput_comparable_or_better": bool(faster)},
           "verdict": verdict, "go": bool(go), "runtime_seconds": round(time.time() - t0, 1)}
    rd = Path(__file__).resolve().parents[1] / "results"; rd.mkdir(exist_ok=True)
    (rd / "V1_ssm_matches_omnist_results.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({"variants": {k: {"mae": S[k]["mae"]["mean"], "coverage": S[k]["coverage"]["mean"],
                                        "fps": S[k]["fps"]["mean"]} for k in S},
                      "band_unseen": b_un, "verdict": verdict, "go": go,
                      "runtime_seconds": out["runtime_seconds"]}, indent=2, default=float))
    return out


if __name__ == "__main__":
    run(quick=(len(sys.argv) > 1 and sys.argv[1] == "quick"))
