# Experiments Index — Claim → Script → Result File

Every factual claim in the abstract, proposal and report is traced here to the experiment that
produces it and the committed result file that holds the numbers. Status is **EXECUTED** (number is in
a committed result file), **PRELIMINARY** (executed, but under a protocol the review found too weak to
support the claim), or **PLANNED** (not yet run).

Paths are relative to the repo root. Phase 1 lives in `phase1-omnist/`, Phase 2 in
`phase2-omnist-scale/`.

---

## Phase 1 — OmniST

### Primary evidence: C1, random disjoint-station evaluation (added after review)

| # | Claim | Script | Result files | Status |
|---|---|---|---|---|
| C1 | Coverage at unseen stations over many random train/calibration/test station splits, with calibration on disjoint unseen stations; also the old training-station calibration on the same trained models; per-station coverage; interval width | `phase1-omnist/experiments/C1_rigorous_inductive_eval.py`, summary by `phase1-omnist/experiments/C1_summarise.py` | `phase1-omnist/results/exp_C1_delhi_air_quality.json`, `exp_C1_beijing_air_quality.json`, `exp_C1_ghcn_weather.json`, `exp_C1_pemsd7_traffic.json`, `exp_C1_pemsbay_traffic.json` | EXECUTED |
| C2 | Per-station coverage against distance to the nearest training station under contiguous-region holdout, and the same analysis of the C1 scattered holdouts; within-station slopes | `phase1-omnist/experiments/C2_region_holdout_distance.py` (`analyse` mode) | `phase1-omnist/results/exp_C2_delhi_air_quality.json`, `exp_C2_beijing_air_quality.json`, `exp_C2_ghcn_weather.json`, `exp_C2_pemsd7_traffic.json`, `exp_C2_pemsbay_traffic.json`, `exp_C2_analysis.json` | EXECUTED |
| C3 | Total-variation distance between station score distributions, noise floor, and relation to distance (feasibility of a total-variation coverage bound) | `phase1-omnist/experiments/C3_score_shift_vs_distance.py` | `phase1-omnist/results/exp_C3_delhi_air_quality.json`, `exp_C3_ghcn_weather.json` | EXECUTED |

### Original protocol (calibration on training-station residuals, fixed held-out stations)

These runs use 3 to 7 hard-coded held-out stations, the same in every seed, so seeds vary only the
initialisation. They are kept as the original record; C1 is the primary evidence.

