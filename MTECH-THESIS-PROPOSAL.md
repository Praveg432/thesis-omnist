# M.Tech Thesis Proposal

## Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor Locations in Evolving Networks

**Candidate:** Praveg Vashishtha (ID No. IITP006424)
**Date:** November 2026
**Supervisor:** Pankaj Chaswal
**Program:** M.Tech, Computer Science and Engineering, IIT Patna
**Hardware envelope:** Apple M4 Pro (MPS, ~24 GB unified memory), single machine, no cluster
**Status:** title and abstract submitted and finalised 17 Nov 2026; this is the thesis of record.

> **One-sentence thesis.** Build and evaluate uncertainty quantification for forecasting at sensor
> locations a model was not trained on, in networks whose layout changes (Phase 1, complete), then
> establish where that coverage fails and whether it can be repaired, whether it holds as networks
> grow, and whether the intervals are useful against simple baselines (Phase 2).

**Terminology.** "Calibrated coverage" means marginal coverage from split conformal prediction, with calibration on
stations the model never saw. Stations are split at random into train, calibration and test sets, so
a test station is exchangeable with the calibration stations. The exchangeable unit is the station,
not the individual score: scores within a station are dependent and the conformal quantile pools
them, so the coverage statement is approximate, and the approximation improves with the number of
calibration stations (8 in the Delhi experiments, 3 in Beijing). It is checked empirically over many
random splits. It is not a guarantee for every station and not a guarantee against arbitrary spatial
dependence. The title is subject to the supervisor's approval.

---

## 0. Scope and status of the two phases

- **Phase 1: OmniST.** A topology-invariant forecaster with conformal intervals at unseen sensors.
  **Built and validated** on four real datasets from three domains, and re-evaluated after review
  under a stricter protocol (Section 2). Released as a **preprint (arXiv:2611.04256)**, not submitted
  to any venue. It is a timestamped record of thesis work, not external prior art.
- **Phase 2: OmniST-Scale.** Three open questions: where coverage at a new site fails and whether
  calibration that accounts for the site's position can repair it; whether the approach holds, in
  coverage and compute, as networks grow; and whether the intervals are useful against simple
  baselines. **Planned for Semester 4; the scope is proposed and pending supervisor approval.**
  Measured so far (`phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`): neighbour attention matches
  exact attention in output and uses about 17 times less inference memory at 8,000 sensors, with no
  gain below about 1,000; the state-space block brought no speed gain and is dropped; on real traffic
  the intervals are narrower than persistence but wider than a seasonal forecast. A first parity check
  is preliminary and is replaced by a stricter one that has not been run. The authoritative Phase 2 plan, rewritten on 26 Nov 2026 after
  Phase 1 closed, is `THESIS-COMPLETION-PLAN.md`; Section 3 below summarises it.

---

## 1. The problem

Cities and states depend on large sensor networks (air quality, traffic, weather, power) to forecast
conditions and act on them. Two properties decide whether such a system is deployable.

1. **The network is not fixed.** Sensors fail, go offline, or are newly installed. The model must keep
   forecasting, including at locations with no sensor history, without retraining each time the
   topology changes.
2. **A point forecast is not enough.** A public-health advisory or a traffic action needs an interval
   with a stated coverage level. A confident but wrong forecast is worse than none.

---

## 2. Phase 1: OmniST (built, validated, preprinted)

Three design choices remove any structural dependence on the sensor count `N`:

- **Coordinate tokenisation.** Each sensor is embedded from its coordinates, with no positional index.
- **k-nearest-neighbour spatial attention.** Neighbours are selected from coordinates at every forward
  pass, so the graph adapts to whatever sensors are present.
- **Per-node temporal processing.** A bidirectional GRU runs independently per node.

With split-conformal calibration this gives prediction intervals at coordinates never seen in
training. A locality property was verified: each node's nonconformity score is unchanged by nodes
outside its neighbour set (far-change prediction difference 8.9×10⁻⁸). That is a statement about
invariance, not about exchangeability.

### 2.1 Primary evidence: random disjoint-station evaluation (experiment C1)

A review found that the original experiments (Section 2.2) calibrated on the residuals of the training
stations and tested on 3 to 7 fixed held-out stations. Experiment C1 repeats the evaluation with
stations split at random into train, calibration and test sets, with the model never seeing the
latter two, over many splits. Target coverage 0.90. The 95% interval is over splits.

