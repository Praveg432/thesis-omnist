# Thesis Completion Plan: 12 weeks (16 Nov 2026 to 7 Feb 2027)

Replaces the timeline in `phase2-omnist-scale/docs/RESEARCH-PLAN.md` Section 4, which assumed six
months, and revises its work packages in light of the 15 Nov measurements
(`phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`) and a prior-art scan on 16 Nov 2026.
Acceptance thresholds are fixed now. They may be tightened, never loosened, after seeing results.
Scope is subject to supervisor approval.

## 0. Status and action register (17 Nov 2026)

The title and abstract were submitted and finalised on 17 Nov 2026. Nothing in Sections 3 to 4 has been started yet (week 1 begins
now). Section 0 lists what is left; Sections 1 to 9 give the reasoning and acceptance criteria.

### Phase 1 (OmniST): complete, with these items left

| ID | Item | Why | Week | Done when |
|---|---|---|---|---|
| P1-1 | Re-run C1 with chronological calibration; save per-station scores | C1 calibrates on errors from the test period (2.2). The submitted abstract quotes 87.6% to 90.6% | 1 | Both protocols tabulated. If the range moves by more than 0.01, file an abstract revision request |
| P1-2 | Re-test the baseline comparison, dropout robustness, drift handling and the 7-sensor run under C1 | Still on the original protocol (1 to 2.5 points optimistic) | 1 to 3 | Each claim restated or withdrawn in the thesis chapter |
| P1-3 | Local coordinate frame replacing the Delhi constants | Needed for GHCN and real PeMS-BAY coordinates | 1 | Tests pass; Phase 1 numbers unchanged within noise |
| P1-4 | Decide on a revised preprint (arXiv:2611.04256 overstates relative to C1) | Public claim exceeds evidence | decide wk 1, post after wk 4 | Decision recorded in `FINALIZATION-RECORD.md` |
| P1-5 | Verify references [1], [3], [4], [5] venue details; check the two traffic datasets' raw files can be recovered | Open items in the finalization record, Section 4 | 9 to 11 | Reference list verified |

### Phase 1 closure plan (before the Semester 3 progress report is submitted)

Goal: the report states every Phase 1 number under a protocol it can defend, and lists what is still
untested. Phase 1 numbers are produced with the legacy coordinate frame, so they stay comparable with
the submitted abstract. Report submission window: **20 to 30 Nov 2026**. The earliest date is 20 Nov, so S1 to S3 and S9 come first and S4, S5 only if time allows.

| Step | Work | Output | Effort |
|---|---|---|---|
| S1 | **Write C1b_chronological_eval.py** (new script in phase1-omnist/experiments; leaves committed C1 files untouched). Same splits, seeds and models as C1. For each test window t, the quantile uses calibration-station scores from windows before t only (expanding window), and only windows after a warm-up of the first 25% are scored. Same-window and pooled-over-time coverage are recomputed on exactly those windows for a like-for-like comparison. Per-station, per-window scores are saved. Targets of window t-1 end at the origin of window t (stride equals horizon), so no future target is used. Add tests: planted-shift check (the chronological quantile under-covers when scale grows, same-window does not) and a no-leak check | script, 3 to 5 tests, quick-mode run | 0.5 day |
| S2 | **Pre-registered decision rules, written before the full run.** (a) Chronological mean coverage within 0.02 of 0.90 per dataset: claim stays "consistent with nominal". (b) If any dataset's mean moves by more than 0.01 from the C1 value, or the range 87.6% to 90.6% changes, file an abstract revision request. (c) If a dataset falls below 0.85, report it as under-coverage in the report and thesis | rules in this file | 0.1 day |
| S3 | **Full C1b runs.** Delhi, Beijing, weather (20 splits each, about 15 to 25 minutes per dataset), then PeMSD7-M and PeMS-BAY (6 splits each, run overnight). Resumable | five result files, one per dataset | 1 day, mostly unattended |
| S4 | **Cheap baselines under C1 splits.** Re-run nearest-neighbour and inverse-distance interpolation, persistence and seasonal-naive on the C1 test stations with disjoint calibration, same splits. No training needed. IGNNK on Delhi only if time allows | table: OmniST vs baselines under C1 | 0.5 day |
| S5 | **Local coordinate frame (P1-3), now a defect fix, not an option.** The Delhi constants put inputs up to 656 units out on four of five networks and inflate MAE and width (`FINALIZATION-RECORD.md`, Section 12). Done: frame option in both phases (default legacy), 9 tests. C1b with the training-station frame is complete on all five networks (Section 12 of the record): met on four networks, PeMSD7-M misses the same-window coverage criterion by 0.001. Chronological under-coverage on Delhi and Beijing is unchanged by the frame. **Done when:** coverage within 0.01 of the legacy frame on every network under the same-window protocol; MAE and width reported before and after, PeMSD7-M included. Then decide which frame the report and thesis use (proposed: the training-station frame, with the legacy results kept as a record) | code, tests, five C1b norm files | 0.5 day plus run time |
| S6 | **Items not re-run before the report, stated as such:** dropout robustness, drift handling, the 7-sensor large-network run, E-STGCN comparison. They stay labelled original-protocol and are scheduled in plan weeks 2 to 3 (P1-2) | report limitation text | 0 |
| S7 | **Preprint decision (P1-4).** After S3, compare the preprint abstract's claims (90% or above under 30 to 50% dropout and at 325 sensors) with C1 and C1b. Draft a correction paragraph; the decision to post v2 is yours and is recorded in `FINALIZATION-RECORD.md` | decision note | 0.2 day |
| S8 | **References (P1-5).** Verify venue, year and pages of [1], [3], [4], [5] against the publisher or DBLP | verified list | 0.2 day |
| S9 | **Update the report.** Add the C1b table to Section 4; replace the Section 6 plan (WP0 to WP6) with the contributions A to D and the 12-week schedule; update Phase 1 status and limitations; regenerate the PDF with `tools/md_to_pdf.py`; run all checkers. The abstract is not touched unless S2(b) triggers | report .md and .pdf | 0.5 day |

