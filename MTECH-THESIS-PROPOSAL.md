# M.Tech Thesis Proposal

## Certified Topology-Invariant Spatiotemporal Forecasting with Trustworthy Uncertainty at Unseen Sensors, and Its Scaling to Large Networks

**Candidate:** Praveg Vashishtha
**Program:** M.Tech, Computer Science and Engineering, IIT Patna
**Hardware envelope:** Apple M4 Pro (MPS, ~24 GB unified memory), single machine — no cluster

> **One-sentence thesis.** Design a spatiotemporal forecaster that carries a distribution-free
> coverage guarantee at unseen sensor locations and keeps it as the network changes (Phase 1), then
> re-engineer its engine to be sub-quadratic in nodes and parallel in time and certify that the
> guarantee survives scaling toward thousands of sensors (Phase 2).

---

## 0. Scope and status of the two phases (read first)

This thesis is delivered in two phases, both of which are thesis work.

- **Phase 1 — OmniST.** Designed and validated a topology-invariant forecaster with a certified
  inductive coverage guarantee at unseen sensors. **Status: built and validated** on four real
  datasets across three physical domains; released as a **preprint (arXiv:2611.04256)**. The preprint
  has **not been submitted to any venue for publication** — it is a timestamped record of thesis work,
  not external prior art. Building and validating OmniST is the thesis's first contribution.

- **Phase 2 — OmniST-Scale.** Re-engineers OmniST's engine to reach the thousands-of-sensors regime
  while preserving the guarantee exactly. **Status: the two load-bearing vetting gates (V1 parity, V2
  equivalence) are executed and passed on real data;** the coverage-at-scale gate (V3) and the
  state-space crossover gate (V4) are pending.

The two phases share one research identity: *a forecaster that is trustable (certified coverage),
resilient (topology-invariant), and now scalable.* Phase 2 depends on Phase 1 and treats OmniST's
exact-O(N²) attention and sequential GRU as the baselines to beat.

---

## 1. The problem

Cities and states depend on large sensor networks — air quality, traffic, weather, power — to
forecast conditions and act on them. Two properties decide whether such a system is deployable.

1. **The network is not fixed.** Sensors fail, go offline, or are newly installed. The model must
   keep forecasting, including at locations with no sensor history, without retraining each time the
   topology changes.
2. **A point forecast is not enough.** A public-health advisory or a traffic action needs a *trustable*
   interval — one guaranteed to contain the true value with a stated probability. A confident-but-wrong
   forecast is worse than none.

No off-the-shelf forecaster provides both at once, at the scale real networks operate.

---

## 2. Phase 1 — OmniST (built, validated, preprinted)

OmniST is the thesis's first contribution. It achieves both properties together through three design
choices with no structural dependence on the sensor count `N`:

- **Coordinate tokenization** — each sensor is embedded from its geographic coordinates, with no
  positional index or global node count.
- **k-NN spatial attention** — neighbours are selected from coordinates at every forward pass, so the
  graph adapts to whatever sensors are present (no precomputed N×N adjacency).
- **Per-node temporal processing** — a bidirectional GRU runs independently per node; adding/removing
  a node changes no other node's representation.

Composed with inductive split-conformal calibration, this yields a **distribution-free coverage
guarantee at sensor coordinates never seen in training**, preserved as sensors are added or removed.
A locality Proposition formalizes the consequence: each node's nonconformity score is exactly
invariant to nodes outside its k-NN set, so the guarantee is recalibration-free under far topology
changes (verified: far-change prediction difference 8.9×10⁻⁸).

**What Phase 1 established (all from committed result files):**

- **Cross-domain coverage** on four real datasets / three domains: Delhi air quality 0.914, Beijing
  0.928, NOAA weather 0.919, PeMSD7-M traffic 0.915 (target 0.90), holding under 30–50% node dropout;
  the only method among four model-free interpolators to hold target on all four.
