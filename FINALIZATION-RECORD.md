# Finalization Record: Verification of the Work and Review Corrections

This record states what was checked, how, and what was not checked. It distinguishes results **run
live in this repository** from results **read from committed result files**, and lists the changes
made after a preliminary review and a novelty assessment.

## 1. Environment

| Item | Value |
|---|---|
| Machine | Apple M4 Pro, MPS available |
| Python | 3.14.3 |
| torch / numpy / pandas / scikit-learn / matplotlib | 2.13.0 / 2.4.6 / 3.0.3 / 1.9.0 / 3.10.9 |
| Repository | https://github.com/Praveg432/thesis-omnist, branch `main` |

## 2. Checks run live

| Check | Result |
|---|---|
| Phase 1 tests | 50 of 50 passed: 13 original, 12 for the distance-analysis code (including a planted-slope check and a station-confound check), and 25 integrity checks on the C1, C2 and C3 result files |
| Phase 2 tests | 18 of 18 passed (4 original, 14 added for the review fixes and the verdict logic) |
| Experiment C1 (random disjoint-station evaluation), five datasets | Completed: Delhi 20 splits, Beijing 20, weather 20, PeMSD7-M 6, PeMS-BAY 6 |
| Experiment C2 (contiguous-region holdout, coverage against distance), five datasets | Completed with the same split counts. Within-station analysis computed from C1 and C2 together. |
| Experiment C3 (total-variation distance between station score distributions) | Completed for Delhi and weather, 5 models each |
| Diagnostic T1 (state-space block against GRU timing), idle machine | State-space 29.0, 115.7, 462.3 ms against GRU 14.0, 53.3, 233.7 ms at T = 60, 240, 960 |
| V1b smoke test (quick mode) | Runs end to end and returns INCONCLUSIVE for one seed, as it should. **No V1b result exists.** |
| Defects reproduced and fixed | Neighbour-cache key collision; a verdict rule that reported a coverage collapse as INCONCLUSIVE instead of NO-GO |
| Inventory of GHCN-Daily TMAX stations | 7,435 stations in the contiguous US with records spanning 2019 to 2023 (inventory file only; the daily series were not downloaded) |
| Number check (`tools/check_report_numbers.py`) | Every C1 and C2 table entry, the C3 figures, the V1 and T1 figures, the V2 minimum cosine and the IGNNK errors quoted in the report and proposal match the result files |
| Link and path audit (`tools/audit_links.py`) | 21 Markdown files, 0 broken links, 0 missing paths |
| Number check | Verified 25 quoted figures; deliberately corrupting one number made it fail with exit code 1 |
| Submission text check (`tools/check_submission_text.py`) | Title identical in README, proposal and report; 15 words and within the manual's rules; abstract 580 words (limit 600) and identical in README and report; the abstract's coverage range and slope tie to the result files; deliberately breaking the title made it fail |
| References 1 to 6 | Titles and authors checked against arXiv metadata |
| C2 geometry | Regions and distances recomputed independently from the raw station coordinates for Delhi, Beijing and weather |

## 3. Checked by reading committed result files, not re-run

| Claim | Source file | Verified value |
|---|---|---|
| Original-protocol coverage on four datasets | `exp_multidomain_v2.json` | Delhi 0.9139 (10 seeds), Beijing 0.9275 (10), weather 0.9193 (10), PeMSD7-M 0.9150 (6); sample standard deviations 0.006, 0.003, 0.007, 0.009 |
| Comparison with four interpolators | `exp_baselines.json` | OmniST 0.914, 0.927, 0.919, 0.911; each interpolator below 0.90 on at least one dataset |
| Dropout coverage | `exp_multidomain_v2.json` | Dataset means 0.912 to 0.931; seeds down to 0.89 |
| IGNNK comparison (Delhi) | `exp_ignnk_inductive.json` | MAE 26.67 against 34.00, 21.5% lower, 5 seeds |
| Fixed-adjacency baseline | `exp_estgcn_controlled.json`, `exp_fixedtopo_crash_demo.json` | Cannot predict at unseen sensors; does not run under 30% or 50% dropout |
| Drift | `exp_temporal_conformal.json` | Worst-window coverage 0.498 (static) against 0.962 (rolling adaptive) |
| Large network, original protocol | `exp_largeN_pemsbay.json` | Coverage 0.9207, **7 held-out sensors**, 3 seeds, identical split |
| First parity check (preliminary) | `V1_ssm_matches_omnist_results.json` | MAE 64.56 and 65.62; coverage 0.948 and 0.944 |
| Attention equivalence | `V2_attention_equivalence_results.json` | Minimum cosine 0.999874 for N = 37 to 2,000 |

