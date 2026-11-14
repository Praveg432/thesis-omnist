# M.Tech Thesis Proposal

## Topology-Invariant Spatiotemporal Forecasting with Calibrated Uncertainty at Unseen Sensors, and Its Scaling to Large Networks

**Candidate:** Praveg Vashishtha (ID No. IITP006424)
**Date:** November 2026
**Supervisor:** Pankaj Chaswal
**Program:** M.Tech, Computer Science and Engineering, IIT Patna
**Hardware envelope:** Apple M4 Pro (MPS, ~24 GB unified memory), single machine, no cluster

> **One-sentence thesis.** Design a spatiotemporal forecaster that produces calibrated prediction
> intervals at unseen sensor locations and keeps working as the network changes (Phase 1), then make
> its engine scale toward thousands of sensors and study how its coverage behaves as the network
> grows (Phase 2).

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
- **Phase 2: OmniST-Scale.** Calibration at newly placed sensors using the geometry of the site, and
  scaling toward larger networks. **Planned for Semester 4; the scope is proposed and pending
  supervisor approval.** Existing: an implemented neighbour attention whose output matches exact
  attention on random inputs, and a state-space block that currently runs sequentially and is slower
  than the GRU. A first parity check exists but is preliminary and is replaced by a stricter one that
  has not been run. See `phase2-omnist-scale/docs/RESEARCH-PLAN.md` for work packages, acceptance
  criteria, fallbacks and the novelty assessment.

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
  percentile 0.72 to 0.88). This is the case for the geometry-aware calibration planned in Phase 2, although Section 2.3
  shows that the distance effect is confined to the sparse network.
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
6. The coordinate embedding is centred and scaled with constants fixed for Delhi, so inputs for other
   regions are far outside the intended range. Training adapted, but cross-region transfer is
   untested and would need a local coordinate frame.

---

## 3. Phase 2: OmniST-Scale (planned; scope proposed, pending supervisor approval)

> **Research question.** When a sensor is placed at a new site, can its prediction interval be
> calibrated using the geometry of the site (distance to, and density of, the training sensors) so
> that coverage holds where distance matters without harming networks where it does not, and does the
> approach carry to larger networks?

The scope follows a novelty assessment of five candidate ideas against verified prior work and
experiments C2 and C3. Close prior art exists for localised and spatial conformal calibration
(Mao, Martin and Reich; Kim et al., 2026; Hore and Barber; Tibshirani et al.), so the contribution is
scoped as the combination for a deep inductive forecaster, with an honest finding about when it
matters, and not as a new theorem. The work packages, acceptance criteria, fallbacks and the full
assessment are in `phase2-omnist-scale/docs/RESEARCH-PLAN.md`. In summary:

| Package | Content | Fallback if it fails |
|---|---|---|
| WP0 | Corrected parity gate V1b (attention swap alone, and the full model); local coordinate frame; a large sparse network from GHCN-Daily; check that LargeST is usable | Smaller curated sparse network |
| WP1 | Geometry-aware calibration at new sites: spatial-block calibration pool, kernel localisation in geometry space with randomised localisation; compared with five published methods | Characterisation of when distance matters |
| WP2 | Per-site coverage-risk estimate from geometry using a threshold-specific shift (total variation is vacuous, C3), with an explicit assumption | Report that coverage loss is not predictable from geometry |
| WP3 | Peak memory and time against N; neighbour-set agreement; coverage against N on a large sparse network | Restrict the claim to equivalence |
| WP4 | Alerts with a controlled miss rate at unseen sites (conformal risk control) | Miss rate against calibration sample size |
| WP5 | Stronger baselines with equal tuning; leakage-free protocol; reusable PyTorch package | Cut baselines first |
| WP6 | Thesis in IIT Patna format | None |

Optional, if WP0 to WP4 are on schedule at the end of month 4: transfer between cities, a
time-parallel state-space block, and sensor placement guided by the coverage-risk estimate. The
state-space line was demoted because the current block is about twice as slow as the GRU.

Current status of the existing Phase 2 components (details in
`phase2-omnist-scale/docs/VETTING-REPORT.md`):
- Neighbour attention: output cosine similarity to exact attention at least 0.99987 on random tokens
  for N up to 2,000. No memory or speed advantage has been shown.
- State-space block: sequential, about 2.0 to 2.2 times slower than the GRU at T = 60, 240 and 960.
- First parity check (V1): preliminary. Its coverage gate accepted any value above 0.723.

---

## 4. Impact

- A forecaster that keeps producing intervals at sensors it never saw, with its coverage measured over
  random station splits.
- Deployment guidance: where the coverage at a new sensor can be trusted (dense networks, per C2) and
  where it needs care (sparse networks), with a per-site risk estimate if WP2 succeeds.
- Alerts with a controlled miss rate at unseen sites (WP4) and a reusable PyTorch package (WP5).

---

## 5. Timeline

| Period | Work | Status |
|---|---|---|
| Semester 3 | Phase 1 design and validation; preprint; stricter C1 re-evaluation; C2 and C3; review corrections; revised Phase 2 plan | Done |
| Semester 4, month 1 | WP0: V1b, local coordinate frame, large sparse network, LargeST check, timing baseline | Planned |
| Month 2 | WP1 design and implementation | Planned |
| Month 3 | WP1 evaluation; WP2 coverage-risk estimate | Planned |
| Month 4 | WP3 memory and coverage against N; WP4 alerts | Planned |
| Month 5 | WP5 baselines and package; optional extension if on schedule | Planned |
| Month 6 | WP6 write-up; final literature re-scan; supervisor review | Planned |

---

## 6. Risks and honest limits

- **The geometry effect is narrow.** C2 found a distance effect in one 30-station network. WP0 builds a
  larger sparse network to test it; if it does not replicate, WP1 becomes the characterisation
  fallback.
- **Data.** The GHCN subset may have too many gaps, and LargeST may be unusable. Replicating sensors
  is never used to claim coverage.
- **Small effective calibration size.** Localised calibration can leave few stations near a site; the
  method abstains when it cannot calibrate.
- **Conditional exchangeability** (the score depends on the site only through its geometry) may fail;
  it is tested, not assumed.
- **Exchangeability** across stations can break under spatial and temporal dependence. C1 measures
  the outcome; it does not prove validity.
- **Baselines.** E-STGCN and IGNNK are the author's re-implementations.
- **Scope.** Optional extensions are cut first if time runs short.

---

## 7. Expected contributions

1. OmniST, a topology-invariant forecaster with calibrated intervals at unseen sensors, validated on
   four real datasets with a random-split protocol (Phase 1).
2. A measured characterisation of when distance from the training network matters for coverage at a
   new sensor: it does in the sparse weather network and not in the dense networks tested (C2).
3. Geometry-aware calibration for newly placed sensors, with a per-site coverage-risk estimate, or a
   documented analysis of why it did not help (Phase 2).
4. A neighbour attention with measured memory and time against N, and coverage against N on a large
   sparse network (Phase 2).
5. Alerts with a controlled miss rate at unseen sites, and a reusable PyTorch package (Phase 2).

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
