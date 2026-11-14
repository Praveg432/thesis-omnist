# Vetting Report — OmniST-Scale (revised after the preliminary review)

This report states what was run on Phase 2 components, what each result does and does not show, and
which defects the review found. The first version of this report called V1 a clean GO and the
attention "provably equivalent". Neither statement is supported, and both are withdrawn here.

> **Summary.** One result stands as stated: the neighbour attention matches exact attention in output
> on random inputs (V2). One result is preliminary: a first parity check (V1) used a gate that could
> not fail. One finding is negative: the state-space block is sequential and about twice as slow as the
> GRU (T1). Calibration, memory and large-network evidence for Phase 2 do not exist yet. The plan to
> produce them is in [`RESEARCH-PLAN.md`](RESEARCH-PLAN.md).

---

## V1 — first parity check (PRELIMINARY, superseded by V1b)

Four variants, same data, seeds and budget (15 epochs), real Delhi PM2.5, 3 seeds, evaluated at 13
unseen stations on winter days after training on non-winter days. The committed result file is
`results/V1_ssm_matches_omnist_results.json`.

| variant | MAE (mean, 95% interval) | coverage | forward passes per second, N=37 |
|---|:---:|:---:|:---:|
| gru+exact (OmniST baseline) | 64.56 [60.73, 68.38] | 0.948 | 95 |
| ssm+exact | 65.82 [51.74, 79.89] | 0.944 | 94 |
| gru+fast | 64.56 [60.73, 68.38] | 0.948 | 51 |
| ssm+fast | 65.62 | 0.944 | 54 |

**What it shows.** With 3 seeds the accuracy intervals overlap almost entirely, so no difference is
detected. Replacing exact attention by the neighbour attention changed nothing at all (gru+fast equals
gru+exact to four decimals), which is expected when both select the same neighbours.

**Why it is not evidence of parity.**
- The coverage pass band was the finite-sample band [0.753, 0.998] widened by 0.03 on each side,
  that is [0.723, 1.028]. The upper end exceeds 1, so any coverage above 0.723 passed.
- The accuracy tolerance in the code was 10%, not the 2% quoted in earlier documents.
- Three seeds with overlapping intervals show no detectable difference. Parity needs a pre-specified
  equivalence margin and a test.
- The conformal threshold came from training-station residuals, which are not exchangeable with the
  residuals at unseen stations. Coverage of 0.944 to 0.948 against a 0.90 target indicates
  over-coverage, not a verified guarantee.
- Interval width was not reported.
- Preprocessing: normalisation used all 37 stations including the unseen ones, imputation used a
  backward fill and a full-series median, seasons came from `index % 365`, and training windows were
  stitched across the winter gap. The effect of each on the result is small but was not measured.
- It differs from the Phase 1 protocol (7-day horizon, seasonal shift), so its MAE of about 64 cannot
  be compared with the Phase 1 Delhi MAE of about 27.

## V1b — corrected parity gate (PLANNED; smoke-tested only)

`experiments/V1b_parity_equivalence.py` fixes each point above before any full run:
- random train, calibration and unseen-test stations per seed, with calibration on the disjoint
  calibration stations;
- paired equivalence of ssm+fast to gru+exact on per-seed differences, with the two-sided 90% interval
  of the mean difference required to lie inside a margin of 5% of the baseline MAE and 0.03 in
  coverage (the TOST procedure at 5%), over 10 seeds;
- a verdict of GO, NO-GO or INCONCLUSIVE, with widths and per-seed values stored;
- causal imputation, explicit calendar dates, a fixed year reference, no windows across the winter
  gap, normalisation from training stations on training days only.

It has been run in quick mode only to check that it executes. No V1b result exists.

## V2 — neighbour attention versus exact attention (EXECUTED, limited scope)

With shared weights, only neighbour selection differs. Output cosine similarity on random tokens and
uniformly random coordinates in a Delhi-sized box, batch size 1, one layer, d=64:

