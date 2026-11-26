"""The committed V1b parity result must follow its pre-registered decision rule."""
import json
from pathlib import Path

RESULT = Path(__file__).resolve().parents[1] / "results" / "V1b_parity_equivalence_results.json"


def test_shouldUsePreRegisteredMarginsAndSeeds():
    d = json.loads(RESULT.read_text())
    assert d["seeds"] == 10 and d["epochs"] == 15
    assert d["pre_registered"] == {"mae_margin_fraction": 0.05, "coverage_margin": 0.03, "ci_level": 0.9}


def test_shouldDeclareGoOnlyWhenBothIntervalsSitInsideTheirMargins():
    d = json.loads(RESULT.read_text())
    for gate, verdict in ((d["attention_only"], d["attention_only"]["verdict"]),
                          ({"mae_equivalence": d["mae_equivalence"], "coverage_equivalence": d["coverage_equivalence"]}, d["verdict"])):
        inside = all(-g["margin"] < g["ci"][0] and g["ci"][1] < g["margin"]
                     for g in (gate["mae_equivalence"], gate["coverage_equivalence"]))
        assert (verdict == "GO") == inside


def test_shouldHaveMaeMarginEqualToFivePercentOfTheExactAttentionBaseline():
    d = json.loads(RESULT.read_text())
    assert abs(d["mae_equivalence"]["margin"] - 0.05 * d["variants"]["gru+exact"]["mae"]["mean"]) < 1e-3
