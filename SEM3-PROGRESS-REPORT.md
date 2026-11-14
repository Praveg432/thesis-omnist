# M.Tech Project Progress Report (Semester 3)

**Indian Institute of Technology Patna — Department of Computer Science and Engineering**

| | |
|---|---|
| **Project Title** | Certified Topology-Invariant Spatiotemporal Forecasting with Trustworthy Uncertainty at Unseen Sensors, and Its Scaling to Large Networks |
| **Candidate** | Praveg Vashishtha |
| **ID No.** | IITP006424 |
| **Supervisor** | Pankaj Chaswal |
| **Program / Semester** | M.Tech (CSE) — Semester 3 Progress Report |
| **Hardware** | Apple M4 Pro (MPS, ~24 GB unified memory); single machine, no cluster |

> **Scope of this report.** This is a Semester-3 progress report. It documents the completed work,
> states its limits, and gives the plan for Semester 4. The full thesis after Semester 4 will follow
> the IIT Patna M.Tech Thesis Manual. The project has two phases: **Phase 1 (OmniST)**, completed and
> re-evaluated this semester, and **Phase 2 (scaling)**, planned for Semester 4.
>
> **Terminology.** "Certified coverage" in the title means finite-sample marginal coverage from split
> conformal prediction when stations are split at random into train, calibration and test sets, so
> that calibration and test scores are exchangeable across stations. It is checked empirically over
> many random splits. It is not a guarantee for every station and not a guarantee against arbitrary
> spatial dependence.

---

## 1. Introduction

Large sensor networks for air quality, road traffic, weather and power are used to forecast conditions
and drive decisions. Two properties decide whether a forecaster is usable in deployment.

1. **Resilience to a changing network.** Sensors fail, go offline, or are newly installed. The model
   must keep forecasting, including at locations with no sensor history, without retraining each time
   the layout changes.
2. **Usable uncertainty.** Decisions need a prediction interval with a stated coverage level, not a
   bare point estimate whose reliability is unknown.

Phase 1 builds a forecaster with both properties. Phase 2 aims to make it run at the scale of real
networks (thousands of sensors) and to study how its coverage behaves as the network grows.

## 2. Objectives and Scope

1. Design a forecaster whose computation has no structural dependence on the number of sensors.
   **(Phase 1: completed.)**
2. Equip it with conformal prediction intervals at unseen sensor locations and evaluate the coverage on
   real data from several domains, using random disjoint splits of stations. **(Phase 1: completed.)**
3. Make the engine sub-quadratic in the number of sensors and time-parallel, and measure memory and
   time against network size. **(Phase 2: planned.)**
4. Evaluate and improve per-station coverage with a localised calibration method, and study coverage
   as the network grows. **(Phase 2: planned.)**
5. Deliver a reusable, installable PyTorch package. **(Phase 2: planned.)**

**Out of scope.** The contribution is a calibrated, scalable system and an honest evaluation of its
coverage, not a point-accuracy record and not a new state-space model.

## 3. Related Work

The design sits among four lines of work (references in Section 8).

- **Spatiotemporal graph networks.** Fixed-adjacency models such as STGCN [1] and DCRNN [2] are
  accurate on a fixed sensor set but cannot predict at a newly added sensor.
- **Inductive kriging.** IGNNK [3] predicts at unseen locations but gives no coverage statement. Recent
  work shows that common kriging evaluation protocols leak spatial information and proposes a
  leakage-free partition that separates training, validation and testing in space and time [11].
- **Conformal prediction.** Split conformal prediction [4], [5] gives finite-sample coverage when
  calibration and test scores are exchangeable. Two directly relevant extensions exist: conformal
  prediction for inductive graph models, which corrects the shift in calibration scores caused by new
  nodes [9], and conformal prediction for spatially dependent data, which addresses failure of
  exchangeability under spatial dependence and scales through nearest-neighbour approximations [10].
  Neither is used in the present work yet; both are comparison points for Phase 2.
- **Efficient sequence and spatiotemporal models.** Selective state-space models [6] process
  sequences in linear time. STGformer [12] reports a 100-fold speedup and a 99.8% reduction in GPU
  memory against the STAEformer baseline during batch inference on a California road graph with
  8,600 sensors, and is evaluated on the LargeST benchmark [13].

The project's contribution is the combination: a topology-invariant forecaster whose interval
calibration is evaluated under random disjoint station splits, carried toward larger networks with
measured memory and time evidence. A full cited related-work chapter will appear in the thesis.