## 4. Not verified, and weaknesses of what was measured

- **V1b has not been run in full**, and the first parity check (V1) was not re-run.
- **The distance effect rests on one network.** C2 found a coverage decline with distance only in the
  30-station weather data. It was not tested in any other sparse network. Beijing's positive
  correlation is probably confounded by station type (12 stations).
- **C2 and C3 sample sizes.** C3 used 5 models per dataset and a 10-bin histogram estimator; its noise
  floor is the main finding. Correlation p-values from C2 are optimistic because stations repeat
  across splits; the within-station slopes use a bootstrap over stations.
- **Traffic distances.** Coordinates of the two traffic datasets are reconstructed from distance
  matrices and have heavy-tailed density, so their distances are not comparable with the others.
- **The large sparse network does not exist yet.** Only the station inventory was checked. Whether the
  daily series are complete enough, and whether they load, is unknown.
- **Novelty claims rest on limited searches.** Prior work was checked through arXiv metadata and a few
  web searches in November 2026, not through a systematic review, and abstracts only. The plan states
  the close prior art that was found.
- **LargeST availability and licence were not checked.**
- **Other Phase 1 experiments** (baseline comparisons, dropout robustness, drift, the 7-sensor run)
  were not repeated under C1.
- **The public preprint states stronger claims** than the C1 results support: its abstract says the
  guarantee holds at 90 percent or above under 30 to 50 percent node dropout and at 325 sensors,
  whereas C1 mean coverage ranges from 0.876 to 0.906 across datasets. Whether to post a revised
  version is the author's decision; this repository does not change the preprint.
- The baselines E-STGCN and IGNNK are the author's re-implementations, and equal tuning effort has not
  been verified.
- The year-feature check in C1 was uninformative by construction (the temporal embedding is periodic,
- Venue and page details of references [1], [3], [4] and [5] were not verified; arXiv confirms only titles
  and authors.
- The C2 regions and distances could not be recomputed for the two traffic datasets from a fresh clone,
  because their raw files are gitignored.
- The title and the Semester-4 scope have not been approved by the supervisor.
  so 0.0 and 1.0 are identical).

## 5. Corrections made

