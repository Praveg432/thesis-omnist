# Learnings

What the OmniST work showed that is worth carrying into the remaining thesis work. All runs used one
Apple M4 Pro.

## 1. Directions tried and dropped within OmniST

| Direction | Verdict | Evidence |
|---|---|---|
| State-space block replacing the GRU | Dropped. Sequential scan is 2.0 to 2.2 times slower than the GRU at T = 60, 240, 960; a chunked scan is still 1.7 to 2.0 times slower and not exact | `phase2-omnist-scale/results/T1_ssm_vs_gru_timing.json`, `V4_scaling_crossover_results.json` |
| Neighbour attention below about 1,000 sensors | No memory or speed advantage; 7.2x less inference memory at N = 4,000 and 16.7x at N = 8,000 | `V4_scaling_crossover_results.json` |
| Total-variation bound on coverage under distance shift | Vacuous at available sample sizes | C3 |

## 2. Lessons

1. **Pre-register thresholds, report failures as results.** The state-space claim and the parity gate
   both failed or were corrected under this rule. `phase2-omnist-scale/docs/RESEARCH-PLAN.md` works
   this way.
2. **The calibration protocol decides what a coverage number means.** Three protocols appear in this
   work and give different numbers: training-station calibration (original Phase 1, optimistic),
   disjoint-station calibration pooled over time (C1, V3 deployable), and same-window calibration
   (V3 `same_window`, needs targets that are unknown at forecast time). Only the middle one is
   deployable, and C1 itself still calibrates on the test period (plan item P1-1). See
   `phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`.
3. **A valid-coverage result is weak evidence on its own.** Conformal intervals are valid by
   construction under exchangeability and can be wide. Report width against trivial baselines
   (persistence, seasonal-naive). In V3 the model lost to seasonal-naive at 300 training steps.
4. **Under drift, calibrate on a held-out slice of the deployment regime.** Early runs under- and
   over-covered until this was done.
5. **Verify data assumptions.** `pems_bay_coords.csv` turned out to be real coordinates in the right
   order (Spearman -1.000 against the adjacency), which removes a limitation. The coordinate
   embedding's Delhi constants are a real portability limit.
6. **Verify after writing.** Background-process output can be stale, and edits applied through shell
   heredocs failed silently once and were caught only by re-reading the file.

## 3. Where each artefact lives

| Artefact | Location | Status |
|---|---|---|
| OmniST (Phase 1), C1 to C3 | `phase1-omnist/` | complete |
| OmniST-Scale (Phase 2) | `phase2-omnist-scale/` | in progress; see consolidated findings |
