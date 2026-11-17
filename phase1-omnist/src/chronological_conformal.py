"""Chronological (forecast-time-only) calibration of split-conformal intervals at unseen stations.

Pure functions, no I/O. Inputs are absolute-error arrays of shape (windows, stations, horizon) in time
order. Window t is a forecast issued at origin t; its targets end where window t+1 begins (stride equals
horizon), so the errors of windows 0..t-1 are all known at the origin of window t. Errors of window t
and later are not.

Three calibration protocols are compared on the same scored windows:
  chronological  q_t from calibration-station errors of windows before t (expanding window).
                 The only protocol usable at forecast time.
  same_window    q_t from calibration-station errors of window t itself (needs targets not yet known;
                 the protocol used by C1).
  pooled         one q from the calibration-station errors of all windows (also uses the future).
"""
from __future__ import annotations

import numpy as np


def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """Finite-sample-corrected split-conformal quantile. Same formula as experiments/C1."""
    n = len(scores)
    if n == 0:
        raise ValueError("conformal_quantile needs at least one calibration score")
    return float(np.quantile(scores, min(1.0, (1.0 - alpha) * (1.0 + 1.0 / n))))


def warmup_windows(n_windows: int, fraction: float) -> int:
    """Number of leading windows used only as calibration history, never scored."""
    if not 0.0 < fraction < 1.0:
        raise ValueError(f"warm-up fraction must be in (0, 1), got {fraction}")
    first = max(1, int(np.ceil(n_windows * fraction)))
    if first >= n_windows:
        raise ValueError(f"warm-up of {first} windows leaves nothing to score out of {n_windows}")
    return first


def chronological_quantiles(cal_scores: np.ndarray, first_scored: int, alpha: float) -> np.ndarray:
    """q_t for t = first_scored .. W-1, using calibration errors of windows 0..t-1 only."""
    _check_scores(cal_scores)
    if first_scored < 1:
        raise ValueError("first_scored must be at least 1 so that some history exists")
    return np.array([conformal_quantile(cal_scores[:t].reshape(-1), alpha)
                     for t in range(first_scored, cal_scores.shape[0])])


def same_window_quantiles(cal_scores: np.ndarray, first_scored: int, alpha: float) -> np.ndarray:
    _check_scores(cal_scores)
    return np.array([conformal_quantile(cal_scores[t].reshape(-1), alpha)
                     for t in range(first_scored, cal_scores.shape[0])])


def pooled_quantile(cal_scores: np.ndarray, alpha: float) -> float:
    _check_scores(cal_scores)
    return conformal_quantile(cal_scores.reshape(-1), alpha)


def coverage_with_quantiles(test_scores: np.ndarray, quantiles: np.ndarray, first_scored: int) -> dict:
    """Coverage of intervals +-q_t on windows first_scored.. ; quantiles is scalar or per-window."""
    _check_scores(test_scores)
    scored = test_scores[first_scored:]
    q = np.broadcast_to(np.asarray(quantiles, dtype=float), (scored.shape[0],))
    covered = scored <= q[:, None, None]
    per_station = covered.mean(axis=(0, 2))
    return {"coverage": float(covered.mean()),
            "width": float(2.0 * q.mean()),
            "per_station_coverage": [float(c) for c in per_station]}


def compare_protocols(cal_scores: np.ndarray, test_scores: np.ndarray, alpha: float,
                      warmup_fraction: float) -> dict:
    """Coverage and width of the three protocols on exactly the same scored windows."""
    _check_scores(cal_scores)
    _check_scores(test_scores)
    if cal_scores.shape[0] != test_scores.shape[0]:
        raise ValueError("calibration and test scores must cover the same windows: "
                         f"{cal_scores.shape[0]} vs {test_scores.shape[0]}")
    first = warmup_windows(cal_scores.shape[0], warmup_fraction)
    out = {"first_scored_window": first, "n_scored_windows": int(cal_scores.shape[0] - first)}
    out["chronological"] = coverage_with_quantiles(
        test_scores, chronological_quantiles(cal_scores, first, alpha), first)
    out["same_window"] = coverage_with_quantiles(
        test_scores, same_window_quantiles(cal_scores, first, alpha), first)
    out["pooled"] = coverage_with_quantiles(test_scores, pooled_quantile(cal_scores, alpha), first)
    return out


def _check_scores(scores: np.ndarray) -> None:
    if scores.ndim != 3:
        raise ValueError(f"scores must have shape (windows, stations, horizon), got {scores.shape}")
