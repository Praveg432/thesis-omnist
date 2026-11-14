# Finalization Record: Verification of the Work and Review Corrections

This record states what was checked, how, and what was not checked. It distinguishes results **run
live in this repository** from results **read from committed result files**, and lists the changes
made after a preliminary review of the work.

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
| Phase 2 tests | 14 of 14 passed (4 existing, 10 added for the review fixes) |
| Experiment C1 (random disjoint-station evaluation), all five datasets | Completed: Delhi 20 splits, Beijing 20, weather 20, PeMSD7-M 6, PeMS-BAY 6. Results are in `phase1-omnist/results/exp_C1_*.json`. |
| Diagnostic T1 (state-space block against GRU timing), idle machine | State-space 29.0, 115.7, 462.3 ms against GRU 14.0, 53.3, 233.7 ms at T = 60, 240, 960 |
| Cache-key defect | Reproduced (two layouts with equal coordinate sum and spread shared a key and received the wrong neighbours); fixed; regression tests added |
| Data checks on the Delhi series | Invalid entries 0.0000% in training years and 0.0074% in the test year; PM2.5 highest in November, December and January under the declared dates |
| `phase1-omnist/experiments/06_inductive_conformal.py` and `phase2-omnist-scale/experiments/V2_attention_equivalence.py` (earlier pass) | Matched their committed result files apart from timings |
| Number check (`tools/check_report_numbers.py`) | Every C1 table row, the V1 and T1 figures, the V2 minimum cosine and the IGNNK errors quoted in the report and proposal match the result files |
| Link and path audit (`tools/audit_links.py`) | 21 Markdown files, 0 broken links, 0 missing paths |

## 3. Checked by reading committed result files, not re-run

| Claim | Source file | Verified value |
|---|---|---|
| Original-protocol coverage on four datasets | `exp_multidomain_v2.json` | Delhi 0.9139 (10 seeds), Beijing 0.9275 (10), weather 0.9193 (10), PeMSD7-M 0.9150 (6); sample standard deviations 0.006, 0.003, 0.007, 0.009 |
| Comparison with four interpolators | `exp_baselines.json` | OmniST 0.914, 0.927, 0.919, 0.911; each interpolator below 0.90 on at least one dataset |
| Dropout coverage | `exp_multidomain_v2.json` | Dataset means 0.912 to 0.931; seeds down to 0.89 |
| IGNNK comparison (Delhi) | `exp_ignnk_inductive.json` | MAE 26.67 against 34.00, 21.5% lower, 5 seeds; coverage 0.9145 against 0.8905 |
| Fixed-adjacency baseline | `exp_estgcn_controlled.json`, `exp_fixedtopo_crash_demo.json` | Cannot predict at unseen sensors; does not run under 30% or 50% dropout |
| Drift | `exp_temporal_conformal.json` | Worst-window coverage 0.498 (static) against 0.962 (rolling adaptive) |
| Large network, original protocol | `exp_largeN_pemsbay.json` | Coverage 0.9207, **7 held-out sensors**, 3 seeds, identical split |
| First parity check (preliminary) | `V1_ssm_matches_omnist_results.json` | MAE 64.56 (baseline) and 65.62 (rebuilt); coverage 0.948 and 0.944 |
| Attention equivalence | `V2_attention_equivalence_results.json` | Minimum cosine 0.999874 for N = 37 to 2,000 |

## 4. Not verified

- **V1b has not been run in full.** It was smoke-tested in quick mode only, and no V1b number is
  quoted anywhere. The first parity check (V1) was not re-run.
- **Phase 1 experiments other than C1 and the Delhi headline were not re-run.** Their numbers come
  from committed result files.
- **The baseline comparison, dropout robustness, drift handling and the 7-sensor large-network run
  were not repeated under C1.** They are reported as original-protocol results.
- **C1 uses 6 splits for the two traffic datasets**, so their intervals are wide.
- **LargeST availability and licence were not checked.** It is a candidate data source only.
- **Related-work positioning** rests on abstracts read in November 2026; the full papers were not read.
- The arXiv listing for 2611.04256 was located by search and its title matches reference [8]; its
  version history was not inspected.
- The baselines E-STGCN and IGNNK are the author's re-implementations, and equal tuning effort has not
  been verified.
- The year-feature check in C1 was uninformative by construction (the temporal embedding is periodic,
  so 0.0 and 1.0 are identical). No effect of the year encoding was demonstrated or ruled out beyond
  that.

## 5. Corrections made

| Finding in the review | Correction |
|---|---|
| "Certified" coverage rested on calibration with training-station residuals and a few fixed held-out stations | Experiment C1 added; the term "certified" is defined in the report, proposal and README; the original-protocol numbers are relabelled and no longer the headline |
| The large-network result used 7 held-out sensors | Stated in every document; C1 evaluates PeMS-BAY with 45 test sensors per split over 6 random splits |
| The state-space block is sequential, not parallel, and about twice as slow as the GRU | Descriptions corrected in the report, proposal, README, overview and code docstrings; T1 added; a parallel scan is a planned work package with an acceptance test |
| The neighbour attention was described as provably equivalent with no memory evidence | Described as numerically equivalent on random inputs; memory and speed advantages stated as not yet shown |
| The first parity check could not fail | Marked preliminary and superseded; V1b added with pre-registered margins and paired equivalence |
| Scalable conditional conformal was described as implemented | Marked planned in all documents |
| Neighbour cache key could collide and the cache was unbounded | Fixed with a content hash and a size limit; regression tests |
| Docstring and documents overstated "no per-item loop" | Self-removal vectorised and checked against brute force |
| Related work was thin | Four directly relevant works and LargeST added with verified authors |
| Leakage in the V1 preprocessing | Fixed in V1b (training-station normalisation, causal imputation, no cross-gap windows). Phase 1 loaders already normalised with training stations; the effect of full-series imputation was measured on Delhi and is negligible. |
| Delhi season assumption | Phase 1 uses explicit dates; seasonality checked; V1b uses explicit dates |
| Phase 2 plan lacked acceptance criteria | Rewritten with work packages, criteria and fallbacks fixed in advance |
| The library was described as a "NumPy tool" | Described as a PyTorch package |

## 6. State of the work

| Component | Status |
|---|---|
| Phase 1 design, validation, preprint, random-split re-evaluation | Complete |
| Phase 2 neighbour attention | Implemented; output equivalence measured; memory and speed not yet shown |
| Phase 2 state-space block | Implemented as a sequential scan; slower than the GRU |
| Phase 2 corrected parity gate (V1b) | Written; not run |
| Phase 2 localised calibration, parallel scan, memory study, large-network coverage, baselines, package | Planned with acceptance criteria |

## 7. Reproduce

```bash
cd phase1-omnist && python3 -m pip install -r requirements.txt && python3 -m pytest -q
python3 experiments/C1_rigorous_inductive_eval.py delhi_air_quality   # about 15 to 25 minutes
python3 experiments/C1_summarise.py
cd ../phase2-omnist-scale && python3 -m pytest -q
python3 experiments/T1_ssm_vs_gru_timing.py
python3 experiments/V2_attention_equivalence.py
cd .. && python3 tools/audit_links.py && python3 tools/check_report_numbers.py
```
