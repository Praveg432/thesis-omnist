"""Tests for the analysis code behind the C1 and C2 findings.

The C2 within-station slope produced the main distance finding, so it is tested against synthetic data
with a known answer, including a confound (noisier stations sit farther from the network) that a pooled
correlation would mistake for a distance effect.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))
import C1_rigorous_inductive_eval as c1  # noqa: E402
import C2_region_holdout_distance as c2  # noqa: E402
from scipy import stats as ss  # noqa: E402


# ------------------------------------------------------------------ geometry helpers
def test_one_degree_of_latitude_is_about_111_km():
    coords = np.array([[28.0, 77.0], [29.0, 77.0]])
    plane = c2.to_plane(coords, "delhi_air_quality")
    assert np.linalg.norm(plane[1] - plane[0]) == pytest.approx(111.19, abs=0.1)


def test_traffic_coordinates_are_left_in_their_own_plane():
    coords = np.array([[0.0, 0.0], [3.0, 4.0]])
    assert np.allclose(c2.to_plane(coords, "pemsd7_traffic"), coords)


def test_network_spacing_is_the_median_nearest_neighbour_distance():
    plane = np.array([[0.0, 0.0], [2.0, 0.0], [4.0, 0.0], [6.0, 0.0]])
    assert c2.network_spacing(plane) == pytest.approx(2.0)


def test_distances_to_training_uses_nearest_and_three_nearest():
    plane = np.array([[0.0, 0.0], [10.0, 0.0], [20.0, 0.0], [30.0, 0.0], [1.0, 0.0]])
    site, train = np.array([4]), np.array([0, 1, 2, 3])
    d1, d3 = c2.distances_to_training(plane, site, train, spacing=1.0)
    assert d1[0] == pytest.approx(1.0)                          # nearest training station at 1
    assert d3[0] == pytest.approx((1 + 9 + 19) / 3)             # three nearest at 1, 9, 19


# ------------------------------------------------------------------ within-station slope
def _arm(stations, d1, cov):
    n = len(d1)
    return (np.asarray(d1, float), np.asarray(cov, float), np.zeros(n), np.zeros(n), np.asarray(stations))


def _planted(slope, n_stations=30, n_obs=8, noise=0.01, confound=0.0, seed=0):
    """Coverage = station offset + slope * distance + noise, with distance varying within a station.
    `confound` makes stations that are farther on average also noisier (lower offset)."""
    rng = np.random.default_rng(seed)
    stations, d1, cov = [], [], []
    for s in range(n_stations):
        mean_d = rng.uniform(1.0, 4.0)
        offset = 0.90 + rng.normal(0, 0.02) - confound * mean_d
        for _ in range(n_obs):
            d = max(0.2, mean_d + rng.normal(0, 0.8))
            stations.append(s); d1.append(d)
            cov.append(offset + slope * d + rng.normal(0, noise))
    return _arm(stations, d1, cov)


def test_within_station_effect_recovers_a_planted_slope():
    result = c2.within_station_effect({"region": _planted(slope=-0.015)})
    assert result is not None
    lo, hi = result["ci95"]
    assert lo < -0.015 < hi
    assert result["slope_per_spacing"] == pytest.approx(-0.015, abs=0.004)


def test_within_station_effect_finds_nothing_when_there_is_no_effect():
    result = c2.within_station_effect({"region": _planted(slope=0.0)})
    lo, hi = result["ci95"]
    assert lo < 0.0 < hi


def test_station_confounding_fools_pooled_correlation_but_not_the_within_station_slope():
    arm = _planted(slope=0.0, confound=0.02)         # far stations are worse, but distance has no effect
    pooled_rho, _ = ss.spearmanr(arm[0], arm[1])
    within = c2.within_station_effect({"region": arm})
    assert pooled_rho < -0.3, "the confound should create a strong spurious pooled correlation"
    lo, hi = within["ci95"]
    assert lo < 0.0 < hi, "the within-station slope should not be fooled"


def test_within_station_effect_returns_none_without_repeated_stations():
    arm = _arm(stations=np.arange(10), d1=np.linspace(1, 3, 10), cov=np.full(10, 0.9))
    assert c2.within_station_effect({"region": arm}) is None


def test_tertile_table_accounts_for_every_station():
    rng = np.random.default_rng(1)
    d1, cov = rng.uniform(1, 5, 60), rng.uniform(0.8, 0.95, 60)
    ids = np.repeat(np.arange(6), 10)
    rows = c2.tertile_table(d1, cov, ids, edges=[2.3, 3.7], n_boot=200)
    assert sum(r["n"] for r in rows if r) == 60
    for r in rows:
        assert r["ci95"][0] <= r["coverage"] <= r["ci95"][1]


# ------------------------------------------------------------------ C1 helpers
def test_conformal_quantile_is_at_least_the_empirical_quantile():
    scores = np.arange(1.0, 101.0)
    assert c1.conformal_quantile(scores, 0.1) >= np.quantile(scores, 0.9)
    assert c1.conformal_quantile(scores, 0.1) <= scores.max()


def test_coverage_summary_per_station_and_marginal():
    scores = np.zeros((4, 2, 3))
    scores[:, 1, :] = 10.0                                    # station 1 always above the threshold
    out = c1.coverage_summary(scores, q=5.0)
    assert out["per_station_coverage"] == [1.0, 0.0]
    assert out["coverage"] == pytest.approx(0.5)
    assert out["width"] == pytest.approx(10.0)


def test_aggregate_matches_a_direct_recomputation():
    def split(cov):
        block = {"coverage": cov, "width": 100.0, "per_station_coverage": [cov, cov]}
        return {"disjoint_calibration": block, "legacy_train_station_calibration": block, "test_mae": 5.0}
    splits = [split(0.88), split(0.90), split(0.92)]
    agg = c1.aggregate(splits)["disjoint_calibration"]["coverage_over_splits"]
    assert agg["mean"] == pytest.approx(0.90)
    assert agg["sd"] == pytest.approx(np.std([0.88, 0.90, 0.92], ddof=1), abs=1e-4)
