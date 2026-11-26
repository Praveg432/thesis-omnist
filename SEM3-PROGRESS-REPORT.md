# M.Tech Project Progress Report (Semester 3)

**Indian Institute of Technology Patna — Department of Computer Science and Engineering**

| | |
|---|---|
| **Project Title** | Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor Locations in Evolving Networks |
| **Candidate** | Praveg Vashishtha |
| **ID No.** | IITP006424 |
| **Supervisor** | Pankaj Chaswal |
| **Date** | November 2026 |
| **Program / Semester** | M.Tech (CSE) — Semester 3 Progress Report |
| **Hardware** | Apple M4 Pro (MPS, ~24 GB unified memory); single machine, no cluster |

> **Scope of this report.** This is a Semester-3 progress report. It documents the completed work,
> states its limits, and gives the plan for Semester 4. The full thesis after Semester 4 will follow
> the IIT Patna M.Tech Thesis Manual. The project has two phases: **Phase 1 (OmniST)**, completed and
> re-evaluated this semester, and **Phase 2**, which asks where that coverage fails, whether it
> holds as networks grow, and whether the intervals are useful. Phase 2 is planned for Semester 4
> and partly measured (`phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`).
>
> **Revision note.** The abstract was submitted on 17 Nov 2026 and is revised here in one sentence, in three
> steps recorded in `SUBMISSION-TITLE-AND-ABSTRACT.md`, Section 6. (1) Its 87.6% to 90.6% coverage range comes from
> experiment C1, which calibrates on errors from the period it evaluates; the revised sentence adds the
> forecast-time range, 77.8% to 89.1% (Section 4.3a). (2) It then adds the result of calibrating on earlier
> years' errors. (3) That result is quoted from a test whose rule and pass criteria were committed before it
> was run (Section 4.3c). The coordinate embedding also used Delhi constants on every network, which inflated
> error and interval width on four networks (Section 4.6); same-window coverage moved by at most 0.011.
>
> **Terminology.** "Calibrated coverage" means marginal coverage from split conformal prediction, with calibration on
> stations the model never saw. Stations are split at random into train, calibration and test sets, so
> a test station is exchangeable with the calibration stations. The exchangeable unit is the station,
> not the individual score: scores within a station are dependent and the conformal quantile pools
> them, so the coverage statement is approximate, and the approximation improves with the number of
> calibration stations (8 in the Delhi experiments, 3 in Beijing). It is checked empirically over many
> random splits. It is not a guarantee for every station and not a guarantee against arbitrary spatial
> dependence.


---

## Abstract

Sensor networks for air quality, traffic and weather are used to forecast conditions and to act on them. Two features of real deployments make this hard. The networks change: sensors fail, go offline and are installed at new sites, so forecasts are often needed at locations the model has never seen. And a single predicted value is not enough to act on. An operator needs an interval that contains the true value with a stated probability, and needs to know where that statement can be trusted.

This thesis studies uncertainty quantification for forecasting at sensor locations a model was not trained on, in networks whose layout changes. Its first part, now complete and released as a preprint, built and evaluated OmniST. OmniST is a forecaster that does not depend on a fixed network layout, so it can predict at a new sensor without being retrained, and it attaches split conformal prediction intervals to its forecasts at unseen sensors. On five real networks covering air quality, weather and traffic, with stations split at random into training, calibration and test sets many times over, average coverage at unseen sensors was between 87.6% and 90.6% for a 90% target when calibrated on errors from the evaluation period itself. Using only errors available at forecast time, averages were between 77.8% and 89.1%, lowest in the two air-quality networks, where error roughly doubled through the test year and simple baselines fell short alike. Calibrating instead on earlier years' errors from the same season, scaled by the forecast's magnitude, gave 90.2% and 89.0% in a pre-registered test on fresh station splits, and 90.8% on the weather network, which played no part in choosing the rule. The evaluation also showed the limits of an average. Coverage varied from split to split, and some individual stations were covered far less often than the target. A fall in coverage with distance from the training network, 1.4 points per station spacing in one sparse weather network, disappeared once a coordinate-encoding defect was corrected. And the cost of the model's attention grows with the square of the number of sensors.

The remaining work asks three open questions. First, where does coverage at a new site fail, and can calibration that accounts for the site's position relative to the existing network repair it without harming sites that are already well covered? Second, does the approach continue to hold, in coverage and in compute, as networks grow from hundreds toward thousands of sensors? Third, are the intervals useful as well as calibrated, judged against simple forecasting baselines and in decision tasks such as threshold alerts with a controlled miss rate? Early measurements bear on the last two. Restricting attention to each sensor's nearest neighbours reduced the attention layer's inference memory about seventeenfold at 8,000 sensors, with no gain below about a thousand. Replacing the recurrent time model with a state-space block brought no speed gain on this hardware. On real traffic data the intervals were narrower than those of a persistence forecast but wider than those of a seasonal one.

The expected contributions are an evaluation protocol for coverage at unseen sensors that uses only information available at forecast time, a characterisation of where and why that coverage fails, the methods tried to repair it together with their measured effect, and open, reproducible code. Each question is answered by measurement against criteria fixed in advance, so a negative answer is reported as a finding of the thesis. Coverage statements throughout are marginal and approximate, not guarantees for every sensor.

**Keywords:** spatiotemporal forecasting; uncertainty quantification; conformal prediction; inductive forecasting; sensor networks.

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
3. Make coverage at a newly placed sensor valid at the station level and usable in its first weeks:
   hierarchical conformal prediction with the station as the exchangeable unit, and a cold-start to
   warm-up study as the sensor accumulates its own data. **(Phase 2: planned.)**
4. Establish where position relative to the network matters (a gated, geometry-aware calibration
   compared with published spatial conformal methods) and whether the intervals are useful against
   persistence and seasonal-naive forecasts. **(Phase 2: planned.)**
