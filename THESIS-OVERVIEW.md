# Thesis Overview — Narrative, Status, and Timeline

A single read-through of the whole thesis: what it argues, what is already done, what is pending, and
how the two phases fit the thesis timeline. For the formal proposal see
[`MTECH-THESIS-PROPOSAL.md`](MTECH-THESIS-PROPOSAL.md); for the claim→evidence map see
[`EXPERIMENTS-INDEX.md`](EXPERIMENTS-INDEX.md).

---

## 1. The one argument

A forecasting system for real sensor networks is only useful if it keeps working when sensors come
and go, and if every forecast carries an uncertainty a decision-maker can trust. This thesis builds
such a system (Phase 1, OmniST) and then makes it run at the scale real networks actually have
(Phase 2, OmniST-Scale) without giving up the trust guarantee.

The through-line is a single property — a **distribution-free coverage guarantee at unseen sensor
locations, preserved under topology change** — carried from a few-hundred-sensor validation (Phase 1)
to the thousands-of-sensors regime (Phase 2).

---

## 2. Status at a glance

| | Phase 1 — OmniST | Phase 2 — OmniST-Scale |
|---|---|---|
| Design | **Done** | **Done** (fast attention, SSM block, scalable conformal implemented) |
| Validation on real data | **Done** — 4 datasets, 3 domains, up to 325 real sensors | **Partial** — V1 parity + V2 equivalence passed on real Delhi |
| Pending | — | V3 coverage-at-scale, V4 SSM crossover, full multi-seed eval, demo |
| Artifact | preprint arXiv:2611.04256 + full code/experiments/paper | code + two executed vetting gates |

---

## 3. Phase 1 — OmniST: what is done

Everything in `phase1-omnist/` is executed and committed. The headline, drawn from committed result
JSONs (see `phase1-omnist/RESULTS-INDEX.md`):

- **Guaranteed inductive coverage** at unseen sensors on 4 real datasets / 3 domains (Delhi 0.914,
  Beijing 0.928, weather 0.919, PeMSD7-M traffic 0.915; target 0.90), holding under 30–50% dropout.
- **Only method among four model-free interpolators** to hold target on all four datasets.
- **Beats learned IGNNK kriging** at unseen nodes (~21% MAE on Delhi), tighter/better-calibrated.
- **Controlled E-STGCN head-to-head** (identical conditions): comparable transductive accuracy; the
  fixed-topology baseline structurally cannot predict at unseen nodes and crashes under dropout —
  demonstrated, not asserted.
- **Temporal drift solved** with rolling-ACI (0.89/0.96 vs static 0.50), honest width cost.
- **Scale to 325 real sensors** (PeMS-BAY) via a scalable k-NN attention numerically equivalent to
  exact (cosine 0.99996).
- **Verified Proposition** (locality ⇒ recalibration-free coverage); **Mondrian** conditional
  conformal narrows (not eliminates) the per-node spread on the hard traffic network.

Honest Phase-1 limits (and the reason Phase 2 exists): exact attention is O(N²); temporal is a
sequential GRU; coverage is certified only to 325 real sensors; the guarantee is marginal with a
partial Mondrian fix.

---

## 4. Phase 2 — OmniST-Scale: done vs pending

### Done (executed, in `phase2-omnist-scale/`)

- **V1 — parity make-or-break (GO).** On real Delhi, 3 seeds: the scalable `ssm+fast` model matches
  the `gru+exact` OmniST baseline — MAE 65.62 vs 64.56 (within 2%), coverage 0.944 vs 0.948 (in the
  finite-sample band). `gru+fast` is identical to `gru+exact`; the SSM preserves the guarantee.
- **V2 — fast-attention equivalence (GO).** O(N·k) attention vs exact (shared weights, only neighbour
  selection differs): min cosine 0.99987 ≥ 0.999 across N up to 2000; exact's tiny-N advantage gone
  by N≈325.
- **Engineering finding (kept):** caching neighbour indices per coordinate set makes the fast path
  fast in *training*, not just inference (the k-NN graph is static within a run).

### Pending (the remaining thesis work)

- **V3 — coverage at scale.** Inductive coverage stays in band as N grows (37 → hundreds → thousands
  via real + realistic replication); scalable conditional conformal. *Main residual risk lives here —
  it is a data-access gate, mitigated with the explicit "replication cannot certify" caveat.*
- **V4 — SSM earns its keep (MambaOut-analog).** Throughput/memory curves SSM vs GRU and fast vs exact
  as N and T grow; identify the crossover, or scope the SSM claim to long-T.
- **Full real-data eval** (Delhi + traffic + weather), multi-seed + CIs, throughput/memory curves.
- **Large-N demo** + scalable conditional-conformal result + ablations.

---

## 5. Timeline mapping

- **Phase 1 (prior months of the thesis):** OmniST designed, validated cross-domain, drift fix,
  scaled to 325 real sensors, written up, preprinted. **Complete.**
- **M1–M2 (now):** Phase-2 make-or-break gates. **V1 + V2 done → GO.** V4 throughput next.
- **M3–M4:** coverage-at-scale ladder + scalable conditional conformal; full real-data eval.
- **M5–M6:** large-N demo, ablations, write-up, final preemption scan, submit.

Every pending gate has a pre-committed fail-branch (see the proposal §5/§6): a failed gate is reported
as a finding, not threshold-shopped, and the engine + equivalence bound stand regardless.

---

## 6. Honesty ledger (carried from both projects)

- Preprint ≠ publication: OmniST is a timestamped record of Phase-1 thesis work, not external prior
  art, and not yet submitted anywhere.
- Point accuracy is *matched, not beaten* — the contribution is the capability (certified UQ under
  dynamic topology) and its scaling, not a point-accuracy SOTA.
- Coverage is marginal, not conditional; the scalable conditional-conformal front improves it.
- Large-N *real* coverage certification is a data gate; replication is used honestly and cannot
  certify.
- Baselines (E-STGCN, IGNNK) are faithful reimplementations, stated as such.