| Dataset | Stations (train / cal / test) | Splits | Coverage, disjoint calibration | Same models, training-station calibration | Per-station coverage: mean / 10th percentile / minimum |
|---|---|:---:|---|---|---|
| Delhi PM2.5 | 21 / 8 / 8 | 20 | 0.893 [0.884, 0.901] | 0.901 | 0.893 / 0.840 / 0.777 |
| Beijing PM2.5 | 6 / 3 / 3 | 20 | 0.903 [0.895, 0.912] | 0.902 | 0.903 / 0.876 / 0.861 |
| NOAA weather | 18 / 6 / 6 | 20 | 0.906 [0.881, 0.931] | 0.888 | 0.906 / 0.772 / 0.654 |
| PeMSD7-M traffic | 168 / 30 / 30 | 6 | 0.876 [0.843, 0.909] | 0.890 | 0.876 / 0.718 / 0.519 |
| PeMS-BAY traffic | 235 / 45 / 45 | 6 | 0.892 [0.872, 0.913] | 0.887 | 0.892 / 0.808 / 0.402 |

What this shows:
- Mean coverage over random splits is close to the target in every dataset, and every interval
  contains 0.90, so the results are consistent with the nominal level. Three of the five point
  estimates sit below it (by 0.7 to 2.4 points), so mild under-coverage is possible and is not
  excluded.
- Individual splits vary: the standard deviation over splits is 0.02 to 0.05, and in the weather data
  coverage ranged from 0.79 to 0.99. Only 33% to 55% of splits reached 0.90, as expected when the
  mean is near the target.
- Coverage is marginal. Individual stations can be badly under-covered (minimum 0.40 to 0.86, tenth
  percentile 0.72 to 0.88). Per-station coverage is contribution A of Phase 2.
- Calibrating on training stations, as the original experiments did, gave similar average coverage
  here (disjoint-calibration coverage minus training-station coverage ranged from -0.014 to +0.018
  across the five datasets). The review's concern about exchangeability did not translate
  into a large average error on these data, but it remains an unsupported assumption.

### 2.2 Original protocol, kept as the record

Coverage 0.914 (Delhi), 0.928 (Beijing), 0.919 (weather), 0.915 (PeMSD7-M) from 10 or 6 seeds with the
same 3 to 5 held-out stations in every seed, so the spread reflects initialisation only. These are
1 to 2.5 points higher than the random-split means above and should not be quoted as the headline.
Other original-protocol results, none re-tested under C1:
- Four simple interpolators (nearest neighbour, inverse-distance weighting, mean of k, Gaussian
  process): OmniST's mean coverage was at or above 0.90 on all four datasets and each interpolator's
  was below 0.90 on at least one. Thresholds were applied to means without intervals.
- Point error 21.5% lower than a learned kriging baseline (IGNNK) on Delhi. IGNNK is the author's
  re-implementation, and equal tuning effort has not been verified.
- A fixed-adjacency model cannot predict at unseen sensors or run when sensors are dropped. This
  motivates the design; it is not evidence of better accuracy.
- Drift: a rolling adaptive conformal layer raised worst-window coverage from 0.498 to 0.962, at the
  cost of wider intervals.
- Large network: coverage 0.921 on PeMS-BAY with **7 held-out sensors in one fixed split**. Under C1
  the same data give 0.892 over 6 random splits with 45 test sensors each.

### 2.3 Does distance from the training network matter? (experiments C2 and C3)

Experiment C2 holds out a contiguous region of stations, calibrates on stations outside it, and
measures per-station coverage against the distance to the nearest training station, in units of the
network spacing, using the variation within each station across splits. A distance effect appears only
in the sparse weather network: coverage falls by 0.0136 per extra spacing [95% interval -0.0221,
-0.0063], from about 0.93 in the nearest third of stations to 0.84 in the farthest third. In Delhi,
Beijing, PeMSD7-M and PeMS-BAY the within-station slopes are within 0.004 of zero, although the
held-out regions of Delhi, PeMSD7-M and PeMS-BAY sat 1.7 to 13 times farther from the network than the
calibration stations. Region-holdout coverage was 0.899, 0.893, 0.876, 0.885 and 0.914 (Delhi,
Beijing, weather, PeMSD7-M, PeMS-BAY), with a split-to-split standard deviation of 0.088 in the
weather data. Only one sparse network of 30 stations was available.

**Correction (26 Nov 2026).** These C2 runs used the coordinate embedding's Delhi constants, which put the
weather inputs about 650 units outside the intended range. Re-run with a frame built from the training stations,
the weather slope is -0.0023 per spacing [-0.0116, +0.0079], an interval that includes zero, and the nearest and
farthest thirds are 0.894 and 0.858. The distance effect reported above is therefore not established
(`SEM3-PROGRESS-REPORT.md`, Section 4.4).

