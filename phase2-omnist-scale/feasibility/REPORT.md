# OmniST v2 feasibility: results

Sandbox test of the three proposed upgrades, run 26 Nov 2026 against the rules in `PREREG.md` (commit 1df2868, made
before any training). Code at commit 889a7be. `thesis-omnist/` was only read: its HEAD (7a0f69e) and working tree are
unchanged and no file in it is newer than the pre-registration. Numbers: `results/verdicts.json`.

## Verdicts

| ID | Claim | Delhi (10 splits) | PeMS-BAY (5 splits) | Verdict |
|---|---|---|---|---|
| F1 | Relative-bias attention helps stations with history | v2 27.18 vs GRU 26.61 MAE; difference +0.56 [-0.20, +1.33] | 2.831 vs 2.868; -0.04 [-0.10, +0.03] | **FAIL** on both |
| F2 | Masked training costs nothing for stations with history | ratio 1.004 | ratio 0.983 | **PASS** |
| F3 | Day-0 forecasting beats neighbour baselines by 5% or more | v2 29.16 vs GRU forecasts interpolated from neighbours 29.50; -0.34 [-1.29, +0.60], 1.2% better | 4.72 vs 5.59; -0.88 [-1.15, -0.60], 15.6% better | **FAIL** Delhi, **PASS** PeMS-BAY |
| F4 | Seasonal residual plus scale head beats seasonal-naive intervals | (not applicable) | interval score 25.9 vs 40.9; -14.9 [-16.7, -13.1]; coverage 0.895 | **PASS** |
| F4b | ...and the gain needs the spatial parts | | v2 25.92 vs GRU with the same head 26.06; -0.15 [-0.47, +0.18] | **FAIL** |
| F5 | Relative-bias attention keeps the memory advantage | | 85 MB vs 879 MB dense at N = 8,000 (10.4 times less); 3.7-fold growth from 2,000 to 8,000 | **PASS** |

## What this means for each upgrade

**Upgrade 1 (relative-distance bias, zero-initialised gate).** It does not make the spatial branch useful for stations
that have their own history. The learned gate stays small (mean |gate| about 0.06), and warm accuracy is equal to the
shared GRU on both networks. The shortcut-learning diagnosis is consistent with this, but this upgrade alone does not
fix it. The zero-initialised gate makes v2 equal to the GRU at initialisation (tested), not after training: on Delhi
v2 ended slightly worse (not significant). It is translation-invariant by construction (tested), which removes the
Delhi-constants class of defect.

**Upgrade 2 (masked-station training).** This is the one upgrade with a measured benefit that a GRU cannot match on its
own terms, and only for Day-0 forecasting at a sensor with no history. It costs nothing for warm stations.
- On PeMS-BAY, Day-0 error is 15.6% below the best neighbour baseline (GRU forecasts at neighbouring sensors,
  inverse-distance weighted). Learned attention over relative geometry beats distance weighting on a road network,
  where the nearest sensor can be on another freeway.
- On Delhi it ties that baseline (1.2%, not significant). For a dense air-quality network, "why not a GRU?" has
  a simple answer: a GRU plus inverse-distance weighting of its neighbours' forecasts is as good at Day 0.
- Without masked training the spatial model is useless at Day 0 (Delhi 65.6, PeMS-BAY 5.62), so masking is what
  creates the capability, not the attention.
- Day-0 error is still far above warm error (PeMS-BAY 4.72 against 2.87), so the warm-up curve (contribution B) is
  where the value would be shown.
- Prior art: mask-and-reconstruct training is the standard inductive-kriging approach (IGNNK, AAAI 2021). KITS
  (AAAI 2025, arXiv:2311.02565) argues that masking creates a gap between training and test graphs and adds virtual
  nodes instead. UniSTOK (arXiv:2603.05301) addresses blockwise missingness. The proposal's description of KITS as
  masking is inaccurate. A Day-0 forecaster is a kriging-plus-forecasting model, not new. What was not found here is
  that combined with forecast-time conformal intervals at a new sensor, which is the thesis's angle.

**Upgrade 3 (seasonal residual and scale head).** It fixes traffic intervals: interval score 37% below seasonal-naive
at coverage 0.895. But the same head on the plain GRU does equally well, so this is a forecasting-head change for any
backbone, not evidence for OmniST. Two further points:
- The residual needs the target's own value one period earlier, so it cannot be used at Day 0. The code refuses it
  (tested). It does not combine with Upgrade 2 for a cold sensor unless the base is borrowed from neighbours (not tested).
- In this sandbox even the plain GRU beats seasonal-naive on PeMS-BAY (MAE 2.87 against 3.41; interval score 33.2
  against 40.9), while the thesis's OmniST lost (MAE 4.73 against 3.47). The sandbox models receive a time-of-day
  input that the thesis model's time encoding lacks (it encodes day of year, day of week, month and year only). That
  is a likely cause of the thesis's traffic weakness, but the setups also differ in training procedure, so it is a
  hypothesis to test directly by adding time of day to OmniST v1, not a finding.

## Recommendation

- **Adopt for contribution B:** masked-station training, stated as kriging-style training with prior art cited, and
  evaluated on the 0 to 60 day curve with forecast-time intervals. Claim the Day-0 advantage only where it is measured
  (road networks so far), with GRU-plus-interpolation as the baseline, not "a GRU cannot do it".
- **Adopt for contribution D:** the seasonal residual and scale head, credited as a head change that works with any
  backbone. First test the cheaper explanation: time of day added to the thesis model's inputs.
- **Do not claim Upgrade 1 as an improvement.** Keep the relative features only because masked training needs a
  translation-invariant spatial input.
- **Do not frame Phase 2 as "OmniST v2 is necessary over a GRU".** The evidence supports "spatial context matters at
  Day 0 on road networks", which is narrower and defensible.

## Limits of this test

- 10 Delhi and 5 PeMS-BAY splits, one training budget (1,500 steps), one mask ratio (20%), one k (8). Not tested:
  PeMSD7-M, weather, Beijing, other budgets or ratios.
- The sandbox GRU is not the thesis's OmniST v1; v1 was not re-run here. The comparison is v2 against a GRU with
  identical inputs, which is what the proposal's argument needs.
- Day-0 results are point accuracy only; coverage of intervals at Day 0 was not tested.
- Memory was measured on CPU with resident-set size, inference only; not the same method as the thesis's V4, so the
  10.4-fold figure is not comparable with its 16.7-fold one.

## Files

`PREREG.md` (rules), `v2lib.py` (data, model, baselines), `run_feasibility.py` (F1 to F4), `memory_check.py` (F5),
`summarise.py` (verdicts), `tests/test_v2lib.py` (6 tests: zero gate equals GRU at initialisation, Day-0 forecast
independent of own history, neighbours exclude the target, translation invariance, residual refused at Day 0, thesis
station split), `results/` (per-split results, `memory.json`, `verdicts.json`), `logs/` (run logs, not committed).