5. Measure memory, time and coverage as the network grows, demonstrate alerts with a controlled
   miss rate at unseen sites, and deliver a reproducible repository. **(Phase 2: planned.)**
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
  calibration and test scores are exchangeable. Extensions relevant here: hierarchical conformal prediction [21], [22]; weighted conformal
  prediction under covariate shift [14] and beyond exchangeability [15], randomised localisation for
  local guarantees [16], local spatial conformal prediction [17], cluster-aware calibration of
  spatiotemporal forecasts by sampling density [18], conformal prediction for inductive graph models
  [9], conformal prediction for spatially dependent data [10], and conformal risk control [19]. Station-level
  (hierarchical) conformal prediction [21] is used in Section 4.3b to 4.3d; the others are the comparison points and
  building blocks for Phase 2.
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
  contains 0.90, so the results are consistent with the nominal level. Three of the five point
  estimates sit below it (by 0.7 to 2.4 points: Delhi, PeMSD7-M, PeMS-BAY), so mild under-coverage is
  possible and is not excluded by these data.
- Individual splits vary. The standard deviation over splits is 0.02 to 0.05, and in the weather data
  coverage ranged from 0.79 to 0.99. Only 33% to 55% of splits reached 0.90, which is what one expects
  when the mean sits near the target.
- Coverage is marginal. Some stations are badly under-covered (minimum per-station coverage 0.40 to
  0.86). This motivates the geometry-aware calibration planned for Phase 2, although Section 4.4 shows the distance effect is confined to the sparse network.
- Calibrating on training stations gave similar average coverage on these data (the disjoint-station
  value minus the training-station value ranged from -0.014 to +0.018). The exchangeability concern
  did not produce a large average error here, but the assumption remains unsupported for that
  protocol.
