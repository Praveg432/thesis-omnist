"""Integrity tests for the forecast-time calibration results (C1b to C1j, C2n).

They recompute every stored summary from the stored per-split values and check structural invariants that any
correct run must satisfy. They do not need raw data and do not retrain anything.
"""
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))
import C1_rigorous_inductive_eval as c1  # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
DOMAINS = list(c1.DOMAINS)
AIR_WEATHER = ["delhi_air_quality", "beijing_air_quality", "ghcn_weather"]
EXPECTED_C1H_SPLITS = {"delhi_air_quality": range(10, 30), "beijing_air_quality": range(10, 30), "ghcn_weather": range(0, 20)}
EXPECTED_C1I_SPLITS = {"delhi_air_quality": range(30, 50), "beijing_air_quality": range(30, 50), "ghcn_weather": range(20, 40),
                       "pemsd7_traffic": range(0, 20), "pemsbay_traffic": range(0, 20)}


def load(name):
    return json.load(open(os.path.join(RESULTS, name)))


def station_sets(domain, split, n_stations, offset=1000):
    spec = c1.DOMAINS[domain]
    perm = np.random.default_rng(offset + split).permutation(n_stations)
    test = np.sort(perm[:spec["n_test"]])
    cal = np.sort(perm[spec["n_test"]:spec["n_test"] + spec["n_cal"]])
    return test, cal


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("variant", ["exp_C1b_", "exp_C1b_norm_"])
def test_c1b_stations_follow_the_seed_and_summaries_recompute(domain, variant):
    d = load(f"{variant}{domain}.json")
    assert len(d["splits"]) == c1.DOMAINS[domain]["splits"]
    assert sorted(s["split"] for s in d["splits"]) == list(range(c1.DOMAINS[domain]["splits"]))
    for s in d["splits"]:
        test, cal = station_sets(domain, s["split"], d["n_stations"])
        assert s["test_stations"] == [int(i) for i in test] and s["cal_stations"] == [int(i) for i in cal]
        assert not set(s["test_stations"]) & set(s["cal_stations"])
        for proto in ("chronological", "same_window", "pooled"):
            r = s[proto]
            assert 0.0 <= r["coverage"] <= 1.0 and r["width"] > 0
            assert abs(np.mean(r["per_station_coverage"]) - r["coverage"]) < 2e-3
    for proto in ("chronological", "same_window", "pooled"):
        mean = np.mean([s[proto]["coverage"] for s in d["splits"]])
        assert abs(mean - d["aggregate"][proto]["coverage_over_splits"]["mean"]) < 1.5e-4


@pytest.mark.parametrize("domain", DOMAINS)
def test_chronological_never_has_fewer_scored_windows_than_the_warmup_rule_allows(domain):
    for s in load(f"exp_C1b_norm_{domain}.json")["splits"]:
        assert s["first_scored_window"] >= 1
        assert s["first_scored_window"] + s["n_scored_windows"] == s["n_windows"]
        assert s["first_scored_window"] == int(np.ceil(0.25 * s["n_windows"]))


@pytest.mark.parametrize("domain", AIR_WEATHER)
def test_c1h_splits_are_the_preregistered_fresh_ones_and_scores_are_consistent(domain):
    d = load(f"exp_C1h_{domain}.json")
    assert sorted(s["split"] for s in d["splits"]) == list(EXPECTED_C1H_SPLITS[domain])
    assert not set(EXPECTED_C1H_SPLITS[domain]) & set(range(0, 10)) or domain == "ghcn_weather"  # C1f used 0 to 9
    for s in d["splits"]:
        for method in ("omnist", "persistence", "seasonal_naive"):
            for rule in ("same_year", "scaled_seasonal"):
                r = s[method][rule]
                assert r["interval_score"] >= r["width"] - 1e-6, "an interval score can never be below the width"
                assert abs(np.mean(r["per_station_coverage"]) - r["coverage"]) < 2e-3


