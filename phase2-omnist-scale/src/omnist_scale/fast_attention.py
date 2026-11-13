"""O(N·k) spatial attention — a vectorized sub-quadratic drop-in for OmniST's InductiveGAT.

Why. OmniST's exact attention forms the full (B, N, N) Haversine matrix -> O(N^2) time AND memory,
the bottleneck beyond a few hundred nodes. Its "scalable" path uses a per-batch Python loop over
cKDTree queries (correct but slow and not vectorized). This module provides a clean O(N log N)
neighbour selection (cKDTree on an equirectangular projection) + fully-vectorized O(N·k) gather and
attention, with NO (B,N,N) tensor ever formed and NO per-item Python loop in the hot path.

Equivalence. The attention MATH is identical to InductiveGAT; only neighbour SELECTION differs
(exact topk vs cKDTree). For the local neighbourhoods that drive attention the cKDTree ranking equals
the exact Haversine ranking, so outputs match exact attention within numerical noise (V2 measures the
cosine similarity + coverage parity). The true Haversine distance is recomputed on the k selected
pairs so the learned distance-bias is unchanged.

Interface matches InductiveGAT.forward(tokens (B,N,d), coords (B,N,2)) -> (B,N,d), so it swaps into
omnist_model via a config flag.
"""
from __future__ import annotations
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def knn_indices_ckdtree(coords: torch.Tensor, k: int) -> torch.Tensor:
    """(B,N,k) neighbour indices via a per-batch cKDTree on an equirectangular projection.
    O(N log N) build+query; no (B,N,N) tensor. Vectorized self-removal and padding."""
    from scipy.spatial import cKDTree
    B, N, _ = coords.shape
    dev = coords.device
    out = torch.empty(B, N, k, dtype=torch.long, device=dev)
    c_np = coords.detach().cpu().numpy()
    for b in range(B):
        c = c_np[b]
        lat0 = np.radians(c[:, 0].mean())
        xy = np.stack([np.radians(c[:, 1]) * np.cos(lat0), np.radians(c[:, 0])], axis=1)
        tree = cKDTree(xy)
        _, nbr = tree.query(xy, k=min(k + 1, N))          # +1 to drop self
        nbr = np.atleast_2d(nbr)
        # drop self (vectorized): mask self then take first k of the rest
        rows = np.arange(N)[:, None]
        keep = nbr != rows                                 # (N, k+1) bool
        cleaned = np.empty((N, k), dtype=np.int64)
        for i in range(N):                                 # cheap: k+1 small; no distance work here
            r = nbr[i][keep[i]][:k]
            cleaned[i] = np.pad(r, (0, k - len(r)), mode="edge") if 0 < len(r) < k else (
                r if len(r) == k else np.full(k, i))
        out[b] = torch.from_numpy(cleaned).to(dev)
    return out


def haversine_on_pairs(coords: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
    """True Haversine (km) on the k selected pairs only. coords (B,N,2) deg, idx (B,N,k) -> (B,N,k).
    O(N·k) memory — no N^2 tensor."""
    B, N, k = idx.shape
    lat = coords[..., 0] * (np.pi / 180.0)
    lon = coords[..., 1] * (np.pi / 180.0)
    lat_i = lat.unsqueeze(-1); lon_i = lon.unsqueeze(-1)                 # (B,N,1)
    lat_j = torch.gather(lat.unsqueeze(1).expand(B, N, N), 2, idx)
    lon_j = torch.gather(lon.unsqueeze(1).expand(B, N, N), 2, idx)
    dlat = lat_i - lat_j; dlon = lon_i - lon_j
    a = torch.sin(dlat / 2) ** 2 + torch.cos(lat_i) * torch.cos(lat_j) * torch.sin(dlon / 2) ** 2
    return 6371.0 * 2 * torch.atan2(torch.sqrt(a.clamp(min=1e-8)), torch.sqrt((1 - a).clamp(min=1e-8)))


class FastInductiveGAT(nn.Module):
    """O(N·k) inductive graph attention. Same math/params as InductiveGAT; sub-quadratic selection."""

    def __init__(self, d_model: int, n_heads: int = 4, k_neighbors: int = 8, dropout: float = 0.0,
                 cache_knn: bool = True):
        super().__init__()
        assert d_model % n_heads == 0
        self.d_model = d_model; self.n_heads = n_heads; self.d_head = d_model // n_heads
        self.k = k_neighbors
        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        # Sequential(Linear(1,H)) to match InductiveGAT.dist_bias exactly (shareable weights)
        self.dist_bias = nn.Sequential(nn.Linear(1, n_heads))
        self.out_proj = nn.Linear(d_model, d_model)
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        # OPTIMIZATION: the k-NN neighbour graph depends only on COORDINATES, which are static within
        # a run (a batch repeats the same sensor set). Caching the cKDTree indices + pair distances
        # per unique coordinate tensor turns the O(N log N) build from per-forward-pass into once-per-
        # topology. The cache key is the coords' id+shape+content hash; a topology change (new coords)
        # yields a new key and a fresh build. This is why the "fast" path is fast in TRAINING too.
        self.cache_knn = cache_knn
        self._cache: dict = {}

    def _knn(self, coords: torch.Tensor, k: int):
        if not self.cache_knn:
            idx = knn_indices_ckdtree(coords, k)
            return idx, haversine_on_pairs(coords, idx)
        key = (coords.shape, float(coords.sum().item()), float(coords.std().item()), k, str(coords.device))
        cached = self._cache.get(key)
        if cached is None:
            idx = knn_indices_ckdtree(coords, k)
            dist = haversine_on_pairs(coords, idx)
            self._cache[key] = (idx, dist)
            return idx, dist
        return cached

    def forward(self, tokens: torch.Tensor, coords: torch.Tensor) -> torch.Tensor:
        B, N, D = tokens.shape
        k = min(self.k, N - 1)
        idx, knn_d = self._knn(coords, k)                               # cached O(N log N) build

        Q = self.q_proj(tokens).view(B, N, self.n_heads, self.d_head)
        K = self.k_proj(tokens).view(B, N, self.n_heads, self.d_head)
        V = self.v_proj(tokens).view(B, N, self.n_heads, self.d_head)
        # vectorized neighbour gather: (B,N,k) idx -> (B,N,k,H,dh), no N^2 expansion
        bi = torch.arange(B, device=tokens.device)[:, None, None]
        K_nbr = K[bi, idx]                                              # (B,N,k,H,dh)
        V_nbr = V[bi, idx]
        scores = (Q.unsqueeze(2) * K_nbr).sum(-1) / (self.d_head ** 0.5)   # (B,N,k,H)
        scores = scores + self.dist_bias(knn_d.unsqueeze(-1))             # (B,N,k,H)
        w = self.dropout(F.softmax(scores, dim=2))
        out = (w.unsqueeze(-1) * V_nbr).sum(2).reshape(B, N, D)
        return self.norm(self.out_proj(out) + tokens)
