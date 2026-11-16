# Thesis Completion Plan: 12 weeks (16 Nov 2026 to 7 Feb 2027)

Replaces the timeline in `phase2-omnist-scale/docs/RESEARCH-PLAN.md` Section 4, which assumed six
months, and revises its work packages in light of the 15 Nov measurements
(`phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`) and a prior-art scan on 16 Nov 2026.
Acceptance thresholds are fixed now. They may be tightened, never loosened, after seeing results.
Scope is subject to supervisor approval.

## 1. Bottom line

- **Done:** Phase 1 (OmniST, five real networks, C1 to C3, preprint, 50 tests); Phase 2 measurements
  V2, V3, V3b, V4; title and abstract; consolidated records.
- **Not yet defensible:** the thesis's central claim. Its coverage numbers are approximate (station
  scores are pooled as if independent), are computed with contemporaneous calibration (see 2.2), vary
  widely by station (per-station minimum 0.40 to 0.86), and the intervals lose to a seasonal forecast
  on traffic. The current Phase 2 spine (WP1 geometry-aware calibration, WP2 risk diagnostic) now has
  close, recent prior art (2.6).
- **Proposed spine:** *valid and useful intervals at a new sensor, from the day it is installed.* Four
  contributions, each with a fallback that is still a result:
  - **A.** station-level validity that is exact rather than approximate;
  - **B.** how coverage and width change as a new sensor accumulates its own data;
  - **C.** where the sensor's position matters, and whether calibration that uses it helps;
  - **D.** whether the intervals beat simple forecasting baselines, and how to make them.
- **Novelty, honestly:** no single component is new statistics. What is new is applying them, with
  the temporal adaptations they need, to deep forecasting at unseen sensors in changing networks, with
  a forecast-time-only protocol across six real networks. The prior-art scan found no paper doing A or B
  in this setting. That is an evaluation-and-methods thesis, which suits an M.Tech and matches the
  submitted abstract.

## 2. What is missing from the current Phase 2 plan

| # | Gap | Evidence | Fix in this plan |
|---|---|---|---|
| 2.1 | **Station-level validity is only approximate.** Pooled split conformal treats each station's hundreds of dependent scores as separate points. | `RESEARCH-PLAN.md` Section 1 says so; effective calibration size is 3 to 45 stations | **A:** hierarchical conformal prediction (Lee, Barber and Willett, arXiv:2306.06342) gives exact coverage for an observation from a *previously unseen group*, here a station, under hierarchical exchangeability, with any dependence inside the group |
| 2.2 | **Phase 1 coverage uses contemporaneous calibration.** C1 computes the quantile on the calibration stations' errors over the same test period it evaluates, so a forecast at time t uses calibration errors from after t. | Docstring of `phase1-omnist/experiments/C1_rigorous_inductive_eval.py`, line 18 | **Week 1:** re-run C1 with chronological calibration (calibration errors from before the forecast time only). Report both. The abstract's figures are C1's; if they move by more than 0.01, update the abstract (the checker will flag it) |
| 2.3 | **Per-station coverage is not controlled.** Mean coverage is near target, but some stations sit far below it. | C1 per-station minimum 0.40 to 0.86 | **A:** the "second-moment coverage" variant of hierarchical conformal, which bounds per-group miscoverage spread. Measure the share of stations below 0.80 |
| 2.4 | **No account of a sensor's first weeks.** The plan treats a new sensor as permanently unseen. In practice it starts producing data the day it is installed. | Not in plan | **B:** cold start with hierarchical conformal; warm-up with Generalized HCP (arXiv:2608.15500), which uses a new group's first observations; compared with per-station adaptive conformal inference |
| 2.5 | **Usefulness is not a work package.** Width is reported but nothing targets it, and the intervals are 21% wider than seasonal-naive on PeMS-BAY. | V3, V3b | **D:** seasonal-naive and persistence as required baselines everywhere; locally scaled scores and a seasonal-residual variant |
| 2.6 | **WP1 and WP2 now face close prior art.** Sequential whitening (Saha et al., arXiv:2610.10168, Oct 2026) gives exact coverage under any spatial design given a correct covariance, plus a diagnostic for regions at risk of undercoverage, with a PM2.5 application. Plus Mao, Martin and Reich; Kim et al. 2026; Hore and Barber. | Scan of 16 Nov | **C** keeps WP1 only as a gated comparison on sparse networks with whitening as a baseline. WP2 as a separate contribution is dropped; its question is absorbed into C's diagnostic |
| 2.7 | **Temporal drift under deployable calibration is unhandled.** Synthetic N=4,000 deployable coverage was 0.880 at the band edge. | V3 | **A/B:** chronological calibration with a rolling window, and adaptive conformal inference over time as an option |
| 2.8 | **The schedule assumes six months.** | `RESEARCH-PLAN.md` Section 4 | This plan: 12 weeks, writing from week 6 |
| 2.9 | **The public preprint claims more than C1 supports.** | `FINALIZATION-RECORD.md` | Decide in week 1; post a revised version once A and 2.2 are settled (about week 4) |

