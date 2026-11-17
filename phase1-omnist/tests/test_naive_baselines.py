import numpy as np
import pytest

from src.naive_baselines import persistence_errors, seasonal_naive_errors, window_starts


def test_shouldMatchDatasetIndexingWhenListingWindowStarts():
    assert window_starts(n_steps=100, window=10, horizon=5, stride=5) == list(range(0, 86, 5))


def test_shouldHaveZeroErrorWhenSeriesIsConstantUnderPersistence():
    series = np.full((60, 3), 7.0)
    err = persistence_errors(series, window_starts(60, 10, 5, 5), 10, 5)
    assert err.shape == (10, 3, 5) and err.max() == 0.0


def test_shouldHaveZeroErrorWhenSeriesIsPeriodicUnderSeasonalNaive():
    t = np.arange(200)
    series = np.stack([np.sin(2 * np.pi * t / 7), np.cos(2 * np.pi * t / 7)], axis=1)
    err, kept = seasonal_naive_errors(series, window_starts(200, 20, 10, 10), 20, 10, period=7)
    assert err.max() < 1e-9 and len(kept) > 0


def test_shouldUseOnlyValuesBeforeTheOriginWhenForecastingSeasonally():
    t = np.arange(120, dtype=float)
    series = np.stack([t, t], axis=1)
    shifted = series.copy()
    shifted[40:50] += 5.0  # the targets of the window starting at 30 (origin 40), window 10, horizon 10
    err_a, _ = seasonal_naive_errors(series, [30], 10, 10, period=5)
    err_b, _ = seasonal_naive_errors(shifted, [30], 10, 10, period=5)
    # predictions come from before the origin, so shifting the targets by 5 shifts every error by exactly 5
    assert np.allclose(err_b - err_a, 5.0)


def test_shouldDropWindowsWithoutEnoughHistory():
    series = np.zeros((300, 2))
    starts = window_starts(300, 20, 10, 10)
    _, kept = seasonal_naive_errors(series, starts, 20, 10, period=48)
    assert kept[0] + 20 >= 48 and len(kept) < len(starts)


def test_shouldRejectBadInputs():
    with pytest.raises(ValueError, match="period"):
        seasonal_naive_errors(np.zeros((50, 2)), [0], 5, 5, period=0)
    with pytest.raises(ValueError, match="no window"):
        seasonal_naive_errors(np.zeros((30, 2)), [0], 5, 5, period=100)