| # | Claim | Script | Result file | Status |
|---|---|---|---|---|
| 1 | Coverage at unseen sensors, Delhi, original protocol | `phase1-omnist/experiments/06_inductive_conformal.py` | `phase1-omnist/results/exp_inductive_conformal.json` | EXECUTED (original protocol) |
| 2 | Coverage on four datasets, original protocol | `phase1-omnist/experiments/B1_multidomain_v2.py` | `phase1-omnist/results/exp_multidomain_v2.json` | EXECUTED (original protocol) |
| 3 | Comparison with four simple interpolators | `phase1-omnist/experiments/B2_baselines.py` | `phase1-omnist/results/exp_baselines.json` | EXECUTED (original protocol) |
| 4 | Robustness across targets and held-out sizes | `phase1-omnist/experiments/07_inductive_conformal_rigor.py`, `11_realmultidomain_rigor.py` | `phase1-omnist/results/exp_inductive_conformal_rigor.json`, `exp_realmultidomain_rigor.json` | EXECUTED (original protocol) |
| 5 | Point error against a learned kriging baseline (the author's re-implementation) | `phase1-omnist/experiments/B9_ignnk_inductive.py` | `phase1-omnist/results/exp_ignnk_inductive.json` | EXECUTED; tuning parity not verified |
| 6 | A fixed-adjacency model cannot predict at unseen sensors (motivation, not evidence of superiority) | `phase1-omnist/experiments/B6_estgcn_controlled.py`, `B8_fixedtopo_crash_demo.py` | `phase1-omnist/results/exp_estgcn_controlled.json`, `exp_fixedtopo_crash_demo.json` | EXECUTED |
| 7 | Drift: rolling adaptive conformal restores coverage over time | `phase1-omnist/experiments/10_temporal_conformal.py` | `phase1-omnist/results/exp_temporal_conformal.json` | EXECUTED |
| 8 | Coverage on PeMS-BAY, 325 sensors, **7 held-out sensors, one fixed split** | `phase1-omnist/experiments/B7_largeN_pemsbay.py` | `phase1-omnist/results/exp_largeN_pemsbay.json` | EXECUTED (original protocol); see C1 for random splits |
| 9 | Locality property: score invariance to far-away nodes (not an exchangeability result) | `phase1-omnist/experiments/B5_theorem_check.py` | `phase1-omnist/results/exp_theorem_check.json` | EXECUTED |
| 10 | Mondrian conditional conformal narrows per-node spread on traffic | `phase1-omnist/experiments/13_mondrian_conformal.py` | `phase1-omnist/results/exp_mondrian_conformal.json` | EXECUTED |
| 11 | Neighbour attention versus exact, and cost scaling | `phase1-omnist/experiments/14_approx_knn_test.py`, `12_scalability_stress.py` | `phase1-omnist/results/exp_approx_knn.json`, `exp_scalability_stress.json` | EXECUTED |
| 12 | Ablations, calibration diagnostics, multi-seed hardening | `phase1-omnist/experiments/B3_ablations.py`, `B4_calibration.py`, `08_optimizations.py`, `05_final_comparison.py` | `phase1-omnist/results/exp_ablations_v2.json`, `exp_calibration.json`, `exp_optimizations.json`, `exp_final_5seed.json`, `exp_definitive_10seed.json` | EXECUTED |

Full claim-to-file map for Phase 1: `phase1-omnist/RESULTS-INDEX.md`.

---

## Phase 2 — OmniST-Scale

| # | Claim | Script | Result file | Status |
|---|---|---|---|---|
| V1 | First parity check of ssm+fast against gru+exact, 3 seeds. Gate was non-discriminating and calibration used training stations. | `phase2-omnist-scale/experiments/V1_ssm_matches_omnist.py` | `phase2-omnist-scale/results/V1_ssm_matches_omnist_results.json` | PRELIMINARY; superseded by V1b |
| V1b | Corrected parity gate: disjoint calibration stations, paired equivalence with margins fixed in advance, 10 seeds | `phase2-omnist-scale/experiments/V1b_parity_equivalence.py` | *(written when V1b is run in full; none exists yet)* | PLANNED (smoke-tested only) |
| V2 | Neighbour attention output equals exact attention (random tokens, shared weights); no memory measured | `phase2-omnist-scale/experiments/V2_attention_equivalence.py` | `phase2-omnist-scale/results/V2_attention_equivalence_results.json` | EXECUTED; limited scope |
| T1 | Diagnostic: the state-space block is sequential and slower than the GRU | `phase2-omnist-scale/experiments/T1_ssm_vs_gru_timing.py` | `phase2-omnist-scale/results/T1_ssm_vs_gru_timing.json` | EXECUTED (diagnostic) |
| V4 | Peak memory and time against N (exact vs neighbour attention, inference and training) and time against T (GRU vs state-space sequential vs chunked). CPU peak RSS, MPS time | `phase2-omnist-scale/experiments/V4_scaling_crossover.py` | `phase2-omnist-scale/results/V4_scaling_crossover_results.json` | EXECUTED (15 Nov). Partial WP3 evidence; WP3's 5x-at-N=2000 criterion **not met** (2.6x) |
| V3 | Coverage and interval width against N, random train/calibration/test node split, deployable (chronological) and same-window calibration, vs persistence and seasonal-naive; real PeMS-BAY with real coordinates, synthetic ladder N=100 to 4000 | `phase2-omnist-scale/experiments/V3_coverage_at_scale.py` | `phase2-omnist-scale/results/V3_coverage_at_scale_real.json`, `phase2-omnist-scale/results/V3_coverage_at_scale_synthetic.json` | EXECUTED (15 Nov); 3 seeds; N>325 is synthetic |
| V3b | Training-budget sweep on real PeMS-BAY (300, 1200, 3000 steps), deployable protocol | `phase2-omnist-scale/experiments/V3b_training_budget.py` | `phase2-omnist-scale/results/V3b_training_budget.json` | EXECUTED (15 Nov); one seed |
| X2 audit | Chunked state-space scan against the sequential scan | `phase2-omnist-scale/tests/test_consolidation.py` | (test assertions; timings in V4) | EXECUTED; X2 criteria fail, X2 dropped |
| WP1 | Geometry-aware calibration at new sites, compared with five published methods | *(planned)* | *(planned)* | PLANNED |
| WP2 | Per-site coverage-risk estimate from geometry (threshold-specific shift) | *(planned)* | *(planned)* | PLANNED |
| WP3 | Peak memory and time against N; coverage against N on a large sparse network | *(planned)* | *(planned)* | PLANNED |
| WP4 | Alerts with a controlled miss rate at unseen sites (conformal risk control) | *(planned)* | *(planned)* | PLANNED |

Acceptance criteria and fallbacks for each work package: `phase2-omnist-scale/docs/RESEARCH-PLAN.md`.

---

## How the abstract maps to status

- *Phase 1 forecaster, validated on four real datasets* → C1 and rows 1 to 12 above. EXECUTED.
- *Released as a preprint* → arXiv:2611.04256, not submitted for publication.
- *Nearest-neighbour attention gives numerically the same output as exact* → V2. EXECUTED, with the
  scope limits stated above.
- *A first parity check found the rebuilt engine close to the original* → V1. PRELIMINARY.
- *Coverage falls with distance from the training network only in the sparse weather network* → C2.
  EXECUTED. *A total-variation coverage bound would be vacuous* → C3. EXECUTED.
- *Its memory advantage at large sensor counts is still to be measured* → partly measured by V4
  (15 Nov): 7.2x less inference memory at N=4000, 16.7x at N=8000, but 2.6x at N=2000 and 2.6x for
  training at N=4000. The abstract has **not** been updated with these numbers.
- *Geometry-aware calibration; per-site coverage-risk estimate; alerts with a controlled miss rate;
  coverage on larger real networks* → WP1, WP2, WP4, WP3. PLANNED. No number is asserted for these.

Full Phase 2 numbers, protocol notes and corrections: `phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`.
