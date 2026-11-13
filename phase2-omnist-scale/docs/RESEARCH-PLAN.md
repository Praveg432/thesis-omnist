# Research Plan — OmniST-Scale

*Scalable, certified topology-invariant spatiotemporal forecasting. Keeps OmniST's distribution-free
inductive coverage guarantee; re-engineers the engine to run sub-quadratically in nodes and in
parallel over time, and certifies coverage at scale.*

**Candidate:** Praveg Vashishtha · IIT Patna, CSE · **Hardware:** Apple M4 Pro (MPS, ~24 GB)

---

## 1. Lineage (honest)

Direct successor to the author's published **OmniST** (arXiv:2611.04256), reusing its backbone as the
baseline. Supersedes the retired `../adaptive-st-conformal/` fusion (NO-GO on real data — see its
`ARCHIVED-LEARNINGS.md`). The retired effort's key carried lesson: *validate any claim against a
deployable-strength backbone early*; this project's make-or-break (V1) does exactly that.

## 2. Problem

OmniST gives a distribution-free coverage guarantee at unseen sensor locations, preserved under
topology change — a genuinely useful, validated capability. But its engine does not scale, and its
own limitations section says so:

- **Spatial attention is O(N²)** in memory (exact); the "scalable" path is a per-batch Python loop.
- **Temporal backbone is a sequential GRU** — O(T), not parallelizable over time; the throughput
  bottleneck at long horizons (the project is even *named* for an SSM it never contained).
- **Coverage is certified only to 325 real sensors**, and conditional coverage is only partially
  fixed (Mondrian; traffic worst-group ≈0.86).

The thousands-of-sensors regime (city-scale air quality, national traffic grids) is exactly where a
*trustable, resilient* forecaster is most valuable — and exactly where OmniST cannot currently go.

**Research question.** Can we keep OmniST's finite-sample inductive coverage guarantee *exactly* while
making the forecaster sub-quadratic in nodes and parallel in time, and certify that the coverage
guarantee still holds as the network scales to thousands of nodes?

## 3. The three optimization fronts (the contributions)

1. **O(N·k) spatial attention with a proven equivalence bound** (`fast_attention.FastInductiveGAT`).
   Vectorized cKDTree neighbour selection + O(N·k) gather; no (B,N,N) tensor, no per-item Python loop.
   Contribution = the vectorized sub-quadratic realization + a stated/measured equivalence bound to
   exact attention (cosine similarity + coverage parity), benchmarked to thousands of nodes on M4 Pro.
2. **Selective state-space (Mamba-style) temporal block** (`ssm_temporal.BidirectionalSSM`). Linear-
   time, parallel-scan, constant per-step state — a drop-in for the GRU. Contribution = the
   integration + the ablation of *where the SSM earns its keep* (long T / large N), honestly bounded
   by the MambaOut-analog kill-gate (V4).
3. **Coverage preserved at scale** (`conformal.py`). The part that makes it trustworthy-ML, not just
   systems: show the finite-sample inductive conformal coverage holds as N grows, and tighten
   conditional coverage with a scalable conditional-conformal scheme (generalizing OmniST's partial
   Mondrian fix). This is the novel core; speed alone is not novel.

## 4. Hypotheses → vetting (each kill-gated)

- **H1 (parity — the make-or-break).** The SSM temporal block + O(N·k) attention **match OmniST's
  accuracy *and* inductive coverage** on real Delhi. *If the scalable components lose accuracy or
  break coverage, the scale-up is moot — STOP.* → **V1.**
- **H2 (equivalence).** O(N·k) attention output matches exact attention within numerical noise
  (cosine ≥ 0.999) and gives identical coverage. → **V2.**
- **H3 (coverage at scale).** Inductive coverage stays in the finite-sample band as N grows
  (scaling ladder: 37 real → hundreds → thousands via real + realistic replication). → **V3.**
- **H4 (SSM earns its keep — the MambaOut-analog kill-gate).** The SSM beats the GRU on
  throughput/memory at long T / large N, and at least matches accuracy; identify the crossover. *If a
  gated-conv/GRU matches the SSM everywhere at these scales, scope the SSM claim to the long-T regime
  and report the crossover honestly.* → **V4.**

## 5. Timeline (two semesters, monthly gates)

| Phase | Work | Gate |
|-------|------|------|
| M1 | **V1 parity (make-or-break)** on real Delhi: ssm+fast vs gru+exact (accuracy + coverage) | parity holds |
| M2 | **V2 equivalence** bound of fast attention; **V4** SSM-vs-GRU throughput/memory + crossover | equivalence tight; SSM earns its keep (or scoped) |
| M3 | **V3 coverage-at-scale** ladder (37 → hundreds → thousands); scalable conditional conformal | coverage in band at scale |
| M4 | Full real-data eval (Delhi + traffic + weather); throughput/memory curves; multi-seed + CIs | scalable model matches OmniST accuracy/coverage at lower cost |
| M5 | Large-N demo + (stretch) a coverage-at-scale statement; ablations (which component earns what) | demo runs; ablation clean |
| M6 | Write-up; fresh preemption scan (scalable ST-GNN + SSM-forecasting move fast) | paper submitted |

## 6. Novelty boundary (honest)

- **Not novel (cite):** scalable/linear attention and SSM forecasting both exist; OmniST's
  topology-invariant inductive coverage is the author's own published result.
- **The defended residual:** a topology-invariant forecaster that **preserves a distribution-free
  inductive coverage guarantee while scaling sub-quadratically to thousands of nodes** — the
  *certified-coverage-at-scale* combination, with the equivalence bound and the conditional-conformal
  tightening. Lead with coverage-at-scale, not raw speed.
- **Framing:** systems + trustworthy-ML contribution; **not** a point-accuracy SOTA or a new SSM.

## 7. Risks / honest limits

- **MambaOut analog (real risk):** a gated-conv/GRU may match the SSM at these T/N. V4 is the explicit
  kill-gate; if so, scope the SSM to long-T and report the crossover rather than overclaim.
- **Coverage-at-thousands-of-REAL-nodes needs a real dataset that size** (OmniST's data gate). PEMS-07/08
  exist but are LFS-gated; the scaling ladder uses real-where-available + realistic replication, with
  the honest caveat that replication cannot *certify* coverage (OmniST documented this).
- **Parity is the make-or-break:** if the scalable components can't match OmniST's accuracy/coverage
  (V1), the thesis stops — this is checked first, cheaply.
- **Fast-moving area:** re-scan at project start and before submission.

## 8. Expected contributions

1. A **sub-quadratic (O(N·k)) spatial attention** for inductive ST-GNNs with a measured equivalence
   bound to exact attention.
2. An **SSM temporal backbone** for topology-invariant forecasting, with an honest crossover analysis
   vs the GRU (the MambaOut-analog finding either way).
3. **Certified inductive conformal coverage at scale** + a scalable conditional-conformal tightening.
4. A **scalable, certified forecaster** that matches OmniST's accuracy/coverage at a fraction of the
   compute, with throughput/memory curves to thousands of nodes on commodity (M4 Pro) hardware.
