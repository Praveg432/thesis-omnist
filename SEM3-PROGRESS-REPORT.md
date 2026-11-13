# M.Tech Project Progress Report (Semester 3)

**Indian Institute of Technology Patna — Department of Computer Science and Engineering**

| | |
|---|---|
| **Project Title** | Certified Topology-Invariant Spatiotemporal Forecasting with Trustworthy Uncertainty at Unseen Sensors, and Its Scaling to Large Networks |
| **Candidate** | Praveg Vashishtha |
| **ID No.** | IITP006424 |
| **Supervisor** | Pankaj Chaswal |
| **Program / Semester** | M.Tech (CSE) — Semester 3 Progress Report |
| **Reporting period** | Semester 3 |
| **Hardware** | Apple M4 Pro (MPS, ~24 GB unified memory); single machine, no cluster |

> **Note on scope of this report.** This is a *Semester-3 progress report*. It documents the work
> completed so far and the plan for Semester 4. Per the department instruction, the Semester-3 report
> may be in any format; the full thesis submitted after Semester 4 will follow the IIT Patna M.Tech
> Thesis Manual format. The project is organized in two phases: **Phase 1 (OmniST)** — completed this
> reporting period — and **Phase 2 (scaling + deliverable)** — in progress, to be completed in
> Semester 4.

---

## 1. Introduction

Large sensor networks — for air quality, road traffic, weather, and power — are used to forecast
conditions and drive decisions. For a forecasting system to be useful in deployment, it must satisfy
two properties that existing methods do not provide together:

1. **Resilience to a changing network.** Sensors fail, go offline, or are newly installed. The model
   must keep forecasting, including at locations with no sensor history, without retraining each time
   the network layout changes.
2. **Trustworthy uncertainty.** Decisions need a prediction *interval* with a stated, guaranteed
   probability of containing the true value — not a bare point estimate whose reliability is unknown.

This project designs a forecaster that provides both (Phase 1) and then makes it run efficiently at
the scale of real networks — thousands of sensors — without weakening the guarantee (Phase 2).

## 2. Objectives and Scope

1. Design a spatiotemporal forecaster whose computation has no structural dependence on the number of
   sensors, so it keeps forecasting as the network's topology changes. **(Phase 1 — completed.)**
2. Equip it with a distribution-free, finite-sample coverage guarantee at *unseen* sensor locations,
   and validate that the guarantee holds on real data across multiple domains. **(Phase 1 — completed.)**
3. Re-engineer the forecasting engine to be sub-quadratic in the number of sensors and parallel over
   time, so it can scale to thousands of sensors on commodity hardware. **(Phase 2 — in progress.)**
4. Certify that the coverage guarantee still holds as the network scales, and tighten per-sensor
   (conditional) coverage. **(Phase 2 — in progress / planned.)**
5. Package the method as a reusable, installable software library so practitioners can apply it to
   their own sensor networks. **(Phase 2 deliverable — planned for Semester 4.)**

**Out of scope (stated honestly):** the contribution is the *capability* (trustworthy, resilient,
scalable uncertainty), not a point-accuracy state-of-the-art; coverage certification at *thousands of
real* sensors is bounded by the availability of a real dataset of that size.

## 3. Review of Related Work (summary)

The design sits at the intersection of three established lines, and is positioned against each:

- **Spatiotemporal graph neural networks** (e.g. fixed-adjacency STGCN-family models) give strong
  accuracy on a *fixed* sensor set but cannot predict at a newly added sensor and break when the node
  count changes.
- **Inductive graph kriging** (e.g. IGNNK) predicts at unseen locations but provides no coverage
  guarantee.
- **Conformal prediction** gives distribution-free coverage guarantees, but standard split-conformal
  assumes a fixed model and data exchangeability; applying it under changing topology and at scale is
  the open problem this project addresses.

The project's distinct contribution is the *combination*: coverage guaranteed at spatially unseen
sensor coordinates, preserved under topology change, validated cross-domain on real data, and (Phase
2) carried to the thousands-of-sensors regime. A full, cited related-work chapter will appear in the
Semester-4 thesis.

## 4. Work Completed in Semester 3 — Phase 1: Formulation and Testing of OmniST

### 4.1 Model formulation

The forecaster (named OmniST) is built from three design choices, none of which references a global
sensor count:

1. **Coordinate-based tokenization** — each sensor is embedded from its geographic coordinates via a
   learned spatial mapping, with no positional index or fixed node count.
