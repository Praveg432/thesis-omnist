# Pre-registration: confirmation of the forecast-time calibration rule (experiment C1h)

Written and committed on 17 Nov 2026 **before** any C1h result exists. Thresholds may be tightened later,
never loosened. Results go to `FINALIZATION-RECORD.md`, Section 17, whatever they show.

## Why

Experiment C1f found that one calibration rule brought forecast-time coverage on Delhi and Beijing to 0.898 and
0.896. The rule was chosen after seeing those results (splits 0 to 9), so they do not count as evidence for it.
C1h tests the fixed rule on data that played no part in choosing it.

## The rule (fixed)

"Scaled seasonal": for a forecast issued at window t at a new station, take the calibration stations' absolute
errors from **earlier test years only**, at windows whose forecast origin lies within **45 days** (circular day of
year) of window t's origin; divide each error by the mean absolute forecast of its own window and station
(floored at 10% of the training mean); take the split-conformal quantile at 90% with the finite-sample correction;
the interval is the forecast plus or minus that quantile times the new station's mean absolute forecast. If fewer
than 2 matching windows exist, use all earlier windows. Implemented in `phase1-omnist/src/multiyear_calibration.py`
(`seasonal` rule) and `phase1-omnist/experiments/C1f_multiyear_calibration.py` (`scaled_predmag_seasonal`).

## Data not used for selection

- **Fresh station splits** 10 to 29 (20 splits; random seeds 1010 to 1029) on Delhi and Beijing. C1f used 0 to 9.
- **A network not used for selection:** NOAA weather, three test years (2020, 2021, 2022), each model trained on
  earlier years only, 20 splits (0 to 19).

Everything else is as in C1f: corrected coordinate frame, same model and training budget, first test year as
history only, first 25% of each later year's windows not scored.

## Hypotheses and pass rules

| ID | Hypothesis | Pass if |
|---|---|---|
| H1 | The rule gives nominal coverage on fresh splits | Mean coverage over splits within 0.02 of 0.90 on Delhi **and** Beijing |
| H2 | It transfers to a network not used for selection | Mean coverage within 0.02 of 0.90 on weather |
| H3 | OmniST's intervals are better than simple forecasts given the same rule | Mean interval score (Winkler, 90%) of OmniST below that of persistence and of seasonal-naive (7-day) under the same rule, paired over splits, 95% interval of the difference below 0, on each network |
| H4 | The rule improves on the same-year rule once coverage is accounted for | Mean interval score of the rule below that of the same-year rule, paired 95% interval below 0, on each network |

Interval score for an interval forecast ± h and outcome y: 2h + (2/0.1) · max(|y − forecast| − h, 0), averaged
over windows, stations and horizon steps; lower is better.

## Reporting

Every hypothesis is reported as pass or fail with the numbers. A failed H1 or H2 means the abstract's 89.8% and
89.6% are withdrawn and replaced by the confirmation figures. Exploratory analyses (other rules, hierarchical
conformal with more calibration stations) are labelled exploratory.