## 4. Work Completed in Semester 3: Phase 1 (OmniST)

### 4.1 Model formulation

Three design choices remove any structural dependence on the sensor count:

1. **Coordinate tokenisation.** Each sensor is embedded from its coordinates, with no positional index
   or fixed node count.
2. **k-nearest-neighbour spatial attention.** Each sensor attends to its nearest neighbours, selected
   from coordinates at every forward pass, so no precomputed adjacency matrix is needed.
3. **Per-sensor temporal processing.** A bidirectional GRU runs independently for each sensor, so
   adding or removing a sensor does not change any other sensor's representation.

With split-conformal calibration the model produces prediction intervals at coordinates never seen in
training. A locality property was verified numerically: a sensor's nonconformity score is unchanged by
sensors outside its neighbour set (prediction difference 8.9×10⁻⁸ after a far-away change). This is an
invariance property, not a proof of exchangeability.

### 4.2 Evaluation protocol (experiment C1)

The first evaluation used a fixed list of 3 to 7 held-out stations per dataset, the same in every seed,
and calibrated the conformal threshold on the residuals of the training stations. A preliminary review
pointed out two problems: training-station residuals are not exchangeable with unseen-station
residuals, and seed-to-seed spread on a fixed station set measures initialisation noise, not variation
across sensor sets. Experiment C1 therefore repeats the evaluation as follows.

- The stations are split at random into train, calibration and test sets. The model never sees the
  calibration or test stations.
- The conformal threshold is computed from the calibration stations; coverage is measured at the test
  stations. The same trained models are also evaluated with the old training-station calibration.
- The split is the unit of inference: results are the mean and 95% interval over random splits (20
  splits for the three small datasets, 6 for the two traffic datasets).
- Target coverage is 0.90. Scores are per-day absolute errors in original units.

### 4.3 Results

| Dataset | Stations (train / cal / test) | Splits | Coverage, disjoint calibration | Coverage, training-station calibration | Per-station coverage: mean / 10th percentile / minimum |
|---|---|:---:|---|:---:|---|
| Delhi PM2.5 | 21 / 8 / 8 | 20 | 0.893 [0.884, 0.901] | 0.901 | 0.893 / 0.840 / 0.777 |
| Beijing PM2.5 | 6 / 3 / 3 | 20 | 0.903 [0.895, 0.912] | 0.902 | 0.903 / 0.876 / 0.861 |
| NOAA weather | 18 / 6 / 6 | 20 | 0.906 [0.881, 0.931] | 0.888 | 0.906 / 0.772 / 0.654 |
| PeMSD7-M traffic | 168 / 30 / 30 | 6 | 0.876 [0.843, 0.909] | 0.890 | 0.876 / 0.718 / 0.519 |
| PeMS-BAY traffic | 235 / 45 / 45 | 6 | 0.892 [0.872, 0.913] | 0.887 | 0.892 / 0.808 / 0.402 |

Reading the table:

- Mean coverage over random splits is close to the 0.90 target in every dataset, and every interval
  contains 0.90. This supports the marginal coverage statement under the random-split protocol.
- Individual splits vary. The standard deviation over splits is 0.02 to 0.05, and in the weather data
  coverage ranged from 0.79 to 0.99. Only 33% to 55% of splits reached 0.90, which is what one expects
  when the mean sits near the target.
- Coverage is marginal. Some stations are badly under-covered (minimum per-station coverage 0.40 to
  0.86). This motivates the localised calibration planned for Phase 2.
- Calibrating on training stations gave similar average coverage on these data (the disjoint-station
  value minus the training-station value ranged from -0.014 to +0.018). The exchangeability concern
  did not produce a large average error here, but the assumption remains unsupported for that
  protocol.
