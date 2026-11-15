# Phase 2 Consolidated Findings (15 Nov 2026)

New measurements run after the review-corrected plan (`RESEARCH-PLAN.md`), reconciled with what the
repository already recorded. Tables in Section 2 are generated from `results/*.json` by
`tools/summarise_phase2.py`; prose numbers are checked against them.

Hardware: Apple M4 Pro. Time on MPS; peak memory as peak-RSS delta in a fresh CPU process (MPS has no
resettable peak counter). Memory ratios therefore describe CPU-side tensor memory, not MPS memory.

## 1. What was run

| Id | What | Result file |
|---|---|---|
| V4 | Memory and time against N (exact vs neighbour attention); time against T (GRU vs SSM sequential vs SSM chunked) | `results/V4_scaling_crossover_results.json` |
| V3 | Coverage and interval width against N, node-exchangeable split (train 55% / calibration 20% / test 25%), two calibration protocols; real PeMS-BAY (N=325, real coordinates) and a synthetic ladder to N=4000 | `results/V3_coverage_at_scale_real.json`, `results/V3_coverage_at_scale_synthetic.json` |
| V3b | Real-data training-budget sweep (300, 1200, 3000 steps), one seed | `results/V3b_training_budget.json` |
| X2 audit | Chunked closed-form SSM scan against the sequential scan (relative L2 and max absolute difference, T from 16 to 500) | `tests/test_consolidation.py`, `src/omnist_scale/ssm_temporal.py` |
| Data check | Real PeMS-BAY coordinates against the released adjacency | Section 4 |

## 2. Results

### V4 spatial (inference, CPU peak RSS delta; time on MPS)

| N | exact ms | exact MB | fast ms | fast MB | memory ratio |
|---|---|---|---|---|---|
| 100 | 1.4 | 4 | 1.5 | 28 | 0.1 |
| 500 | 3.4 | 13 | 2.4 | 32 | 0.4 |
| 1000 | 3.1 | 34 | 3.7 | 36 | 1.0 |
| 2000 | 6.6 | 115 | 3.0 | 44 | 2.6 |
| 4000 | 25.4 | 417 | 4.4 | 58 | 7.2 |
| 8000 | 78.7 | 1551 | 9.3 | 93 | 16.7 |

### V4 spatial (training: 8 per-timestep applications + backward, CPU peak RSS delta)

| N | exact MB | fast MB | ratio |
|---|---|---|---|
| 500 | 41 | 62 | 0.7 |
| 1000 | 86 | 86 | 1.0 |
| 2000 | 203 | 129 | 1.6 |
| 4000 | 575 | 220 | 2.6 |

### V4 temporal (forward+backward, N=100 nodes, d=64, 2 layers, MPS)

| T | GRU ms | SSM sequential ms | SSM chunked ms | chunked / GRU |
|---|---|---|---|---|
| 30 | 26.0 | 38.4 | 51.4 | 1.98 |
| 60 | 51.1 | 78.8 | 101.8 | 1.99 |
| 120 | 119.8 | 173.0 | 204.7 | 1.71 |
| 240 | 224.4 | 412.6 | 409.7 | 1.83 |
| 480 | 462.1 | 1332.5 | 849.5 | 1.84 |
| 960 | 1030.7 | 4584.9 | 1828.5 | 1.77 |

### V3 synthetic ladder (3 seeds; SYNTHETIC)

| N | n_cal | band | coverage same-window (oracle timing) | coverage deployable | width model (dep.) | width persistence | width seasonal-naive | worst-group global | worst-group Mondrian | infer s/window |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | 20 | [0.751, 0.988] | 0.947 [0.916, 0.977] | 0.914 [0.847, 0.981] | 3.13 | 3.25 | 6.44 | 0.886 | 0.893 | 0.037 |
| 500 | 100 | [0.836, 0.951] | 0.908 [0.889, 0.927] | 0.901 [0.866, 0.936] | 3.10 | 3.51 | 6.34 | 0.891 | 0.873 | 0.055 |
| 1000 | 200 | [0.856, 0.938] | 0.911 [0.905, 0.917] | 0.912 [0.881, 0.944] | 3.13 | 3.53 | 6.42 | 0.904 | 0.903 | 0.071 |
| 2000 | 400 | [0.869, 0.928] | 0.906 [0.893, 0.920] | 0.905 [0.864, 0.946] | 3.02 | 3.46 | 6.51 | 0.901 | 0.893 | 0.111 |
| 4000 | 800 | [0.878, 0.920] | 0.902 [0.901, 0.904] | 0.880 [0.821, 0.940] | 2.91 | 3.53 | 5.96 | 0.874 | 0.874 | 0.185 |

### V3 real PeMS-BAY, N=325 (3 seeds, real coordinates)