@pytest.mark.parametrize("domain", AIR_WEATHER)
def test_c1h_verdicts_recompute_from_split_values(domain):
    sp = load(f"exp_C1h_{domain}.json")["splits"]
    v = load("exp_C1h_verdicts.json")[domain]
    cov = np.array([s["omnist"]["scaled_seasonal"]["coverage"] for s in sp])
    assert abs(cov.mean() - v["coverage_scaled_seasonal"]["mean"]) < 6e-5
    hyp = "H2" if domain == "ghcn_weather" else "H1"
    assert v[hyp] == ("PASS" if abs(cov.mean() - 0.90) <= 0.02 else "FAIL")
    diff = np.array([s["omnist"]["scaled_seasonal"]["interval_score"] - s["persistence"]["scaled_seasonal"]["interval_score"] for s in sp])
    diff_sn = np.array([s["omnist"]["scaled_seasonal"]["interval_score"] - s["seasonal_naive"]["scaled_seasonal"]["interval_score"] for s in sp])
    t = 2.093  # t quantile, 19 degrees of freedom
    upper = lambda x: x.mean() + t * x.std(ddof=1) / np.sqrt(len(x))
    assert v["H3"] == ("PASS" if upper(diff) < 0 and upper(diff_sn) < 0 else "FAIL")
    same = np.array([s["omnist"]["scaled_seasonal"]["interval_score"] - s["omnist"]["same_year"]["interval_score"] for s in sp])
    assert v["H4"] == ("PASS" if upper(same) < 0 else "FAIL")


@pytest.mark.parametrize("domain", DOMAINS)
def test_c1i_splits_are_fresh_finite_and_consistent(domain):
    d = load(f"exp_C1i_{domain}.json")
    assert sorted(s["split"] for s in d["splits"]) == list(EXPECTED_C1I_SPLITS[domain])
    for s in d["splits"]:
        for name, r in s.items():
            if not isinstance(r, dict) or "coverage" not in r:
                continue
            assert np.isfinite(r["width"]) and np.isfinite(r["interval_score"]), "infinite intervals must never be reported"
            assert r["interval_score"] >= r["width"] - 1e-6
            assert 0.0 <= r["coverage"] <= 1.0


@pytest.mark.parametrize("domain", AIR_WEATHER)
def test_c1i_fixed_rule_is_the_same_rule_as_in_c1h_so_widths_are_comparable(domain):
    """Different splits, weekly origins: coverage may differ, but the rule's width must be in the same range."""
    h = np.mean([s["omnist"]["scaled_seasonal"]["width"] for s in load(f"exp_C1h_{domain}.json")["splits"]])
    i = np.mean([s["c1h_seasonal_scaled"]["width"] for s in load(f"exp_C1i_{domain}.json")["splits"]])
    assert 0.7 < i / h < 1.4


def test_online_selection_chose_only_candidate_rules():
    allowed = {"same_year", "all", "all_scaled", "c1h_seasonal_scaled", "same_year_scaled"}
    for domain in AIR_WEATHER:
        for s in load(f"exp_C1i_{domain}.json")["splits"]:
            assert set(s["online_selection"]["chosen_counts"]) <= allowed
            assert sum(s["online_selection"]["chosen_counts"].values()) == s["n_scored_windows"]


@pytest.mark.parametrize("domain", ["delhi_air_quality", "beijing_air_quality"])
def test_c1f_aggregate_recomputes(domain):
    d = load(f"exp_C1f_{domain}.json")
    for rule, agg in d["aggregate"].items():
        mean = np.mean([s["rules"][rule]["coverage"] for s in d["splits"]])
        assert abs(mean - agg["coverage_mean"]) < 6e-5


@pytest.mark.parametrize("domain", ["delhi_air_quality", "ghcn_weather", "pemsd7_traffic", "pemsbay_traffic"])
def test_hcp_results_have_finite_thresholds_and_enough_stations(domain):
    d = load(f"exp_C1g_hcp_{domain}.json")
    assert d["n_calibration_stations"] >= 9, "HCP at a 90% target is infinite below 9 calibration stations"
    for s in d["splits"]:
        assert s["rules"]["hcp_expanding"]["fraction_finite_windows"] == 1.0


def test_c2n_regions_and_calibration_sets_are_disjoint_and_sized():
    for domain in AIR_WEATHER:
        d = load(f"exp_C2n_{domain}.json")
        spec = c1.DOMAINS[domain]
        assert len(d["splits"]) == 20
        for s in d["splits"]:
            assert not set(s["test_stations"]) & set(s["cal_stations"])
            assert len(s["test_stations"]) == spec["n_test"] and len(s["cal_stations"]) == spec["n_cal"]
            assert s["n_train"] == d["n_stations"] - spec["n_test"] - spec["n_cal"]
            assert abs(np.mean(s["station_coverage"]) - s["coverage"]) < 2e-3


def test_corrected_frame_never_changes_the_station_splits():
    """C1b legacy and C1b norm must evaluate exactly the same stations, otherwise they are not comparable."""
    for domain in DOMAINS:
        a, b = load(f"exp_C1b_{domain}.json")["splits"], load(f"exp_C1b_norm_{domain}.json")["splits"]
        for x, y in zip(sorted(a, key=lambda s: s["split"]), sorted(b, key=lambda s: s["split"])):
            assert x["test_stations"] == y["test_stations"] and x["cal_stations"] == y["cal_stations"]
