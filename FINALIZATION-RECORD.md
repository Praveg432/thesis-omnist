# Finalization Record — Verification of Phase 1 and the Repository Workflow

This record states what was checked before the Semester-3 submission, how each check was done, and
what was not checked. It distinguishes results **re-run live in this repository** from results
**read from committed result files**.

## 1. Environment

| Item | Value |
|---|---|
| Machine | Apple M4 Pro, MPS available |
| Python | 3.14.3 |
| torch / numpy / pandas / scikit-learn / matplotlib | 2.13.0 / 2.4.6 / 3.0.3 / 1.9.0 / 3.10.9 (matches `phase1-omnist/requirements.txt`) |
| Repository | https://github.com/Praveg432/thesis-omnist, branch `main` |

## 2. Checks run live in this repository

| Check | Result |
|---|---|
| Phase 1 test suite (`phase1-omnist/tests`) | 13 of 13 passed |
| Phase 2 test suite (`phase2-omnist-scale/tests`) | 4 of 4 passed |
| Phase 1 headline experiment `phase1-omnist/experiments/06_inductive_conformal.py` (real Delhi, 3 seeds, 212 s) | Coverage at unseen sensors 0.9067, 0.9187, 0.9207 (mean 0.9154). Identical to the committed result file except for run time. |
| Phase 2 equivalence experiment `phase2-omnist-scale/experiments/V2_attention_equivalence.py` | Minimum cosine similarity to exact attention 0.999874 across N = 37, 100, 325, 1000, 2000. Identical to the committed result file except for timings. |
| Link and path audit (`tools/audit_links.py`) | 20 Markdown files scanned, 0 broken links, 0 missing paths |

The two re-run result files differed from the committed versions only in wall-clock timings. They
were restored to the committed versions so the repository keeps the canonical record.

## 3. Checks done by reading committed result files (not re-run)

Each figure quoted in the Semester-3 report was compared with the committed result files.

| Claim in the report | Source file | Verified value |
|---|---|---|
| Coverage at unseen sensors, 4 datasets | `exp_multidomain_v2.json` | Delhi 0.9139 (10 seeds), Beijing 0.9275 (10), weather 0.9193 (10), traffic 0.9150 (6) |
| Only method at or above 0.90 on all four datasets, among four interpolators | `exp_baselines.json` | OmniST 0.914, 0.927, 0.919, 0.911. Nearest-neighbour, IDW, mean-of-k and Gaussian-process each fall below 0.90 on at least one dataset. |
| Coverage under 30% and 50% sensor dropout | `exp_multidomain_v2.json` | Dataset means 0.912 to 0.931; individual seeds range down to 0.89 |
| Learned baseline IGNNK | `exp_ignnk_inductive.json` | MAE 26.67 (OmniST) vs 34.00 (IGNNK), 21.5% lower; coverage 0.9145 vs 0.8905 |
| Fixed-topology baseline fails | `exp_estgcn_controlled.json`, `exp_fixedtopo_crash_demo.json` | Cannot predict at unseen sensors; does not run under 30% or 50% dropout; captured `RuntimeError` |
| Drift over time | `exp_temporal_conformal.json` | Static conformal worst-window 0.498; rolling adaptive conformal 0.962 |
| Scale to 325 real sensors | `exp_largeN_pemsbay.json` | Coverage 0.9207 over 3 seeds |
| Phase 2 parity gate | `V1_ssm_matches_omnist_results.json` | MAE 64.56 (original) vs 65.62 (rebuilt); coverage 0.948 vs 0.944; finite-sample band [0.753, 0.998] |

## 4. Not verified

- **Phase 2 parity gate (V1) was not re-run in this repository.** A full run did not finish within
  28 minutes and was stopped. Its numbers are those in the committed result file, produced earlier on
  the same machine.
- **Phase 1 experiments other than the Delhi headline were not re-run.** Their numbers come from
  committed result files (Section 3).
- **Experiments that need the traffic speed series or the raw Beijing archive cannot run from a fresh
  clone.** Those files are gitignored; `phase1-omnist/data/README.md` lists where to download them.
- The arXiv identifier 2611.04256 is taken from the repository documents and was not re-checked
  against arXiv.
- The baselines E-STGCN and IGNNK are the author's re-implementations, not the original authors' code.

## 5. Corrections made during finalization

| Finding | Correction |
|---|---|
| Phase 2 contains no conformal module; the parity gate uses plain split-conformal calibration inline. Several documents described the scalable conditional conformal front as implemented. | Marked as planned for Semester 4 in the report, the overview, the proposal, and the Phase 2 package docstring. |
| The abstract said the attention gives "provably the same answer". The experiment measures numerical equivalence. | Changed to "numerically the same answer in testing". |
| The abstract described the conformal rework in the present tense. | Changed to future tense. |
| The report appendix and proposal cited files a PDF reader cannot open. | Report made self-contained; proposal paths now carry the phase folder prefix. |
| Phase 2 documents pointed to a file in a retired project outside this repository. | References removed. |

## 6. State of the work at submission

| Component | Status |
|---|---|
| Phase 1 (OmniST): design, validation on four real datasets, drift handling, scale to 325 sensors | Complete |
| Phase 2: sub-quadratic attention, parallel temporal block | Implemented; parity and equivalence gates passed |
| Phase 2: scalable conditional conformal | Planned, not implemented |
| Phase 2: coverage at scale, throughput and memory study, full multi-seed evaluation | Planned |
| Reusable software library | Planned |

## 7. Reproduce

```bash
cd phase1-omnist && python3 -m pip install -r requirements.txt && python3 -m pytest -q
python3 experiments/06_inductive_conformal.py        # about 3.5 minutes on an M4 Pro
cd ../phase2-omnist-scale && python3 -m pytest -q
python3 experiments/V2_attention_equivalence.py      # no training
cd .. && python3 tools/audit_links.py
```
