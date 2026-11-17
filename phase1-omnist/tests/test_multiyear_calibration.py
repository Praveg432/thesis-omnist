import numpy as np
import pytest

from src.multiyear_calibration import (circular_day_distance, hcp_threshold, history_indices, rule_quantiles)

FOLDS = np.array([0] * 5 + [1] * 5 + [2] * 5)
DOY = np.array([10, 100, 200, 300, 350] * 3)


def test_shouldWrapDayOfYearWhenMeasuringCircularDistance():
    assert circular_day_distance(np.array([360]), 5.0)[0] == 11.0


def test_shouldUseOnlyEarlierWindowsForEveryRule():
    for rule in ("expanding_all", "expanding_within", "rolling", "seasonal"):
        for t in range(1, 15):
            idx = history_indices(rule, t, FOLDS, DOY)
            assert (idx < t).all()


def test_shouldMatchSeasonOfEarlierFoldsWhenUsingSeasonalRule():
    idx = history_indices("seasonal", 13, FOLDS, DOY, half_width_days=30, min_windows=2)  # doy 300, fold 2
    assert set(FOLDS[idx]) <= {0, 1} and (circular_day_distance(DOY[idx], 300.0) <= 30).all()


def test_shouldFallBackToAllHistoryWhenNoSeasonalMatchExists():
    idx = history_indices("seasonal", 7, FOLDS, DOY, half_width_days=1, min_windows=2)
    assert len(idx) == 7


def test_shouldCoverSeasonalErrorsBetterThanExpandingWhenErrorsFollowTheSeason():
    rng = np.random.default_rng(0)
    folds = np.repeat([0, 1, 2, 3], 12)
    doy = np.tile(np.arange(12) * 30, 4)
    scale = 1.0 + 3.0 * (doy > 270)  # the last three windows of every year have 4x larger errors
    cal = np.abs(rng.normal(size=(48, 6, 4))) * scale[:, None, None]
    test = np.abs(rng.normal(size=(48, 6, 4))) * scale[:, None, None]
    scored = np.arange(24, 48)

    def coverage(rule):
        q = rule_quantiles(cal, folds, doy, scored, 0.1, rule, half_width_days=45)
        return float((test[scored] <= q[:, None, None]).mean())

    assert coverage("seasonal") > coverage("expanding_all")
    assert abs(coverage("seasonal") - 0.9) < 0.06


def test_shouldReturnInfiniteThresholdWhenTooFewStationsForHcp():
    scores = [np.arange(1, 31, dtype=float) for _ in range(8)]  # K = 8, 1/(K+1) = 0.111 > 0.1
    assert hcp_threshold(scores, 0.1) == float("inf")


def test_shouldMatchSplitConformalWhenEveryStationHasOneScore():
    scores = [np.array([float(i)]) for i in range(1, 20)]  # K = 19 groups of size one
    assert hcp_threshold(scores, 0.1) == 18.0  # ceil(0.9 * 20) = 18th smallest


def test_shouldWeightStationsEquallyRegardlessOfSize():
    small = np.array([1.0, 1.0])
    large = np.full(1000, 10.0)
    groups = [small] * 6 + [large] * 6  # K = 12; each station weighs 1/13, so the small-score stations hold 6/13
    assert hcp_threshold(groups, 0.55) == 1.0   # 6/13 = 0.4615 >= 0.45
    assert hcp_threshold(groups, 0.50) == 10.0  # needs 0.50, so the large-score level is reached
    # pooling the raw scores would put 12000 of 12012 points at 10.0 and always return 10.0


def test_shouldRejectEmptyStationOrBadAlpha():
    with pytest.raises(ValueError, match="at least one score"):
        hcp_threshold([np.array([])], 0.1)
    with pytest.raises(ValueError, match="alpha"):
        hcp_threshold([np.array([1.0])], 1.5)