## 3. Contributions, methods and gates

"Splits" means at least 20 random station splits, or region splits on sparse networks. Every result is
reported as mean and 95% interval over splits, under the chronological (forecast-time-only) protocol,
with pooled split conformal as the reference.

### A. Exact station-level coverage at unseen sensors (core; weeks 1 to 5)
- **Method.** Hierarchical conformal prediction with the station as the group. The time series inside a
  station need not be exchangeable for the group-level guarantee. Implement two versions: HCP
  (one-score-per-station-equivalent weighting; marginal over stations) and the second-moment variant,
  which needs exchangeable repeated measurements within a station. For the second, form within-station
  measurements from temporally separated windows (a gap of at least the autocorrelation length) and
  state the assumption.
- **Data.** All five Phase 1 networks plus the large sparse GHCN network (G0).
- **Accept if:** (a) HCP mean coverage is within 0.02 of 0.90 on every network; (b) the second-moment
  variant halves the share of stations below 0.80 coverage relative to pooled split conformal, with mean
  width at most 15% larger. (a) makes the validity statement exact; (b) is the useful improvement.
- **Fallback:** if (b) fails, report the per-station trade-off curve (width against worst-station
  coverage). (a) alone still replaces an approximate claim with an exact one under a stated assumption,
  which is the main defensibility gain.

### B. A new sensor's first weeks: cold start to warm (core, novel; weeks 3 to 7)
- **Question.** At installation the sensor has no history (cold start). After k days it has k days of
  its own residuals. How should calibration move from network-level to sensor-level, and how fast does
  coverage and width improve?
- **Method.** Simulate installation by revealing a held-out station's history day by day. Compare: (i)
  cold HCP, ignoring the new data; (ii) Generalized HCP using the first k days; (iii) split conformal on
  the station's own k days; (iv) adaptive conformal inference started from the HCP interval. k from 0 to
  60 days (traffic: 0 to 14 days at 30-minute cadence).
- **Accept if:** for every k on the grid, (ii) or (iv) keeps coverage within 0.03 of 0.90 and has width
  no larger than (i), and is strictly narrower than (i) by at least 5% by the largest k on at least four
  of six networks.
- **Fallback:** report the coverage and width against k curves for all four methods; the crossover
  point (when own-data calibration overtakes network calibration) is itself the finding.
- **Related work to cite:** cold-start forecasting at unseen traffic sensors with a short support period
  (SC-SAMG, *Sensors* 2026), point forecasting only.

### C. Where position matters (gated; weeks 2 to 7)
- **Gate G0 (week 2).** The large sparse GHCN network exists (300 to 1,500 stations after quality
  filtering) and, over at least 20 region splits, far-tercile coverage is at least 0.03 below near-tercile
  under pooled calibration (as in the 30-station weather data). If not, C becomes the characterisation:
  "distance did not matter at scale", with the C2 analysis extended.
- **Method if G0 passes.** WP1 as specified (spatial-block calibration pool, geometry-weighted
  localisation with randomised localisation), plus a station-level variant built on A.
- **Baselines:** pooled split conformal, HCP, sequential whitening (arXiv:2610.10168; code if released,
  otherwise the nearest-neighbour version as described), local spatial conformal (Mao, Martin and Reich).