| variant | steps | band | coverage same-window | coverage deployable | width model (dep.) | persistence | seasonal-naive | MAE model | MAE seasonal | worst-group global | worst-group Mondrian |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gru+fast | 1200 | [0.830, 0.965] | 0.940 [0.917, 0.963] | 0.918 [0.901, 0.935] | 21.60 | 26.20 | 17.89 | 3.57 | 3.41 | 0.906 | 0.899 |
| gru+exact | 1200 | [0.830, 0.965] | 0.939 [0.916, 0.961] | 0.921 [0.907, 0.935] | 21.93 | 26.20 | 17.89 | 3.48 | 3.41 | 0.908 | 0.897 |

### V3b training budget (PeMS-BAY, seed 0, deployable protocol)

| steps | train s | coverage dep. | width model | width seasonal | width persistence | MAE model | MAE seasonal |
|---|---|---|---|---|---|---|---|
| 300 | 82 | 0.919 | 23.95 | 15.87 | 28.70 | 3.68 | 3.48 |
| 1200 | 364 | 0.926 | 22.61 | 15.87 | 28.70 | 3.48 | 3.48 |
| 3000 | 790 | 0.923 | 19.37 | 15.87 | 28.70 | 3.23 | 3.48 |

Verdict string in file: Width stays above seasonal-naive at the largest budget -> the patch-trained model is not competitive with a trivial seasonal predictor on this real traffic data.

## 3. Calibration protocols (read before comparing any coverage number)

| Protocol | Quantile comes from | Deployable? | Where used |
|---|---|---|---|
| Training-station calibration | residuals at training stations | yes, but optimistic (stations already fitted) | Phase 1 original runs |
| **Deployable (chronological)** | residuals at held-out calibration stations pooled over the earlier half of the evaluation windows; applied to test stations in the later half | **yes** | V3 headline; closest to Phase 1 C1 |
| Same-window | residuals at calibration stations at the very window being forecast | **no**: needs their targets before they exist | V3 `same_window`, kept for comparison |

The same-window protocol removes temporal non-stationarity from the comparison and so overstates
validity. The gap between the two columns in the tables is the cost of that non-stationarity.

## 4. Findings

### 4.1 Neighbour attention (V4, supports WP3)
- Output equivalence with exact attention was already shown on random tokens (V2, minimum cosine
  0.99987). V4 adds the cost curves in Section 2: from N=4000 the neighbour path uses 7.2x less
  inference memory (417 vs 58 MB) and 5.8x less time (25.4 vs 4.4 ms); at N=8000, 16.7x less memory
  (1551 vs 93 MB) and 8.4x less time. At N=1000 the two cost about the same, and below that the
  neighbour path is slightly heavier (fixed overhead of the neighbour search).
- **Training memory gains less:** 1.6x at N=2000 and 2.6x at N=4000, because the gathered
  neighbour tensors are kept for the backward pass.
- On real PeMS-BAY (N=325), `gru+fast` and `gru+exact` give coverage 0.918 and 0.921 and MAE 3.57 and
  3.48. Differences are small, but this is three seeds and no equivalence test; V1b is the planned
  equivalence test. (An earlier 300-step run gave near-identical numbers; at 1200 steps the two
  variants differ slightly, as expected from accumulated floating-point differences.)

### 4.2 State-space block (V4, supports the X2 decision)
- The chunked closed-form scan is 1.7 to 2.0 times slower than the GRU at every T from 30 to 960
  (forward+backward). The sequential scan is 1.5 to 4.5 times slower. This agrees with the earlier
  T1 diagnostic (about 2x slower).
- The chunked scan stays within about 6e-5 relative L2 of the sequential scan but has a maximum
  absolute difference up to 7.8e-3, because the log-decay is clamped to keep the scan finite.
- **Both X2 acceptance criteria fail** (equal within 1e-4; no slower than the GRU at T >= 240). By the
  plan's own rule X2 is dropped. The code is kept as an exploratory option (`mode="chunked"`), default
  unchanged.

### 4.3 Coverage against N (V3, supports WP3)
- **Real, N=325:** deployable coverage 0.918 [0.901, 0.935] (`gru+fast`) and 0.921 [0.907, 0.935]
  (`gru+exact`), inside the band [0.830, 0.965] over 65 calibration stations. Phase 1's C1 reports
  0.892 for PeMS-BAY (6 splits, 45 test stations, models trained on the full network). The two are
  **not directly comparable**: V3 trains on spatial patches for 1200 steps, uses a different split
  size, and pools calibration residuals over windows differently.
- **Synthetic, N=100 to 4000:** deployable coverage 0.914, 0.901, 0.912, 0.905, 0.880. The N=4000
  mean is at the lower edge of its band [0.878, 0.920] and two of three seeds are below it (0.869,
  0.864); three seeds cannot settle whether this is chance or a genuine under-coverage of about 2
  points when calibration residuals come from earlier windows. The same-window numbers (0.902 at
  N=4000) hide it. This is a synthetic field with slowly drifting regional factors, not evidence about
  real networks.
