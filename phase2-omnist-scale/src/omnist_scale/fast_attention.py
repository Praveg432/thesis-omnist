"""O(N·k) spatial attention — a vectorized sub-quadratic drop-in for OmniST's InductiveGAT.

Why. OmniST's exact attention forms the full (B, N, N) Haversine matrix -> O(N^2) time AND memory,
the bottleneck beyond a few hundred nodes. Its "scalable" path uses a per-batch Python loop over
cKDTree queries (correct but slow and not vectorized). This module provides a clean O(N log N)
neighbour selection (cKDTree on an equirectangular projection) + fully-vectorized O(N·k) gather and
attention. No (B,N,N) tensor is formed. The only Python-level loop is over the batch dimension inside
the (cached) neighbour build.

Equivalence. The attention MATH is identical to InductiveGAT; only neighbour SELECTION differs
(exact topk vs cKDTree). For the local neighbourhoods that drive attention the cKDTree ranking is
expected to equal the exact Haversine ranking, so outputs should match exact attention within
numerical noise. V2 measures this with output cosine similarity on random tokens; planned (Semester
4): neighbour-set agreement and trained-weight equivalence. The true Haversine distance is recomputed
on the k selected pairs so the learned distance-bias is unchanged.

Status of the speed/memory claim. Equivalence is measured; a speed or memory advantage is NOT yet
demonstrated (V2 measured no memory; at N=37 this path is slower than exact). Scaling curves are
planned for Semester 4.

Interface matches InductiveGAT.forward(tokens (B,N,d), coords (B,N,2)) -> (B,N,d), so it swaps into
omnist_model via a config flag.
"""
from __future__ import annotations
import hashlib
from collections import OrderedDict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def knn_indices_ckdtree(coords: torch.Tensor, k: int) -> torch.Tensor:
    """(B,N,k) neighbour indices via a per-batch cKDTree on an equirectangular projection.
    O(N log N) build+query per batch item; no (B,N,N) tensor. The loop over the batch dimension B is
    the only Python-level loop; self-removal and padding are vectorized."""
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
        # Drop self without a Python loop: a stable argsort on the "is self" mask moves the kept
        # entries to the front in their original (nearest-first) order; take the first k.
        keep = nbr != np.arange(N)[:, None]               # (N, k+1) bool
        order = np.argsort(~keep, axis=1, kind="stable")
        cleaned = np.take_along_axis(nbr, order, axis=1)[:, :k]
        if cleaned.shape[1] < k:                           # only when N - 1 < k (tiny graphs)
            cleaned = np.pad(cleaned, ((0, 0), (0, k - cleaned.shape[1])), mode="edge")
        out[b] = torch.from_numpy(np.ascontiguousarray(cleaned, dtype=np.int64)).to(dev)
    return out


def haversine_on_pairs(coords: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
    """True Haversine (km) on the k selected pairs only. coords (B,N,2) deg, idx (B,N,k) -> (B,N,k).
    Intended O(N·k) memory. NOTE: the gather below reads from an expanded (stride-0) view; peak
    memory has not been measured yet (planned: memory-vs-N curves in the Semester-4 evaluation)."""
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
                 cache_knn: bool = True, cache_size: int = 8):
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
        # topology. The key is a hash of the exact coordinate BYTES (plus shape, dtype, k, device), so
        # any change in layout, including a reordering of the same sensors, gives a new key. (An
        # earlier key built from coords.sum() and coords.std() collided for permuted layouts and
        # silently returned the wrong neighbours.) The cache holds at most `cache_size` topologies and
        # evicts the least recently used.
        self.cache_knn = cache_knn
        self.cache_size = cache_size
        self._cache: "OrderedDict[tuple, tuple]" = OrderedDict()

    @staticmethod
    def _coords_key(coords: torch.Tensor, k: int) -> tuple:
        arr = np.ascontiguousarray(coords.detach().cpu().numpy())
        digest = hashlib.blake2b(arr.tobytes(), digest_size=16).digest()
        return (tuple(arr.shape), str(arr.dtype), k, str(coords.device), digest)

    def _knn(self, coords: torch.Tensor, k: int):
        if not self.cache_knn:
            idx = knn_indices_ckdtree(coords, k)
            return idx, haversine_on_pairs(coords, idx)
        key = self._coords_key(coords, k)
        cached = self._cache.get(key)
        if cached is not None:
            self._cache.move_to_end(key)
            return cached
        idx = knn_indices_ckdtree(coords, k)
        entry = (idx, haversine_on_pairs(coords, idx))
        self._cache[key] = entry
        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)
        return entry

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
