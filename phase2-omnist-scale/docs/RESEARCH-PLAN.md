# Research Plan: OmniST-Scale (revised after the preliminary review and the novelty assessment)

*Calibrated forecasting at newly placed sensors, scaled toward large networks.*

**Candidate:** Praveg Vashishtha (ID IITP006424) · IIT Patna, CSE · **Supervisor:** Pankaj Chaswal
**Hardware:** Apple M4 Pro (MPS, ~24 GB)
**Status of this document:** the scope in Sections 3 to 5 is a **proposal pending supervisor approval**.

---

## 0. What changed and why

Two reviews shaped this plan. A preliminary review found that the original plan promised more than the
code and evidence supported. A later novelty assessment tested five candidate ideas against verified
prior work and two new measurements (C2 and C3). The plan keeps the research question, replaces claims
with acceptance criteria fixed **before** any run, and gives each work package a fallback, so a
negative result still yields a defensible thesis chapter.

| Finding | Consequence for this plan |
|---|---|
| The state-space block is sequential and about 2x slower than the GRU (T1) | Demoted to an optional extension (X2). "Parallel in time" is no longer claimed. |
| Neighbour attention matches exact attention in output, but no memory or speed advantage was measured | WP3 measures peak memory and time against N. |
| The first parity gate (V1) could not fail | V1b replaces it, with paired equivalence, fixed margins, and a separate gate for the attention swap alone. |
| The title word "certified" overstated an empirical, marginal, approximate result | The title now says "calibrated"; Section 1 defines the term and its limits. |
| The large-network claim rested on 7 held-out sensors | C1 re-evaluated it; WP3 adds a larger real network. |
| **C2:** coverage falls with distance from the training network only in the sparse weather network (about 1.4 points per extra network spacing); not in the dense urban and traffic networks | The geometry-aware work (WP1, WP2) targets sparse networks and must not harm dense ones. |
| **C3:** differences between station score distributions are no larger than the estimator's noise floor (about 0.13) at roughly 360 dependent scores per station, and do not grow with distance in the weather data | A coverage bound built on total-variation distance would be vacuous. WP2 uses a threshold-specific, empirically validated diagnostic instead. |
| The coordinate embedding uses Delhi-specific constants | A local coordinate frame is a precondition (WP0) for any new region and for portability (X1). |

## 1. Terminology: what "calibrated coverage" means in this thesis

Split conformal prediction gives finite-sample marginal coverage **if** the calibration scores and the
test score are exchangeable. In this thesis the stations are split at random into train, calibration
and test sets, and the model never sees the calibration or test stations. Under that design a test
station is exchangeable with the calibration stations. The exchangeable unit is the **station**, not
the individual score. The many scores of one station are dependent, and the pooled quantile treats
them as separate calibration points, so the effective calibration size is the number of calibration
stations (3 to 45 in the Phase 1 experiments). The coverage statement is therefore **approximate**,
and the approximation improves as calibration stations are added. Four limits are stated wherever the
term is used:

1. The statement is **marginal** over stations and time, not conditional on a station or a region.
2. Spatial and temporal dependence can break exchangeability. Experiment C1 measures how close the
   achieved coverage is to the target over many random splits; it does not prove validity.
3. The statement is about the random-split protocol. A sensor chosen adversarially, or at a distance
   from the network that the calibration stations do not represent, is outside it. WP1 addresses the
   second case where C2 shows it matters.
4. A calibration set that is small relative to the number of scores carries sampling noise of the
   order of the split-to-split spread seen in C1 (standard deviation 0.02 to 0.05).

The thesis uses "calibrated" and not "certified" for this reason. The title is subject to the advisor's approval.

## 2. Problem and research question

The Phase 1 forecaster (OmniST) produces calibrated intervals at unseen sensor locations. Three things
are open. Its coverage is marginal and varies across stations. The distance of a new site from the
existing network can matter, but only in some networks (C2). And its engine has not been shown to scale.