- **Accept (fixed in the current plan, unchanged):** far-tercile coverage within 0.03 of 0.90, mean
  within 0.02, width at most +10%; on dense networks no worse than baseline by 0.01 and 5%. **Plus:**
  not worse than sequential whitening on far-tercile coverage at equal mean width.
- **Fallback:** characterisation, and an honest comparison showing which existing method handles the
  sparse case.

### D. Useful as well as valid (weeks 2 to 8)
- **Gate G2 (week 2): diagnose the seasonal-naive gap on PeMS-BAY.** Break down width and coverage by
  horizon, time of day and station; check whether a heavy error tail at a few stations drives the
  quantile.
- **Methods (in order of cost):** (1) a combined base forecast (OmniST plus seasonal-naive, weight fit on
  training stations); (2) locally scaled scores (residual divided by a per-window predicted scale); (3) a
  quantile head (conformalised quantile regression).
- **Accept if:** on PeMS-BAY and PeMSD7-M, the best variant's mean width at deployable coverage within
  0.02 of 0.90 is at most that of conformalised seasonal-naive, and on the air-quality and weather
  networks it is at most that of conformalised persistence and seasonal-naive. The method is chosen on
  validation splits before test splits are scored.
- **Fallback:** report the limitation; the thesis does not claim usefulness where it fails.
- **Decision demonstration (small, week 8):** threshold alerts with a controlled miss rate (the old
  WP4), on one air-quality network only, using the best interval from A and D.

### Supporting work (weeks 1 to 9)
- **V1b** (paired equivalence of `gru+fast` and `gru+exact`, 10 seeds, margins as in the plan): week 1.
- **Local coordinate frame** replacing the Delhi constants: week 1; required for GHCN and for PeMS-BAY
  with real coordinates.
- **Scale (trimmed WP3):** LargeST compute scaling only (memory and time to 8,600 sensors, the point where
  exact attention runs out of memory), plus coverage against N on GHCN. Weeks 7 to 9. The comparison with a
  published efficient model is optional.
- **Baselines (trimmed WP5):** seasonal-naive and persistence (required, everywhere); IGNNK official code
  (required, one tuning budget); a Gaussian-process baseline with native intervals on the two air-quality
  networks (optional).
- **Code:** an installable repository with a worked example reproducing one headline table. A PyPI package
  is not promised.

### Dropped or deferred from the current plan
- WP2 as a separate contribution (overlaps sequential whitening's diagnostic; C3 already showed a
  total-variation bound is vacuous). Kept as a short negative result in the thesis.
- X1 portability, X2 time-parallel state-space block (criteria already failed), X3 sensor placement.
- Comparison with a published efficient model (optional).

## 4. Schedule

| Week | Dates | Work | Exit check |
|---|---|---|---|
| 1 | 16 to 22 Nov | Save per-station scores in C1; chronological re-run of C1 (2.2); HCP pilot on Delhi and PeMS-BAY; V1b; local frame; preprint decision | **G1:** HCP implemented and matches pooled within 0.02 on the pilot, or the difference is explained; chronological C1 numbers recorded |
| 2 | 23 to 29 Nov | GHCN download and quality filter; G0 replication test; seasonal-naive diagnosis (G2) | **G0** and **G2** decided and recorded |
| 3 | 30 Nov to 6 Dec | A on all five networks; second-moment variant; B design and simulation harness | A results on five networks |
| 4 | 7 to 13 Dec | A on GHCN; B runs (cold, GHCP, own-data, ACI); D method 1 | A accepted or fallback declared; revised preprint if needed |
| 5 | 14 to 20 Dec | B on all networks; D methods 2 and 3 | B curves complete |
| 6 | 21 to 27 Dec | C (if G0 passed) with whitening baseline; start thesis chapters 1 to 3 (introduction, background, related work) | B accepted or fallback declared |
| 7 | 28 Dec to 3 Jan | C evaluation on sparse and dense networks; D evaluation | C and D accepted or fallback declared |
| 8 | 4 to 10 Jan | Alerts demonstration; IGNNK baseline; LargeST compute scaling | All result tables final |
| 9 | 11 to 17 Jan | Coverage against N on GHCN; reproducibility pass (fresh environment, one headline table) | Repository reproduces the headline table |
| 10 | 18 to 24 Jan | Thesis chapters 4 to 7 (OmniST, contributions A to D, scale) | Full draft |
| 11 | 25 to 31 Jan | Supervisor review; literature re-scan; corrections; checkers re-run against final numbers | Revised draft |
| 12 | 1 to 7 Feb | Final formatting to the manual; defence slides; buffer | Submission-ready |