| Finding | Correction |
|---|---|
| "Certified" coverage rested on training-station calibration and a few fixed held-out stations | C1 added; coverage defined as approximate marginal coverage with the station as the exchangeable unit; the original-protocol numbers relabelled as the record; the word "certified" removed from the title and abstract in favour of "calibrated" |
| Three of five C1 means sit below 0.90 | Wording changed from "supports" to "consistent with the nominal level"; mild under-coverage stated as not excluded |
| The large-network result used 7 held-out sensors | Stated in every document; C1 evaluates PeMS-BAY with 45 test sensors per split |
| The state-space block is sequential and about twice as slow as the GRU | Descriptions corrected; T1 added; the block is an optional extension in the plan |
| The attention was called provably equivalent, with no memory evidence | Described as numerically equivalent on random inputs; memory and speed advantages stated as not yet shown |
| The first parity check could not fail | Marked preliminary; V1b added with paired equivalence, fixed margins, and a separate gate for the attention swap |
| The V1b verdict rule mishandled a coverage drop | New `parity_verdict` function with tests; a coverage departure in either direction is NO-GO |
| Neighbour cache key could collide; cache unbounded | Content hash and size limit; regression tests |
| The coordinate embedding uses Delhi constants | Documented as a limitation; a local coordinate frame is a precondition in the plan; the claim that tokenisation supports cross-region transfer is withdrawn |
| A coverage bound from total variation was proposed | C3 shows it would be vacuous; replaced in the plan by a threshold-specific, empirically validated estimate |
| Novelty of geometry-aware calibration overstated | Close prior art identified and cited; the contribution is scoped as a combination plus a measured finding |
| Plan lacked acceptance criteria | Rewritten with work packages, criteria and fallbacks fixed in advance; the scope is marked as pending supervisor approval |
| The Phase 2 package metadata omitted pandas and still advertised certified coverage and an SSM backbone | Dependency added; description and keywords corrected |
| The analysis code behind the distance finding had no tests | Tests added, including recovery of a planted slope and immunity to a station-noisiness confound |
| The title promised a guarantee the thesis does not claim | Title changed from "Certified ... Trustworthy Uncertainty" to "... Calibrated Uncertainty"; subject to supervisor approval |
| The library was described as a NumPy tool | Described as a PyTorch package |

## 6. State of the work

| Component | Status |
|---|---|
| Phase 1 design, validation, preprint, random-split re-evaluation, distance experiments | Complete |
| Phase 2 neighbour attention | Implemented; output equivalence measured; memory and speed not yet shown |
| Phase 2 state-space block | Implemented as a sequential scan; slower than the GRU; optional extension |
| Phase 2 corrected parity gate (V1b) | Written and smoke-tested; not run |
| Phase 2 geometry-aware calibration, coverage-risk estimate, memory study, large-network coverage, alerts, baselines, package | Planned with acceptance criteria; scope pending supervisor approval |

## 7. Reproduce

```bash
cd phase1-omnist && python3 -m pip install -r requirements.txt && python3 -m pytest -q
python3 experiments/C1_rigorous_inductive_eval.py delhi_air_quality   # about 15 to 25 minutes
python3 experiments/C2_region_holdout_distance.py delhi_air_quality   # about 15 minutes
python3 experiments/C2_region_holdout_distance.py analyse
python3 experiments/C3_score_shift_vs_distance.py delhi_air_quality
cd ../phase2-omnist-scale && python3 -m pytest -q
python3 experiments/T1_ssm_vs_gru_timing.py
cd .. && python3 tools/audit_links.py && python3 tools/check_report_numbers.py && python3 tools/check_submission_text.py
```

## 8. Consolidation of 15 Nov 2026

Earlier Phase 2 scaffold work was brought into this repository and re-run on the corrected Phase 2 code
(hash-keyed neighbour cache).

| Check | Result |
|---|---|
| Phase 1 tests | 50 of 50 passed (unchanged) |
| Phase 2 tests | 24 of 24 passed: the 18 earlier ones plus 6 in `phase2-omnist-scale/tests/test_consolidation.py` (chunked-scan closeness, default SSM mode, conformal band, group coverage, deployable calibration valid when stationary and under-covering when residual scale grows) |
| V4 memory/time against N and T | Run live; `phase2-omnist-scale/results/V4_scaling_crossover_results.json` |
| V3 coverage against N, real PeMS-BAY and synthetic | Run live, 3 seeds; `phase2-omnist-scale/results/V3_coverage_at_scale_real.json`, `phase2-omnist-scale/results/V3_coverage_at_scale_synthetic.json` |
| V3b training budget | Run live, one seed; `phase2-omnist-scale/results/V3b_training_budget.json` |
| PeMS-BAY coordinate file | `pems_bay_coords.csv` order matches the adjacency: Spearman -1.000 over 19,281 pairs; shuffled control -0.010 |
| New number check (`tools/check_phase2_findings.py`) | 28 Phase 2 figures in the findings document, overview, brief and index match the result files; corrupting one figure made it exit 1. It caught two rounding errors (17.6% and 20.7% written; 17.5% and 20.8% correct), now fixed |
| Earlier checks | `check_report_numbers.py` 25 of 25; `check_submission_text.py` OK; `audit_links.py` 0 broken links, 0 missing paths |

