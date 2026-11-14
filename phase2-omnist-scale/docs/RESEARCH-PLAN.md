# Research Plan — OmniST-Scale (revised after the preliminary review)

*Scaling a topology-invariant spatiotemporal forecaster, with calibrated uncertainty at unseen
sensors, toward thousands of sensors.*

**Candidate:** Praveg Vashishtha (ID IITP006424) · IIT Patna, CSE · **Supervisor:** Pankaj Chaswal
**Hardware:** Apple M4 Pro (MPS, ~24 GB)

---

## 0. What changed and why

A preliminary review found that the original plan promised more than the code and the evidence
supported. This revision keeps the research question and replaces claims with acceptance criteria that
are fixed **before** any run. Each work package has a fallback, so a negative result still yields a
defensible thesis chapter.

| Review finding | Consequence for this plan |
|---|---|
| The state-space block is a sequential loop, about 2x slower than the GRU (diagnostic T1) | "Parallel in time" is no longer claimed. WP2 must implement a parallel scan and beat the GRU, or the claim is dropped. |
| The fast attention is numerically equivalent to exact, but no memory or speed advantage was measured | WP3 measures peak memory and time against N, with a stronger equivalence test. |
| The scalable conditional conformal front does not exist yet, and it was named the novel core | WP1 designs, implements and tests it, and positions it against two directly related conformal methods. |
| The V1 gate could not fail | V1 is retained only as a preliminary record. V1b (paired equivalence, fixed margins) replaces it. |
| Calibration used training-station residuals | All new evaluation calibrates on a disjoint set of unseen stations (already done for Phase 1 in experiment C1). |
| The held-out sets were tiny and fixed | All new evaluation uses many random station splits; the split is the unit of inference. |
| "Certified" was used for an empirical, marginal coverage result | See Section 1. The thesis defines the term and states its assumption. |
| The large-N claim rested on 7 held-out sensors | C1 re-evaluates PeMS-BAY with random splits and tens of held-out sensors. WP4 adds a larger real network. |
| Baselines were the author's re-implementations | WP5 adds official-code or independently validated baselines with an equal tuning budget. |

## 1. Terminology: what "certified" means in this thesis

Split conformal prediction gives finite-sample marginal coverage **if** the calibration scores and the
test score are exchangeable. In this thesis the stations are split at random into train, calibration
and test sets, and the model never sees the calibration or test stations. Under that design the scores
of calibration and test stations are exchangeable across stations at a given time, and the coverage
statement is a finite-sample, marginal one. Three limits are stated wherever the term is used:

1. The statement is **marginal** over stations and time, not conditional on a station or a region.
2. Spatial and temporal dependence can break exchangeability. Experiment C1 measures how close the
   achieved coverage is to the target over many random splits; it does not prove validity.
3. The statement is about the random-split protocol. A sensor chosen adversarially or from a different
   region is outside it.

Where a shorter word is needed, the thesis uses "calibrated". The title wording is the advisor's call.

## 2. Problem and research question

The Phase 1 forecaster (OmniST) works at unseen locations with calibrated intervals, but its engine
does not scale: exact attention is O(N^2) in memory, the temporal model is a sequential GRU, and
coverage has been checked only up to 325 real sensors (on a fixed set in the original protocol).

> **Research question.** Can the forecaster be made sub-quadratic in the number of sensors, with
> time-parallel temporal processing, while keeping accuracy and the random-split coverage behaviour of
> Phase 1, and how does that coverage behave as the network grows?

## 3. Work packages, acceptance criteria and fallbacks

All thresholds below are fixed now. They may be tightened, never loosened, after seeing results.

### WP0. Preconditions (first two weeks)
- Run **V1b** (10 seeds). Gate: ssm+fast is equivalent to gru+exact within 5% MAE and 0.03 coverage
  (paired, 90% interval inside the margin). A "worse" verdict stops the SSM line (see WP2 fallback);
  "inconclusive" means more seeds.
- Check that **LargeST** (8,600 California sensors) can be downloaded and used for research, and what
  memory a 2,000 to 8,600 sensor subset needs on the 24 GB machine. Record the licence terms.
- Run **T1** on an idle machine to fix the baseline timing ratio.

### WP1. Calibration under inductive shift (the trustworthy-ML contribution)
- Implement `conformal.py` with: (a) split conformal on disjoint calibration stations (the Phase 1 C1
  protocol); (b) a **localised/conditional** variant that weights calibration stations by spatial
  proximity, or groups them by region, to improve per-station coverage; (c) an exchangeability
  diagnostic (calibration versus test score distributions).
- Compare with two published approaches: conformal prediction for inductive graph models (Zargarbashi
  and Bojchevski, ICLR 2024) and conformal prediction for spatially dependent data (Sen and Saha,
  2026), re-implemented or run from released code.
- **Accept** if, over at least 20 random splits on each of Delhi, Beijing and weather: mean marginal
  coverage is within 0.02 of 0.90, and the 10th-percentile per-station coverage improves over (a) by a
  paired test at the 5% level without widening intervals by more than 10%.