**Progress (17 Nov 2026):** S1 and S2 done (chronological module, 8 passing tests, C1b script, quick run
OK; decision rules are in the script header). S3 done for all five datasets (`FINALIZATION-RECORD.md`, Section 11).
Result: chronological coverage is 0.777 (Beijing), 0.818 (Delhi), 0.869 (PeMSD7-M), 0.869 (PeMS-BAY),
0.889 (weather). Rule (c) fired on Delhi and Beijing and rule (b) on four datasets, so the **abstract
revision (S2 rule b) was triggered and has been applied**. **Status of the Phase 1 closure plan (17 Nov 2026): S1 to S9 done**
(`FINALIZATION-RECORD.md`, Sections 11 to 13). Diagnosis (C1d): the under-coverage follows error growth
over the test period (late over early error 1.90 Delhi, 2.11 Beijing), not station mismatch. Baselines
(C1c) under-cover the same way. The report is updated and its PDF regenerated; the abstract is unchanged
and its coverage sentence was revised on 17 Nov 2026 (`SUBMISSION-TITLE-AND-ABSTRACT.md`, Section 6); further
revisions are expected in the final thesis. Phase 1 carries into Semester 4 only these items: the S6 re-runs (dropout, drift, 7-sensor,
E-STGCN, interpolators), C2 and C3 with the corrected frame, and the preprint revision.
Per-window scores for rolling-window and adaptive rules are saved in the C1d result files and feed
contributions A and B.

Schedule (for a 22 Nov target, with 30 Nov as the hard limit): 17 to 18 Nov S1, S2; 18 to 20 Nov S3 (start Delhi, Beijing, weather first), S5, S8; 19 to 20 Nov S4; 20 to 21 Nov S7, then S9; 22 Nov buffer and submission. If the date is earlier, S5 and S4 are cut first (both are Semester 4 items anyway); S1 to S3, S9 are not cut.

Exit check for Phase 1: C1b exists for all five datasets; the report's coverage claims state which
protocol they come from; `check_report_numbers.py` is extended to cover the C1b figures and passes;
open Phase 1 items are listed in the report as limitations.

### Phase 2 (OmniST-Scale): done so far

V2 attention equivalence, V3 coverage against N, V3b training budget, V4 memory and time, T1 state-space
timing. State-space block and X2 dropped. WP2 as a separate contribution dropped.

### Phase 2: remaining action plan

| ID | Work | Weeks | Gate and accept rule | Fallback |
|---|---|---|---|---|
| P2-0 | V1b parity gate (10 seeds, `gru+fast` vs `gru+exact`) | 1 | Paired equivalence within the margins in `phase2-omnist-scale/docs/RESEARCH-PLAN.md` | If it fails, report neighbour attention as a different model, not a drop-in |
| P2-1 | GHCN sparse network: download, quality filter, G0 replication test | 2 | G0: far tercile at least 0.03 below near tercile over 20 or more region splits | C becomes characterisation only |
| P2-2 | G2: diagnose the 21% width gap to seasonal-naive on PeMS-BAY | 2 | Cause identified by horizon, time of day and station | Limitation stated |
| P2-3 | Contribution A: hierarchical conformal (HCP and second-moment variant) on six networks | 3 to 5 | Mean coverage within 0.02 of 0.90 on every network; share of stations below 0.80 halved at most 15% wider | Trade-off curve |
| P2-4 | Contribution B: new-sensor cold start to warm (HCP, Generalized HCP, own-data split conformal, ACI), k = 0 to 60 days | 3 to 7 | Coverage within 0.03 at every k; at least 5% narrower at the largest k on 4 of 6 networks | Coverage and width against k curves |
| P2-5 | Contribution D: combined forecast, locally scaled scores, quantile head | 4 to 7 | Width at most conformalised seasonal-naive at deployable coverage within 0.02 | Limitation stated |
| P2-6 | Contribution C, only if G0 passes: geometry-aware calibration against whitening and local spatial conformal | 6 to 7 | Far tercile within 0.03; mean within 0.02; width at most +10%; not worse than whitening | Characterisation |
| P2-7 | Alerts demonstration (one air-quality network), IGNNK official-code baseline, LargeST compute scaling, coverage against N on GHCN | 8 to 9 | Tables final | Cut in this order after C: alerts, scale |
| P2-8 | Reproducibility pass in a fresh environment, one headline table | 9 | Table reproduces | n/a |
| T-1 | Thesis writing: chapters 1 to 3 from week 6, chapters 4 to 9 weeks 10 to 11, supervisor review week 11, final formatting and slides week 12 | 6 to 12 | Submission-ready 7 Feb 2027 | n/a |

Cut order if time runs short: C, then alerts, then scale. A, B, D diagnosis and the writing are protected.

### Open decisions (author or supervisor)

1. Supervisor approval of this scope and of the title.
2. Whether to post a revised preprint, and when (proposed: after week 4).
3. Whether to keep C if G0 fails (proposed: no).
4. Abstract revision request if P1-1 moves the quoted coverage range.

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
8. Scale: equivalence, memory and time, coverage against N; negative results (state-space block).
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
| "Why are there negative results?" | Pre-registered criteria; negative results are findings (state-space block, WP2, and any failed gate) |

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
