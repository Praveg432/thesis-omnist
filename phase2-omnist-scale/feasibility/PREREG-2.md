# Pre-registration 2: strengthening the two working leads

Committed before any run of this round. Sandbox only; `thesis-omnist/` is read, never written. Results go to
`REPORT-2.md` whatever they show.

## Lead L1: masked-station training gives a Day-0 forecaster that beats neighbour interpolation on road networks

Round 1 evidence: PeMS-BAY, 5 splits, 15.6% below the best neighbour baseline; Delhi ties. Questions: does it replicate
with more splits and on a second road network, which component carries it, do its Day-0 intervals hold, and is it
sensitive to the mask ratio?

Design as in `PREREG.md`, plus:
- **Networks and splits.** PeMS-BAY splits 0 to 9 (5 to 9 are fresh). PeMSD7-M (228 sensors, 5-minute cadence,
  window 48, horizon 12, coordinates reconstructed by the thesis loader from the road-distance matrix) splits 0 to 9,
  a network not used in round 1. PeMSD7-M has no seasonal-naive baseline (its daily period of 288 steps exceeds the
  window).
- **Ablations, all with masked training at ratio 0.2.** (a) learned attention with the relative-distance bias (v2 as
  in round 1); (b) the same without the distance bias; (c) a plain mean over the same k neighbours, no attention.
- **Mask ratio.** 0.1 and 0.4 on PeMS-BAY splits 0 to 4.
- **Day-0 intervals.** Calibration stations are also treated as Day-0 stations (history removed), so calibration and
  test stations are exchangeable; forecast-time expanding conformal at 90%. The neighbour baseline gets the same
  procedure.

| ID | Pass if |
|---|---|
| L1a | On PeMS-BAY (10 splits) and separately on PeMSD7-M (10 splits): v2 Day-0 MAE at least 5% below the best neighbour baseline, paired 95% interval below 0. Splits 5 to 9 of PeMS-BAY are also reported alone |
| L1b | Learned attention needed: v2 Day-0 MAE below the mean-over-neighbours ablation, paired 95% interval below 0, on both networks. Distance bias needed: v2 below the no-bias ablation, same rule |
| L1c | Day-0 intervals: coverage within 0.03 of 0.90 and interval score below the neighbour baseline's, paired 95% interval below 0, on both networks |
| L1d | Robust to mask ratio: at 0.1 and 0.4 the Day-0 MAE is still at least 5% below the best neighbour baseline on PeMS-BAY |

## Lead L2: the thesis model's traffic weakness is caused by its missing time-of-day input

The thesis model (OmniST v1) encodes day of year, day of week, month and year; for the single-year traffic series the
year input is constant. Test: the thesis's own C1b pipeline (corrected coordinate frame, same splits, seeds and
training), run from the sandbox, with the constant year input replaced by the time of day as a fraction of the day.
No other change. The comparison is against the committed `exp_C1b_norm_<domain>.json` (6 splits each).

- **Control.** The sandbox copy of the pipeline must first reproduce split 0 of the committed corrected-frame result
  exactly (coverage and test MAE to four decimals) on both traffic networks, with time of day switched off. If it does
  not, L2 is not run.

| ID | Pass if |
|---|---|
| L2a | Time of day lowers the thesis model's test MAE by at least 10%, paired 95% interval below 0, on PeMS-BAY and on PeMSD7-M |
| L2b | With time of day the thesis model's MAE is below seasonal-naive on PeMS-BAY (3.47, thesis C1c) and below persistence on PeMSD7-M (3.63, thesis C1c) |
| L2c | Forecast-time (chronological) coverage stays within 0.02 of 0.90 and the interval width falls |

Every rule is reported as pass or fail with its numbers.
