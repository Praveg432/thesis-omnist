# Thesis Overview: Narrative, Status, and Timeline

A single read-through of the whole thesis: what it argues, what is done, what is planned, and how the
two phases fit the thesis timeline. The formal proposal is
[`MTECH-THESIS-PROPOSAL.md`](MTECH-THESIS-PROPOSAL.md). The claim-to-evidence map is
[`EXPERIMENTS-INDEX.md`](EXPERIMENTS-INDEX.md).

---

## 1. The argument

A forecasting system for real sensor networks is useful only if it keeps working when sensors come
and go, and if every forecast carries an uncertainty a decision-maker can use. Phase 1 builds such a
system (OmniST). Phase 2 makes it run at the scale real networks have, and studies how its coverage
behaves as the network grows.

The through-line is one property: **conformal prediction intervals at unseen sensor locations, with
coverage close to a stated target**. "Certified" in the title means finite-sample marginal coverage
under a random, disjoint split of stations into train, calibration and test sets; it is checked
empirically over many random splits and is not a guarantee for every station.

---

## 2. Status at a glance

| | Phase 1: OmniST | Phase 2: OmniST-Scale |
|---|---|---|
| Design | Done | Neighbour attention and a sequential state-space block exist. Localised calibration is not implemented. |
| Validation on real data | Done on four datasets. Re-evaluated over random disjoint-station splits (C1). | Attention output equals exact attention on random inputs (V2). A preliminary parity check (V1) is superseded by V1b, not yet run. |
| Pending | Re-test of the baseline comparisons and dropout robustness under C1 | WP0 to WP7 of the revised plan |
| Artifact | Preprint arXiv:2611.04256, code, experiments, results | Code, plan with acceptance criteria |

---

## 3. Phase 1: what is done

Everything in `phase1-omnist/` is executed and committed. After the preliminary review the headline
evidence is experiment C1 (random disjoint-station splits). Results in the proposal, Section 2.1.

- Mean coverage over random splits, target 0.90: Delhi 0.893, Beijing 0.903, weather 0.906,
  PeMSD7-M 0.876, PeMS-BAY 0.892. Every 95% interval over splits contains 0.90.
- Per-split standard deviation 0.02 to 0.05. Individual stations can be well below target (minimum
  per-station coverage 0.40 to 0.86).
- The original-protocol numbers (0.914 to 0.928) are kept as a record. They came from fixed sets of 3
  to 5 held-out stations and were 1 to 2.5 points higher.
- Original-protocol results not re-tested under C1: comparison with simple interpolators, the learned
  kriging baseline (the author's re-implementation), dropout robustness, drift handling, and the
  7-sensor large-network run.

Limits that define Phase 2: O(N²) exact attention, a sequential GRU, coverage checked only to 325
sensors with reconstructed coordinates for the traffic data, and marginal rather than per-station
coverage.

---

## 4. Phase 2: done, found, planned

### Done and found

- **Neighbour attention (V2).** Output cosine similarity to exact attention at least 0.99987 for N up
  to 2,000, on random tokens. No memory was measured and no speed advantage appeared.
- **State-space block (T1).** Sequential, about 2.0 to 2.2 times slower than the GRU at T = 60, 240
  and 960. The earlier "parallel in time" description was incorrect.
- **First parity check (V1).** Preliminary: its gate accepted any coverage above 0.723 and tolerated
  10% error with 3 seeds.
- **Code fixes after review.** A neighbour-cache key collision and unbounded cache were fixed, with
  regression tests; misleading docstrings were corrected.

### Planned (Semester 4)

WP0 to WP7 in `phase2-omnist-scale/docs/RESEARCH-PLAN.md`: V1b parity gate with paired equivalence
over 10 seeds, localised calibration compared with two published conformal methods, a parallel scan
for the state-space block, memory and time against N, coverage on a larger real network if usable,
stronger baselines, a PyTorch package, and the thesis. Acceptance criteria and fallbacks are fixed in
advance.

---

## 5. Timeline

- **Semester 3 (complete):** Phase 1 designed, validated, preprinted; stricter C1 re-evaluation;
  review corrections; revised Phase 2 plan.
- **Semester 4, months 1 to 6:** WP0 to WP7, ending with the thesis write-up. Every work package has a
  pre-committed fallback, so a negative result is reported as a finding and does not stop the thesis.

---

## 6. Honesty ledger

- A preprint is not a publication. OmniST is a timestamped record of Phase 1 work and has not been
  submitted anywhere.
- Point accuracy is matched, not beaten, against the baselines tried; the contribution is the
  capability and its evaluation.
- Coverage is marginal. Per-station coverage varies widely.
- The traffic datasets use coordinates reconstructed from distance matrices.
- E-STGCN and IGNNK are the author's re-implementations.
- Evidence on large networks is limited to 325 sensors so far.