**Corrections made to results produced in the earlier Phase 2 scaffold before this consolidation.** The earlier
V3 calibrated each window on the calibration stations' residuals at that same window, which needs
targets unknown at forecast time. Under the deployable protocol: coverage at synthetic N=4,000 falls
from 0.902 to 0.880; the model's interval on real traffic is 22% wider than seasonal-naive at 3,000
steps, not 9% tighter; and the suggested 0.86 to 0.89 worst-group gap is not supported (real PeMS-BAY
worst tercile 0.906). Details in `phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`, Section 6.

**Not verified in this round.** V1b was not run. MPS memory was not measured (CPU peak RSS only). No
real network above 325 sensors. Three seeds per V3 cell; V3b has one seed. Timings in V3 were taken
while other jobs shared the machine; V4 is the timing reference. The abstract, proposal and
Semester-3 report were not changed.

## 9. Title and abstract revised for initial submission (15 Nov 2026)

| Item | Before | After |
|---|---|---|
| Title | *Topology-Invariant Spatiotemporal Forecasting with Calibrated Uncertainty at Unseen Sensors, and Its Scaling to Large Networks* (15 words) | *Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor Locations in Evolving Networks* (12 words) |
| Abstract | 580 words; promised specific Phase 2 methods (geometry-localised calibration with spatial-block pools, a PyTorch library) | 503 words (514 with the keywords line); states only completed measurements as facts and the remaining work as three open questions; says negative answers are findings |
| Keywords | none | five, identical in the README and report |

Reason: the title and abstract should stay accurate if Phase 2 methods change, give negative results,
or are re-scoped. The scenario check is in `SUBMISSION-TITLE-AND-ABSTRACT.md`, Section 2. A switch to an
unrelated topic would still need a new title.

Applied to `README.md`, `MTECH-THESIS-PROPOSAL.md` (title, one-sentence thesis, Phase 2 scope note),
`SEM3-PROGRESS-REPORT.md` (title, scope note, abstract) and `SEM3-PROGRESS-REPORT.pdf` (regenerated with
`tools/md_to_pdf.py`; 14 pages; extracted text contains the new title and abstract and none of the old
title). Text that referred to the old title or abstract was updated in `THESIS-OVERVIEW.md`,
`EXPERIMENTS-INDEX.md` (claim-to-evidence map for the new abstract) and
`phase2-omnist-scale/docs/RESEARCH-PLAN.md`. Section 2 of this record describes the earlier title and is
left as a record.

Checks: `tools/check_submission_text.py` (title rules, identical title and abstract across documents,
coverage range and slope tied to C1/C2), `tools/check_draft_abstract.py` (all abstract figures, including
the Phase 2 memory, state-space and traffic-width statements, tied to the result files),
`tools/check_report_numbers.py`, `tools/check_phase2_findings.py`, `tools/audit_links.py`.

Still pending: supervisor approval of the title and the Phase 2 scope. The public preprint is unchanged.

## 10. Submission recorded (17 Nov 2026)

The title and abstract of Section 9 were submitted on 17 Nov 2026 and are the finalised thesis topic.
The status and remaining action plan are in `THESIS-COMPLETION-PLAN.md`, Section 0.
Not verified: supervisor approval of the title.

## 11. C1b: chronological calibration (17 Nov 2026)

C1b re-runs C1 (same splits, seeds, models) and calibrates each window only on calibration-station
errors from earlier windows, scoring the last 75% of the test period. Rules were fixed in the script
header before the run (`phase1-omnist/experiments/C1b_chronological_eval.py`). New code:
`phase1-omnist/src/chronological_conformal.py`, 8 tests (Phase 1 suite: 58 passed). Results:
`phase1-omnist/results/exp_C1b_<domain>.json`; table from `phase1-omnist/experiments/C1b_summarise.py`.

