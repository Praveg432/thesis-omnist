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


def test_shouldRestoreCoverageWhenErrorsScaleWithAKnownLevelAndScoresAreScaled():
    from src.chronological_conformal import scaled_coverage
    level = np.linspace(1.0, 4.0, 300)[:, None, None] * np.ones((300, 6, 1))
    rng = np.random.default_rng(7)
    cal = np.abs(rng.normal(size=(300, 6, 5))) * level
    test = np.abs(rng.normal(size=(300, 6, 5))) * level
    plain = compare_protocols(cal, test, ALPHA, 0.25)["chronological"]["coverage"]
    scaled = scaled_coverage(cal, level, test, level, 75, ALPHA)["coverage"]
    assert plain < 0.88 and abs(scaled - 0.90) < 0.03


def test_shouldUseOnlyRecentWindowsWhenRolling():
    from src.chronological_conformal import rolling_quantiles
    cal = _scores(np.concatenate([np.full(20, 100.0), np.ones(20)]))
    q_roll = rolling_quantiles(cal, 30, ALPHA, n_recent=5)
    q_all = chronological_quantiles(cal, 30, ALPHA)
    assert q_roll.max() < q_all.min()  # the old large errors no longer inflate the quantile


def test_shouldRejectNonPositiveScale():
    from src.chronological_conformal import scaled_coverage
    cal = _scores(np.ones(20))
    with pytest.raises(ValueError, match="positive"):
        scaled_coverage(cal, np.zeros((20, 6, 1)), cal, np.ones((20, 6, 1)), 5, ALPHA)


def test_shouldRejectInvalidWarmupFraction():
    with pytest.raises(ValueError, match="warm-up fraction"):
        warmup_windows(100, 1.0)


def test_shouldRejectMismatchedWindowCounts():
    with pytest.raises(ValueError, match="same windows"):
        compare_protocols(_scores(np.ones(50)), _scores(np.ones(40)), ALPHA, 0.25)


def test_shouldRejectEmptyCalibrationScores():
    with pytest.raises(ValueError, match="at least one"):
        conformal_quantile(np.array([]), ALPHA)