- Test errors (mean absolute error, in each dataset's units) were 27.6 (Delhi), 49.3 (Beijing), 5.8
  (weather), 10.3 (PeMSD7-M) and 5.5 (PeMS-BAY).

All rows of the table above use the Delhi coordinate constants and C1's calibration rule; Sections 4.3a and 4.6 give
the forecast-time and corrected-frame results.

### 4.3a Calibration at forecast time (experiment C1b), diagnosis, and baselines
**Why.** C1 computes the conformal quantile from the calibration stations' errors over the same test
period it then scores, so the interval for a window uses errors from windows after it. That information
does not exist at forecast time. C1b keeps C1's splits, seeds and models and compares three rules on
identical scored windows (the first 25% of test windows are warm-up history and are not scored):
*chronological* (quantile from calibration-station errors of earlier windows only; the only rule usable at
forecast time), *same-window* (C1's rule) and *pooled* (one quantile over all windows). The decision rules
were fixed in the script before the run. Window t-1 ends where window t begins, so no future target is used.

| Dataset | Splits | C1, full period | C1b same-window | C1b chronological (Delhi constants) | C1b chronological (training-station frame) |
|---|:---:|:---:|:---:|:---:|:---:|
| Delhi PM2.5 | 20 | 0.893 | 0.896 | 0.818 | 0.811 |
| Beijing PM2.5 | 20 | 0.903 | 0.905 | 0.777 | 0.778 |
| NOAA weather | 20 | 0.906 | 0.883 | 0.889 | 0.888 |
| PeMSD7-M traffic | 6 | 0.876 | 0.871 | 0.869 | 0.891 |
| PeMS-BAY traffic | 6 | 0.892 | 0.893 | 0.869 | 0.881 |

- On Delhi and Beijing, chronological calibration under-covers badly: the 95% intervals over splits (Delhi constants) are
  [0.810, 0.826] and [0.772, 0.783]. On weather and the two traffic networks it is within 0.02 of 0.90
  once the coordinate frame is corrected. **The 87.6% to 90.6% range in the abstract as first submitted
  describes the C1 rule, not forecast-time calibration, for which the range is 77.8% to 89.1% with the corrected
  coordinate frame (77.7% to 88.9% with the Delhi constants). The abstract has been revised to say so.**
- **Diagnosis (experiment C1d, 10 splits, corrected frame).** Three candidate causes were measured.
  (H1) Error scale changes over the test period: the late-third mean error divided by the early-third
  mean error is 1.90 on Delhi and 2.11 on Beijing, and 0.87 on weather. (H2) Calibration stations are not
  representative: the test-station to calibration-station mean-error ratio is 1.03 (Delhi), 0.99 (Beijing)
  and 1.08 (weather), close to 1. (H3) Chronological coverage by third of the scored windows is 0.99,
  0.89, 0.50 on Delhi; 0.88, 0.73, 0.73 on Beijing; 0.84, 0.83, 0.94 on weather. The under-coverage tracks
  growth in error over time, not a mismatch between stations. That error grows with the pollution level
  is consistent with this but was not tested. The two air-quality test periods contain only 10 and 22
  windows, so a rule that estimates the scale from earlier windows has little to work with.
- **Baselines under the same rule** (experiment C1c; persistence and seasonal-naive forecasts with
  chronological conformal intervals on the same stations; corrected frame for OmniST). Seasonal period:
  7 days (air quality), one day (traffic); weather has none. Seasonal-naive is scored on the windows with a
  full period of history, a later subset of windows.

| Dataset | Method | Chronological coverage | Interval width | MAE |
|---|---|:---:|:---:|:---:|
| Delhi | OmniST / persistence / seasonal-naive | 0.811 / 0.772 / 0.788 | 90.0 / 111.9 / 117.7 | 28.5 / 37.7 / 37.9 |
| Beijing | OmniST / persistence / seasonal-naive | 0.778 / 0.806 / 0.773 | 138.7 / 186.2 / 202.6 | 48.5 / 51.9 / 62.8 |
| Weather | OmniST / persistence | 0.888 / 0.923 | 19.8 / 21.1 | 4.73 / 4.72 |
| PeMSD7-M | OmniST / persistence / seasonal-naive | 0.891 / 0.894 / 0.896 | 17.3 / 16.8 / 23.4 | 3.79 / 3.63 / 4.45 |
| PeMS-BAY | OmniST / persistence / seasonal-naive | 0.881 / 0.879 / 0.889 | 18.8 / 28.6 / 14.1 | 4.73 / 5.35 / 3.47 |

  The simple baselines under-cover in the same two networks, so the forecast-time shortfall belongs to the
  data and the calibration rule, not to OmniST. Against persistence, OmniST has lower error and narrower intervals on Delhi,
  Beijing and PeMS-BAY, and against seasonal-naive on the two air-quality networks. It does **not** beat persistence on
  PeMSD7-M (MAE 3.79 against 3.63) or weather (tie), and on PeMS-BAY its intervals are about 33% wider
  than seasonal-naive. Usefulness is therefore established against persistence on three networks and not
  established against seasonal forecasts.
- **A backbone control.** Separate experiments in the OmniST repository (10 random splits; 4 for the two traffic
  networks; corrected coordinate frame; copied with provenance to
  `phase1-omnist/results/external_controls_omnist_repo.json`) compare OmniST with a GRU shared across sensors that
  uses no coordinates and no attention. OmniST's point error relative to that GRU is +2.0% (Delhi), +0.9% (Beijing),
  -1.4% (weather), -1.5% (PeMSD7-M) and +0.9% (PeMS-BAY), and persistence is better than both on weather and
  PeMSD7-M. The ability to forecast at an unseen sensor therefore comes from sharing parameters across sensors; the
  coordinates and the attention layer show no measured accuracy benefit. The thesis contribution is the calibration and
  its evaluation, not the architecture, and the Semester-4 plan repeats the calibration results with the shared GRU as
  the backbone (Section 6, E).
### 4.3b Strengthening forecast-time coverage (experiments C1e to C1g)
Three directions were tried after Section 4.3a. All use the corrected coordinate frame and only information
available at forecast time. The rule recommended below was chosen after seeing these results; Section 4.3c
confirms it in a pre-registered test.

**More history: several test years (C1f).** Each network was re-evaluated over consecutive test years, with
the model retrained for each year on earlier years only (Delhi: 2021, 2022 and 2023; Beijing: two test
years). Calibration rules may then use the calibration stations' errors from earlier years. 10 random station
splits; windows of the first test year are history only.

| Rule (forecast-time only) | Delhi coverage | Delhi width | Beijing coverage | Beijing width |
|---|:---:|:---:|:---:|:---:|
| Same test year only (the C1b rule) | 0.824 | 105.1 | 0.774 | 137.3 |
| All earlier windows, across years | 0.873 | 134.0 | 0.869 | 173.3 |
| Earlier years, same season (within 45 days) | 0.926 | 143.1 | 0.915 | 233.6 |
| All earlier windows, errors scaled by forecast magnitude | 0.901 | 133.6 | 0.865 | 164.7 |
| Earlier years, same season, scaled by forecast magnitude | 0.898 | 136.7 | 0.896 | 221.0 |

- Using earlier years' errors removes most of the shortfall: the share of stations below 0.80 coverage falls
  from 23% to 1% on Delhi and from 77% to 0% on Beijing for every cross-year rule.
- The scaled seasonal rule is the only one within 0.01 of 0.90 on both networks (split halves: Delhi 0.912
  and 0.885, Beijing 0.899 and 0.892). The cost is width: 30% wider than the same-year rule on Delhi and 61%
  wider on Beijing. Whether the baselines gain as much from the same rule was not measured.
- A single-year pilot (C1e) had already shown that rolling and scaled rules recover part of the shortfall
  (Delhi 0.808 to 0.885, Beijing 0.774 to 0.860) but that no rule reaches 0.90 within one test year.

**Station-level (hierarchical) conformal (C1g).** Hierarchical conformal prediction [21] gives each
calibration station equal weight and needs at least 9 calibration stations at a 90% target. With 10
calibration stations and forecast-time history, it raised coverage from 0.809 to 0.924 on Delhi and from
0.873 to 0.985 on weather, with no station below 0.80, but widened the intervals by 90% and 41%. It is valid
but conservative at this number of stations, as its theory predicts (coverage up to 0.90 + 2/11). Errors within
a station are not exchangeable over time, so this is an empirical result, not the theorem's guarantee.

**Better point forecasts: residual head.** Making the model forecast the change from the last observed
value moved mean absolute error from 3.79 to 3.69 on PeMSD7-M (persistence 3.63), from 4.73 to 4.76 on
weather and from 4.73 to 5.04 on PeMS-BAY. It does not close the gap to persistence and is not adopted.

**What this changes.** The forecast-time shortfall on the air-quality networks is mostly a calibration
problem with too little history, and it is largely repairable by calibrating on earlier years, at a cost in
width. Weather was re-run over several years in Section 4.3c; the traffic series cover weeks to months, so a multi-year design does not apply to them (Section 4.3d).

### 4.3c Pre-registered confirmation (experiment C1h)
The rule of Section 4.3b (earlier years' errors from the same season, scaled by the forecast's magnitude) was
fixed and four hypotheses with pass rules were committed before any confirmation run
(`PRE-REGISTRATION-C1H.md`). The test used station splits not used to choose the rule (20 fresh splits on Delhi
and Beijing) and a network not used at all (weather, three test years, each model trained on earlier years only).
Interval score is the Winkler score of the 90% interval (width plus 20 times the distance of a miss); lower is
better. Persistence and seasonal-naive receive the same rule.

| Network | Splits | Coverage, same-year rule | Coverage, fixed rule [95% CI] | Width, same-year / fixed | Stations below 0.80 | Interval score: OmniST / persistence / seasonal-naive / OmniST same-year | Coverage (H1, H2) | Beats baselines (H3) | Beats same-year rule (H4) |
|---|:---:|:---:|:---:|:---:|:---:|---|:---:|:---:|:---:|
| Delhi | 20 | 0.829 | 0.902 [0.893, 0.911] | 105.4 / 137.1 | 0.006 | 169.9 / 300.2 / 388.8 / 247.9 | PASS | PASS | PASS |
| Beijing | 20 | 0.780 | 0.890 [0.883, 0.896] | 140.0 / 215.0 | 0.000 | 327.1 / 853.1 / 533.6 / 384.0 | PASS | PASS | PASS |
| Weather (not used for selection) | 20 | 0.884 | 0.908 [0.884, 0.931] | 19.3 / 25.3 | 0.125 | 30.1 / 34.5 / 33.1 / 24.4 | PASS | PASS | FAIL |

- **Coverage is confirmed.** The fixed rule gives 0.902 and 0.890 on fresh Delhi and Beijing splits and 0.908 on
  weather, all within the pre-registered 0.02 of 0.90; the post-hoc figures of Section 4.3b (0.898 and 0.896) are
  replaced by these.
- **OmniST's intervals beat both simple forecasts** given the same rule on all three networks (paired 95% intervals
  of the interval-score difference below zero).
- **The rule is not uniformly better.** On weather, where the same-year rule already reaches 0.884, the fixed rule
  widens the intervals and its interval score is worse by 5.7 [4.0, 7.4]
  (H4 fails). It helps where error changes strongly through the year (air quality) and costs width where it does
  not. 12.5% of weather stations remain below 0.80.
- **Station-level conformal with more stations (exploratory).** On PeMSD7-M with 30 calibration stations,
  hierarchical conformal gave coverage 0.922 against 0.891 for pooled
  conformal, with 31% more width, and cut the share of stations below 0.80 from
  11.7% to 1.7%. Its width cost falls as the number of calibration
  stations grows (90% at 10 stations on Delhi, 31% at 30 here).

### 4.3d Second pre-registered round (experiments C1i, C1j)
Four gaps remained after Section 4.3c: no test on traffic, few scored windows per split, the width cost of the
rule, and station-level conformal on one network only. A second round with four new hypotheses was committed
before any run (`PRE-REGISTRATION-C1I.md`). It used fresh station splits (Delhi and Beijing 30 to 49, weather 20
to 39), and a forecast origin every 7 days, which gives 4 times more scored windows on Delhi (60 against 14 per
split). A window's errors are used only once all its targets are observed. Online selection picks, at each
origin, the candidate rule with the lowest interval score on the calibration stations over earlier observed
windows, from five rules fixed in advance. A timestamp-unit defect in the first traffic run gave some intervals
infinite width; it was fixed, the script now refuses infinite intervals, and only the re-run is reported
(`FINALIZATION-RECORD.md`, Section 18).

| Network | Splits | Coverage, same-year rule | Coverage, fixed rule | Coverage, online selection | Width: fixed / online | Interval score: fixed / online | Fixed rule holds (H6) | Online selection (H7) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Delhi | 20 | 0.823 [0.816, 0.830] | 0.908 [0.900, 0.916] | 0.905 [0.899, 0.912] | 128.9 / 127.0 | 163.4 / 163.8 | PASS | PASS |
| Beijing | 20 | 0.787 [0.778, 0.796] | 0.900 [0.894, 0.905] | 0.868 [0.863, 0.872] | 225.3 / 215.5 | 325.0 / 331.2 | PASS | FAIL |
| Weather | 20 | 0.880 [0.855, 0.905] | 0.913 [0.894, 0.932] | 0.900 [0.878, 0.921] | 25.0 / 22.3 | 29.6 / 27.5 | PASS | PASS |

| Traffic network | Splits | Coverage, expanding | Coverage, time-of-day rule | Width: expanding / time-of-day | Interval score: expanding / time-of-day | Time-of-day rule (H5) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| PeMSD7-M | 6 | 0.891 | 0.888 | 17.30 / 21.43 | 35.56 / 36.33 | PASS |
| PeMS-BAY | 6 | 0.881 | 0.877 | 18.82 / 26.78 | 56.31 / 50.12 | FAIL |

**Traffic extended to 20 splits (not pre-registered; splits 6 to 19 added on 26 Nov 2026).** The six pre-registered
traffic splits were extended to 20 with the same code, to narrow the intervals. The table above keeps the
pre-registered six.

| Traffic network | Expanding, splits 0 to 5 | Expanding, splits 6 to 19 | Expanding, all 20 | Station-level conformal, all 20 | Stations below 0.80: expanding / station-level | Width: expanding / station-level |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| PeMSD7-M | 0.891 [0.881, 0.900] | 0.899 [0.892, 0.906] | 0.896 [0.891, 0.902] | 0.927 [0.923, 0.931] | 8.7% / 1.3% | 17.4 / 22.7 |
| PeMS-BAY | 0.881 [0.860, 0.902] | 0.884 [0.872, 0.895] | 0.883 [0.874, 0.892] | 0.906 [0.898, 0.913] | 13.9% / 6.2% | 17.8 / 22.3 |

The extension agrees with the pre-registered splits. With 20 splits, PeMS-BAY under expanding calibration is within
the 0.02 tolerance but its interval excludes 0.90, so a small under-coverage there is real; station-level conformal
removes it and more than halves the share of under-covered stations, at about 25% to 31% more width.

- **The fixed rule replicates** on a third set of station splits with four times more forecast origins: 0.908,
  0.900 and 0.913, with a narrower interval on Delhi than in C1h.
- **Online selection recovers efficiency where the fixed rule over-widens.** On weather it reaches 0.900 with a
  lower interval score than the fixed rule (-2.1 [-3.4, -0.8]); on Delhi it matches the fixed rule.
  On Beijing it falls to 0.868 (H7 fails): with only one earlier test year, the selection often prefers
  same-year rules that under-cover later in the year. The fixed rule remains the recommendation for networks
  with strong seasonal change; selection is recommended only where several earlier years exist.
- **On traffic the rule is not needed and does not help coverage.** Plain expanding calibration already gives
  0.891 and 0.881. The time-of-day rule gives 0.888 and 0.877 (H5 passes on PeMSD7-M and fails on PeMS-BAY, by
  0.003). It lowers the interval score on PeMS-BAY but widens the intervals.
- **Station-level conformal repairs per-station coverage on both traffic networks.** On PeMS-BAY with 45
  calibration stations it gives 0.903 against 0.881 and halves the share of stations below
  0.80 (12.2% to 5.9%) at 25% more width (H8 passes); on PeMSD7-M, 0.922
  against 0.891. For traffic, station-level conformal, not a seasonal rule, is the repair.

**Overall.** Every network now has a forecast-time calibration method confirmed within 0.02 of the 90% target
on data not used to design it. Air quality and weather use the fixed seasonal rule (0.890 to 0.913 across two
confirmation rounds). Traffic uses expanding calibration (0.896 and 0.883 over 20 splits), with station-level
conformal for per-station coverage (0.927 and 0.906). The remaining costs are width (about 25% to 60% over the under-covering
same-year rule) and stations that stay under-covered on weather (13%).

### 4.4 Does distance from the training network matter? (experiments C2 and C3)

A new sensor placed far from the existing network may be harder to predict than one placed near it,
and calibration stations scattered inside the network may then overstate coverage there. Experiment C2
tests this. In each dataset a contiguous region of stations (a random station and its nearest
neighbours) is held out instead of scattered stations, a separate set of calibration stations is drawn
from outside the region, and the model is trained on the rest. For every test station the distance to
its nearest training station is recorded in units of the network spacing (the median nearest-neighbour
distance among all stations of the dataset). Because the same station is held out in several splits at
different distances, the effect of distance can be estimated within a station, which removes the
influence of stations that are simply noisier.

| Dataset | Region-holdout coverage (mean, standard deviation over splits) | Scattered holdout (C1) | Distance to nearest training station, test vs calibration (spacings) | Change in coverage per extra spacing, within station [95% interval] |
|---|---|:---:|:---:|---|
| Delhi PM2.5 | 0.899 (0.023) | 0.893 | 2.31 vs 1.35 | +0.0037 [+0.0016, +0.0064] |
| Beijing PM2.5 | 0.893 (0.020) | 0.903 | 1.78 vs 1.83 | -0.0002 [-0.0056, +0.0022] |
| NOAA weather | 0.876 (0.088) | 0.906 | 2.79 vs 1.29 | -0.0136 [-0.0221, -0.0063] |
| PeMSD7-M traffic | 0.885 (0.048) | 0.876 | 17.95 vs 2.32 | +0.0005 [+0.0001, +0.0009] |
| PeMS-BAY traffic | 0.914 (0.009) | 0.892 | 64.99 vs 4.96 | +0.0000 [-0.0000, +0.0001] |

Reading the table:

- With the Delhi constants, a distance effect appears only in the sparse weather network (station spacing about
  81 km); it does not survive the coordinate correction below.
  Coverage there falls by about 1.4 points per extra spacing, and from about 0.93 in the nearest third
  of test stations to 0.84 in the farthest third under region holdout.
- In the dense urban and traffic networks, held-out regions sat 1.7 to 13 times farther from the
  network than the calibration stations (Delhi, PeMSD7-M, PeMS-BAY) and coverage stayed near the
  target; the within-station slopes are close to zero (Delhi's is slightly positive). The coverage
  result of Section 4.3 is therefore more robust to distance than feared in those networks.
- Distances in the two traffic datasets are in a reconstructed plane with heavy-tailed density, so
  their large values are not comparable with the others.
- Only one sparse network, of 30 stations, was available, so the weather result is the evidence of a
  single dataset.

**Re-run with the corrected coordinate frame (experiments C2 and C3, `norm`).** The table above used the Delhi
coordinate constants, which put the weather network's coordinate inputs about 650 units out of range (Section 4.6).
Experiments C2 and C3 were repeated with the frame built from the training stations, same splits and seeds (20
splits; the scattered arm is the same-window coverage of the corrected C1b run). The two traffic networks were not
repeated.

| Dataset | Region-holdout coverage (mean, standard deviation over splits) | Scattered holdout | Distance to nearest training station, test vs calibration (spacings) | Change in coverage per extra spacing, within station [95% interval] | Coverage in nearest / farthest third of test stations |
|---|---|:---:|:---:|---|:---:|
| Delhi PM2.5 | 0.897 (0.025) | 0.893 | 2.31 vs 1.35 | +0.0028 [-0.0031, +0.0088] | 0.902 / 0.890 |
| Beijing PM2.5 | 0.894 (0.019) | 0.907 | 1.78 vs 1.83 | +0.0014 [-0.0118, +0.0050] | 0.879 / 0.917 |
| NOAA weather | 0.874 (0.063) | 0.880 | 2.79 vs 1.29 | -0.0023 [-0.0116, +0.0079] | 0.894 / 0.858 |

- **The weather distance effect does not reproduce.** With the corrected frame the within-station slope is
  -0.0023 [-0.0116, +0.0079], an interval that includes zero (it was -0.0136 [-0.0221, -0.0063]). Coverage in the
  nearest and farthest thirds is 0.894 and 0.858 (it was 0.930 and 0.843), a gap of 0.036 with overlapping
  intervals. The effect reported with the Delhi constants was therefore largely a consequence of the defect,
  not a property of sparse networks. A smaller decline in coverage with distance in the weather data is not
  excluded (the interval reaches -1.2 points per spacing), but it is not established.
- Delhi's small positive slope also loses significance (+0.0028 [-0.0031, +0.0088]).
  Beijing's slope is near zero (+0.0014); its tertile trend of 0.879 to 0.917 runs the
  other way, with coverage rising with distance.
- In C3 the corrected frame gives a median pairwise total-variation distance of 0.12 (Delhi) and 0.16
  (weather), against noise floors of 0.13 and 0.13, and a distance correlation of
  +0.006 in the weather data. The conclusion is unchanged: the estimator cannot resolve
  differences below the noise floor, so a total-variation bound would be vacuous.
- **Consequence for the plan.** The case for geometry-aware calibration (contribution C) rested on this effect and
  is now weak. C stays gated: it proceeds only if a larger sparse network shows a far-tercile deficit of at least
  0.03 over 20 or more region splits, and otherwise the thesis reports that distance did not matter.

Experiment C3 asks whether a coverage bound built on the total-variation distance between station
score distributions could be informative. The estimated distance between held-out stations had a
median of 0.12 in Delhi and 0.18 in the weather data, against a noise floor of 0.13 obtained by
splitting one station's own scores into random halves. In the weather data it did not grow with
separation (Spearman correlation -0.02). With about 360 dependent scores per station the estimator
cannot resolve differences below roughly 0.13, which exceeds the 0.10 miscoverage budget, so a
total-variation bound would be vacuous. The Semester-4 plan therefore drops the coverage-risk estimate.

### 4.5 Original-protocol results (kept as a record)

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

### 4.6 Threats to validity and limitations

- **Marginal, not conditional coverage.** Per-station coverage varies widely (Section 4.3).
- **Exchangeability is assumed, at the level of stations.** Spatial and temporal dependence can break
  it, and the pooled quantile treats the many dependent scores of one station as if they were
  independent calibration points, so the effective calibration size is the number of calibration
  stations (3 to 45 here). C1 measures the outcome over random splits; it is not a proof.
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
- **Coordinate normalisation (defect found and fixed).** The coordinate embedding centred and scaled its
  inputs with constants fixed for Delhi. On the other networks its inputs were 132 (Beijing), 656
  (weather) and 651 (both traffic networks) times the intended range. Coverage is insensitive to this
  because calibration absorbs the extra error, but accuracy and width are not. Re-running C1b with a
  frame built from the training stations only: mean absolute error fell from 5.84 to 4.73 (weather),
  10.33 to 3.79 (PeMSD7-M) and 5.54 to 4.73 (PeMS-BAY), and interval width by 19%, 59% and 8%;
  Beijing changed little, and Delhi worsened slightly (27.63 to 28.53). Same-window coverage moved by
  at most 0.011 (PeMSD7-M, 6 splits, 0.871 to 0.882), just outside the 0.01 criterion set in advance.
  The committed C1 to C3 results used the Delhi constants; the corrected frame is now an option in the
  code (default unchanged) and the C1b rows above are reported with both. The training-station frame
  will be used from here on. Cross-region transfer has not been tested.
- **Baselines.** E-STGCN and IGNNK are the author's re-implementations.

### 4.7 Dissemination

The Phase-1 work has been released as a preprint [8] (arXiv:2611.04256). It has not been submitted to
any journal or conference. The code, experiment scripts and committed results for both phases are in
the public project repository [7].

## 5. Phase 2: Status of Existing Components
Phase 2 is part of the final thesis work and is planned for Semester 4. Some components were built and
measured in exploratory work; the review corrected what had been claimed for them. The Phase 2 models use the
same coordinate embedding with the Delhi constants, but the real-network runs re-centre the PeMS-BAY coordinates
into the Delhi range, so their inputs stayed within 0.47 of the intended range (synthetic fields within 1.9); the
defect of Section 4.6 did not distort them. The real-network coverage run was repeated with the corrected frame: coverage and width are unchanged within
about 3% (table below).
### 5.1 Components and what has been measured
| Component | State | Evidence |
|---|---|---|
| Neighbour attention (cost proportional to sensors × neighbours) | Implemented | Output cosine similarity to exact attention at least 0.99987 for N up to 2,000 (random tokens, shared weights; not affected by the coordinate frame). Inference memory is 2.6 times lower at N = 2,000, 7.2 times at 4,000 and 16.7 times at 8,000; no advantage below about 1,000 sensors |
| State-space temporal block | Implemented, then dropped | Sequential scan about 2.0 to 2.2 times slower than the GRU at sequence lengths 60, 240 and 960; a chunked scan is 1.7 to 2.0 times slower and not exact |
| Coverage against network size | Measured; re-run with the corrected frame | Deployable (chronological) calibration; real PeMS-BAY 0.918 and 0.921 (neighbour and exact attention), 0.918 and 0.917 with the corrected frame (width 22.3 and 21.8 against 21.6 and 21.9); synthetic networks of 100 to 4,000 sensors 0.880 to 0.914. No real network above 325 sensors |
| Interval width against baselines | Measured, delhi-constants model | On PeMS-BAY the intervals were narrower than persistence and about 21% wider than seasonal-naive; to be re-measured with the corrected frame (Section 4.3a gives 33% under the C1b protocol) |
| Corrected parity gate (V1b) | Run, 10 seeds, pre-registered margins | Neighbour attention against exact attention: **GO** (MAE difference 0.0001, 90% interval inside the 2.43 margin; coverage difference 0.000). Full model with the state-space block: **NO-GO** (MAE worse by 6.4 [4.6, 8.3], margin 2.4), consistent with dropping the block |
### 5.2 Defects found and fixed
- A neighbour-index cache key could collide for two different sensor layouts; it is now a hash of the exact
  coordinates, with a size limit and regression tests.
- Descriptions of the state-space block as parallel and of the attention equivalence as proven were
  incorrect and were corrected.
- The first parity check (V1) reported a mean absolute error of 65.62 against 64.56 and coverage of
  0.944 against 0.948 on three seeds, but its gate could not fail; V1b replaces it (disjoint calibration
  stations, paired equivalence with margins fixed in advance, 10 seeds).
- An earlier scale-up result calibrated each window on that window's own errors, which is not available
  at forecast time. Under the deployable protocol coverage at 4,000 synthetic sensors falls from 0.902 to
  0.880, and the suggested worst-group gap was not supported.
- The Delhi-specific coordinate normalisation (Section 4.6), fixed in both phases.
## 6. Plan for Semester 4 (proposed, pending supervisor approval)
The plan was rewritten on 26 Nov 2026 from the evidence of Sections 4.3a to 4.4; the full plan, with dated
pre-registration of every contribution, is `THESIS-COMPLETION-PLAN.md`. Acceptance criteria are fixed before the
experiments, and each contribution has a fallback, so a negative result is still a thesis result. Semester 4
runs 16 Nov 2026 to 7 Feb 2027; week 3 starts on 30 Nov.
**What the evidence changed.** The forecast-time repair is already shown on air quality and weather and on traffic
with a different rule, so contribution A starts from a result. The weather distance effect did not survive the
coordinate correction, so contribution C becomes a gated, powered test that probably ends as a characterisation. The
learned model beats simple forecasts on air quality and weather but not on traffic, so contribution D concentrates
on traffic. A coordinate-free GRU matches the architecture's accuracy, so the scale work is reduced to measurement
and every calibration result is repeated with that backbone.
| Contribution | Work | Acceptance criterion | Fallback |
|---|---|---|---|
| A. Per-station coverage at forecast time (protected) | Station-level conformal combined with the seasonal scaled scores; second-moment variant; width against the number of calibration stations on a large GHCN network | On every network over at least 20 fresh splits: mean coverage within 0.02 of 0.90, at most 5% of stations below 0.80, width at most 30% above the Phase 1 fixed rule | Width against worst-station coverage, and which networks cannot meet both |
| B. A new sensor's first weeks (protected) | Cold start then own-data split conformal, generalized hierarchical conformal [22], adaptive conformal inference, 0 to 60 days of history | Coverage within 0.03 at every history length; at least 5% narrower at 60 days than at 0 days on 4 of 6 networks | Coverage and width against history |
| C. Does position matter? (gated) | Gate G0 on a 300 to 1,500 station GHCN network with the corrected frame: far tercile at least 0.03 below near over 20 or more region splits. Geometry-aware calibration [16], [17] against whitening [10] and cluster-aware calibration [18] only if G0 passes | If G0 passes: far tercile within 0.03 of 0.90, mean within 0.02, width at most +10%, not worse than whitening | If G0 fails (expected): a powered negative, the interval of the distance slope on a much larger network |
| D. Useful intervals (protected on traffic) | Seasonal-residual forecaster, locally scaled scores, quantile head, and a diagnosis of the PeMS-BAY width gap, on PeMSD7-M and PeMS-BAY | Interval score below persistence and seasonal-naive under the same rule, paired 95% interval below zero, coverage within 0.02 | State that on traffic the learned model does not beat a seasonal baseline, with the diagnosis |
| E. Scale and remaining comparisons | Parity gate V1b; corrected-frame V3 and V3b; coverage against N on the large GHCN network; LargeST compute scaling; dropout, drift, 7-sensor, E-STGCN, IGNNK and interpolator comparisons under the forecast-time rules; calibration results repeated with the coordinate-free GRU backbone | At least 5 times lower peak memory than exact attention at N of 2,000 or more; neighbour-set agreement at least 0.99; coverage within 0.02 of 0.90 at every size, at least 10 splits per size | Restrict the claim to equivalence; state evidence to 325 sensors if no larger network is usable |
| F. Alerts (cut candidate) | Conformal risk control [19] at one air-quality network with published thresholds | Mean miss rate at or below target plus 0.02, false alarms against a point-forecast threshold | Miss rate against the number of calibration exceedances |
| G. Package and thesis (protected) | Pip-installable package that reproduces one headline table in a fresh environment; thesis in the IIT Patna format with at least 30 verified references; chapters 1 to 3 from week 6, supervisor review week 11 | Table reproduces; supervisor review | None |
Cut order if time runs short: F, then LargeST compute scaling, then the breadth of the comparisons in E, then C's method.
Dropped: the state-space block, a separate coverage-risk estimate, sensor placement, cross-city transfer, and online rule
selection as a default (it failed on Beijing).
## 7. Summary of Progress
Phase 1 is complete as a design, an implementation and an evaluation. The forecaster was validated on
five real networks and released as a preprint. Under the rule used in C1, mean coverage was 87.6% to
90.6% of a 90% target. Under calibration restricted to forecast-time information (C1b) it is 77.7% to
89.1%: Delhi and Beijing under-cover because forecast error roughly doubles over the test period, while
weather and the two traffic networks stay near target. Persistence and seasonal-naive intervals show the same
shortfall on the air-quality networks. Calibrating on earlier years' errors, scaled by the forecast's magnitude,
gave 0.902 and 0.890 on Delhi and Beijing and 0.908 on weather in a pre-registered test on
data not used to choose the rule, and OmniST's intervals then scored better than persistence and
seasonal-naive on all three; on weather the rule costs width without a coverage gain. Station-level
conformal was valid, and its width cost fell from 90% to 31% as calibration stations rose from 10 to 30. A second
pre-registered round confirmed the rule again (0.900 to 0.913, four times more forecast origins), found that
traffic needs no seasonal rule (0.881 and 0.891), and confirmed station-level conformal on PeMS-BAY (0.903). A coordinate-normalisation defect that inflated error and width on
four networks was found and fixed. Against persistence, OmniST is better on three networks and not on
PeMSD7-M or weather; against a seasonal forecast it is wider on PeMS-BAY. Distance from the training
network showed an effect only in the sparse weather network with the Delhi constants, and that effect
disappeared with the corrected coordinate frame (slope -0.2 points per spacing, interval including zero). Phase 2 is part of the final thesis: neighbour attention
cuts attention memory 7 to 17 times from 4,000 sensors with equal output, the state-space block was dropped,
and the Semester-4 plan (Section 6) is organised around per-station coverage, a new sensor's first weeks, a gated
test of whether position matters, useful intervals on traffic, and scale, with acceptance criteria and fallbacks,
pending supervisor approval. A coordinate-free GRU matches the architecture's accuracy, so the thesis contribution is
the calibration and its evaluation, not the architecture.
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

[5] A. N. Angelopoulos and S. Bates, "Conformal Prediction: A Gentle Introduction," *Foundations and Trends in
Machine Learning*, vol. 16, no. 4, pp. 494–591, 2023 (arXiv:2107.07511, "A Gentle Introduction to Conformal
Prediction and Distribution-Free Uncertainty Quantification").

[6] A. Gu and T. Dao, "Mamba: Linear-Time Sequence Modeling with Selective State Spaces,"
*arXiv:2312.00752*, 2023.

[7] P. Vashishtha, "thesis-omnist: Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor
Locations in Evolving Networks (project repository)," 2026. [Online]. Available:
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

[14] R. J. Tibshirani, R. F. Barber, E. J. Candes, and A. Ramdas, "Conformal Prediction Under
Covariate Shift," *arXiv:1904.06019*, 2019. [Online]. Available: https://arxiv.org/abs/1904.06019

[15] R. F. Barber, E. J. Candes, A. Ramdas, and R. J. Tibshirani, "Conformal prediction beyond
exchangeability," *arXiv:2202.13415*, 2022. [Online]. Available: https://arxiv.org/abs/2202.13415

[16] R. Hore and R. F. Barber, "Conformal prediction with local weights: randomization enables local
guarantees," *arXiv:2310.07850*, 2023. [Online]. Available: https://arxiv.org/abs/2310.07850

[17] H. Mao, R. Martin, and B. Reich, "Valid model-free spatial prediction," *arXiv:2006.15640*, 2020.
[Online]. Available: https://arxiv.org/abs/2006.15640

[18] G. Kim, C. Y. Lim, W.-T. Wang, H.-Y. Huang, et al., "Cluster-Aware Conformal Calibration for
Spatio-Temporal Distributional Prediction," *arXiv:2606.06753*, 2026. [Online]. Available:
https://arxiv.org/abs/2606.06753

[19] A. N. Angelopoulos, S. Bates, A. Fisch, L. Lei, et al., "Conformal Risk Control,"
*arXiv:2208.02814*, 2022. [Online]. Available: https://arxiv.org/abs/2208.02814

[20] Y. Zhu, J. Yu, L. Li, G. Zhang, et al., "Conformalized Large Language Models under Configuration
Shift," *arXiv:2608.01460*, 2026. [Online]. Available: https://arxiv.org/abs/2608.01460
[21] Y. Lee, R. F. Barber, and R. Willett, "Distribution-free inference with hierarchical data,"
*arXiv:2306.06342*. [Online]. Available: https://arxiv.org/abs/2306.06342
[22] S. Mallick, E. Tchetgen Tchetgen, E. Dobriban, and Y. Lee, "Generalized Hierarchical Conformal Prediction,"
*arXiv:2608.15500* [stat.ME], 2026. [Online]. Available: https://arxiv.org/abs/2608.15500

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

**A.2 Distance experiments (C2 and C3), additional statistics.**

| Dataset | Coverage by distance tertile, near / middle / far (region holdout) | Spearman correlation of station coverage with distance, scattered / region holdout |
|---|---|---|
| Delhi PM2.5 | 0.905 / 0.904 / 0.894 | -0.018 / -0.075 |
| Beijing PM2.5 | 0.876 / 0.891 / 0.918 | +0.566 / +0.796 |
| NOAA weather | 0.930 / 0.897 / 0.843 | -0.305 / -0.270 |
| PeMSD7-M traffic | 0.815 / 0.896 / 0.881 | -0.006 / -0.037 |
| PeMS-BAY traffic | 0.942 / 0.924 / 0.909 | +0.015 / -0.088 |

Tertile edges come from the pooled distances of both arms, so the nearest bins of the two traffic
datasets hold few region stations (4 and 3). Correlation p-values are optimistic because stations
repeat across splits. Beijing's positive correlation probably reflects the type of station (12
stations) and not distance.

| Dataset | Median total-variation distance between stations | Noise floor (random halves of one station) | Nearest vs farthest quartile of pairs | Loss if weight is spread over the 3 nearest stations (median) |
|---|:---:|:---:|:---:|:---:|
| Delhi PM2.5 | 0.120 | 0.133 | 0.107 vs 0.127 | 0.113 |
| NOAA weather | 0.176 | 0.133 | 0.224 vs 0.194 | 0.188 |

**A.3 Phase 2, measurements on existing components.**

| Measurement | Setting | Result |
|---|---|---|
| Attention equivalence (V2) | Shared weights, random tokens, N = 37, 100, 325, 1,000, 2,000 | Minimum cosine similarity to exact attention 0.99987 |
| Attention time (V2) | N = 325 / 1,000 / 2,000, one layer, batch 1 | Neighbour path 145 / 152 / 189 ms; exact path 194 / 225 / 182 ms |
| State-space block vs GRU (T1) | T = 60 / 240 / 960, batch 4, 37 nodes, two layers | State-space 29.0 / 115.7 / 462.3 ms; GRU 14.0 / 53.3 / 233.7 ms |
| First parity check (V1, preliminary) | 3 seeds, Delhi | MAE 64.56 [60.73, 68.38] (baseline) vs 65.62 (rebuilt); coverage 0.948 vs 0.944 |

---

*Candidate: Praveg Vashishtha (ID No. IITP006424) | Supervisor: Pankaj Chaswal | Semester-3 Progress
Report | Project repository: https://github.com/Praveg432/thesis-omnist*
