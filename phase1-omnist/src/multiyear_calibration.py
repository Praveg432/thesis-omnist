"""Calibration rules over several test years (rolling-origin evaluation) and hierarchical conformal prediction.

Pure functions, no I/O. Scores have shape (windows, stations, horizon) in time order, concatenated over
folds (one fold per test year; earlier folds first). A forecast at window t may use only the
calibration-station errors of windows before t, which already include every window of earlier folds.
"""
from __future__ import annotations

import numpy as np

from src.chronological_conformal import conformal_quantile


def circular_day_distance(doy_a: np.ndarray, doy_b: float, period: int = 366) -> np.ndarray:
    d = np.abs(np.asarray(doy_a, dtype=float) - doy_b)
    return np.minimum(d, period - d)


def history_indices(rule: str, t: int, fold_ids: np.ndarray, origin_doy: np.ndarray, n_recent: int = 4,
                    half_width_days: int = 45, min_windows: int = 2) -> np.ndarray:
    """Indices of the earlier windows whose calibration errors rule `rule` uses for window t."""
    earlier = np.arange(t)
    if rule == "expanding_all":
        return earlier
    if rule == "expanding_within":
        return earlier[fold_ids[earlier] == fold_ids[t]]
    if rule == "rolling":
        return earlier[max(0, t - n_recent):]
    if rule == "seasonal":
        prior_folds = earlier[fold_ids[earlier] < fold_ids[t]]
        near = prior_folds[circular_day_distance(origin_doy[prior_folds], origin_doy[t]) <= half_width_days]
        return near if len(near) >= min_windows else earlier  # fall back to all history, never to nothing
    raise ValueError(f"unknown rule {rule!r}")


def rule_quantiles(cal_scores: np.ndarray, fold_ids: np.ndarray, origin_doy: np.ndarray, scored: np.ndarray,
                   alpha: float, rule: str, **params) -> np.ndarray:
    """q_t for each scored window t under `rule`. Raises if a scored window has no history."""
    out = []
    for t in scored:
        idx = history_indices(rule, int(t), fold_ids, origin_doy, **params)
        if len(idx) == 0:
            raise ValueError(f"rule {rule!r} has no history at window {t}")
        out.append(conformal_quantile(cal_scores[idx].reshape(-1), alpha))
    return np.array(out)


def hcp_threshold(station_scores: list, alpha: float) -> float:
    """Hierarchical conformal threshold (Lee, Barber, Willett, arXiv:2306.06342, eq. 6) for a new station.

    station_scores: one 1-D array of calibration scores per calibration station. Each station carries equal
    total weight 1/(K+1), spread evenly over its scores, and 1/(K+1) of mass sits at +infinity. The
    threshold is the (1 - alpha)-quantile of that distribution; it is +inf when K is too small, that is
    when 1/(K+1) > alpha (K < 9 at alpha = 0.1).
    """
    k = len(station_scores)
    if k == 0 or any(len(s) == 0 for s in station_scores):
        raise ValueError("every calibration station needs at least one score")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    values = np.concatenate([np.asarray(s, dtype=float) for s in station_scores])
    weights = np.concatenate([np.full(len(s), 1.0 / ((k + 1) * len(s))) for s in station_scores])
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order])
    hit = np.nonzero(cumulative >= (1.0 - alpha) - 1e-12)[0]
    return float(values[order][hit[0]]) if len(hit) else float("inf")
