"""Integrity of the committed C1, C2 and C3 result files.

Checks that station sets are disjoint and the right size, that stored summary numbers agree with the
per-split data they were computed from, and (for datasets whose raw data is committed) that the C2
regions and distances can be recomputed independently from the station coordinates.
"""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), "results")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "experiments"))
import C1_rigorous_inductive_eval as c1  # noqa: E402
import C2_region_holdout_distance as c2  # noqa: E402

DOMAINS = list(c1.DOMAINS)
COMMITTED_DATA = ["delhi_air_quality", "beijing_air_quality", "ghcn_weather"]   # raw data is in the repo


def load(name):
    return json.load(open(os.path.join(RESULTS, name)))


@pytest.mark.parametrize("domain", DOMAINS)
def test_c1_station_sets_are_disjoint_and_sized(domain):
    d = load(f"exp_C1_{domain}.json")
    spec = c1.DOMAINS[domain]
    assert len(d["splits"]) == spec["splits"], "the run should have completed every split"
    for s in d["splits"]:
        cal, test = set(s["cal_stations"]), set(s["test_stations"])
        assert not cal & test
        assert len(cal) == spec["n_cal"] and len(test) == spec["n_test"]
        assert s["n_train"] + len(cal) + len(test) == d["n_stations"]
        assert len(s["disjoint_calibration"]["per_station_coverage"]) == spec["n_test"]


@pytest.mark.parametrize("domain", DOMAINS)
def test_c1_split_coverage_equals_mean_of_station_coverage(domain):
    """Every test station has the same number of scores, so the two must agree up to rounding."""
    for s in load(f"exp_C1_{domain}.json")["splits"]:
        for key in ("disjoint_calibration", "legacy_train_station_calibration"):
            block = s[key]
            assert np.mean(block["per_station_coverage"]) == pytest.approx(block["coverage"], abs=6e-4)
            assert 0.0 <= block["coverage"] <= 1.0


@pytest.mark.parametrize("domain", DOMAINS)
def test_c1_stored_aggregate_matches_recomputation(domain):
    d = load(f"exp_C1_{domain}.json")
    fresh = c1.aggregate(d["splits"])
    for key in ("disjoint_calibration", "legacy_train_station_calibration"):
        assert d["aggregate"][key]["coverage_over_splits"]["mean"] == pytest.approx(
            fresh[key]["coverage_over_splits"]["mean"], abs=1e-9)


@pytest.mark.parametrize("domain", DOMAINS)
def test_c2_region_and_calibration_are_disjoint_and_sized(domain):
    d = load(f"exp_C2_{domain}.json")
    spec = c1.DOMAINS[domain]
    assert len(d["splits"]) == spec["splits"]
    for s in d["splits"]:
        region, cal = set(s["test_stations"]), set(s["cal_stations"])
        assert not region & cal
        assert len(region) == spec["n_test"] and len(cal) == spec["n_cal"]
        assert len(s["station_coverage"]) == len(s["test_d1"]) == spec["n_test"]
        assert min(s["test_d1"]) >= 0 and min(s["cal_d1"]) >= 0
        assert all(0.0 <= c <= 1.0 for c in s["station_coverage"])
        assert np.mean(s["station_coverage"]) == pytest.approx(s["coverage"], abs=6e-4)


@pytest.mark.parametrize("domain", COMMITTED_DATA)
def test_c2_regions_are_contiguous_and_distances_recompute(domain):
    plane, spacing = c2.get_plane_and_spacing(domain)
    d = load(f"exp_C2_{domain}.json")
    n = len(plane)
    for s in d["splits"]:
        nearest = np.argsort(np.linalg.norm(plane - plane[s["seed_station"]], axis=1))[:len(s["test_stations"])]
        assert set(nearest) == set(s["test_stations"]), "the region must be the seed station's nearest stations"
        train = np.setdiff1d(np.arange(n), s["test_stations"] + s["cal_stations"])
        d1, d3 = c2.distances_to_training(plane, np.array(s["test_stations"]), train, spacing)
        assert np.allclose(d1, s["test_d1"], atol=2e-4)
        assert np.allclose(d3, s["test_d3"], atol=2e-4)
        assert s["n_train"] == len(train)


@pytest.mark.parametrize("domain", ["delhi_air_quality", "ghcn_weather"])
def test_c3_values_are_valid_distances(domain):
    d = load(f"exp_C3_{domain}.json")
    tv = d["tv_pairs"]
    assert 0.0 <= tv["p10"] <= tv["median"] <= tv["p90"] <= 1.0
    assert 0.0 <= d["noise_floor_random_halves_median"] <= 1.0
    assert d["n_pairs"] == d["n_models"] * d["n_held_out_per_model"] * (d["n_held_out_per_model"] - 1) // 2
