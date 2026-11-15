# Learnings and Retired Directions (consolidated 15 Nov 2026)

What was tried around this thesis, what each attempt showed, and what carries forward. Everything
here was run on the same Apple M4 Pro. Sources are the sibling repositories, named in each section;
none of them is part of the thesis deliverable.

## 1. Retired: the topology x drift "fusion" (`../adaptive-st-conformal/`)

**Idea.** Combine OmniST's inductive conformal coverage with label-free test-time adaptation, and
fix a presumed coverage collapse at new sensors when drift and topology change together.

| Stage | Verdict | What it showed |
|---|---|---|
| Surrogate, naive version (uniform drift, global adaptation) | NO-GO, twice | Adaptation simply removes the drift; no coupling |
| Surrogate, sharpened (heterogeneous drift, local adaptation) | GO | Unseen-node coverage falls 0.875 to 0.534 as heterogeneity rises; a global fix misses it |
| Online per-group conformal estimator, surrogate | GO | Reaches the unseen-node band (0.838 vs 0.520 stale) at about 17% wider intervals |
| Real Delhi, lightweight forecaster | PARTIAL | Coupling reproduces (unseen 0.688 vs seen 0.895); restoration incomplete |
| **Real Delhi, full OmniST backbone** | **NO-GO** | **Unseen coverage 0.982 equals seen 0.982. The coupling does not survive a deployable-strength model** |

**Why it died.** The effect existed only for a weak forecaster. OmniST generalises across
coordinates well enough that nothing remains to repair.

**Carry forward.**
1. Test any "coverage breaks here" premise against the strongest realistic backbone first, not a toy.
2. Under drift, calibrate on a held-out slice of the deployment regime. Early runs under- and
   over-covered until this was done.
3. The negative result is worth one paragraph in the thesis limitations: OmniST's inductive coverage
   was not broken by combined drift and topology change in the Delhi test (one dataset, one drift type).

## 2. Parallel exploration: SafeTTA (`../safe-tta/`, `../t9-conformal-tta/`, `../thesis/`)

Not an OmniST work package. Summarised because the progression decision compares the two theses.

- **Setting.** Label-free test-time adaptation of an image classifier under stain shift, with a conformal
  layer and an adapt/abstain gate. PathMNIST (real histopathology).
- **Measured.** Accuracy 0.45 to 0.86 with no target labels; coverage stays valid (0.91 to 0.99). A
  fragile head collapses (0.72 to 0.11) and the gate abstains. Impact runs (5 seeds): recovery +0.406
  [0.362, 0.450], served coverage 0.912, `labels_saved` above 2000 on 4 of 5 seeds.
- **Gate.** AUROC 0.785 on a real CNN. It leaks fast-settling collapses (served-coverage floor 0.063),
  so the frozen conservative reference carries the guarantee and the gate is an efficiency layer.
  A fix was needed along the way: the first proxy counted beneficial repair as corruption (244 of 290
  confident flips were helpful), so the proxy now conditions on confidence inflation.
- **Independent check (`../mtech-thesis-vetting/`, G6, 15 Nov).** With an equal labelled budget,
  label-free adaptation beats supervised fine-tuning only below roughly 100 labelled patches (0.85 vs
  0.74 accuracy at k=50); by k=250 fine-tuning is ahead. The SafeTTA guarantee also needs a labelled
  calibration set, so "label-free" holds for adaptation only. That review marked the pre-registered
  rule FAIL.

## 3. Transferable lessons (apply to this thesis)

1. **Pre-register thresholds, report failures as results.** The fusion, the SSM claim and the G6 rule
   all failed their gates. `phase2-omnist-scale/docs/RESEARCH-PLAN.md` already works this way.
2. **The calibration protocol decides what a coverage number means.** Three protocols appear in this
   work and give different numbers: training-station calibration (original Phase 1, optimistic),
   disjoint-station calibration pooled over time (C1, V3 deployable), and same-window calibration
   (V3 `same_window`, needs targets that are unknown at forecast time). Only the middle one is
   deployable. See `phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`.
3. **A valid-coverage result is weak evidence on its own.** Conformal intervals are valid by
   construction under exchangeability and can be wide. Always report width against trivial baselines
   (persistence, seasonal-naive). In V3 the model lost to seasonal-naive at 300 training steps.
4. **Detectors and gates are efficiency layers.** In both SafeTTA and the fusion, a label-free detector
   leaked failures. Do not let a heuristic carry a guarantee.
5. **Verify data assumptions.** The unused `pems_bay_coords.csv` turned out to be real coordinates in
   the right order (Spearman -1.000 against the adjacency), which removes a limitation. Conversely the
   coordinate embedding's Delhi constants are a real portability limit.
6. **Tooling cautions seen in this work.** Background-process output can be stale; edits applied
   through shell heredocs failed silently once and were only caught by re-reading the file. Verify
   after writing.

## 4. Where each artefact lives

| Artefact | Location | Status |
|---|---|---|
| OmniST (Phase 1), C1 to C3 | `phase1-omnist/` | complete |
| OmniST-Scale (Phase 2) | `phase2-omnist-scale/` | in progress; see consolidated findings |
| Retired fusion | `../adaptive-st-conformal/` (has its own `ARCHIVED-LEARNINGS.md`) | retired, kept |
| SafeTTA | `../safe-tta/`, `../thesis/` | parallel candidate |
| Earlier scaffold of Phase 2 | `../omnist-scale/` | superseded by `phase2-omnist-scale/`; V3 and V4 are re-run there on the corrected code; V1 is not re-run (V1b is the planned replacement) |
| Thesis-track vetting | `../mtech-thesis-vetting/` | external input to the decision |
