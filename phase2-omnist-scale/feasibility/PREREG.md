# Pre-registration: feasibility of the proposed OmniST v2 upgrades

Committed before any model in this folder was trained. Sandbox only: `thesis-omnist/` is read, never written
(imports run with bytecode writing off; its git status is checked before and after).

## Claims under test

| ID | Claim in the proposal | Test |
|---|---|---|
| F1 | Relative-distance-biased k-NN attention with a zero-initialised gate makes the spatial branch useful when a station has its own history | Warm MAE of v2 (no masking) against a shared GRU with identical inputs |
| F2 | Masked-station training does not cost accuracy for stations with history | Warm MAE of v2 (masked training) against the shared GRU |
| F3 | Masked-station training gives a genuine Day-0 forecaster that a GRU cannot match | Cold MAE (target history removed) of v2 against neighbour baselines that need no training on the target: nearest-neighbour and inverse-distance weighting of neighbours' persistence, seasonal-naive and shared-GRU forecasts. A GRU alone cannot forecast at Day 0, so beating "nothing" is not the bar |
| F4 | Seasonal-residual plus a scale head fixes traffic intervals | On PeMS-BAY, forecast-time conformal interval score of v2 with residual and scale head against seasonal-naive, and against a GRU with the same residual and scale head (attribution) |
| F5 | The relative-bias attention keeps the memory advantage | Peak memory of the v2 spatial layer against dense attention at N = 2,000 to 8,000 |

## Fixed design

- Networks: Delhi PM2.5 (37 stations, daily; window 60, horizon 30) and PeMS-BAY (325 sensors, 30-minute
  cadence; window 48, horizon 12; real sensor coordinates from `pems_bay_coords.csv`).
- Station splits: the thesis C1 partitions (permutation seeded 1000 + split; Delhi 8 calibration and 8 test stations,
  PeMS-BAY 45 and 45). Delhi splits 0 to 9, PeMS-BAY splits 0 to 4. Model seed = split.
- Temporal split as in the thesis loaders (Delhi: test year 2023, last 180 training days unused; PeMS-BAY: last 20%
  test, 10% before it unused). Normalisation from training stations in the training period.
- All variants share one encoder (input projection and a one-layer GRU, width 64) and the same inputs: the station's
  own normalised values, an observed flag, and day-of-year, day-of-week and time-of-day features. The shared GRU is
  the same model with the spatial branch switched off.
- Spatial branch: k = 8 nearest observed neighbours, relative features (dx, dy, d, log(1 + d)) in units of the
  network's median nearest-neighbour spacing, 2-head attention with a learned bias from those features, output added
  through a per-channel gate initialised at zero. Neighbours are always training stations; evaluated stations never
  see each other.
- Masked training: 20% of training stations per window have their history zeroed and flagged; they remain targets
  and are never neighbours.
- Loss: L1 on the normalised scale; with a scale head, Laplace negative log-likelihood. Training: 1,500 steps, Adam,
  learning rate 1e-3; batch 16 windows (Delhi), 8 (PeMS-BAY).
- Evaluation: test period, windows every horizon length; MAE in original units on the test stations.
  Neighbour baselines use inverse squared distance weights over the same 8 neighbours.
- Intervals (F4): forecast-time (chronological, expanding) split conformal at 90% from the calibration stations,
  first 25% of windows as history, using the thesis's `chronological_conformal` functions; interval score as in
  the thesis.

## Pass rules

| ID | Pass if |
|---|---|
| F1 | On at least one network, v2 (no masking) warm MAE is at least 2% below the shared GRU, paired 95% interval of the difference below 0 |
| F2 | On both networks, mean warm MAE of v2 (masked) is at most 1.01 times the shared GRU's |
| F3 | On each network, v2 (masked) cold MAE is at least 5% below the best neighbour baseline (lowest mean), paired 95% interval below 0 |
| F4 | On PeMS-BAY, v2 with residual and scale head has interval score below seasonal-naive (paired 95% interval below 0) with coverage within 0.02 of 0.90; attribution to OmniST requires it also to be below the GRU with residual and scale head (paired interval below 0) |
| F5 | At N = 8,000 the v2 spatial layer uses at least 5 times less peak memory than dense attention (or dense attention does not fit), and its memory grows at most 5-fold from N = 2,000 to 8,000 |

Every rule is reported as pass or fail with its numbers. Small sample: 10 and 5 splits; intervals over splits.