> **Research question.** When a sensor is placed at a new site, can its prediction interval be
> calibrated using the geometry of the site (distance to, and density of, the training sensors) so
> that coverage holds where distance matters without harming networks where it does not, and does the
> approach carry to larger networks?

## 3. Work packages, acceptance criteria and fallbacks

All thresholds are fixed now. They may be tightened, never loosened, after seeing results. "Random
splits" means at least 20 random station or region splits unless stated.

### WP0. Preconditions (month 1)
- Run **V1b** (10 seeds). Two gates: the attention swap alone (`gru+fast` against `gru+exact`), which
  is required, and the full model with the state-space block, which is optional. Margins: 5% of the
  baseline MAE and 0.03 in coverage, paired, 90% interval inside the margin. A NO-GO on the attention
  gate must be resolved before WP3.
- Replace the Delhi-specific coordinate constants by a per-region local frame (centre and scale from
  the training stations) and confirm Phase 1 coverage is unchanged within the spread over splits.
- Build the **large sparse network**: a subset of GHCN-Daily TMAX stations (7,435 stations in the
  contiguous US have records spanning 2019 to 2023 per the inventory file; completeness of the daily
  series and loading are **not yet checked**). Target 300 to 1,500 stations after quality filtering.
- Check that **LargeST** (8,600 California sensors) can be downloaded and used, for compute scaling
  only, and record the licence.
- Re-run **T1** on an idle machine as a timing baseline.

### WP1. Geometry-aware calibration at new sites (spine, part A)
- **Problem.** Calibration stations that sit close to the network overstate coverage at distant sites
  where distance matters (C2, weather: far third about 0.84 to 0.88 against 0.93 near).
- **Method.** Build a calibration pool with realistic geometry: split the stations into spatial
  blocks, hold out each block in turn, train on the rest, and record for every held-out station its
  score and its geometry features under that fold (distance to the nearest training stations, local
  density). This gives calibration scores for all stations at varied distances, not only the few
  scattered calibration stations. At a new site with geometry g*, weight the pool by a kernel in
  geometry space, using randomised localisation (Hore and Barber) so the localised quantile keeps a
  finite-sample guarantee under conditional exchangeability. When no calibration station has similar
  geometry the effective sample size is small and the method widens or abstains, which is the
  intended signal of extrapolation.
- **Assumption, stated in the thesis.** The score distribution depends on the site only through its
  geometry features. This is checked, not assumed: C2-style held-out regions test it.
- **Compare with:** global split conformal (C1); weighted conformal under covariate shift (Tibshirani
  et al.); local spatial conformal (Mao, Martin and Reich); cluster-aware conformal calibration
  (Kim et al., 2026); conformal prediction for spatially dependent data (Sen and Saha, 2026).
- **Accept** if, on the sparse networks (weather and the large GHCN subset) over random region splits:
  coverage in the farthest distance tertile is within 0.03 of 0.90 (the global baseline is 0.84 to
  0.875 on the 30-station weather data), mean coverage is within 0.02 of 0.90, and mean interval
  width is at most 10% larger than the global baseline. **Do no harm:** on dense networks (Delhi,
  Beijing, PeMSD7-M, PeMS-BAY) coverage and width are not worse than the global baseline by more than
  0.01 and 5% respectively (paired).
- **Fallback:** if the geometry-aware method does not beat the baseline, the contribution becomes the
  measured characterisation of when distance matters (C2 extended to the large sparse network, with
  the within-station analysis), which is still a thesis result.

### WP2. Coverage-risk diagnostic (spine, part B)
- **Why not a total-variation bound.** C3 shows that total-variation distances between station score
  distributions cannot be estimated below about 0.13 with roughly 360 dependent scores per station,
  which exceeds the 0.10 miscoverage budget; and in the weather data they do not grow with distance.
  A bound charging total variation would be vacuous.