| N | cosine vs exact | neighbour attention | exact attention |
|---|:---:|:---:|:---:|
| 37 | 1.000000 | 1212 ms (includes first-call setup) | 236 ms |
| 100 | 1.000000 | 142 ms | 3 ms |
| 325 | 0.99998 | 145 ms | 194 ms |
| 1000 | 0.99999 | 152 ms | 225 ms |
| 2000 | 0.99987 | 189 ms | 182 ms |

**What it shows.** The two paths agree in output to cosine 0.99987 or better on this input.

**What it does not show.**
- Cosine similarity of a layer-normalised, residual output on random tokens is insensitive to
  differences in a few neighbours. Neighbour-set agreement and agreement with trained weights are
  not measured.
- Memory was not measured at all. The old claim that exact attention's O(N²) memory "forces the
  switch" is an argument, not a measurement.
- At N=2000 the neighbour path (189 ms) and the exact path (182 ms) take about the same time, and at
  small N the neighbour path is far slower. No speed advantage has been shown at any tested N.
- "Provably equivalent" was wrong. The equivalence is empirical.

## T1 — the state-space block versus the GRU (EXECUTED, diagnostic)

`experiments/T1_ssm_vs_gru_timing.py`, idle machine, MPS, batch 4, 37 nodes, d=64, two layers,
forward pass only:

| sequence length T | GRU | state-space block | ratio |
|:---:|:---:|:---:|:---:|
| 60 | 14.0 ms | 29.0 ms | 2.07 |
| 240 | 53.3 ms | 115.7 ms | 2.17 |
| 960 | 233.7 ms | 462.3 ms | 1.98 |

The block evaluates its recurrence in a Python loop over time, so it is sequential. It is about twice
as slow as the GRU at every length, and both grow linearly in T. Earlier documents described it as a
"parallel scan" and "parallel in time"; that was incorrect. Only the step size is input-dependent;
B and C are fixed parameters, so it is a partial version of Mamba's selection mechanism. A parallel
prefix scan is a planned work package (WP2) with an explicit acceptance test.

## Defects found and fixed in existing code

| Defect | Evidence | Fix |
|---|---|---|
| The neighbour cache key was built from `coords.sum()` and `coords.std()`, so two different sensor layouts with equal sum and spread (for example two nodes swapped) shared a key and the second layout silently received the first layout's neighbours | reproduced in a test | key is now a hash of the exact coordinate bytes plus shape, dtype, k and device |
| The cache grew without bound | code inspection | least-recently-used eviction, default 8 topologies |
| The docstring said "no per-item Python loop", but self-removal looped over nodes | code inspection | self-removal vectorised with a stable argsort; checked against brute force, including duplicate locations |
| The docstrings called the state-space scan parallel and the equivalence "proven" | T1 and V2 | docstrings corrected |
| Parity gate could not fail | arithmetic above | V1b |

None of these changed the committed V1 or V2 numbers: the cache layouts in those runs differed in
size, and each seed built a new model. Regression tests are in `tests/test_review_fixes.py`.

## Engineering note kept from the first version

The first full V1 run was very slow because the neighbour attention rebuilt the k-d tree on every
forward pass. Caching neighbour indices per coordinate set removes that cost, because the neighbour
graph depends only on coordinates, which are fixed within a run. The cache now has a correct key and
a size bound (see above).

## What remains

See [`RESEARCH-PLAN.md`](RESEARCH-PLAN.md): V1b with 10 seeds, localised calibration, a parallel scan,
memory and time against N, coverage on a larger real network, stronger baselines, and a PyTorch
package. Each work package has an acceptance criterion and a fallback fixed in advance.

## Reproduce

```bash
python experiments/V2_attention_equivalence.py     # no training
python experiments/T1_ssm_vs_gru_timing.py         # timing diagnostic, run on an idle machine
python experiments/V1b_parity_equivalence.py quick # smoke test only; full run is a Semester 4 task
pytest -q
```

*External-source content rephrased for licensing compliance. Related-work positioning rests on
abstracts read in November 2026 and must be re-checked before submission.*
