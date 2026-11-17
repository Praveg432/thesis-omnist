"""Persistence and seasonal-naive forecast errors on the same sliding windows as SpatiotemporalDataset.

Pure functions. A window starting at index s has input series[s : s + w] and targets
series[s + w : s + w + H]; the forecast origin is s + w. Both baselines use only values before the origin.
"""
from __future__ import annotations

import numpy as np


def window_starts(n_steps: int, window: int, horizon: int, stride: int) -> list:
    """Same indexing as SpatiotemporalDataset: range(0, T - window - horizon + 1, stride)."""
    return list(range(0, n_steps - window - horizon + 1, stride))


def persistence_errors(series: np.ndarray, starts: list, window: int, horizon: int) -> np.ndarray:
    """|target - last observed value|, shape (windows, stations, horizon). series is (T, stations)."""
    _check_series(series)
    out = []
    for s in starts:
        origin = s + window
        out.append(np.abs(series[origin:origin + horizon] - series[origin - 1]).T)
    return np.stack(out)


def seasonal_naive_errors(series: np.ndarray, starts: list, window: int, horizon: int, period: int):
    """|target - value one or more full periods earlier that is known at the origin|.

    For lead h the forecast is series[origin + h - k * period] with the smallest k >= 1 that is before the
    origin, i.e. k = ceil((h + 1) / period). Windows without enough history (origin - k_max * period < 0)
    are dropped. Returns (errors (windows, stations, horizon), kept_starts).
    """
    _check_series(series)
    if period < 1:
        raise ValueError(f"period must be at least 1, got {period}")
    k_max = -(-horizon // period)
    kept, out = [], []
    for s in starts:
        origin = s + window
        if origin - k_max * period < 0:
            continue
        pred = np.stack([series[origin + h - (-(-(h + 1) // period)) * period] for h in range(horizon)])
        out.append(np.abs(series[origin:origin + horizon] - pred).T)
        kept.append(s)
    if not out:
        raise ValueError(f"no window has {k_max * period} steps of history; series has {len(series)} steps")
    return np.stack(out), kept


def _check_series(series: np.ndarray) -> None:
    if series.ndim != 2:
        raise ValueError(f"series must have shape (steps, stations), got {series.shape}")