Experiment C3 estimates the total-variation distance between the score distributions of different
stations, which a non-exchangeable conformal coverage bound would charge against coverage. It was 0.12
(median) in Delhi and 0.18 in the weather data, no larger than the 0.13 noise floor obtained by
splitting one station's scores into random halves, and it did not grow with distance in the weather
data. A total-variation bound would therefore be vacuous at about 360 dependent scores per station.

### 2.4 Limits that define Phase 2

1. Exact attention needs O(N²) memory.
2. The temporal model is a sequential GRU.
3. Coverage has been checked only up to 325 real sensors. The two traffic datasets use coordinates
   reconstructed from the distance matrix, not measured latitude and longitude.
4. Coverage is marginal, with large per-station spread (Section 2.1).
5. Dropout robustness (30 to 50% of sensors removed) was shown under the original protocol only.
6. The coordinate embedding was centred and scaled with constants fixed for Delhi. This is fixed (a frame from
   the training stations), and its effect on accuracy, width and the distance result is measured in the progress
   report, Section 4.6.
7. Forecast-time calibration under-covers on air quality unless earlier years' errors are used; the repaired
   rule was confirmed in two pre-registered rounds (progress report, Sections 4.3a to 4.3d).
8. A coordinate-free GRU shared across sensors matches the architecture's accuracy, so the contribution is the
   calibration and its evaluation, not the architecture.

---

## 3. Phase 2 (planned; scope proposed, pending supervisor approval)

> **Research question.** Can one forecasting system give valid and useful intervals at a sensor across its
> lifecycle, from the day it is installed (no history) through its warm-up to a full history, using only
> information available at forecast time, and where does that fail?

The full plan, with acceptance criteria, fallbacks and a week-by-week schedule, is `THESIS-COMPLETION-PLAN.md`.
Every step gets a dated pre-registration before its first run. The plan rests on two pre-registered feasibility
rounds (`phase2-omnist-scale/feasibility/`): masked-station training forecasts sensors with no history 16.2% and
10.3% better than interpolating neighbours' forecasts on PeMS-BAY and PeMSD7-M (not on Delhi), with Day-0 coverage
of 0.879 and 0.880; the gain comes from masked training with neighbour pooling rather than the attention; and a
seasonal-residual head lowers PeMS-BAY interval score 37% below seasonal-naive for any backbone. Day-0 forecasting
itself is published (IGNNK, KITS, MoGERNN); the calibrated transition from Day 0 to warm is the part claimed as new.

| Step | Content | Fallback |
|---|---|---|
| S0. Training-window fix (first) | Pre-registered test of overlapping training windows on traffic (an exploratory run lowered PeMS-BAY error 19%) | Report the effect size |
| B. Lifecycle curve (headline, protected) | Masked training with partial histories; error, coverage and width against model-input history and calibration history (0 to 60 days), with own-data, generalized hierarchical and adaptive conformal; Delhi as negative control | The curves as measured |
| D. Useful intervals (protected) | Seasonal-residual and scale head as a backbone-agnostic head on PeMS-BAY and PeMSD7-M | State the limitation with a diagnosis |
| A. Per-station coverage (protected) | Station-level conformal on the scale-head scores, at full history and along the curve | Width against worst-station coverage |
| C. Does position matter? (gated) | Gate on a 300 to 1,500 station GHCN network; a geometry-aware method only if the gate passes | Powered characterisation (expected) |
| E. Scale and remaining comparisons | Memory, time and coverage against N; Phase 1 comparisons under the forecast-time rules; headline results repeated with the shared GRU | Evidence to 325 sensors |
| F. Alerts (cut candidate) | Conformal risk control at one air-quality network | Miss rate against calibration exceedances |
| G. Package and thesis (protected) | Installable package reproducing one table; thesis in the IIT Patna format | None |

Dropped: tuning the attention to beat the GRU on sensors with history, the time-of-day input (refuted), the
state-space block (about twice as slow as the GRU), a separate coverage-risk estimate, sensor placement,
cross-city transfer and online rule selection as a default.
## 4. Impact
- Intervals at sensors a model never saw, with coverage measured using only information available at forecast
  time, over random station splits and in pre-registered tests.
- Deployment guidance: which calibration rule to use for which kind of network, the width it costs, and how
  quickly a new sensor's intervals improve as it collects data.