| Dataset | Splits | Chronological | Same window (C1 protocol) | Pooled over time | C1 full-period mean |
|---|:---:|---|---|---|:---:|
| Delhi | 20 | 0.818 | 0.896 | 0.870 | 0.893 |
| Beijing | 20 | 0.777 | 0.905 | 0.875 | 0.903 |
| Weather | 20 | 0.889 | 0.883 | 0.900 | 0.906 |
| PeMSD7-M | 6 | 0.869 | 0.871 | 0.874 | 0.876 |
| PeMS-BAY | 6 | 0.869 | 0.893 | 0.883 | 0.892 |

Rule outcomes: (c) under-coverage below 0.85 on Delhi and Beijing; (b) chronological mean differs from
C1 by more than 0.01 on Delhi, Beijing, weather and PeMS-BAY. Only weather meets (a). The 95% intervals
over splits for Delhi and Beijing exclude 0.90 by a wide margin.

**Consequence.** The submitted abstract quotes 87.6% to 90.6%, which are C1 figures. Those hold for the
C1 protocol but not for forecast-time calibration, where the means span 77.7% to 88.9%. The abstract was revised on 17 Nov 2026 (Section 14); the submitted wording is kept in
`SUBMISSION-TITLE-AND-ABSTRACT.md`, Section 6.

**Not established.** The cause. Under-coverage is largest where the pooled-over-time quantile also falls
below target (Delhi, Beijing), which is consistent with errors growing over the test period, but per-window
scores were not saved, so this is untested. The expanding-window quantile is one choice; a rolling window
or adaptive conformal inference may do better (plan item B). Two seeds' timings were taken with jobs in
parallel. PeMS datasets have 6 splits.

## 12. Coordinate-frame defect (reported 17 Nov 2026)

The spatial embedding normalised every station's coordinates with Delhi constants,
`(lat - 28.6) / 0.2` and `(lon - 77.1) / 0.3` (`phase1-omnist/src/cc_hash.py` and the identical copy in
`phase2-omnist-scale/src/omnist_scale/omnist/cc_hash.py`; the Phase 2 scalable model imports it). The report
came from a defect report written in the separate OmniST repository.

| Item | Status |
|---|---|
| Both `cc_hash.py` copies identical; constants at lines 48 to 49 | Verified here |
| Legacy MLP input range per network: Delhi 1.1, Beijing 131.9, weather 656.0, PeMSD7-M 651.3, PeMS-BAY 651.3 | Verified here from the loaders' coordinates |
| C1 test MAE: Delhi 27.63, Beijing 49.30, weather 5.84, PeMSD7-M 10.33, PeMS-BAY 5.54 | Verified here from `exp_C1_*.json` |
| Effect of a training-station frame: MAE and width fall on four networks, coverage within 0.0013 (same-window protocol) | **Relayed from the OmniST repository, not yet reproduced here.** The C1b runs below reproduce it on the thesis code |
| The thesis tests could not detect it (`test_cc_hash.py` uses Delhi coordinates) | Confirmed; new test uses weather-like coordinates |

**Code change (both phases).** `SpatialMLP` takes `center` and `scale` as persistent buffers; defaults are
the legacy constants, so every committed result is reproducible. `ModelConfig.coord_center` and
`coord_scale` pass the frame through; `training_coordinate_frame(train_coords)` builds it from the
training stations only. Tests: `phase1-omnist/tests/test_coordinate_frame.py` (7) and
`phase2-omnist-scale/tests/test_coordinate_frame.py` (2). Suites: Phase 1 65 passed, Phase 2 26 passed.