- Test errors (mean absolute error, in each dataset's units) were 27.6 (Delhi), 49.3 (Beijing), 5.8
  (weather), 10.3 (PeMSD7-M) and 5.5 (PeMS-BAY).

### 4.4 Original-protocol results (kept as a record)

The first protocol gave coverage 0.914 ± 0.006 (Delhi, 10 seeds), 0.928 ± 0.003 (Beijing, 10),
0.919 ± 0.007 (weather, 10) and 0.915 ± 0.009 (PeMSD7-M, 6), where ± is the standard deviation over
seeds on the same fixed held-out stations. These are 1 to 2.5 points higher than the random-split
means in Section 4.3 and should not be read as the headline. The following original-protocol results
were not repeated under C1 and carry the stated caveats.

- **Simple interpolators.** Nearest neighbour, inverse-distance weighting, mean of k neighbours and a
  Gaussian process: OmniST's mean coverage was at or above 0.90 on all four datasets, and each
  interpolator's was below 0.90 on at least one. Thresholds were applied to means without intervals.
- **Learned kriging baseline.** Point error at unseen Delhi stations was 26.7 for OmniST against 34.0
  for IGNNK (21.5% lower; 5 seeds). IGNNK is the author's re-implementation, and equal tuning effort
  has not been verified.
- **Fixed-adjacency baseline.** A fixed-adjacency model cannot produce an output at a newly added
  sensor and fails when sensors are removed. This motivates the design; it is not evidence of better
  accuracy.
- **Drift over time.** A rolling adaptive conformal layer raised worst-window coverage on Delhi from
  0.498 to 0.962, at the cost of wider intervals.
- **Larger network.** PeMS-BAY coverage was 0.921, but with **7 held-out sensors in one fixed split**.
  Under C1 the same data give 0.892 over 6 random splits with 45 test sensors each.
- **Dropout robustness.** Dataset-mean coverage with 30% or 50% of sensors removed was 0.912 to 0.931
  under the original protocol; individual seeds went as low as 0.89.

### 4.5 Threats to validity and limitations

- **Marginal, not conditional coverage.** Per-station coverage varies widely (Section 4.3).
- **Exchangeability is assumed.** Spatial and temporal dependence can break it. C1 measures the
  outcome over random splits; it is not a proof.
- **Small station sets.** The Beijing and weather datasets have 12 and 30 stations, so each split
  tests 3 to 6 stations.
- **Coordinates.** The two traffic datasets use sensor coordinates reconstructed from the published
  distance matrix, not measured latitude and longitude.
- **Preprocessing.** Missing-value filling uses the full series. In the Delhi data 0.0000% of
  training-year entries and 0.0074% of test-year entries were invalid, so the effect is negligible
  there; it was not measured for the other datasets. The calendar dates of the Delhi series are
  declared in the loader (starting 1 January 2019); PM2.5 peaks in November to January under those
  dates, as expected for Delhi.
- **Year feature.** The year input is scaled against each dataset's own range, so the test year is
  encoded as 0.0. The temporal embedding is periodic, so 0.0 and 1.0 give the same embedding, and the
  test year aliases to the latest training year. A check that set the feature to 1.0 therefore
  changed nothing, and it was uninformative by construction. No effect on results was found; a better
  year encoding is a Semester-4 cleanup.
- **Baselines.** E-STGCN and IGNNK are the author's re-implementations.

### 4.6 Dissemination

The Phase-1 work has been released as a preprint [8] (arXiv:2611.04256). It has not been submitted to
any journal or conference. The code, experiment scripts and committed results for both phases are in
the public project repository [7].

## 5. Phase 2: Status of Existing Components

Phase 2 is planned work for Semester 4. Some components already exist from exploratory work, and the
review corrected what had been claimed for them.

### 5.1 Components and what has been measured

| Component | State | Evidence |
|---|---|---|
| Neighbour attention (cost proportional to sensors × neighbours) | Implemented | Output cosine similarity to exact attention is at least 0.99987 for N up to 2,000 on random tokens with shared weights. **No memory measurement exists and no speed advantage appeared**: at N=2,000 the two paths took 189 ms and 182 ms, and at small N the neighbour path was slower. |
| State-space temporal block | Implemented as a **sequential** scan | About 2.0 to 2.2 times slower than the GRU at sequence lengths 60, 240 and 960 (29.0 vs 14.0 ms, 115.7 vs 53.3 ms, 462.3 vs 233.7 ms). No time-parallel advantage exists. Only the step size is input-dependent. |
| Localised calibration | **Not implemented** | Planned (work package WP1). |
| First parity check (V1) | Preliminary | 3 seeds, Delhi: the rebuilt engine had MAE 65.62 against 64.56 and coverage 0.944 against 0.948. The pass criteria were too permissive to be informative (the coverage band was widened to [0.723, 1.028], accuracy tolerance was 10%, calibration used training stations), so this is not evidence of parity. |

### 5.2 Defects found and fixed

- A cache of neighbour indices used a key built from the coordinate sum and spread, so two different
  sensor layouts with equal sum and spread (for example two nodes swapped) could silently share
  neighbours. The key is now a hash of the exact coordinates, the cache is size-limited, and
  regression tests cover both. The committed V1 and V2 numbers were not affected.
- Descriptions of the state-space block as a parallel scan and of the attention equivalence as proven
  were incorrect and have been corrected throughout.
- A corrected parity gate (V1b) replaces V1: random calibration stations disjoint from the test
  stations, an equivalence test on paired per-seed differences with margins fixed in advance (5% of
  baseline error, 0.03 in coverage), 10 seeds, and interval widths reported. It has been smoke-tested
  only.

## 6. Plan for Semester 4

All acceptance criteria are fixed before the experiments are run, and each work package has a
fallback so that a negative result is still a thesis result.

| Package | Work | Acceptance criterion | Fallback |
|---|---|---|---|
| WP0 | Run V1b; check that the LargeST benchmark [13] (8,600 sensors) is usable; fix a timing baseline | V1b verdict recorded; data decision made | Decide the state-space line and data plan from the outcome |
| WP1 | Localised calibration; compare with [9] and [10] | Over at least 20 random splits on three datasets, mean coverage within 0.02 of 0.90 and improved 10th-percentile per-station coverage without widening intervals by more than 10% | Empirical study of when random-split conformal coverage holds and fails |
| WP2 | Parallel prefix scan for the state-space block | Matches the sequential version within 1e-4 for T up to 960 and is no slower than the GRU for T ≥ 240 | Drop the time-parallel claim |
| WP3 | Peak memory and time against N (325 to 8,600); neighbour-set agreement | At least 5× lower peak memory than exact attention at N ≥ 2,000; agreement ≥ 0.99 | Restrict the claim to equivalence |
| WP4 | Coverage against N on a larger real network | Mean coverage within 0.02 of 0.90 at every size, spread over at least 10 splits reported | State evidence to 325 sensors only; never use replicated sensors to claim coverage |
| WP5 | Stronger baselines with equal tuning; leakage-free protocol [11] | Official-code IGNNK or equivalent compared at equal budget | Cut first if time is short |
| WP6 | Reusable PyTorch package with tests and an example | Installs in a fresh environment and reproduces the Delhi result within the spread over splits | Scope to forecaster plus calibration |
| WP7 | Thesis in the IIT Patna format, 60 to 70 pages, at least 30 verified references | Supervisor review | None |

Timeline: month 1 WP0; month 2 WP1; month 3 WP2 and WP3; month 4 WP4 and WP5; month 5 WP6; month 6
WP7 and the final literature re-scan.

## 7. Summary of Progress

Phase 1 is complete. The forecaster was formulated, validated on four real datasets, released as a
preprint, and re-evaluated this semester over random disjoint station splits. Mean coverage was close
to the 0.90 target on all five networks, with considerable variation between splits and between
stations. Phase 2 is planned: a neighbour attention that matches exact attention in output and a
sequential state-space block exist, but neither has shown a speed or memory advantage yet, localised
calibration is not implemented, and the first parity check was too permissive to count. A preliminary
review identified these points, and the code, documents and plan have been corrected accordingly. The
Semester-4 plan has acceptance criteria and fallbacks for each work package.

---

## 8. References

[1] B. Yu, H. Yin, and Z. Zhu, "Spatio-Temporal Graph Convolutional Networks: A Deep Learning
Framework for Traffic Forecasting," in *Proc. 27th Int. Joint Conf. Artificial Intelligence (IJCAI)*,
2018, pp. 3634–3640.

[2] Y. Li, R. Yu, C. Shahabi, and Y. Liu, "Diffusion Convolutional Recurrent Neural Network:
Data-Driven Traffic Forecasting," in *Proc. Int. Conf. Learning Representations (ICLR)*, 2018.

[3] Y. Wu, D. Zhuang, A. Labbe, and L. Sun, "Inductive Graph Neural Networks for Spatiotemporal
Kriging," in *Proc. AAAI Conf. Artificial Intelligence*, vol. 35, no. 5, 2021, pp. 4478–4485.

[4] V. Vovk, A. Gammerman, and G. Shafer, *Algorithmic Learning in a Random World*. New York, NY,
USA: Springer, 2005.

[5] A. N. Angelopoulos and S. Bates, "A Gentle Introduction to Conformal Prediction and
Distribution-Free Uncertainty Quantification," *Foundations and Trends in Machine Learning*, vol. 16,
no. 4, pp. 494–591, 2023.

[6] A. Gu and T. Dao, "Mamba: Linear-Time Sequence Modeling with Selective State Spaces,"
*arXiv:2312.00752*, 2023.

[7] P. Vashishtha, "thesis-omnist: Certified Topology-Invariant Spatiotemporal Forecasting and Its
Scaling (project repository)," 2026. [Online]. Available:
https://github.com/Praveg432/thesis-omnist

[8] P. Vashishtha, "OmniST: Topology-Invariant Spatiotemporal Forecasting with Guaranteed-Coverage
Uncertainty at Unseen Sensor Locations," *arXiv:2611.04256*, 2026. [Online]. Available:
https://arxiv.org/abs/2611.04256

[9] S. H. Zargarbashi and A. Bojchevski, "Conformal Inductive Graph Neural Networks," in *Proc. Int.
Conf. Learning Representations (ICLR)*, 2024. [Online]. Available: https://arxiv.org/abs/2407.09173

[10] A. B. Sen and A. Saha, "Conformal Prediction for Spatially Dependent Data via Sequential
Whitening," *arXiv:2610.10168*, 2026. [Online]. Available: https://arxiv.org/abs/2610.10168

[11] C. Yang, C. Zhao, H. Zhao, Y. He, C. Wang, and J. Fan, "Leakage-Free Evaluation and
Distribution-Robust Spatio-Temporal Graph Learning for Inductive Kriging," *Pattern Recognition*,
2026, doi: 10.1016/j.patcog.2026.114638. [Online]. Available: https://arxiv.org/abs/2509.23631

[12] H. Wang, J. Chen, T. Pan, Z. Dong, L. Zhang, R. Jiang, and X. Song, "STGformer: Efficient
Spatiotemporal Graph Transformer for Traffic Forecasting," *arXiv:2410.00385*, 2024. [Online].
Available: https://arxiv.org/abs/2410.00385

[13] X. Liu, Y. Xia, Y. Liang, J. Hu, Y. Wang, L. Bai, C. Huang, Z. Liu, B. Hooi, and R. Zimmermann,
"LargeST: A Benchmark Dataset for Large-Scale Traffic Forecasting," in *Advances in Neural Information
Processing Systems (NeurIPS)*, 2023. [Online]. Available: https://arxiv.org/abs/2306.08259

---

## Appendix A: Supplementary Results

**A.1 Phase 1, random-split evaluation (C1), additional statistics.** Target coverage 0.90.

| Dataset | Standard deviation over splits | Range over splits | Fraction of splits at or above 0.90 | Mean interval width | Test MAE |
|---|:---:|:---:|:---:|:---:|:---:|
| Delhi PM2.5 | 0.019 | 0.860 to 0.934 | 0.35 | 119.8 | 27.6 |
| Beijing PM2.5 | 0.018 | 0.869 to 0.933 | 0.45 | 176.5 | 49.3 |
| NOAA weather | 0.054 | 0.788 to 0.990 | 0.55 | 24.8 | 5.8 |
| PeMSD7-M traffic | 0.031 | 0.830 to 0.917 | 0.33 | 44.1 | 10.3 |
| PeMS-BAY traffic | 0.019 | 0.863 to 0.917 | 0.33 | 22.9 | 5.5 |

**A.2 Phase 2, measurements on existing components.**

| Measurement | Setting | Result |
|---|---|---|
| Attention equivalence (V2) | Shared weights, random tokens, N = 37, 100, 325, 1,000, 2,000 | Minimum cosine similarity to exact attention 0.99987 |
| Attention time (V2) | N = 325 / 1,000 / 2,000, one layer, batch 1 | Neighbour path 145 / 152 / 189 ms; exact path 194 / 225 / 182 ms |
| State-space block vs GRU (T1) | T = 60 / 240 / 960, batch 4, 37 nodes, two layers | State-space 29.0 / 115.7 / 462.3 ms; GRU 14.0 / 53.3 / 233.7 ms |
| First parity check (V1, preliminary) | 3 seeds, Delhi | MAE 64.56 [60.73, 68.38] (baseline) vs 65.62 (rebuilt); coverage 0.948 vs 0.944 |

---

*Candidate: Praveg Vashishtha (ID No. IITP006424) | Supervisor: Pankaj Chaswal | Semester-3 Progress
Report | Project repository: https://github.com/Praveg432/thesis-omnist*