- An honest answer to whether a sensor's position relative to the network matters, on a network large enough to
  tell.
- A reusable, tested package.
## 5. Timeline
| Period | Work | Status |
|---|---|---|
| Semester 3 | Phase 1 design and validation; preprint; random-split re-evaluation; forecast-time calibration with two pre-registered confirmations; coordinate defect found and fixed; distance re-test; verification | Done |
| Weeks 3 to 5 (30 Nov to 20 Dec) | S0 training-window test; lifecycle curve B on PeMS-BAY, PeMSD7-M and Delhi; preprint decision | Planned |
| Weeks 6 to 7 (21 Dec to 3 Jan) | Useful intervals D; per-station coverage A; chapters 1 to 3 | Planned |
| Weeks 8 to 10 (4 to 24 Jan) | GHCN network and gate for C; scale and comparisons E; alerts if on schedule; reproducibility pass | Planned |
| Weeks 11 to 12 (25 Jan to 7 Feb) | Writing, supervisor review, revisions, submission | Planned |
## 6. Risks and honest limits
- **Width.** Every repair of coverage costs width (25% to 60% on air quality); this is reported as a trade-off.
- **Data.** The GHCN subset may have too many gaps, and LargeST may be unusable. Replicated sensors are never used
  to claim coverage.
- **Traffic samples.** Traffic series cover weeks to months, so rules that use earlier years do not apply there.
- **Exchangeability.** Across stations it can break under spatial and temporal dependence; random splits measure the
  outcome, they do not prove validity.
- **Architecture.** A coordinate-free GRU matches its accuracy for sensors with history; claims are about
  calibration and the Day-0 to warm transition, not the model.
- **Lifecycle scope.** No Day-0 advantage was found on Delhi, so the lifecycle claim is scoped to road networks;
  Day-0 coverage is about 2 points under target so far.
- **Baselines.** E-STGCN and IGNNK are re-implementations; official code is planned (E).
- **Scope.** Alerts and compute scaling are cut first if time runs short.
## 7. Expected contributions
1. An evaluation protocol for coverage at unseen sensors that uses only information available at forecast time, and
   the finding that the common same-period protocol overstates it (Phase 1).
2. Calibration rules that restore forecast-time coverage, matched to network type and confirmed in pre-registered
   tests, with their width cost (Phase 1, extended in Phase 2, A).
3. Calibrated forecasting across a sensor's lifecycle, from no history to warm (B, headline), and per-station
   coverage and its cost (A).
4. A powered test of whether position relative to the network matters (C), and of whether the intervals beat simple
   forecasts on traffic (D).
5. Scale measurements, a corrected record of the Phase 1 comparisons, and open, reproducible code (E, G).
---
### Appendix: provenance

- **Phase 1:** `phase1-omnist/` (`README.md`, `FINDINGS-AND-IMPACT.md`, `RESULTS-INDEX.md`, committed
  `results/*.json`, `paper/`); preprint arXiv:2611.04256. Primary evidence:
  `phase1-omnist/experiments/C1_rigorous_inductive_eval.py` and `phase1-omnist/results/exp_C1_*.json`.
  Distance experiments: `phase1-omnist/experiments/C2_region_holdout_distance.py`,
  `phase1-omnist/experiments/C3_score_shift_vs_distance.py`,
  `phase1-omnist/results/exp_C2_analysis.json` and
  `phase1-omnist/results/exp_C3_delhi_air_quality.json`.
- **Phase 2:** `phase2-omnist-scale/` (`phase2-omnist-scale/README.md`,
  `phase2-omnist-scale/docs/RESEARCH-PLAN.md`, `phase2-omnist-scale/docs/VETTING-REPORT.md`,
  `phase2-omnist-scale/experiments/V1_ssm_matches_omnist.py`,
  `phase2-omnist-scale/experiments/V1b_parity_equivalence.py`,
  `phase2-omnist-scale/experiments/V2_attention_equivalence.py`,
  `phase2-omnist-scale/experiments/T1_ssm_vs_gru_timing.py`,
  `phase2-omnist-scale/results/V1_ssm_matches_omnist_results.json`,
  `phase2-omnist-scale/results/V2_attention_equivalence_results.json`,
  `phase2-omnist-scale/results/T1_ssm_vs_gru_timing.json`).
- **Claim to evidence map:** `EXPERIMENTS-INDEX.md`.

*External-source content was rephrased for compliance with licensing restrictions. Novelty verdicts
rest on abstracts read in November 2026 and must be re-scanned before submission.*