**Which frame produced which result.**
- Committed C1, C2, C3, C1b (`exp_C1b_<domain>.json`) and all Phase 2 results V1 to V4: **legacy constants.**
- `exp_C1b_norm_<domain>.json`: training-station frame, same splits and seeds as C1b.
- Not yet affected by the change but affected by the defect: C1 and C1b accuracy and width; every
  comparison with persistence or seasonal-naive; Phase 2 accuracy and width results (V3, V3b). V2
  (equivalence of attention on identical tokens) is not affected. C2 and C3 are possibly affected (score
  scale) and need re-checking on weather.

**Revised S5 criterion** (replaces "Phase 1 numbers unchanged within noise"): coverage unchanged within
0.01 on every network under the same-window protocol; MAE and width reported before and after; PeMSD7-M
included because it shows the largest effect.

**Result of the thesis-code re-run (C1b, same splits and seeds; mean over splits).** Table from
`phase1-omnist/experiments/C1b_summarise.py`; files `exp_C1b_<domain>.json` (legacy frame) and
`exp_C1b_norm_<domain>.json` (training-station frame).

| Dataset | Splits | MAE, legacy to frame | Chronological width, legacy to frame | Same-window coverage, legacy to frame | Chronological coverage, legacy to frame |
|---|:---:|---|---|---|---|
| Delhi | 20 | 27.63 to 28.53 | 89.4 to 90.0 | 0.896 to 0.893 | 0.818 to 0.811 |
| Beijing | 20 | 49.30 to 48.48 | 139.9 to 138.7 | 0.905 to 0.907 | 0.777 to 0.778 |
| Weather | 20 | 5.84 to 4.73 | 24.3 to 19.8 | 0.883 to 0.880 | 0.889 to 0.888 |
| PeMSD7-M | 6 | 10.33 to 3.79 | 42.7 to 17.3 | 0.871 to 0.882 | 0.869 to 0.891 |
| PeMS-BAY | 6 | 5.54 to 4.73 | 20.4 to 18.8 | 0.893 to 0.897 | 0.869 to 0.881 |

- **The defect report is reproduced on the thesis code.** MAE and width fall on weather, PeMSD7-M and
  PeMS-BAY (PeMSD7-M MAE falls 63% and width 59%), change little on Beijing, and rise slightly on Delhi
  (+0.9 MAE). Same-window coverage moves by at most 0.011.
- **Revised S5 criterion:** met on four networks. **PeMSD7-M misses it by 0.001** (same-window coverage
  0.871 to 0.882, a change of 0.011, with 6 splits and a legacy-frame 95% interval over splits of 0.853 to 0.889), so it is
  recorded as not met rather than rounded.
- **The frame does not explain the chronological under-coverage.** Delhi (0.811) and Beijing (0.778) stay
  far below 0.90 with the corrected frame. The abstract-revision trigger from Section 11 therefore stands.
- On PeMSD7-M and PeMS-BAY chronological coverage rises (0.869 to 0.891, 0.869 to 0.881); with 6 splits
  these changes are within the spread over splits and are not claimed as an effect.
- Persistence comparison: with the frame, model MAE is 3.79 against 3.57 for persistence on PeMSD7-M
  (relayed value, not re-run here), so the model still does not beat persistence there. Baseline tables
  need re-running under the chosen frame (plan step S4).
- The relayed measurements (OmniST repository) and these thesis-code numbers agree within about 0.5 MAE
  on every network, for example weather 5.72 to 4.75 there and 5.84 to 4.73 here.

**Decision needed.** Which frame the report and thesis use. Proposed: the training-station frame, with
every legacy-frame result kept and labelled. Phase 2 results (V3, V3b, V4) were produced with the legacy
frame; V3 and V3b accuracy and width must be re-run before any statement about usefulness is final.

## 13. Phase 1 closure for the Semester 3 report (17 Nov 2026)