Compute is not the constraint: every experiment so far runs in minutes to under an hour on the M4 Pro.
The critical path is weeks 1 and 2. If either gate slips, C is cut first, then the alerts demonstration,
then the scale work. **A, B and the writing are protected.**

## 5. Thesis chapter outline (60 to 70 pages)

1. Introduction: problem, the three questions, contributions A to D.
2. Background: conformal prediction (split, weighted, localised, hierarchical, adaptive over time,
   risk control), spatiotemporal forecasting and kriging.
3. Related work: graph and spatial conformal, sequential whitening, cold-start forecasting, efficient
   spatiotemporal models; at least 30 verified references.
4. OmniST and the evaluation protocol: Phase 1, random-split and chronological protocols, C1 to C3.
5. Exact station-level coverage (A).
6. A new sensor's first weeks (B).
7. Where position matters (C) and useful intervals (D), with the alerts demonstration.
8. Scale: equivalence, memory and time, coverage against N; negative results (state-space block,
   retired fusion).
9. Conclusion, limitations, future work.

## 6. Questions an examiner will ask, and where the answer comes from

| Question | Answer after this plan |
|---|---|
| "Your coverage is approximate; why call it calibrated?" | A makes it exact at the station level under a stated assumption, tested empirically |
| "Your calibration used future data." | 2.2: chronological re-run, both reported |
| "Average coverage hides bad stations." | A's second-moment variant and the per-station distribution |
| "Why not just use a seasonal forecast?" | D: compared everywhere; limitation stated where it holds |
| "What is new over hierarchical conformal or sequential whitening?" | Their use for deep forecasting at unseen sensors with time-dependent scores, the cold-to-warm analysis (B), and a six-network forecast-time-only evaluation. The statistics are cited, not claimed |
| "What happens when a sensor has been running for a month?" | B |
| "Does it scale?" | Memory and time to 8,600 sensors (LargeST); coverage to about 1,000 real stations (GHCN); limits stated |
| "Why are there negative results?" | Pre-registered criteria; negative results are findings (state-space block, fusion, WP2, and any failed gate) |

## 7. Fit with the submitted title and abstract

No change is needed. A, B and C answer the first open question, the scale work answers the second, and
D plus the alerts demonstration answer the third. The contributions sentence (forecast-time-only protocol,
characterisation of failures, methods tried with measured effect, reproducible code) covers all four. Two
things to revisit at final submission: if A succeeds, the abstract's "marginal and approximate" can become
"marginal, and exact at the station level under a stated assumption"; and if the chronological C1 re-run
moves the 87.6% to 90.6% range, the abstract's numbers must be updated
(`tools/check_submission_text.py` will fail until they are).

## 8. Decisions needed now

1. Supervisor approval of this scope (replacing the six-month timeline).
2. Revise the public preprint, and when (proposed: after week 4).
3. Whether C is kept if G0 fails (proposed: no; characterise only).

## 9. Prior work found on 16 Nov 2026 (to verify in full before citing)

- Lee, Barber and Willett. Distribution-free inference with hierarchical data. arXiv:2306.06342 (v4, Aug 2025).
- Mallick et al. Generalized hierarchical conformal prediction. arXiv:2608.15500 (Aug 2026).
- Saha et al. Conformal prediction for spatially dependent data via sequential whitening. arXiv:2610.10168 (Oct 2026).
- Cold-start traffic state forecasting at unseen sensor locations via support-conditioned meta-graph
  learning (SC-SAMG). *Sensors* 26(15):4995 (2026).
- Already in the plan: Mao, Martin and Reich (local spatial conformal); Kim et al. 2026 (cluster-aware
  conformal, arXiv:2606.06753); Hore and Barber (randomised localisation); Tibshirani et al. (weighted
  conformal); Angelopoulos et al. (conformal risk control).
