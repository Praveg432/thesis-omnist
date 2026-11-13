# Experiments Index — Abstract Claim → Script → Result File

Every factual claim in the abstract and proposal is traced here to the experiment that produces it
and the committed result file that holds the numbers. Status is marked **EXECUTED** (number is in a
committed result file) or **PENDING** (planned thesis work, not yet run).

Paths are relative to the repo root. Phase 1 lives in `phase1-omnist/`, Phase 2 in
`phase2-omnist-scale/`.

---

## Phase 1 — OmniST (all EXECUTED)

| # | Abstract / proposal claim | Script | Result file | Status |
|---|---|---|---|---|
| 1 | Guaranteed inductive coverage at unseen sensors (real Delhi headline) | `phase1-omnist/experiments/06_inductive_conformal.py` | `phase1-omnist/results/exp_inductive_conformal.json` | EXECUTED |
| 2 | Coverage holds across 4 real datasets / 3 domains (Delhi 0.914, Beijing 0.928, weather 0.919, traffic 0.915) | `phase1-omnist/experiments/B1_multidomain_v2.py` | `phase1-omnist/results/exp_multidomain_v2.json` | EXECUTED |
| 3 | Only method vs four model-free interpolators to hold target on all four | `phase1-omnist/experiments/B2_baselines.py` | `phase1-omnist/results/exp_baselines.json` | EXECUTED |
| 4 | Coverage tracks the target across domains/targets/held-out sizes; robustness | `phase1-omnist/experiments/07_inductive_conformal_rigor.py`, `11_realmultidomain_rigor.py` | `phase1-omnist/results/exp_inductive_conformal_rigor.json`, `exp_realmultidomain_rigor.json` | EXECUTED |
| 5 | Beats learned IGNNK kriging at unseen nodes (~21% MAE Delhi), tighter intervals | `phase1-omnist/experiments/B9_ignnk_inductive.py` | `phase1-omnist/results/exp_ignnk_inductive.json` | EXECUTED |
| 6 | Controlled E-STGCN head-to-head; fixed-topology cannot predict at unseen nodes | `phase1-omnist/experiments/B6_estgcn_controlled.py` | `phase1-omnist/results/exp_estgcn_controlled.json` | EXECUTED |
| 7 | Fixed-topology model crashes under node dropout (demonstrated) | `phase1-omnist/experiments/B8_fixedtopo_crash_demo.py` | `phase1-omnist/results/exp_fixedtopo_crash_demo.json` | EXECUTED |
| 8 | Temporal-drift coverage restored by rolling-ACI (0.89/0.96 vs static 0.50) | `phase1-omnist/experiments/10_temporal_conformal.py` | `phase1-omnist/results/exp_temporal_conformal.json` | EXECUTED |
| 9 | Certified to 325 real sensors (PeMS-BAY) | `phase1-omnist/experiments/B7_largeN_pemsbay.py` | `phase1-omnist/results/exp_largeN_pemsbay.json` | EXECUTED |
| 10 | Locality Proposition verified (recalibration-free coverage, far-change diff 8.9e-8) | `phase1-omnist/experiments/B5_theorem_check.py` | `phase1-omnist/results/exp_theorem_check.json` | EXECUTED |
| 11 | Mondrian conditional conformal narrows per-node spread (traffic worst-group 0.80→0.86) | `phase1-omnist/experiments/13_mondrian_conformal.py` | `phase1-omnist/results/exp_mondrian_conformal.json` | EXECUTED |
| 12 | Scalable k-NN attention equivalent to exact (cosine 0.99996) + cost scaling | `phase1-omnist/experiments/14_approx_knn_test.py`, `12_scalability_stress.py` | `phase1-omnist/results/exp_approx_knn.json`, `exp_scalability_stress.json` | EXECUTED |
| 13 | Ablations + calibration diagnostics | `phase1-omnist/experiments/B3_ablations.py`, `B4_calibration.py` | `phase1-omnist/results/exp_ablations_v2.json`, `exp_calibration.json` | EXECUTED |
| 14 | Multi-seed hardening (5/10-seed) | `phase1-omnist/experiments/08_optimizations.py`, `05_final_comparison.py` | `phase1-omnist/results/exp_optimizations.json`, `exp_final_5seed.json`, `exp_definitive_10seed.json` | EXECUTED |

Full claim→file map with inline numbers: `phase1-omnist/RESULTS-INDEX.md`.

---

## Phase 2 — OmniST-Scale

| # | Abstract / proposal claim | Script | Result file | Status |
|---|---|---|---|---|
| V1 | The rebuilt engine (SSM + O(N·k) attention) matches OmniST accuracy and coverage on real data (MAE within 2%, coverage in band) | `phase2-omnist-scale/experiments/V1_ssm_matches_omnist.py` | `phase2-omnist-scale/results/V1_ssm_matches_omnist_results.json` | **EXECUTED → GO** |
| V2 | O(N·k) nearest-neighbour attention gives numerically the same output as exact (min cosine 0.99987) | `phase2-omnist-scale/experiments/V2_attention_equivalence.py` | `phase2-omnist-scale/results/V2_attention_equivalence_results.json` | **EXECUTED → GO** |
| V3 | Inductive coverage stays in band as N grows toward thousands; scalable conditional conformal | *(planned — V3 script, M3)* | *(pending)* | **PENDING** |
| V4 | SSM beats GRU on throughput/memory at long T / large N; crossover identified (MambaOut-analog gate) | *(planned — V4 script, M2/M3)* | *(pending)* | **PENDING** |

---

## How the abstract maps to status

- *"designed a forecaster … attaches a distribution-free coverage guarantee … validated on four real
  datasets"* → **Phase 1, EXECUTED** (rows 1–14).
- *"released it as a preprint"* → arXiv:2611.04256 (`phase1-omnist/paper/`), not submitted for
  publication.
- *"the rebuilt engine matches the original model's accuracy, keeps its coverage guarantee, and the
  nearest-neighbour attention gives numerically the same output as the exact version"* → **Phase 2
  V1 + V2, EXECUTED → GO.**
- *"stays valid as the network scales … holds more evenly from sensor to sensor"* → **Phase 2 V3,
  PENDING** (the coverage-at-scale ladder + scalable conditional conformal).
- *"state-space block that handles long sequences in linear time and in parallel"* implemented
  (`phase2-omnist-scale/src/omnist_scale/ssm_temporal.py`); its *earns-its-keep* crossover is
  **Phase 2 V4, PENDING.**

No number in any framing document is unsourced: executed claims point to a committed result file;
pending claims are labelled pending and have no number asserted.
