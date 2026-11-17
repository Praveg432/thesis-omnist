import numpy as np
import pytest

from src.interval_metrics import interval_score, paired_difference
from src.naive_baselines import persistence_forecasts, seasonal_naive_forecasts, targets, window_starts


def test_shouldEqualWidthWhenEveryOutcomeIsInside():
    assert interval_score(np.array([0.5, 1.0]), 2.0, 0.1) == 4.0


def test_shouldPenaliseMissesByTwoOverAlpha():
    # half width 1, error 3: 2*1 + 20*(3-1) = 42
    assert interval_score(np.array([3.0]), 1.0, 0.1) == 42.0


def test_shouldRejectNegativeHalfWidth():
    with pytest.raises(ValueError, match="non-negative"):
        interval_score(np.array([1.0]), -1.0, 0.1)


def test_shouldMatchPersistenceErrorsWhenUsingForecastHelpers():
    rng = np.random.default_rng(0)
    series = rng.normal(size=(100, 3))
    starts = window_starts(100, 20, 5, 5)
    pred = persistence_forecasts(series, starts, 20, 5)
    assert np.allclose(pred[0, :, 0], series[19])
    assert targets(series, starts, 20, 5).shape == pred.shape


def test_shouldReproducePeriodicSeriesWithSeasonalForecasts():
    t = np.arange(120)
    series = np.stack([np.sin(2 * np.pi * t / 7)] * 2, axis=1)
    starts = window_starts(120, 30, 15, 15)
    assert np.allclose(seasonal_naive_forecasts(series, starts, 30, 15, 7), targets(series, starts, 30, 15))


def test_shouldRefuseSeasonalForecastWithoutHistory():
    with pytest.raises(ValueError, match="history"):
        seasonal_naive_forecasts(np.zeros((100, 2)), [0], 5, 15, 7)


def test_shouldGiveIntervalExcludingZeroWhenDifferencesAreConsistent():
    out = paired_difference([1.0, 1.1, 0.9, 1.05], [0.0, 0.1, 0.0, 0.05])
    assert out["ci95"][0] > 0
