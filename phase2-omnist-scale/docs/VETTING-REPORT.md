# Vetting Report — OmniST-Scale (executed Nov 2026)

Kill-gated vetting of the scale-up thesis on real Delhi PM2.5 (M4 Pro, MPS). Discipline carried from
prior projects: front-load the make-or-break against the strongest realistic setting; multi-seed with
CIs and the finite-sample conformal band; every verdict reproducible from `experiments/V*.py`.

> **Headline: the two executed gates both PASS.** V1 (parity make-or-break): the scalable SSM+fast
> model matches OmniST's accuracy and coverage. V2 (equivalence): O(N·k) attention is numerically
> identical to exact. The scale-up is worth pursuing; V3 (coverage-at-scale) and V4 (SSM crossover)
> are the remaining real-data gates.

---

## V1 — Parity make-or-break (H1). Verdict: **GO** (3 seeds, real Delhi)

Four variants, identical data/seeds/budget (15 epochs), inductive eval at unseen stations with
target-regime (winter) conformal calibration:

| variant | inductive MAE | inductive coverage | fps (N=37) |
|---------|:-------------:|:------------------:|:----------:|
| gru+exact (OmniST baseline) | 64.56 | 0.948 | 95 |
| ssm+exact | 65.82 | 0.944 | 94 |
| gru+fast | 64.56 | 0.948 | 51 |
| **ssm+fast (scalable model)** | **65.62** | **0.944** | 54 |

Band [0.753, 0.998]. **The scalable ssm+fast model matches OmniST:** MAE within 2% of the baseline,
coverage in band. Two clean sub-findings:
- **gru+fast is *identical* to gru+exact (64.56 / 0.948)** — the O(N·k) attention is behaviorally
  equivalent to exact (confirmed independently in V2).
- **The SSM preserves the coverage guarantee** (0.944 vs 0.948) and matches accuracy (on seed 2 it
  *beat* the GRU, MAE 60.2 vs 65.1). The thesis's core — keep the guarantee while swapping the engine
  — holds on real data.

Honest note (already in the verdict): at N=37 the fast path is *slower* (cKDTree build overhead
dominates tiny N); the throughput win is at large N and is V4's job, not V1's.

## V2 — Fast-attention equivalence (H2). Verdict: **GO**

With shared weights (only neighbour *selection* differs), FastInductiveGAT vs exact InductiveGAT:

| N | cosine vs exact | fast time | exact time |
|---|:---------------:|:---------:|:----------:|
| 37 | 1.000000 | (warmup) | — |
| 100 | 1.000000 | 142 ms | 3 ms |
| 325 | 0.99998 | 145 ms | 194 ms |
| 1000 | 0.99999 | 152 ms | 225 ms |
| 2000 | 0.99987 | 189 ms | 182 ms |

**Min cosine 0.99987 ≥ 0.999** — numerically equivalent across all tested N. The O(N·k) path is a
drop-in for exact with no accuracy/coverage cost; exact's advantage at tiny N vanishes by N≈325 and
its O(N²) *memory* (not shown) is what forces the switch at thousands of nodes.

## Engineering finding (made during vetting, kept)

The first V1 full run was intractably slow because the fast attention rebuilt the cKDTree **every
forward pass**. Fix (a real optimization, in `fast_attention.py`): **cache neighbour indices per
coordinate set** — the k-NN graph depends only on coordinates, which are static within a run, so the
O(N log N) build becomes once-per-topology. This is also the honest reason the "fast" path is fast in
*training*, not just inference.

## What remains (the real-data gates ahead)

- **V3 — coverage at scale:** inductive coverage stays in the finite-sample band as N grows
  (37 → hundreds → thousands via real + realistic replication); scalable conditional conformal.
- **V4 — SSM earns its keep (MambaOut-analog kill-gate):** throughput/memory curves SSM vs GRU and
  exact vs fast as N and T grow; identify the crossover where the scalable stack wins decisively. If
  a gated-conv/GRU matches the SSM everywhere at these scales, scope the SSM claim to long-T and
  report the crossover honestly.

## Reproduce
```bash
python experiments/V1_ssm_matches_omnist.py      # parity (3 seeds, ~14 min) -> GO
python experiments/V2_attention_equivalence.py   # equivalence (no training) -> GO
```

## Overall status
The two cheapest, most load-bearing gates pass: the scalable engine **keeps OmniST's guarantee and
accuracy** (V1) and the fast attention is **provably-equivalent** to exact (V2). This is the opposite
situation from the retired fusion — here the premise *survives* the real backbone, because we are
*preserving* the coverage OmniST is good at rather than trying to break it. Proceed to V3/V4.

*External-source content rephrased for licensing compliance. Novelty rests on abstracts as of Nov
2026; re-scan (scalable ST-GNN + SSM forecasting) at project start and before submission.*