2. **k-nearest-neighbour spatial attention** — each sensor attends only to its nearest neighbours,
   selected from coordinates at every forward pass, so the graph adapts to whatever sensors are
   present (no precomputed adjacency matrix).
3. **Per-sensor temporal processing** — a bidirectional recurrent (GRU) model runs independently per
   sensor, so adding or removing a sensor does not alter any other sensor's representation.

Composed with inductive split-conformal calibration, this yields a distribution-free coverage
guarantee at sensor coordinates never seen in training, preserved as sensors are added or removed. A
locality property was formulated and verified: each sensor's nonconformity score is exactly invariant
to sensors outside its neighbour set, so the guarantee requires no recalibration under far-away
topology changes.

### 4.2 Testing and validation (executed on real data)

All results below are from committed experiment outputs (reproducible scripts and result files in the
project repository; see Appendix A).

**(a) Guaranteed coverage at unseen sensors, across four real datasets and three domains.** Target
coverage 90%.

| Dataset (domain) | Coverage at unseen sensors |
|---|:---:|
| Delhi air quality (environmental) | 0.914 |
| Beijing air quality (environmental) | 0.928 |
| NOAA weather (meteorology) | 0.919 |
| PeMSD7-M traffic (transportation) | 0.915 |

Coverage holds within a few points of the 90% target on every dataset, and stays on target under
30–50% of sensors being dropped. OmniST is the only method, among four model-free interpolators, to
hold the target on all four datasets.

**(b) Better than a learned baseline at unseen sensors.** Against a learned inductive-kriging baseline
(IGNNK, a faithful reimplementation), OmniST achieves ~21% lower error at unseen sensors on Delhi with
tighter, better-calibrated intervals.

**(c) Resilience demonstrated, not asserted.** A fixed-topology baseline (E-STGCN, faithful
reimplementation), run under identical conditions, structurally cannot produce an output at a newly
added sensor and fails when sensors are dropped — demonstrated with the captured error. OmniST, on the
same reduced network, keeps coverage on target.

**(d) Uncertainty stays valid under drift over time.** A rolling adaptive-conformal layer restores
coverage from 0.50 (static, worst-drift window) to 0.96 on real Delhi data, at an honestly reported
cost of wider intervals.

**(e) Scale tested to 325 real sensors** (PeMS-BAY): coverage 0.921, holding under node dropout.

### 4.3 Honest limitations identified in Phase 1 (these motivate Phase 2)

- The spatial attention's exact computation grows with the square of the sensor count; measured
  training cost scales super-linearly.
- The temporal model is sequential and cannot be parallelised over time.
- Coverage is certified only up to a few hundred real sensors (325), and the guarantee is on average
  (marginal), not per-sensor (conditional), with only a partial fix so far.

### 4.4 Dissemination

The Phase-1 work (formulation + validation) has been written up and released as a **preprint**
(arXiv:2611.04256). It has **not** been submitted to any journal or conference for publication; it is a
timestamped record of this project's Phase-1 work, and is intended to form part of the final thesis.

## 5. Work in Progress — Phase 2: Scaling the Engine While Preserving the Guarantee

The Phase-1 limitations define three re-engineering fronts, all implemented, with the two most
critical validation gates already executed.

### 5.1 Implemented components

1. **Sub-quadratic spatial attention** — a vectorized nearest-neighbour attention with cost and memory
   that grow linearly in (sensors × neighbours) instead of quadratically, using a cached spatial index.
2. **Parallel temporal block** — a selective state-space model that processes the time sequence in
   linear time and in parallel, as a drop-in replacement for the sequential recurrent model.
3. **Scalable conditional conformal** — a calibration scheme intended to keep coverage valid as the
   network scales and to even out per-sensor coverage.

### 5.2 Validation completed this period

| Test | Question | Result |
|---|---|---|
| Parity (make-or-break) | Does the rebuilt engine (parallel temporal block + sub-quadratic attention) match OmniST's accuracy *and* coverage on real data? | **Pass.** On real Delhi (3 seeds): error within 2% of the original (65.62 vs 64.56) and coverage preserved (0.944 vs 0.948, within the finite-sample band). |
| Equivalence | Does the sub-quadratic attention compute the same thing as the exact version? | **Pass.** Output cosine similarity to exact ≥ 0.99987 across sensor counts up to 2000. |