- **Beats a learned inductive-kriging baseline (IGNNK)** at unseen nodes (~21% MAE on Delhi) with
  tighter, better-calibrated intervals.
- **Temporal-drift coverage restored** by a rolling-ACI online layer (0.89 overall / 0.96 worst-drift
  window vs 0.50 static), at an honest width cost.
- **Certified to 325 real sensors** (PeMS-BAY), with a scalable k-NN attention numerically equivalent
  to exact (cosine 0.99996).

**The limits Phase 1 itself states — which define Phase 2:**

1. Spatial attention is **O(N²)** in memory on the exact path; cost-scaling is measured super-linear.
2. The temporal backbone is a **sequential GRU** — O(T), not parallelizable over time.
3. Coverage is **certified only to 325 real sensors**; conditional coverage is only partially fixed
   (Mondrian; traffic worst-group ≈0.86).

---

## 3. Phase 2 — OmniST-Scale (the scaling contribution)

The thousands-of-sensors regime (city-scale air quality, national traffic grids) is exactly where a
trustable, resilient forecaster is most valuable — and exactly where the Phase-1 engine cannot go.

> **Research question.** Can we keep OmniST's finite-sample inductive coverage guarantee *exactly*
> while making the forecaster sub-quadratic in nodes and parallel in time, and certify that the
> guarantee still holds as the network scales to thousands of nodes?

The novelty is **certified coverage *at scale*** — not raw speed (scalable ST-GNNs exist) and not a
new backbone (SSMs exist). It is the combination.

### 3.1 The three fronts (the Phase-2 contributions)

1. **O(N·k) spatial attention with a measured equivalence bound** (`fast_attention.FastInductiveGAT`).
   Vectorized cKDTree neighbour selection + O(N·k) gather; no (B,N,N) tensor, no per-item loop. A
   neighbour-index cache (built once per static coordinate set) makes the path fast in training, not
   just inference.
2. **Selective state-space (Mamba-style) temporal block** (`ssm_temporal.BidirectionalSSM`).
   Linear-time, parallel-scan, constant per-step state — a drop-in for the GRU, with an honest
   ablation of where the SSM earns its keep (long T / large N).
3. **Coverage preserved at scale** (`conformal.py`). Show the finite-sample inductive coverage holds
   as N grows, and tighten conditional coverage with a scalable conditional-conformal scheme
   generalizing OmniST's partial Mondrian fix. This is the novel core; speed alone is not novel.

### 3.2 Hypotheses and vetting gates (two executed, two pending)

- **H1 (parity — make-or-break). EXECUTED → GO.** SSM + O(N·k) attention match OmniST accuracy and
  inductive coverage on real Delhi.

  | variant | inductive MAE | inductive coverage |
  |---|:---:|:---:|
  | gru+exact (OmniST baseline) | 64.56 | 0.948 |
  | ssm+exact | 65.82 | 0.944 |
  | gru+fast | 64.56 | 0.948 |
  | **ssm+fast (scalable)** | **65.62** | **0.944** |

  Band [0.753, 0.998]. Scalable model matches baseline (MAE within 2%, coverage in band).

- **H2 (equivalence). EXECUTED → GO.** O(N·k) attention matches exact: min cosine **0.99987 ≥ 0.999**
  across N ∈ {37, 100, 325, 1000, 2000}; exact's tiny-N advantage vanishes by N≈325.

- **H3 (coverage at scale). PENDING.** Inductive coverage stays in the finite-sample band as N grows
  (37 real → hundreds → thousands via real + realistic replication); scalable conditional conformal.

- **H4 (SSM earns its keep — MambaOut-analog kill-gate). PENDING.** SSM beats GRU on
  throughput/memory at long T / large N; identify the crossover, or scope the SSM claim honestly.

---

## 4. Impact

- Extends a proven, trustable capability (certified inductive UQ under dynamic topology) from 325
  sensors to the city/national scale where it is actually needed.