- **Method.** Estimate the **threshold-specific** shift instead: the difference between a site's
  score CDF and the calibration CDF at the conformal quantile, which is a lower-variance quantity.
  Fit an empirical map from site geometry to expected coverage loss with spatial-block
  cross-validation, with an explicit smoothness assumption and an uncertainty band. The output is a
  per-site "coverage-risk" estimate with a stated assumption, not a certificate. A conditional
  lower bound is reported only where the assumption is stated and tested.
- **Accept** if, over at least 20 held-out regions: the Spearman correlation between predicted and
  observed region coverage loss is at least 0.5, and the predictor has lower mean absolute error than
  the constant (global-mean) predictor by a paired test at the 5% level.
- **Fallback:** if coverage loss is not predictable from geometry, report that, with the diagnostic
  as a negative result.

### WP3. Scale: memory, time and coverage against N
- Measure peak memory and time against N in {325, 1,000, 2,000, 4,000, 8,600} for exact attention,
  the neighbour attention, and at least one published efficient model (for example STGformer), with
  fixed batch size and heads. Strengthen equivalence: neighbour-set agreement and agreement with
  trained weights, not random tokens.
- Evaluate coverage against N on PeMS-BAY, on the large sparse GHCN network from WP0, and, if usable,
  a LargeST subset, with at least 10 random splits per size.
- **Accept** if the neighbour attention uses at least 5x less peak memory than exact at N >= 2,000,
  the N at which exact attention runs out of memory is identified, neighbour-set agreement is >= 0.99,
  and mean marginal coverage stays within 0.02 of 0.90 at every size evaluated.
- **Fallback:** if no advantage appears, restrict the claim to equivalence; if no real network above
  325 sensors is usable, state evidence to 325 sensors. Replicated sensors are never used to claim
  coverage.

### WP4. Exceedance alerts with a controlled miss rate (impact demonstration)
- Use conformal risk control to choose the alert margin so that the miss rate among true exceedances
  (a pollutant category crossing, a heat threshold, congestion) at unseen sites stays below a stated
  level. Calibrate on exceedance cases at calibration stations, so the guarantee is conditional on an
  exceedance occurring. Thresholds come from the agencies' published categories, fixed before running.
- **Accept** if, over random splits, the mean miss rate is within 0.02 of or below the target and the
  false-alarm rate is reported against a naive threshold-on-point-forecast baseline.
- **Fallback:** report miss rate against the number of calibration exceedances, and where the sample
  is too small to control it.

### WP5. Baselines, protocol and package
- Official-code IGNNK (or INCREASE) with the same tuning budget as OmniST; a properly specified
  Gaussian-process baseline with its native intervals; a leakage-free spatial and temporal partition
  (Yang et al., 2025).
- Report every result as mean and 95% interval over random splits. No result is called a guarantee
  unless it is a theorem.
- A pip-installable **PyTorch** package with fit, calibrate and predict methods, tests and a worked
  example. **Accept** if it installs in a fresh environment and reproduces the Delhi result within the
  spread over splits.

### WP6. Thesis
- IIT Patna manual format, 60 to 70 pages, related-work chapter covering conformal prediction (graph,
  spatial, localised, risk control), inductive kriging, and efficient spatiotemporal models, with at
  least 30 verified references.

### Optional extensions (only if WP0 to WP4 are on schedule at the end of month 4)
- **X1. Portability.** After the local-frame fix, train in one city and calibrate on k stations of
  another (for example Delhi to Beijing), and report coverage against k. Calibrating any model on
  target stations is standard; the contribution would be how few calibration stations suffice, and
  the spread. Foundation-model backbones only if public checkpoints exist.
- **X2. Time-parallel state-space block.** Parallel prefix scan; accept only if equal to the
  sequential version within 1e-4 for T up to 960 and no slower than the GRU for T >= 240. Otherwise
  dropped. Not on the critical path.
