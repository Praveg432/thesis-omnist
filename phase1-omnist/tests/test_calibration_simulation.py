"""Simulation tests of the calibration code against known ground truth.

Each test generates data from a known process, applies the code, and checks the coverage that theory or the
construction of the process predicts. They test the code, not the stored results.
"""
import numpy as np

from src.chronological_conformal import conformal_quantile
from src.multiyear_calibration import hcp_threshold
from src.origin_calibration import Rule, half_widths

ALPHA = 0.1


def test_split_conformal_covers_ninety_percent_on_exchangeable_scores():
    rng = np.random.default_rng(0)
    n_cal, trials = 49, 4000
    covered = 0
    for _ in range(trials):
        q = conformal_quantile(np.abs(rng.normal(size=n_cal)), ALPHA)
        covered += abs(rng.normal()) <= q
    rate = covered / trials
    assert 0.89 <= rate <= 0.90 + 1 / (n_cal + 1) + 0.01  # theory: between 0.90 and 0.90 + 1/(n+1)


def test_hcp_reaches_nominal_coverage_for_a_new_group_with_unequal_group_sizes():
    """Hierarchical process: each station has its own error scale; stations have different numbers of scores."""
    rng = np.random.default_rng(1)
    k, trials = 19, 3000
    covered = 0
    for _ in range(trials):
        scales = np.exp(rng.normal(0, 0.8, size=k + 1))          # station-level scale, new station is the last
        sizes = rng.integers(3, 60, size=k)
        stations = [np.abs(rng.normal(size=n)) * scales[i] for i, n in enumerate(sizes)]
        q = hcp_threshold(stations, ALPHA)
        covered += abs(rng.normal()) * scales[k] <= q
    rate = covered / trials
    assert 0.90 - 0.015 <= rate <= 0.90 + 2 / (k + 1) + 0.015  # theory: [1 - alpha, 1 - alpha + 2/(K+1)]


def test_pooled_conformal_over_covers_or_under_covers_unevenly_but_hcp_is_stable_across_group_sizes():
    """When one huge station has small errors, pooling lets it dominate; HCP weights every station equally."""
    rng = np.random.default_rng(2)
    k, trials = 19, 2000
    pooled_cov = hcp_cov = 0
    for _ in range(trials):
        scales = np.exp(rng.normal(0, 0.8, size=k + 1))
        sizes = np.full(k, 5)
        sizes[0] = 2000
        scales[0] = 0.2  # the huge station is also the quietest
        stations = [np.abs(rng.normal(size=n)) * scales[i] for i, n in enumerate(sizes)]
        new_error = abs(rng.normal()) * scales[k]
        pooled_cov += new_error <= conformal_quantile(np.concatenate(stations), ALPHA)
        hcp_cov += new_error <= hcp_threshold(stations, ALPHA)
    assert hcp_cov / trials >= 0.90 - 0.02
    assert pooled_cov / trials < 0.85  # the pooled threshold is dragged down by the quiet station


def test_scaled_seasonal_rule_restores_coverage_when_error_follows_forecast_size_and_season():
    rng = np.random.default_rng(3)
    years, per_year, stations, h = 4, 52, 8, 3
    n = years * per_year
    origin = np.arange(n, dtype=float) * 7
    end = origin + 7 * h
    fold = np.repeat(np.arange(years), per_year)
    phase = (origin % 364) + 1
    level = 10 + 8 * np.sin(2 * np.pi * phase / 364)           # seasonal level: errors scale with it
    trend = 1 + 0.35 * fold                                       # and the level grows year on year
    forecast_size = (level * trend)[:, None, None] * np.ones((n, stations, 1))
    cal = np.abs(rng.normal(size=(n, stations, h))) * 0.1 * forecast_size
    test = np.abs(rng.normal(size=(n, stations, h))) * 0.1 * forecast_size
    scored = np.nonzero(fold >= 1)[0]
    scored = scored[scored >= per_year + 13]

    def coverage(rule):
        half = half_widths(rule, cal, forecast_size, forecast_size, scored, origin, end, fold, phase, ALPHA)
        return float((test[scored] <= half).mean())

    same_year = coverage(Rule("same_year", "same_fold", False))
    scaled_seasonal = coverage(Rule("scaled_seasonal", "prior_folds_phase", True, tolerance=45, period=366))
    assert abs(scaled_seasonal - 0.90) < 0.03
    # the same-year rule is miscalibrated in this process (here it over-covers, 0.94, because its short history
    # spans the seasonal peak); the scaled seasonal rule is closer to the target
    assert abs(same_year - 0.90) > abs(scaled_seasonal - 0.90) + 0.015


def test_a_rule_must_not_use_windows_whose_targets_are_still_in_the_future():
    """Planting a huge error in a window that ends after the origin must not change that window's interval."""
    n, stations, h = 60, 4, 3
    origin = np.arange(n, dtype=float)
    end = origin + h
    fold, phase = np.zeros(n, dtype=int), origin % 10
    rng = np.random.default_rng(4)
    cal = np.abs(rng.normal(size=(n, stations, h)))
    ones = np.ones((n, stations, 1))
    scored = np.array([40])
    rule = Rule("all", "all", False)
    clean = half_widths(rule, cal, ones, ones, scored, origin, end, fold, phase, ALPHA)
    tainted = cal.copy()
    tainted[38:] = 1e9  # windows 38 and 39 end at 41 and 42, after origin 40; window 40 itself is the target
    assert np.array_equal(clean, half_widths(rule, tainted, ones, ones, scored, origin, end, fold, phase, ALPHA))
    tainted_past = cal.copy()
    tainted_past[10] = 1e9  # a window that has ended before the origin is allowed to change the result
    assert not np.array_equal(clean, half_widths(rule, tainted_past, ones, ones, scored, origin, end, fold, phase, ALPHA))