These are the two cheapest, most load-bearing checks: they confirm the scaling does not cost accuracy
or break the guarantee. They have both passed on real data.

### 5.3 Remaining Phase-2 work (planned for Semester 4)

- **Coverage at scale:** certify that coverage stays valid as the sensor count grows toward thousands.
  *Main residual risk: this needs a real sensor dataset of that size; where unavailable, realistic
  replication is used with the explicit caveat that replication cannot by itself certify coverage.*
- **Throughput/memory study:** quantify where the parallel state-space block and sub-quadratic
  attention win over the original, and identify the crossover point honestly.
- **Full evaluation:** multi-seed results with confidence intervals across all datasets; ablations.

## 6. Plan for Semester 4

| Milestone | Work | Target |
|---|---|---|
| M-A | Coverage-at-scale experiments + scalable conditional conformal | Coverage holds in band as sensor count grows |
| M-B | Throughput/memory curves; crossover analysis vs the original engine | Scaling benefit quantified honestly |
| M-C | Full real-data evaluation (multi-seed, confidence intervals, ablations) | Rebuilt engine matches original accuracy/coverage at lower cost |
| M-D | **Deliverable: a reusable software library** (pip-installable) wrapping the forecaster + conformal layer, so practitioners can apply it to their own sensor networks | Installable package + usage example + tests |
| M-E | Thesis write-up in IIT Patna manual format; final preemption/novelty re-scan | Final thesis submitted |

**On the deliverable.** A concrete goal for Semester 4 is to package the method as an installable
Python library (a NumPy/PyTorch-based tool) that takes a user's sensor coordinates and readings and
returns forecasts with guaranteed-coverage intervals, including at unseen locations. This turns the
research from a set of experiments into a tool others can use — the usability contribution.

## 7. Summary of Progress

Phase 1 is complete: the forecaster has been formulated and validated on four real datasets across
three domains, with the coverage guarantee holding under topology change and under drift, and the work
is on record as a preprint. Phase 2 is underway: the scaled engine is implemented, and its two
make-or-break checks (accuracy/coverage parity with the original, and equivalence of the sub-quadratic
attention) have both passed on real data. The remaining Semester-4 work is the coverage-at-scale
certification, the full evaluation, and the packaging of the method into a reusable library.

---

## Appendix A — Reproducibility (claim → experiment → result file)

Every number in this report is backed by a committed experiment script and result file in the project
repository. Phase-1 artifacts are under `phase1-omnist/`; Phase-2 under `phase2-omnist-scale/`.

| Claim in this report | Script | Result file |
|---|---|---|
| Cross-domain coverage (4 datasets) | `phase1-omnist/experiments/B1_multidomain_v2.py` | `phase1-omnist/results/exp_multidomain_v2.json` |
| Headline inductive coverage (Delhi) | `phase1-omnist/experiments/06_inductive_conformal.py` | `phase1-omnist/results/exp_inductive_conformal.json` |
| vs learned IGNNK baseline | `phase1-omnist/experiments/B9_ignnk_inductive.py` | `phase1-omnist/results/exp_ignnk_inductive.json` |
| Fixed-topology failure demo | `phase1-omnist/experiments/B8_fixedtopo_crash_demo.py` | `phase1-omnist/results/exp_fixedtopo_crash_demo.json` |
| Temporal-drift coverage restored | `phase1-omnist/experiments/10_temporal_conformal.py` | `phase1-omnist/results/exp_temporal_conformal.json` |
| Scale to 325 real sensors | `phase1-omnist/experiments/B7_largeN_pemsbay.py` | `phase1-omnist/results/exp_largeN_pemsbay.json` |
| Phase-2 parity (make-or-break) | `phase2-omnist-scale/experiments/V1_ssm_matches_omnist.py` | `phase2-omnist-scale/results/V1_ssm_matches_omnist_results.json` |
| Phase-2 attention equivalence | `phase2-omnist-scale/experiments/V2_attention_equivalence.py` | `phase2-omnist-scale/results/V2_attention_equivalence_results.json` |

A full claim→evidence map is in `EXPERIMENTS-INDEX.md`; the detailed Phase-1 result index is in
`phase1-omnist/RESULTS-INDEX.md`.

---

*Candidate: Praveg Vashishtha (ID No. IITP006424) | Supervisor: Pankaj Chaswal | Semester-3 Progress
Report*
