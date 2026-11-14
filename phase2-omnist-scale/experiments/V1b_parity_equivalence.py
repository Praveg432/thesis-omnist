"""V1b - parity gate, redesigned after review. Supersedes V1 (kept unchanged as the preliminary record).

What was wrong with V1 (see docs/VETTING-REPORT.md, erratum):
  * the coverage test widened the finite-sample band by 0.03 on both sides, giving [0.723, 1.028],
    so almost any coverage passed;
  * the accuracy test tolerated 10% error, with 3 seeds and confidence intervals that overlapped
    completely, which shows no detectable difference, not parity;
  * calibration used the TRAINING stations' residuals, which are not exchangeable with unseen-
    station residuals;
  * interval width was not reported, so trivially wide intervals passed;
  * normalisation used all stations, imputation used bfill and a full-series median, seasons were
    taken from index % 365, and windows were stitched across the winter gap.

This script (PRE-REGISTERED thresholds are the constants below; do not change them after seeing
results):
  * stations are split at random per seed into TRAIN / CALIBRATION / UNSEEN-TEST (never seen in
    training); the conformal threshold comes from the CALIBRATION stations;
  * the model trains on non-winter days and is evaluated on winter days (a deliberate seasonal
    shift, stated, not hidden); windows never cross the winter gap;
  * normalisation uses TRAIN stations on training days only; imputation is causal (ffill, then the
    station's own training-period median; no bfill);
  * calendar dates are explicit (Delhi series starts 2019-01-01); the year feature uses one fixed
    reference for training and test;
  * scores are per-day absolute errors, the same definition as Phase 1;
  * equivalence of ssm+fast to gru+exact is decided on PAIRED per-seed differences with a TOST-style
    90% confidence interval and fixed margins; the verdict is GO, NO-GO or INCONCLUSIVE.

Throughput here is measured at N = 37 on random inputs: it is NOT a scaling measurement.
Run: python experiments/V1b_parity_equivalence.py [quick]
quick mode writes results/V1b_quick.json and never touches committed result files.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import numpy as np
import pandas as pd
import torch

from omnist_scale.omnist.omnist_model import ModelConfig
from omnist_scale.scalable_model import OmniSTScale
from omnist_scale.stats import mean_ci, paired_equivalence, parity_verdict

# ---- pre-registered constants -------------------------------------------------------------------
ALPHA = 0.10
MAE_MARGIN_FRACTION = 0.05      # ssm+fast MAE must be within +/-5% of the gru+exact MAE (paired)
COVERAGE_MARGIN = 0.03          # coverage must be within +/-0.03 of the gru+exact coverage (paired)
EQUIVALENCE_LEVEL = 0.90        # two-sided 90% CI == TOST at alpha = 0.05
N_SEEDS = 10
EPOCHS = 15
TEST_FRACTION, CAL_FRACTION = 0.30, 0.15
WINDOW, HORIZON = 60, 7
START_DATE = "2019-01-01"
BASE_YEAR, YEAR_SPAN = 2019, 4.0
# -------------------------------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "real_delhi"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DEV = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
VARIANTS = {"gru+exact": ("gru", "exact"), "ssm+exact": ("ssm", "exact"),
            "gru+fast": ("gru", "fast"), "ssm+fast": ("ssm", "fast")}


def is_winter(dates: pd.DatetimeIndex) -> np.ndarray:
    return np.isin(dates.month, (12, 1, 2))


def load_delhi():
    """Returns y (T, N) with causal imputation, station coordinates, and calendar dates."""
    loc = pd.read_csv(DATA_DIR / "Location of Stations PM25.csv").dropna(subset=["Station"])
    coords = loc[["LAT", "LONG"]].values[:37].astype(np.float32)
    raw = pd.read_csv(DATA_DIR / "PM25_Daily_Data.csv").values[:, :37].astype(np.float32)
    dates = pd.date_range(START_DATE, periods=len(raw), freq="D")
    train_period = ~is_winter(dates)
    y = raw.copy()
    y[(y <= 0) | (y > 999)] = np.nan
    for s in range(y.shape[1]):
        series = pd.Series(y[:, s])
        fallback = np.nanmedian(y[train_period, s])        # the station's own training-period median
        y[:, s] = series.ffill().fillna(fallback).values   # causal: no backward fill
    return y, coords, dates


def encode_timestamps(dates: pd.DatetimeIndex) -> np.ndarray:
    return np.stack([dates.dayofyear / 366.0, dates.dayofweek / 7.0, (dates.month - 1) / 12.0,
                     (dates.year - BASE_YEAR) / YEAR_SPAN], axis=-1).astype(np.float32)


def contiguous_segments(day_index: np.ndarray) -> list:
    return np.split(day_index, np.where(np.diff(day_index) != 1)[0] + 1)


def make_windows(y, dates, day_index, stations, stride):
    """Sliding windows that stay inside contiguous runs of days (never stitched across a gap)."""
    out = []
    for seg in contiguous_segments(day_index):
        for s in range(0, len(seg) - WINDOW - HORIZON + 1, stride):
            hist, fut = seg[s:s + WINDOW], seg[s + WINDOW:s + WINDOW + HORIZON]
            out.append((y[hist][:, stations][:, :, None], encode_timestamps(dates[hist]),
                        y[fut][:, stations].T[:, :, None]))
    return out


def conformal_quantile(scores: np.ndarray) -> float:
    n = len(scores)
    return float(np.quantile(scores, min(1.0, (1 - ALPHA) * (1 + 1 / n))))


def train_and_evaluate(variant, y, dates, coords, train_days, test_days, mu, sd,
                       train_st, cal_st, test_st, epochs, seed) -> dict:
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    temporal, attention = variant
    cfg = ModelConfig(n_features=1, horizon=HORIZON, d_model=64, k_neighbors=8,
                      n_gat_layers=1, n_temporal_layers=2)
    model = OmniSTScale(cfg, temporal=temporal, attention=attention).to(DEV)
    optimiser = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    yn = (y - mu) / sd
    train = make_windows(yn, dates, train_days, train_st, stride=5)
    c_train = torch.tensor(coords[train_st], dtype=torch.float32, device=DEV).unsqueeze(0)
    for _ in range(epochs):
        rng.shuffle(train)
        model.train()
        for i in range(0, len(train), 16):
            batch = train[i:i + 16]
            fb = torch.tensor(np.stack([b[0] for b in batch]), device=DEV)
            tb = torch.tensor(np.stack([b[1] for b in batch]), device=DEV)
            yb = torch.tensor(np.stack([b[2] for b in batch]), device=DEV)
            optimiser.zero_grad()
            loss = torch.nn.functional.l1_loss(
                model(fb, c_train.expand(len(batch), -1, -1), tb), yb)
            loss.backward()
            optimiser.step()

    @torch.no_grad()
    def abs_errors(stations) -> np.ndarray:
        model.eval()
        wins = make_windows(yn, dates, test_days, stations, stride=HORIZON)
        c = torch.tensor(coords[stations], dtype=torch.float32, device=DEV).unsqueeze(0)
        errs = []
        for feat, ts, tgt in wins:
            pred = model(torch.tensor(feat[None], device=DEV), c, torch.tensor(ts[None], device=DEV))
            errs.append(np.abs(pred.cpu().numpy()[0, :, :, 0] - tgt[:, :, 0]) * sd)
        return np.array(errs)                                # (windows, stations, horizon)

    q = conformal_quantile(abs_errors(cal_st).reshape(-1))
    test_err = abs_errors(test_st)

    c_all = torch.tensor(coords, dtype=torch.float32, device=DEV).unsqueeze(0)
    fx = torch.randn(4, WINDOW, 37, 1, device=DEV)
    tx = torch.randn(4, WINDOW, 4, device=DEV)
    model.eval()
    with torch.no_grad():
        for _ in range(2):
            model(fx, c_all.expand(4, -1, -1), tx)
        t0 = time.time()
        for _ in range(10):
            model(fx, c_all.expand(4, -1, -1), tx)
        fps = 10 * 4 / (time.time() - t0)
    return {"mae": float(test_err.mean()), "coverage": float((test_err <= q).mean()),
            "width": 2.0 * q, "fps_at_N37": fps}


def run(quick: bool = False) -> dict:
    t0 = time.time()
    y, coords, dates = load_delhi()
    n_stations = y.shape[1]
    winter = is_winter(dates)
    train_days, test_days = np.where(~winter)[0], np.where(winter)[0]
    train_mask_vals = y[train_days]
    n_seeds, epochs = (1, 2) if quick else (N_SEEDS, EPOCHS)
    n_test = int(round(n_stations * TEST_FRACTION))
    n_cal = int(round(n_stations * CAL_FRACTION))

    rows = {name: [] for name in VARIANTS}
    for seed in range(n_seeds):
        perm = np.random.default_rng(seed).permutation(n_stations)
        test_st = np.sort(perm[:n_test])
        cal_st = np.sort(perm[n_test:n_test + n_cal])
        train_st = np.sort(perm[n_test + n_cal:])
        mu = float(train_mask_vals[:, train_st].mean())
        sd = float(train_mask_vals[:, train_st].std() + 1e-6)
        for name, variant in VARIANTS.items():
            r = train_and_evaluate(variant, y, dates, coords, train_days, test_days, mu, sd,
                                   train_st, cal_st, test_st, epochs, seed)
            r.update({"seed": seed, "n_train": len(train_st), "n_cal": len(cal_st),
                      "n_test": len(test_st), "test_stations": [int(i) for i in test_st]})
            rows[name].append(r)
            print(f"  seed {seed} {name:>10}: MAE={r['mae']:.2f} cov={r['coverage']:.3f} "
                  f"width={r['width']:.1f} fps={r['fps_at_N37']:.0f}", flush=True)

    summary = {name: {k: mean_ci([r[k] for r in rs]) for k in ("mae", "coverage", "width", "fps_at_N37")}
               for name, rs in rows.items()}
    base, full = rows["gru+exact"], rows["ssm+fast"]
    base_mae = float(np.mean([r["mae"] for r in base]))
    mae_test = paired_equivalence([f["mae"] - b["mae"] for f, b in zip(full, base)],
                                  MAE_MARGIN_FRACTION * base_mae, EQUIVALENCE_LEVEL)
    cov_test = paired_equivalence([f["coverage"] - b["coverage"] for f, b in zip(full, base)],
                                  COVERAGE_MARGIN, EQUIVALENCE_LEVEL)
    verdict = parity_verdict(mae_test, cov_test)

    # Attention swap alone (gru+fast against gru+exact): the gate that matters if the state-space
    # block is dropped from the thesis.
    attn = rows["gru+fast"]
    attn_mae_test = paired_equivalence([f["mae"] - b["mae"] for f, b in zip(attn, base)],
                                       MAE_MARGIN_FRACTION * base_mae, EQUIVALENCE_LEVEL)
    attn_cov_test = paired_equivalence([f["coverage"] - b["coverage"] for f, b in zip(attn, base)],
                                       COVERAGE_MARGIN, EQUIVALENCE_LEVEL)
    verdict_attention_only = parity_verdict(attn_mae_test, attn_cov_test)

    out = {
        "experiment": "V1b parity gate (supersedes V1): ssm+fast vs gru+exact, paired equivalence",
        "data": "CPCB Delhi PM2.5, 37 stations, real; dates from 2019-01-01",
        "device": str(DEV), "seeds": n_seeds, "epochs": epochs, "alpha": ALPHA,
        "protocol": {"split": f"random per seed: {n_test} unseen test, {n_cal} calibration, rest train",
                     "train_period": "non-winter days (Mar-Nov)", "test_period": "winter days (Dec-Feb)",
                     "score": "per-day absolute error", "window": WINDOW, "horizon": HORIZON},
        "pre_registered": {"mae_margin_fraction": MAE_MARGIN_FRACTION,
                           "coverage_margin": COVERAGE_MARGIN, "ci_level": EQUIVALENCE_LEVEL},
        "variants": summary, "per_seed": rows,
        "mae_equivalence": mae_test, "coverage_equivalence": cov_test, "verdict": verdict,
        "attention_only": {"mae_equivalence": attn_mae_test, "coverage_equivalence": attn_cov_test,
                           "verdict": verdict_attention_only},
        "note": "fps_at_N37 is measured at N=37 on random inputs and is not a scaling measurement.",
        "runtime_seconds": round(time.time() - t0, 1)}
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / ("V1b_quick.json" if quick else "V1b_parity_equivalence_results.json")
    path.write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({"verdict_ssm_plus_fast": verdict, "verdict_attention_only": verdict_attention_only,
                      "mae": mae_test, "coverage": cov_test}, indent=2, default=float))
    return out


if __name__ == "__main__":
    run(quick=(len(sys.argv) > 1 and sys.argv[1] == "quick"))
