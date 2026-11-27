"""OmniST v2 feasibility: data preparation, model variants, neighbour baselines, evaluation.

Reads the thesis-omnist data and pure helper functions read-only (bytecode writing disabled), writes nothing there.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # never write __pycache__ into the thesis repository

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy.spatial import cKDTree

THESIS = Path(__file__).resolve().parents[2] / "phase1-omnist"  # thesis-omnist/phase1-omnist
sys.path.insert(0, str(THESIS))
from src.data_real import load_real_delhi  # noqa: E402  (read-only)
from src.data_pemsbay import load_real_pemsbay  # noqa: E402  (read-only)
from src.data_traffic_real import load_real_traffic  # noqa: E402  (read-only)

K_NEIGHBOURS = 8


# ---------------------------------------------------------------------------------------------- data
@dataclass(frozen=True)
class Network:
    name: str
    series: np.ndarray       # (T, N) original units, imputed
    xy_km: np.ndarray        # (N, 2) local plane in km
    dates: pd.DatetimeIndex  # (T,)
    train_end: int           # training steps are [0, train_end)
    test_start: int          # test steps are [test_start, T)
    window: int
    horizon: int
    period: int              # seasonal period in steps
    n_cal: int
    n_test: int


def _impute(data: np.ndarray, upper: float) -> np.ndarray:
    data = data.astype(float).copy()
    data[(data <= 0) | (data > upper)] = np.nan
    for s in range(data.shape[1]):
        ser = pd.Series(data[:, s])
        data[:, s] = ser.ffill().bfill().fillna(ser.median()).values
    return data


def _plane(lat_lon: np.ndarray) -> np.ndarray:
    lat0 = np.radians(lat_lon[:, 0].mean())
    return np.stack([np.radians(lat_lon[:, 1]) * np.cos(lat0), np.radians(lat_lon[:, 0])], 1) * 6371.0


def load_network(name: str) -> Network:
    if name == "delhi":
        data, coords, dates, _ = load_real_delhi(features_to_use=["pm25"])
        series = _impute(data[:, :, 0], 999)
        dates = pd.DatetimeIndex(dates)
        train_mask = dates.year <= 2022
        train_end = int(train_mask.sum()) - 180          # the thesis loader keeps the last 180 days for validation
        test_start = int(np.nonzero(dates.year == 2023)[0][0])
        return Network("delhi", series, _plane(np.asarray(coords, float)), dates, train_end, test_start,
                       window=60, horizon=30, period=7, n_cal=8, n_test=8)
    if name == "pemsbay":
        data, _, dates, _ = load_real_pemsbay()
        series = _impute(data[:, :, 0], np.inf)
        coords = pd.read_csv(THESIS / "data" / "real_pems" / "pems_bay_coords.csv", header=None).values[:, 1:3]
        T = len(series)
        test_len, val_len = int(T * 0.20), int(T * 0.10)
        return Network("pemsbay", series, _plane(coords.astype(float)), pd.DatetimeIndex(dates),
                       train_end=T - test_len - val_len, test_start=T - test_len,
                       window=48, horizon=12, period=48, n_cal=45, n_test=45)
    if name == "pemsd7":
        data, coords, dates, _ = load_real_traffic()
        series = _impute(np.asarray(data)[:, :, 0], np.inf)
        T = len(series)
        test_len, val_len = int(T * 0.20), int(T * 0.10)
        # coordinates are reconstructed by the thesis loader from the road-distance matrix (no measured positions)
        return Network("pemsd7", series, _plane(np.asarray(coords, float)), pd.DatetimeIndex(dates),
                       train_end=T - test_len - val_len, test_start=T - test_len,
                       window=48, horizon=12, period=288, n_cal=30, n_test=30)
    raise ValueError(f"unknown network {name!r}")


def station_split(n_stations: int, split: int, n_cal: int, n_test: int):
    """The thesis C1 partition: permutation seeded 1000 + split; test first, then calibration."""
    perm = np.random.default_rng(1000 + split).permutation(n_stations)
    test, cal = np.sort(perm[:n_test]), np.sort(perm[n_test:n_test + n_cal])
    train = np.setdiff1d(np.arange(n_stations), np.concatenate([test, cal]))
    return train, cal, test


def time_features(dates: pd.DatetimeIndex) -> np.ndarray:
    """(T, 6): sin/cos of day of year, day of week, time of day."""
    doy = 2 * np.pi * dates.dayofyear.values / 366.0
    dow = 2 * np.pi * dates.dayofweek.values / 7.0
    tod = 2 * np.pi * (dates.hour.values * 60 + dates.minute.values) / 1440.0
    return np.stack([np.sin(doy), np.cos(doy), np.sin(dow), np.cos(dow), np.sin(tod), np.cos(tod)], 1).astype(np.float32)


def spacing(xy: np.ndarray) -> float:
    d, _ = cKDTree(xy).query(xy, k=2)
    return float(np.median(d[:, 1]))


def neighbours(xy: np.ndarray, targets: np.ndarray, pool: np.ndarray, scale: float, k: int = K_NEIGHBOURS):
    """k nearest pool stations for each target, never the target itself.
    Returns indices into the full station list (len(targets), k) and relative features (len(targets), k, 4)."""
    tree = cKDTree(xy[pool])
    kk = min(k + 1, len(pool))
    dist, idx = tree.query(xy[targets], k=kk)
    out_idx, out_feat = [], []
    for row, t in enumerate(targets):
        cand = [(d, pool[i]) for d, i in zip(dist[row], idx[row]) if pool[i] != t][:k]
        if len(cand) < k:
            raise ValueError(f"only {len(cand)} neighbours available for station {t}")
        js = np.array([j for _, j in cand])
        delta = (xy[js] - xy[t]) / scale
        dd = np.linalg.norm(delta, axis=1)
        out_idx.append(js)
        out_feat.append(np.stack([delta[:, 0], delta[:, 1], dd, np.log1p(dd)], 1))
    return np.stack(out_idx), np.stack(out_feat).astype(np.float32)


# --------------------------------------------------------------------------------------------- model
@dataclass(frozen=True)
class Variant:
    name: str
    spatial: bool
    mask_ratio: float = 0.0
    residual: bool = False   # predict the change from the value one seasonal period earlier
    scale_head: bool = False
    attention: str = "learned"  # "learned" (relative-distance bias), "nobias", or "mean" (plain mean, no attention)


class OmniSTv2(nn.Module):
    """Shared per-station GRU encoder; optional relative-bias k-NN attention fused through a zero-initialised gate."""

    def __init__(self, variant: Variant, horizon: int, d: int = 64, heads: int = 2):
        super().__init__()
        self.v, self.h, self.d, self.heads = variant, horizon, d, heads
        self.inp = nn.Linear(2 + 6, d)
        self.gru = nn.GRU(d, d, batch_first=True)
        if variant.spatial:
            self.q, self.k, self.val, self.o = (nn.Linear(d, d) for _ in range(4))
            self.bias = nn.Sequential(nn.Linear(4, 32), nn.GELU(), nn.Linear(32, heads))
            self.gate = nn.Parameter(torch.zeros(d))
        self.head = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, horizon))
        if variant.scale_head:
            self.scale = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.Linear(d, horizon))

    def encode(self, x, observed, tfeat):
        """x (B, W, N), observed (B, N) bool, tfeat (B, W, 6) -> (B, N, d)."""
        B, W, N = x.shape
        m = observed[:, None, :].float().expand(B, W, N)
        z = torch.cat([(x * m)[..., None], m[..., None], tfeat[:, :, None, :].expand(B, W, N, 6)], -1)
        z = self.inp(z).permute(0, 2, 1, 3).reshape(B * N, W, self.d)
        _, hn = self.gru(z)
        return hn[-1].reshape(B, N, self.d)

    def spatial_context(self, h, nbr_idx, nbr_feat):
        """h (B, N, d); nbr_idx (B, N, k) long; nbr_feat (B, N, k, 4) -> (B, N, d)."""
        B, N, d = h.shape
        k, H, dh = nbr_idx.shape[-1], self.heads, d // self.heads
        hj = h[torch.arange(B)[:, None, None], nbr_idx]                  # (B, N, k, d): O(N k d) memory
        if self.v.attention == "mean":
            return self.o(self.val(hj).mean(2))
        q = self.q(h).view(B, N, 1, H, dh)
        kk = self.k(hj).view(B, N, k, H, dh)
        vv = self.val(hj).view(B, N, k, H, dh)
        logits = (q * kk).sum(-1) / dh ** 0.5                            # (B, N, k, H)
        if self.v.attention == "learned":
            logits = logits + self.bias(nbr_feat)
        elif self.v.attention != "nobias":
            raise ValueError(f"unknown attention {self.v.attention!r}")
        attn = torch.softmax(logits, dim=2)
        return self.o((attn[..., None] * vv).sum(2).reshape(B, N, d))

    def forward(self, x, observed, tfeat, nbr_idx=None, nbr_feat=None):
        h = self.encode(x, observed, tfeat)
        if self.v.spatial:
            h = h + self.gate * self.spatial_context(h, nbr_idx, nbr_feat)
        mean = self.head(h)                                                # (B, N, H)
        if self.v.residual:
            # the base is the target's own value one period earlier, so a station without history has none
            if not bool(observed.all()):
                raise ValueError("seasonal-residual forecasting needs the target's own history; not usable at Day 0")
            if self.period_steps < self.h or x.shape[1] < self.period_steps:
                raise ValueError("seasonal residual needs period >= horizon and window >= period")
            base = x[:, x.shape[1] - self.period_steps + torch.arange(self.h), :].permute(0, 2, 1)
            mean = mean + base
        scale = nn.functional.softplus(self.scale(h)) + 1e-3 if self.v.scale_head else None
        return mean, scale


# ------------------------------------------------------------------------------------------ training
def train_variant(net: Network, variant: Variant, train: np.ndarray, norm, seed: int, steps: int = 1500,
                  batch: int = 16, lr: float = 1e-3) -> OmniSTv2:
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    mu, sd = norm
    y = (net.series[:, train] - mu) / sd
    tf = time_features(net.dates)
    xy = net.xy_km
    s_km = spacing(xy[train])
    model = OmniSTv2(variant, net.horizon)
    model.period_steps = net.period
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    W, H = net.window, net.horizon
    n = len(train)
    full_idx, full_feat = neighbours(xy[train], np.arange(n), np.arange(n), s_km) if variant.spatial else (None, None)
    for _ in range(steps):
        starts = rng.integers(0, net.train_end - W - H, size=batch)
        xb = np.stack([y[s:s + W] for s in starts])
        yb = np.stack([y[s + W:s + W + H].T for s in starts])
        tb = np.stack([tf[s:s + W] for s in starts])
        obs = np.ones((batch, n), dtype=bool)
        if variant.mask_ratio > 0:
            for b in range(batch):
                obs[b, rng.choice(n, size=max(1, int(round(variant.mask_ratio * n))), replace=False)] = False
        if variant.spatial:
            if variant.mask_ratio > 0:
                g = [neighbours(xy[train], np.arange(n), np.nonzero(obs[b])[0], s_km) for b in range(batch)]
                ni, nf = np.stack([a for a, _ in g]), np.stack([f for _, f in g])
            else:
                ni, nf = np.broadcast_to(full_idx, (batch,) + full_idx.shape), np.broadcast_to(full_feat, (batch,) + full_feat.shape)
            ni, nf = torch.as_tensor(np.ascontiguousarray(ni)), torch.as_tensor(np.ascontiguousarray(nf))
        else:
            ni = nf = None
        mean, scale = model(torch.as_tensor(xb, dtype=torch.float32), torch.as_tensor(obs), torch.as_tensor(tb), ni, nf)
        target = torch.as_tensor(yb, dtype=torch.float32)
        if variant.scale_head:
            loss = ((target - mean).abs() / scale + torch.log(scale)).mean()
        else:
            loss = (target - mean).abs().mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    model.eval()
    return model


# ---------------------------------------------------------------------------------------- evaluation
def eval_starts(net: Network) -> np.ndarray:
    return np.arange(net.test_start, len(net.series) - net.window - net.horizon + 1, net.horizon)


@torch.no_grad()
def predict(model: OmniSTv2, net: Network, train, targets, norm, cold: bool):
    """Forecasts for `targets` (original units), neighbours always drawn from `train`.
    Returns mean (windows, targets, H) and scale (or None) in original units."""
    mu, sd = norm
    stations = np.concatenate([train, targets])
    pos_t = np.arange(len(train), len(stations))
    y = (net.series[:, stations] - mu) / sd
    tf = time_features(net.dates)
    obs = np.ones(len(stations), dtype=bool)
    if cold:
        obs[pos_t] = False
    s_km = spacing(net.xy_km[train])
    ni = nf = None
    if model.v.spatial:
        idx, feat = neighbours(net.xy_km[stations], np.arange(len(stations)), np.arange(len(train)), s_km)
        ni, nf = torch.as_tensor(idx)[None], torch.as_tensor(feat)[None]
    means, scales = [], []
    for s in eval_starts(net):
        xb = torch.as_tensor(y[s:s + net.window][None], dtype=torch.float32)
        mean, scale = model(xb, torch.as_tensor(obs)[None], torch.as_tensor(tf[s:s + net.window][None]), ni, nf)
        means.append(mean[0, pos_t].numpy() * sd + mu)
        if scale is not None:
            scales.append(scale[0, pos_t].numpy() * sd)
    return np.stack(means), (np.stack(scales) if scales else None)


def truth(net: Network, targets) -> np.ndarray:
    return np.stack([net.series[s + net.window:s + net.window + net.horizon, targets].T for s in eval_starts(net)])


def persistence(net: Network, stations) -> np.ndarray:
    return np.stack([np.repeat(net.series[s + net.window - 1, stations][:, None], net.horizon, 1) for s in eval_starts(net)])


def seasonal_naive(net: Network, stations) -> np.ndarray:
    """Value one period before each target step, always inside the input window (requires window >= period)."""
    if net.window < net.period:
        raise ValueError("window shorter than the seasonal period")
    out = []
    for s in eval_starts(net):
        origin = s + net.window
        steps = [origin + h - (-(-(h + 1) // net.period)) * net.period for h in range(net.horizon)]
        out.append(net.series[steps][:, stations].T)
    return np.stack(out)


def idw(values_at_pool: np.ndarray, net: Network, train, targets, nearest_only: bool = False) -> np.ndarray:
    """Inverse-squared-distance weighting of forecasts made at the training stations, over the same k neighbours.
    values_at_pool: (windows, len(train), H)."""
    idx, _ = neighbours(net.xy_km, targets, train, spacing(net.xy_km[train]))
    pos = {s: i for i, s in enumerate(train)}
    out = np.zeros((values_at_pool.shape[0], len(targets), values_at_pool.shape[2]))
    for r, t in enumerate(targets):
        js = idx[r]
        d = np.linalg.norm(net.xy_km[js] - net.xy_km[t], axis=1) + 1e-6
        w = np.zeros_like(d)
        if nearest_only:
            w[np.argmin(d)] = 1.0
        else:
            w = 1.0 / d ** 2
            w /= w.sum()
        out[:, r] = np.tensordot(values_at_pool[:, [pos[j] for j in js]], w, axes=([1], [0]))
    return out
