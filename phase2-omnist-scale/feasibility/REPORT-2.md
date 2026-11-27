# Round 2: strengthening the two leads

Run 26 Nov 2026 against `PREREG-2.md` (commit 99a9d73, before any run). Code commits 06df2bc and d1ef21a (the second
adds an exploratory, non-pre-registered option). `thesis-omnist/` was read only. Numbers: `results/verdicts2.json`,
`results/l2x_stride_summary.json`.

## Lead L1: Day-0 forecasting with masked-station training

| ID | Rule | PeMS-BAY (10 splits) | PeMSD7-M (10 splits, new network) |
|---|---|---|---|
| L1a | Day-0 MAE at least 5% below the best neighbour baseline | **PASS.** 4.71 vs 5.62 (GRU forecasts at neighbours, inverse-distance weighted); -0.91 [-1.04, -0.78]; 16.2% lower. Fresh splits 5 to 9 alone: 16.8% | **PASS.** 7.43 vs 8.29; -0.86 [-1.14, -0.57]; 10.3% lower |
| L1b | Learned attention beats a plain mean over neighbours | **PASS**, by 1.8%: -0.09 [-0.12, -0.06] | **FAIL**: -0.03 [-0.18, +0.12] |
| L1b | The distance bias matters | **PASS**, by 1.6%: -0.07 [-0.10, -0.04] | **FAIL**: -0.02 [-0.14, +0.10] |
| L1c | Day-0 intervals: coverage within 0.03 of 0.90 and interval score below the baseline | **PASS.** Coverage 0.879; interval score 52.1 vs 61.4; width 17.8 vs 26.3 | **PASS.** Coverage 0.880; 61.3 vs 67.5; width 39.2 vs 43.0 |
| L1d | Still at least 5% better at mask ratios 0.1 and 0.4 | **PASS.** Ratio to the baseline 0.858 (0.1), 0.844 (0.2), 0.838 (0.4) | not run |

**What carries the gain.** Masked training with any learned pooling of the neighbours' encoded histories gives most
of it. A plain mean over the k neighbours, with no attention and no distance features, is already 14.7% (PeMS-BAY) and
9.9% (PeMSD7-M) below the baseline. The distance-biased attention adds about 2 points on PeMS-BAY and nothing
measurable on PeMSD7-M. Round 1's finding stands: without masked training the spatial model is useless at Day 0.

**Costs and limits.**
- Day-0 error is still 1.6 to 2.3 times the warm error (PeMS-BAY 4.71 against 2.85; PeMSD7-M 7.43 against 3.24).
- Day-0 coverage is about 2 points below target on both networks.
- On PeMSD7-M masked training cost 1.3% of warm accuracy (3.24 against 3.20 for the GRU). Round 1 allowed 1%, though
  that was a round-1 rule, not re-tested here.
- On Delhi (air quality, round 1) the Day-0 advantage was 1.2% and not significant. The lead holds for road networks.
- Not tested: weather and Beijing; Day 1 to 60 (contribution B proper); other training budgets.

## Lead L2: the thesis model's traffic weakness

**Control.** The sandbox copy of the thesis C1b pipeline reproduced the committed corrected-frame split 0 exactly on
both traffic networks (test MAE and all three coverage protocols to four decimals). The comparisons below therefore
change one thing at a time.

| ID | Rule | PeMS-BAY (6 splits) | PeMSD7-M (6 splits) |
|---|---|---|---|
| L2a | Time of day lowers MAE by at least 10% | **FAIL.** 4.722 vs 4.727; -0.005 [-0.023, +0.013] | **FAIL.** 3.764 vs 3.789; -0.025 [-0.076, +0.025] |
| L2b | ...and beats the simple baseline | **FAIL** (seasonal-naive 3.47) | **FAIL** (persistence 3.63) |
| L2c | Coverage within 0.02, width falls | **PASS** (coverage 0.881, width unchanged) | **PASS** (0.891; width 17.3 to 17.0) |

**The time-of-day hypothesis is refuted.** A missing time-of-day input is not why the thesis model is weak on traffic.

**Exploratory follow-up (not pre-registered, 3 splits).** The thesis traffic loaders train on non-overlapping windows
(stride = window = 48 steps). At PeMS-BAY's 30-minute cadence that is 24 hours, so every training window starts at the
same clock time while evaluation uses four. Changing only the stride to 12:

| Network | MAE, stride 48 (committed) | MAE, stride 12 | Difference [95% CI] | Chronological coverage | Width |
|---|:---:|:---:|:---:|:---:|:---:|
| PeMS-BAY | 4.62 | **3.73** (lower on all 3 splits) | -0.88 [-1.78, +0.01]; 19% lower | 0.882 to 0.895 | 19.0 to 18.4 |
| PeMSD7-M | 3.83 | 3.77 | -0.06 [-0.29, +0.18]; 1.5% lower | 0.888 to 0.891 | 17.1 to 16.6 |

The effect is large where the stride equals a full day (PeMS-BAY) and small where it does not (PeMSD7-M, 5-minute
cadence, stride of 4 hours), which fits the mechanism. With 3 splits it is not significant at 95%. Even with stride 12
the thesis model (3.73) stays above seasonal-naive (3.47) and above the sandbox GRU (2.9). The rest of the gap must
come from other training differences (about 300 optimiser steps with early stopping and the peaks-over-threshold loss,
against 1,500 steps with L1 loss in the sandbox); these were not separated.

## What this changes for the decision

1. **Contribution B (a new sensor's first weeks).** The Day-0 lead is now replicated on two road networks with valid
   intervals and a 10% to 17% advantage over interpolating a GRU's forecasts. It is robust to the mask ratio. The
   evidence supports adding masked-station training to the plan. The defensible claim is *masked training with neighbour
   pooling*, with prior art cited (IGNNK; KITS argues for virtual nodes instead of masking). The distance-biased
   attention should be presented as optional, worth about 2% on one network. It does not hold for the air-quality
   network tested.
2. **Contribution D (useful traffic intervals).** The cheapest first step is not an architecture change. It is the
   training-window sampling of the thesis traffic loaders, which on PeMS-BAY fixes every training window to one clock
   time. That needs a pre-registered test on the full 6 splits before it is relied on. The round-1 seasonal residual
   and scale head remain the next step, credited as a head change for any backbone.
3. **For the thesis record, not acted on here.** If the stride effect is confirmed, the committed PeMS-BAY accuracy
   and width figures are pessimistic for a reason unrelated to calibration. Coverage moved little (0.882 to 0.895), so
   the calibration conclusions are unaffected. Nothing in `thesis-omnist/` was changed.
4. **Still not supported:** "OmniST v2 is necessary over a GRU" for stations with history (round 1, F1 failed on both
   networks; warm accuracy is equal), and time of day as the traffic fix.

## Files added in this round

`PREREG-2.md`, `run_leads.py` (L1), `tod_v1.py` (L2 and the exploratory stride option), `summarise2.py`,
`summarise_stride.py`, `tests/test_v2lib_round2.py` (3 tests; 9 in the sandbox suite), results `leads_*`, `l2_*`,
`l2x_*`, `verdicts2.json`.