- Delivers a reusable artifact — a scalable, certified forecaster matching OmniST's accuracy/coverage
  at a fraction of the compute, with throughput/memory curves to thousands of nodes on commodity (M4
  Pro) hardware.
- Tightens the one trustworthy-ML weakness (conditional coverage) via scalable conditional conformal.

---

## 5. Timeline (two semesters, monthly gates)

| Phase | Work | Gate | Status / fail-branch |
|---|---|---|---|
| Ph1 | **Design + validate OmniST** (4 real datasets, drift fix, large-N to 325, paper) | capability validated | **DONE — preprint arXiv:2611.04256** |
| M1 | **V1 parity** (ssm+fast vs gru+exact, real Delhi) | parity holds | **DONE → GO** |
| M2 | **V2 equivalence**; **V4** SSM-vs-GRU throughput/crossover | equivalence tight; SSM earns keep | **V2 DONE → GO**; V4 pending |
| M3 | **V3 coverage-at-scale** ladder; scalable conditional conformal | coverage in band at scale | report to largest real N; scope rest as data gate |
| M4 | Full real-data eval; throughput/memory curves; multi-seed + CIs | matches OmniST at lower cost | report honest cost/coverage envelope |
| M5 | Large-N demo + conditional-conformal result; ablations | demo runs; ablation clean | demo on largest tractable real N |
| M6 | Write-up; fresh preemption scan | thesis submitted | engine + equivalence bound stand regardless |

---

## 6. Risks and honest limits

- **Main residual risk is data, not mechanism.** Certifying coverage at *thousands of real* nodes
  needs a real dataset that size; PEMS-07/08 are LFS-gated / unfetchable in this environment.
  Mitigation: scaling ladder uses real-where-available (up to 325 real PeMS-BAY) + realistic
  replication, with the explicit caveat that *replication cannot certify coverage* (naive duplication
  breaks exchangeability — shown as an honest negative).
- **MambaOut analog:** a gated-conv/GRU may match the SSM at these T/N. V4 is the explicit kill-gate;
  if so, scope the SSM to long-T and report the crossover.
- **Guarantee is marginal, not conditional** (inherited from Phase 1); scalable conditional conformal
  improves but does not perfect it.
- **Fast-moving area.** Re-scan scalable ST-GNN + SSM forecasting at project start and before
  submission.

---

## 7. Expected contributions

1. **OmniST** — a topology-invariant forecaster with a certified inductive coverage guarantee at
   unseen sensors, validated cross-domain on real data (Phase 1).
2. A **sub-quadratic (O(N·k)) spatial attention** with a measured equivalence bound to exact (Phase 2).
3. An **SSM temporal backbone** for topology-invariant forecasting, with an honest GRU-crossover
   analysis (Phase 2).
4. **Certified inductive conformal coverage at scale** + a scalable conditional-conformal tightening
   (Phase 2).
5. A **scalable, certified forecaster** matching OmniST accuracy/coverage at a fraction of the
   compute, on commodity hardware — delivered as a reusable artifact (Phase 2).

---

### Appendix — provenance

- **Phase 1:** `phase1-omnist/` (`README.md`, `FINDINGS-AND-IMPACT.md`, `RESULTS-INDEX.md`, committed
  `results/*.json`, `paper/`); preprint arXiv:2611.04256.
- **Phase 2:** `phase2-omnist-scale/` (`README.md`, `docs/RESEARCH-PLAN.md`, `docs/VETTING-REPORT.md`,
  `experiments/V1_ssm_matches_omnist.py`, `experiments/V2_attention_equivalence.py`,
  `results/V1_ssm_matches_omnist_results.json`, `results/V2_attention_equivalence_results.json`).
- **Claim → evidence map:** `EXPERIMENTS-INDEX.md`.

*External-source content was rephrased for compliance with licensing restrictions. Novelty verdicts
rest on abstracts/snippets as of November 2026 and must be re-scanned before submission.*
