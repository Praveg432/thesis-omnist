import numpy as np
import pytest

from src.origin_calibration import Rule, circular_distance, half_widths, history, online_selection

ALPHA = 0.1


def _layout(n=40, horizon=3):
    origin = np.arange(n, dtype=float)
    return origin, origin + horizon, np.zeros(n, dtype=int), origin % 10


def test_shouldExcludeWindowsWhoseTargetsAreNotYetObserved():
    origin, end, fold, phase = _layout(horizon=3)
    idx = history(Rule("all", "all", False), 20, origin, end, fold, phase)
    assert idx.max() == 17  # window 17 ends at 20; windows 18 and 19 end after the origin of window 20


def test_shouldMatchPhaseWithinTolerance():
    origin, end, fold, phase = _layout()
    idx = history(Rule("p", "phase", False, tolerance=0.0, period=10.0), 35, origin, end, fold, phase)
    assert set(phase[idx]) == {5.0}


def test_shouldWrapCircularDistance():
    assert circular_distance(np.array([23.5]), 0.5, 24.0)[0] == 1.0


def test_shouldRestrictSeasonalRuleToEarlierFolds():
    origin = np.arange(30, dtype=float)
    end, fold, phase = origin + 1, np.repeat([0, 1, 2], 10), np.tile(np.arange(10.0), 3)
    idx = history(Rule("s", "prior_folds_phase", True, tolerance=0.0, period=10.0), 25, origin, end, fold, phase)
    assert set(fold[idx]) <= {0, 1} and set(phase[idx]) == {5.0}


def test_shouldCoverTimeOfDayPatternWhenPhaseMatched():
    rng = np.random.default_rng(1)
    n = 240
    origin = np.arange(n, dtype=float)
    phase = origin % 24
    scale = np.where(phase >= 18, 5.0, 1.0)
    cal = np.abs(rng.normal(size=(n, 8, 2))) * scale[:, None, None]
    test = np.abs(rng.normal(size=(n, 8, 2))) * scale[:, None, None]
    ones = np.ones((n, 8, 1))
    scored = np.arange(120, n)
    end, fold = origin + 1, np.zeros(n, dtype=int)

    def cov(rule):
        h = half_widths(rule, cal, ones, ones, scored, origin, end, fold, phase, ALPHA)
        evening = phase[scored] >= 18
        return float((test[scored][evening] <= h[evening]).mean())

    assert cov(Rule("p", "phase", False, tolerance=0.0, period=24.0)) > cov(Rule("a", "all", False)) + 0.1


def test_shouldPickTheBetterRuleOnceHistoryExists():
    rng = np.random.default_rng(2)
    n = 120
    origin = np.arange(n, dtype=float)
    end, fold, phase = origin + 1, np.zeros(n, dtype=int), origin % 12
    cal = np.abs(rng.normal(size=(n, 6, 2)))
    good = Rule("good", "all", False)
    bad = Rule("bad", "phase", False, tolerance=0.0, period=12.0)  # few matching windows -> noisier, wider
    scored = np.arange(60, n)
    ones = np.ones((n, 6, 1))
    _, chosen = online_selection([bad, good], "bad", cal, ones, ones, scored, origin, end, fold, phase, ALPHA)
    assert chosen[0] == "bad" and chosen[-1] == "good"


def test_shouldRejectUnknownDefault():
    with pytest.raises(ValueError, match="not a candidate"):
        online_selection([Rule("a", "all", False)], "b", *[None] * 9)
