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
| Phase 1 tests | 13 of 13 passed |
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
  so 0.0 and 1.0 are identical).

## 5. Corrections made

| Finding | Correction |
|---|---|
| "Certified" coverage rested on training-station calibration and a few fixed held-out stations | C1 added; "certified" defined as approximate marginal coverage with the station as the exchangeable unit; the original-protocol numbers relabelled as the record |
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
cd .. && python3 tools/audit_links.py && python3 tools/check_report_numbers.py
```