- **X3. Sensor placement.** Use the coverage-risk estimate as a placement objective and compare with
  farthest-point and POD-QR placement by hiding existing sensors. Only meaningful in sparse networks.

## 4. Timeline (Semester 4)

| Month | Work | Exit check |
|---|---|---|
| 1 | WP0: V1b, local frame, large sparse network, LargeST check, T1 | V1b attention gate recorded; data decision made |
| 2 | WP1 design and implementation; first results on weather | Pool construction and localised quantile working |
| 3 | WP1 evaluation on all networks; WP2 diagnostic | WP1 and WP2 acceptance or fallback declared |
| 4 | WP3 memory and coverage against N; WP4 alerts | WP3 and WP4 results with spread over splits |
| 5 | WP5 baselines and package; optional X1 or X2 if on schedule | Package installs and reproduces the example |
| 6 | WP6 write-up; final literature re-scan; supervisor review | Thesis draft complete |

If time runs short, the optional extensions go first, then the baseline breadth in WP5. WP1, WP3 and
WP6 are protected.

## 5. Novelty assessment of the candidate ideas

Prior work was checked against arXiv metadata in November 2026. The searches were targeted, not an
exhaustive review.

| Idea | Verdict | Reasoning |
|---|---|---|
| 1. Geometry-aware conformal for chosen sites | **Adopt (WP1), with reduced claims** | Close prior art exists: local spatial conformal (Mao et al.), cluster-aware calibration by sampling density (Kim et al., 2026), randomised localisation (Hore and Barber), weighted conformal (Tibshirani et al.), and a spatial-dependence method (Sen and Saha). "The shift is known" holds for a design distribution of sites, not for one chosen site, so localisation rather than a density ratio is the right tool. The defensible contribution is the combination for a deep inductive forecaster: geometry features relative to the training network, spatial-block calibration pool, evaluation under region holdout, and the honest finding that it matters only in sparse networks. |
| 2. Coverage lower bound from geometry | **Adopt in reformulated form (WP2)** | The plug-in-diagnostic template exists (Zhu et al., 2026, for language models). A total-variation bound is vacuous here (C3). A threshold-specific, empirically validated risk estimate with a stated assumption is feasible; a certificate is not claimed. |
| 3. Portability across networks | **Optional (X1)** | The premise that coordinate tokenisation already supports it is false as implemented (Delhi constants). Calibrating a foreign model on target stations is standard; the question is how few stations suffice. Foundation-model wrapping depends on public checkpoints. |
| 4. Actionable alerts | **Adopt as demonstration (WP4)** | Cheap and useful. Conformal risk control is established (Angelopoulos et al.) and applied to wildfire and alarm settings; the unseen-site, topology-changing case was not found. Incremental. A related paper maps exceedance probability and placement without a guarantee (Snaiki and Merabtine, 2026). |
| 5. Sensor placement | **Stretch (X3)** | Placement work exists without guarantees. The objective is only informative where distance matters (sparse networks), and evaluation by hiding sensors risks circularity. |
| Cut: SSM versus GRU crossover | **Demoted (X2)** | Measured 2x slower; a result that it matches the GRU adds little. |

## 6. Risks

- **The geometry effect is narrow.** C2 found a distance effect in one 30-station network. WP0 builds
  a large sparse network to test it properly; if the effect does not replicate there, WP1 becomes the
  characterisation fallback.
- **Data quality.** The GHCN subset may have too many gaps; the fallback is a smaller curated set.
- **Small effective calibration size.** Localised calibration can leave few calibration stations near
  a site. The spatial-block pool addresses this; the method abstains when it cannot.
- **Conditional exchangeability** (score depends on site only through geometry) may fail. It is
  tested, not assumed, and the claim is scoped to where it holds.
- **Scope.** WP0 to WP6 fill a semester. Optional extensions are cut first.
- **Fast-moving area.** Re-scan at the start of month 1 and before submission.