- **Fallback:** if (b) does not improve, the contribution becomes a careful empirical study of when
  random-split conformal coverage holds and fails (per-station spread, exchangeability diagnostics),
  which is still a thesis result.

### WP2. Time-parallel temporal block
- Replace the sequential loop with a parallel prefix scan of the recurrence h_t = a_t h_{t-1} + b_t.
  Make B and C input-dependent if the study shows it matters (ablation).
- **Accept** if (i) outputs match the sequential version within 1e-4 (fp32) for T up to 960, and
  (ii) forward-plus-backward time is no worse than the GRU for T >= 240 on the M4 Pro.
- **Fallback:** if (ii) fails, drop the time-parallel claim. The SSM is then reported only as an
  accuracy-parity alternative, or removed, and the thesis rests on WP1, WP3 and WP4.

### WP3. Sub-quadratic attention: memory and time evidence
- Measure peak memory and time against N in {325, 1,000, 2,000, 4,000, 8,600} for exact attention,
  the fast attention, and at least one published efficient spatiotemporal model (for example
  STGformer, or a linear-attention baseline), with fixed batch size and heads.
- Strengthen equivalence: neighbour-set agreement (Jaccard) between the k-d tree and exact Haversine
  selection, and output agreement with trained weights, not random tokens.
- **Accept** if the fast path uses at least 5x less peak memory than exact at N >= 2,000 and the N at
  which exact attention runs out of memory is identified, with neighbour-set agreement >= 0.99.
- **Fallback:** if no advantage appears at any N that fits in memory, report that honestly and
  restrict the claim to equivalence.

### WP4. Coverage as the network grows
- Evaluate on PeMS-BAY (325), a larger real network from WP0 (target >= 2,000 sensors), with at least
  10 random station splits per size, and report coverage, interval width and per-station spread
  against N.
- **Accept** if mean marginal coverage stays within 0.02 of 0.90 at every size evaluated, with the
  spread over splits reported.
- **Fallback:** if no real network above 325 sensors is usable, the thesis states that coverage is
  evaluated to 325 sensors only, and demonstrates compute scaling separately. Replicated sensors are
  never used to claim coverage.

### WP5. Baselines and reporting standards
- Add the official IGNNK implementation (or INCREASE) with the same tuning budget as OmniST, and a
  properly specified Gaussian-process kriging baseline with its native intervals.
- Follow a leakage-free protocol for inductive kriging (separate spatial and temporal partitions;
  Yang et al., 2025).
- Report every result as mean and 95% interval over random splits. No result is described as a
  guarantee unless it is a theorem.

### WP6. Deliverable: reusable PyTorch package
- A pip-installable package with fit, calibrate and predict methods, input checks, tests and a worked
  example. (It is a PyTorch package; the earlier "NumPy tool" wording was wrong.)
- **Accept** if it installs in a fresh virtual environment and the example reproduces the Delhi
  coverage of C1 within the spread over splits.

### WP7. Thesis
- Write in the IIT Patna manual format, 60 to 70 pages. The related-work chapter covers conformal
  prediction (including graph and spatial variants), inductive kriging, and efficient spatiotemporal
  models, with at least 30 verified references.

## 4. Timeline (Semester 4)

| Month | Work | Exit check |
|---|---|---|
| 1 | WP0 (V1b, LargeST check, T1); start WP1 design | V1b verdict recorded; data decision made |
| 2 | WP1 implementation and Delhi/Beijing/weather study | WP1 acceptance or fallback declared |
| 3 | WP2 parallel scan; WP3 memory and time study | WP2 and WP3 acceptance or fallbacks declared |
| 4 | WP4 coverage versus N; WP5 baselines | WP4 result with spread over splits |
| 5 | WP6 package; ablations; figures | package installs and reproduces the example |
| 6 | WP7 write-up; final related-work re-scan; supervisor review | thesis draft complete |

## 5. Novelty boundary (honest)

- Not novel: efficient attention, SSM forecasting, split conformal prediction, and conformal methods
  for graphs and for spatial data all exist and are cited.
- The defended residual is the **combination**: a topology-invariant forecaster whose interval
  calibration is evaluated under random disjoint station splits, and carried to larger networks with
  measured memory and time evidence. The contribution is a calibrated, scalable system and an
  evaluation of how its coverage behaves; it is not a new theorem and not an accuracy record.

## 6. Risks

- **Data:** a large real network may be unusable (size, licence, memory). Fallback in WP4.
- **SSM:** a pure PyTorch scan may not beat the GRU on MPS. Fallback in WP2.
- **Conformal:** a localised variant may not improve per-station coverage. Fallback in WP1.
- **Scope:** WP1 to WP7 is a full semester. If time runs short, WP5 and the ablations in WP6 are cut
  first; WP1, WP3, WP4 and WP7 are protected.
- **Fast-moving area:** re-scan the literature at the start of month 1 and before submission.
