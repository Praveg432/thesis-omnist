"""Forecast-time calibration with overlapping forecast origins, phase matching and online rule selection.

Pure functions, no I/O. Arrays are indexed by window (one window = one forecast origin), concatenated over folds
in time order. For each window the caller supplies:
  origin[t]  absolute time of the forecast origin (any monotone unit, e.g. day ordinal or minute)
  end[t]     absolute time at which the window's last target is observed
  fold[t]    test-period id (0, 1, ...)
  phase[t]   position in the dominant cycle (day of year, or minute of day)
A window u may inform a forecast at window t only if end[u] <= origin[t] (its targets are fully observed).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.chronological_conformal import conformal_quantile
from src.interval_metrics import interval_score


@dataclass(frozen=True)
class Rule:
    """A calibration rule: which earlier windows to use, and whether errors are scaled."""
    name: str
    history: str           # "same_fold", "all", "prior_folds_phase", "phase"
    scaled: bool
    tolerance: float = 0.0  # phase tolerance for the phase rules
    period: float = 366.0   # length of the phase cycle


def circular_distance(a: np.ndarray, b: float, period: float) -> np.ndarray:
    d = np.abs(np.asarray(a, dtype=float) - b) % period
    return np.minimum(d, period - d)


def history(rule: Rule, t: int, origin, end, fold, phase, min_windows: int = 2) -> np.ndarray:
    known = np.nonzero(end <= origin[t])[0]
    if rule.history == "all":
        return known
    if rule.history == "same_fold":
        return known[fold[known] == fold[t]]
    if rule.history in ("prior_folds_phase", "phase"):
        pool = known[fold[known] < fold[t]] if rule.history == "prior_folds_phase" else known
        near = pool[circular_distance(phase[pool], phase[t], rule.period) <= rule.tolerance]
        return near if len(near) >= min_windows else known
    raise ValueError(f"unknown history {rule.history!r}")


def half_widths(rule: Rule, cal_err, cal_scale, target_scale, windows, origin, end, fold, phase, alpha) -> np.ndarray:
    """Half widths (len(windows), stations, 1) for the stations whose scale is target_scale; inf if no history."""
    scores = cal_err / cal_scale if rule.scaled else cal_err
    out = []
    for t in windows:
        idx = history(rule, int(t), origin, end, fold, phase)
        q = conformal_quantile(scores[idx].reshape(-1), alpha) if len(idx) else float("inf")
        out.append(q * target_scale[t] if rule.scaled else np.full(target_scale[t].shape, q))
    return np.stack(out)


def online_selection(rules: list, default: str, cal_err, cal_scale, test_scale, scored, origin, end, fold, phase,
                     alpha) -> tuple:
    """Per scored window, use the rule with the lowest mean calibration-station interval score over earlier
    scored windows whose targets are observed; `default` until such a window exists.
    Returns (test half widths (len(scored), stations, 1), chosen rule names)."""
    names = [r.name for r in rules]
    if default not in names:
        raise ValueError(f"default rule {default!r} is not a candidate")
    cal_half = {r.name: half_widths(r, cal_err, cal_scale, cal_scale, scored, origin, end, fold, phase, alpha) for r in rules}
    test_half = {r.name: half_widths(r, cal_err, cal_scale, test_scale, scored, origin, end, fold, phase, alpha) for r in rules}
    cal_is = {n: np.array([interval_score(cal_err[t], cal_half[n][i], alpha) if np.isfinite(cal_half[n][i]).all()
                           else np.inf for i, t in enumerate(scored)]) for n in names}
    chosen, halves = [], []
    for i, t in enumerate(scored):
        past = [j for j in range(i) if end[scored[j]] <= origin[t]]
        pick = default if not past else min(names, key=lambda n: (np.mean(cal_is[n][past]), names.index(n)))
        chosen.append(pick)
        halves.append(test_half[pick][i])
    return np.stack(halves), chosen