| Step | Outcome |
|---|---|
| S1 to S3 | C1b run on five networks, both coordinate frames (Sections 11 and 12) |
| S4 | C1c: persistence and seasonal-naive with chronological conformal intervals on the same splits (`phase1-omnist/experiments/C1c_naive_baselines.py`, 6 tests of `phase1-omnist/src/naive_baselines.py`). Persistence and seasonal-naive under-cover on Delhi (0.772, 0.788) and Beijing (0.806, 0.773) as the model does. Against persistence the corrected-frame model is better on Delhi, Beijing and PeMS-BAY, ties on weather (MAE 4.73 against 4.72) and is worse on PeMSD7-M (3.79 against 3.63). On PeMS-BAY the model's chronological width is 18.8 against 14.1 for seasonal-naive (33% wider; seasonal-naive is scored on a later subset of windows). Interpolators and E-STGCN were not re-run under these rules |
| Diagnosis | C1d (10 splits, corrected frame): late-third over early-third error is 1.90 (Delhi), 2.11 (Beijing), 0.87 (weather); test-station over calibration-station error is 1.03, 0.99, 1.08; chronological coverage by third is 0.99/0.89/0.50, 0.88/0.73/0.73, 0.84/0.83/0.94. Under-coverage follows error growth, not station mismatch. Why error grows is untested (the Delhi test period covers the high-pollution season; this is a hypothesis). Delhi has 10 test windows and Beijing 22 |
| S5 | Done (Section 12). Training-station frame adopted for new work |
| S6 | Not re-run, stated as such in the report: dropout robustness, drift handling, 7-sensor run, E-STGCN comparison, interpolator comparison; C2 and C3 with the corrected frame |
| S7 | Preprint: see below |
| S8 | References: [1] IJCAI 2018 (ijcai.org/proceedings/2018/505), [3] AAAI vol. 35 (paper starts on page 4478), [4] Springer 2005 (link.springer.com/10.1007/b106715) and [5] Foundations and Trends in Machine Learning 16(4) (ACM DOI 10.1561/2200000101) match the cited venue and year. Page ranges of [1] (3634 to 3640) and [5] (494 to 591) were not confirmed from the sources reached. New references [21] (Lee, Barber, Willett; arXiv:2306.06342) and [22] (arXiv:2608.15500; the author list was not shown on the page reached, so it is cited as "S. Mallick et al." with that caveat) |
| S9 | Report updated (Sections 4.3a, 4.6, 5, 6, 7 and references; abstract unchanged), PDF regenerated, `tools/check_c1b_report.py` added (41 figures) |

**Preprint (S7).** The public abstract (arXiv:2611.04256) says coverage of 90% or above holds under 30 to
50% dropout and at 325 sensors. C1 gives 87.6% to 90.6% and C1b gives 77.7% to 89.1%. Proposed: post a
revised version after the Semester 4 station-level results (about week 4 of the plan), stating the
calibration rule behind each number and removing the dropout and 325-sensor guarantee claims. The
decision to post, and when, is the author's. Nothing public has been changed.

**Still open for Phase 1.** Abstract revision decision; frame choice applied to C2, C3 and the Phase 2
results; the S6 re-runs; supervisor approval of the title and Phase 2 scope.

## 14. Abstract revised (17 Nov 2026)

The abstract was submitted earlier on 17 Nov 2026 and is revised in the Semester 3 progress report and will be
revised again in the final thesis. One sentence changed: the first-part coverage figures now state the
calibration rule behind each range (87.6% to 90.6% with C1's rule; 77.8% to 89.1% with forecast-time
calibration and the training-station coordinate frame), and name the cause (forecast error roughly doubling
over the air-quality test periods, with persistence and seasonal forecasts falling short in the same way). The
revised text is in `README.md`, `SEM3-PROGRESS-REPORT.md` and `SUBMISSION-TITLE-AND-ABSTRACT.md`; 560 words (limit
600). `tools/check_submission_text.py` now ties the forecast-time range to the C1b result files.
Still open: supervisor approval of the title and the Phase 2 scope; the preprint revision.