- Inference time per window rose from 0.037 s to 0.185 s for a 40x increase in nodes; these timings were
  taken while three jobs shared the machine, so use V4 for timing claims.

### 4.4 Are the intervals useful, or only valid? (V3, V3b)
- **Synthetic:** the model's interval is 4% to 18% tighter than persistence and about half the
  seasonal-naive width, at every N.
- **Real PeMS-BAY:** the model is 17.5% tighter than persistence (21.6 vs 26.2) but **20.8% wider than
  seasonal-naive** (21.6 vs 17.9) at 1200 steps. Point accuracy is close (MAE 3.57 vs 3.41).
- **More training improves point accuracy but not the interval gap** (V3b, one seed): at 3000 steps MAE is
  3.23 against 3.48 for seasonal-naive (7% better), yet the width is 19.37 against 15.87 (22% wider).
  Under the earlier same-window protocol the gap looked like undertraining that training would close;
  under the deployable protocol it does not close within 3000 steps. A plausible cause is a heavier
  error tail of the model at some stations, but this was not investigated.
- Consequence: a claim that the forecaster gives *useful* calibrated intervals on real traffic is not
  supported against a seasonal-naive baseline. WP5 (stronger baselines) matters for this reason.

### 4.5 Coverage by distance from the training network (V3)
- Worst coverage over three distance-to-nearest-training-station terciles, with the global quantile:
  real PeMS-BAY 0.906 (`gru+fast`) and 0.908 (`gru+exact`); synthetic 0.874 to 0.904. With Mondrian
  (per-tercile) quantiles: 0.899 and 0.897 on real data.
- So in PeMS-BAY the worst distance group already sits at about the target. This agrees with Phase 1's
  C2 (distance matters little in dense networks) and means a geometry-aware method (WP1) has little
  to repair there. The distance effect that WP1 targets is expected in sparse networks and still needs
  the large sparse network from WP0. An earlier estimate of a 0.86 to 0.89 gap was inflated by the
  same-window protocol and by taking a minimum over three noisy groups.

### 4.6 Data (check)
`pems_bay_coords.csv` holds real sensor coordinates. Their order matches the released adjacency:
Spearman correlation between adjacency weight and haversine distance is -1.000 over 19,281 connected
pairs, against -0.010 when the order is shuffled. Phase 1 reconstructs PeMS-BAY coordinates from the
adjacency instead; using the real ones removes that limitation for this dataset. PeMSD7-M has no
such file.

## 5. Status against the pre-registered criteria

| Item | Criterion (from `RESEARCH-PLAN.md`) | Status |
|---|---|---|
| WP3 | Neighbour attention uses >= 5x less peak memory than exact at N >= 2,000 | **Not met at N=2000 (2.6x).** Met for inference from N=4000 (7.2x) and N=8000 (16.7x). Training memory: 2.6x at N=4000 |
| WP3 | N at which exact attention runs out of memory identified | Not done (exact used 1.55 GB at N=8000 on CPU) |
| WP3 | Neighbour-set agreement >= 0.99 | Not measured (V2 measured output cosine only) |
| WP3 | Marginal coverage within 0.02 of 0.90 at every size | Real N=325: met (0.918). Synthetic: met to N=2000; N=4000 is 0.880, at the edge. **No real network above 325 sensors** |
| WP3 | Compare with at least one published efficient model | Not done |
| X2 | Equal to sequential within 1e-4; no slower than GRU at T >= 240 | **Both fail. X2 dropped** |
| WP0 | V1b, local frame, large sparse network, LargeST check | Not done |
| WP1, WP2, WP4, WP5 | as in the plan | Not started |

## 6. Corrections to earlier statements

These replace statements in `../../omnist-scale/docs/VALIDATION-REPORT.md` and in the conversation
that produced it.
1. "Coverage in-band at every N" held only for the same-window protocol, which is not deployable.
2. "The model ends up about 9% tighter than seasonal-naive at 3000 steps" came from the same-window
   protocol. Under the deployable protocol the model is 22% wider.
3. "A 0.86 to 0.89 worst-group gap is an open research core" is not supported (Section 4.5).
4. Memory ratios from the first V4 run (17.5x inference, 12x time at N=8000) were 16.7x and 8.4x on
   re-run with the corrected cache code.
5. V1's coverage figures used training-station calibration; accuracy parity from V1 stands as a
   preliminary result only (V1b not run).

## 7. Not established

- No real network above 325 sensors; all results at N=1000 to 4000 are synthetic.
- No equivalence test between `gru+fast` and `gru+exact` on trained models (V1b).
- MPS memory was not measured; memory is CPU peak RSS.
- Three seeds per cell. Intervals are wide at N=4000.
- The synthetic field has smooth, stationary-ish structure and constant density; real networks differ.
- Cause of the model's wider-than-seasonal-naive interval on real traffic is untested.

