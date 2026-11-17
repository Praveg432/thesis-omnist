"""Interval quality metrics. Pure functions."""
from __future__ import annotations

import numpy as np


def interval_score(abs_errors: np.ndarray, half_width: np.ndarray, alpha: float) -> float:
    """Mean interval (Winkler) score of symmetric intervals forecast +/- half_width; lower is better.

    For a central (1 - alpha) interval [l, u] and outcome y the score is (u - l) + (2/alpha) * distance of y
    outside [l, u] (Gneiting and Raftery 2007). For forecast +/- h this is 2h + (2/alpha) * max(|y - f| - h, 0).
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    h = np.broadcast_to(np.asarray(half_width, dtype=float), abs_errors.shape)
    if (h < 0).any():
        raise ValueError("half widths must be non-negative")
    return float(np.mean(2.0 * h + (2.0 / alpha) * np.maximum(abs_errors - h, 0.0)))


def paired_difference(a: list, b: list) -> dict:
    """Mean of a - b over paired splits with a 95% t-interval."""
    from scipy import stats

    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if len(d) < 2:
        raise ValueError("need at least two paired splits")
    m, s = float(d.mean()), float(d.std(ddof=1))
    h = float(stats.t.ppf(0.975, len(d) - 1)) * s / np.sqrt(len(d))
    return {"mean": round(m, 4), "ci95": [round(m - h, 4), round(m + h, 4)], "n": int(len(d))}
