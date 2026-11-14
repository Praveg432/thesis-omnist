# M.Tech Thesis Proposal

## Certified Topology-Invariant Spatiotemporal Forecasting with Trustworthy Uncertainty at Unseen Sensors, and Its Scaling to Large Networks

**Candidate:** Praveg Vashishtha (ID No. IITP006424)
**Supervisor:** Pankaj Chaswal
**Program:** M.Tech, Computer Science and Engineering, IIT Patna
**Hardware envelope:** Apple M4 Pro (MPS, ~24 GB unified memory), single machine, no cluster

> **One-sentence thesis.** Design a spatiotemporal forecaster that produces calibrated prediction
> intervals at unseen sensor locations and keeps working as the network changes (Phase 1), then make
> its engine scale toward thousands of sensors and study how its coverage behaves as the network
> grows (Phase 2).

**Terminology.** "Certified" in the title means finite-sample marginal coverage from split conformal
prediction under a random, disjoint split of stations into train, calibration and test sets, where
calibration and test scores are exchangeable across stations. It is checked empirically over many
random splits. It is not a guarantee for every station, and it is not a guarantee against arbitrary
spatial dependence. Whether to keep the word in the title is the supervisor's decision.

---

## 0. Scope and status of the two phases

- **Phase 1: OmniST.** A topology-invariant forecaster with conformal intervals at unseen sensors.
  **Built and validated** on four real datasets from three domains, and re-evaluated after review
  under a stricter protocol (Section 2). Released as a **preprint (arXiv:2611.04256)**, not submitted
  to any venue. It is a timestamped record of thesis work, not external prior art.
- **Phase 2: OmniST-Scale.** Scaling the engine and studying coverage as the network grows.
  **Planned for Semester 4.** Existing: an implemented neighbour attention whose output matches exact
  attention on random inputs, and a state-space block that currently runs sequentially and is slower
  than the GRU. A first parity check exists but is preliminary and is replaced by a stricter one that
  has not been run. See `phase2-omnist-scale/docs/RESEARCH-PLAN.md` for work packages, acceptance
  criteria and fallbacks.

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
  contains 0.90. This supports the marginal coverage claim under the random-split protocol.
- Individual splits vary: the standard deviation over splits is 0.02 to 0.05, and in the weather data
  coverage ranged from 0.79 to 0.99. Only 33% to 55% of splits reached 0.90, as expected when the
  mean is near the target.
- Coverage is marginal. Individual stations can be badly under-covered (minimum 0.40 to 0.86, tenth
  percentile 0.72 to 0.88). This is the case for the localised calibration planned in Phase 2.
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

### 2.3 Limits that define Phase 2

1. Exact attention needs O(N²) memory.
2. The temporal model is a sequential GRU.
3. Coverage has been checked only up to 325 real sensors. The two traffic datasets use coordinates
   reconstructed from the distance matrix, not measured latitude and longitude.
4. Coverage is marginal, with large per-station spread (Section 2.1).
5. Dropout robustness (30 to 50% of sensors removed) was shown under the original protocol only.

---

## 3. Phase 2: OmniST-Scale (planned)

> **Research question.** Can the forecaster be made sub-quadratic in the number of sensors, with
> time-parallel temporal processing, while keeping accuracy and the random-split coverage behaviour of
> Phase 1, and how does that coverage behave as the network grows?

The work packages, with acceptance criteria and fallbacks fixed in advance, are in
`phase2-omnist-scale/docs/RESEARCH-PLAN.md`. In summary:

| Package | Content | Fallback if it fails |
|---|---|---|
| WP0 | Corrected parity gate V1b (10 seeds, paired equivalence); check that LargeST (8,600 sensors) is usable | Decide SSM line and data plan from the outcome |
| WP1 | Localised calibration; comparison with two published conformal methods | Empirical study of when random-split conformal coverage holds and fails |
| WP2 | Parallel prefix scan for the state-space block; must match the sequential version and be no slower than the GRU for T ≥ 240 | Drop the time-parallel claim |
| WP3 | Peak memory and time against N; neighbour-set agreement | Restrict the claim to equivalence |
| WP4 | Coverage against N on a larger real network | State coverage evidence to 325 sensors only |
| WP5 | Stronger baselines with equal tuning; leakage-free protocol | Cut first if time is short |
| WP6 | Reusable PyTorch package with tests and an example | Scoped to the forecaster plus calibration |
| WP7 | Thesis in IIT Patna format | None |

Current status of the existing Phase 2 components (details in `phase2-omnist-scale/docs/VETTING-REPORT.md`):
- Neighbour attention: output cosine similarity to exact attention at least 0.99987 on random tokens
  for N up to 2,000. No memory or speed advantage has been shown.
- State-space block: sequential, about 2.0 to 2.2 times slower than the GRU at T = 60, 240 and 960.
- First parity check (V1): preliminary. Its coverage gate accepted any value above 0.723.

---

## 4. Impact

- A forecaster that keeps producing intervals at sensors it never saw, with its coverage behaviour
  measured honestly over random station splits.
- A reusable PyTorch package for practitioners, if WP6 is completed.
- An evaluation of where marginal conformal coverage holds and where individual stations fall short.

---

## 5. Timeline

| Period | Work | Status |
|---|---|---|
| Semester 3 | Phase 1 design and validation; preprint; stricter C1 re-evaluation; review corrections | Done |
| Semester 4, month 1 | WP0: V1b, LargeST check, timing baseline; start WP1 | Planned |
| Month 2 | WP1 implementation and study | Planned |
| Month 3 | WP2 parallel scan; WP3 memory and time study | Planned |
| Month 4 | WP4 coverage against N; WP5 baselines | Planned |
| Month 5 | WP6 package; ablations | Planned |
| Month 6 | WP7 write-up; final literature re-scan; supervisor review | Planned |

---

## 6. Risks and honest limits

- **Data.** A large real network may not be usable. Replicating sensors is never used to claim
  coverage.
- **State-space block.** A pure PyTorch scan may not beat the GRU on MPS. The claim is dropped if so.
- **Calibration.** A localised variant may not improve per-station coverage. The thesis then reports
  the failure analysis.
- **Exchangeability.** Spatial and temporal dependence can break the assumption behind the coverage
  statement. C1 measures the outcome; it does not prove validity.
- **Baselines.** E-STGCN and IGNNK are the author's re-implementations.
- **Scope.** WP5 and the ablations are cut first if time runs short.

---

## 7. Expected contributions

1. OmniST, a topology-invariant forecaster with calibrated intervals at unseen sensors, validated on
   four real datasets with a random-split protocol (Phase 1).
2. An empirical characterisation of marginal versus per-station coverage under random disjoint-station
   splits (Phase 1, extended in Phase 2).
3. A neighbour attention with measured equivalence to exact attention and measured memory and time
   against N (Phase 2).
4. A localised calibration method, or a documented analysis of why it did not help (Phase 2).
5. A reusable PyTorch package (Phase 2).

---

### Appendix: provenance

- **Phase 1:** `phase1-omnist/` (`README.md`, `FINDINGS-AND-IMPACT.md`, `RESULTS-INDEX.md`, committed
  `results/*.json`, `paper/`); preprint arXiv:2611.04256. Primary evidence:
  `phase1-omnist/experiments/C1_rigorous_inductive_eval.py` and `phase1-omnist/results/exp_C1_*.json`.
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
