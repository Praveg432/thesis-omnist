"""Tests for the chronological calibration protocol (experiment C1b)."""
import numpy as np
import pytest

from src.chronological_conformal import (chronological_quantiles, compare_protocols,
                                         conformal_quantile, same_window_quantiles, warmup_windows)

ALPHA = 0.10


def _scores(scale_per_window, n_stations=6, horizon=5, seed=0):
    rng = np.random.default_rng(seed)
    base = np.abs(rng.normal(size=(len(scale_per_window), n_stations, horizon)))
    return base * np.asarray(scale_per_window)[:, None, None]


def test_shouldUseOnlyEarlierWindowsWhenComputingChronologicalQuantile():
    cal = _scores(np.ones(40))
    q_before = chronological_quantiles(cal, first_scored=20, alpha=ALPHA)
    corrupted = cal.copy()
    corrupted[20:] *= 1000.0  # errors at windows >= 20 are not known at the origin of window 20
    q_after = chronological_quantiles(corrupted, first_scored=20, alpha=ALPHA)
    assert q_before[0] == q_after[0]  # window 20 sees only windows 0..19


def test_shouldChangeLaterQuantilesWhenEarlierWindowsChange():
    cal = _scores(np.ones(40))
    changed = cal.copy()
    changed[5] *= 1000.0
    assert not np.array_equal(chronological_quantiles(cal, 20, ALPHA), chronological_quantiles(changed, 20, ALPHA))


def test_shouldUnderCoverWhenScaleGrowsOverTimeButSameWindowDoesNot():
    scale = np.linspace(1.0, 4.0, 300)
    cal, test = _scores(scale, seed=1), _scores(scale, seed=2)
    result = compare_protocols(cal, test, ALPHA, warmup_fraction=0.25)
    assert result["chronological"]["coverage"] < 0.88
    assert abs(result["same_window"]["coverage"] - 0.90) < 0.05


def test_shouldCoverNearTargetWhenScalesAreStationary():
    cal, test = _scores(np.ones(400), n_stations=8, seed=3), _scores(np.ones(400), n_stations=8, seed=4)
    result = compare_protocols(cal, test, ALPHA, warmup_fraction=0.25)
    assert abs(result["chronological"]["coverage"] - 0.90) < 0.03


def test_shouldScoreSameWindowsForEveryProtocol():
    cal, test = _scores(np.ones(100)), _scores(np.ones(100), seed=5)
    result = compare_protocols(cal, test, ALPHA, warmup_fraction=0.25)
    assert result["first_scored_window"] == 25 and result["n_scored_windows"] == 75
    assert len(same_window_quantiles(cal, 25, ALPHA)) == 75


def test_shouldRejectInvalidWarmupFraction():
    with pytest.raises(ValueError, match="warm-up fraction"):
        warmup_windows(100, 1.0)


def test_shouldRejectMismatchedWindowCounts():
    with pytest.raises(ValueError, match="same windows"):
        compare_protocols(_scores(np.ones(50)), _scores(np.ones(40)), ALPHA, 0.25)


def test_shouldRejectEmptyCalibrationScores():
    with pytest.raises(ValueError, match="at least one"):
        conformal_quantile(np.array([]), ALPHA)
