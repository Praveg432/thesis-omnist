# Progression Decision Brief (15 Nov 2026)

> **Superseded on 16 Nov 2026 by [`THESIS-COMPLETION-PLAN.md`](THESIS-COMPLETION-PLAN.md)**, which adds
> station-level (hierarchical) conformal, the new-sensor warm-up question, the contemporaneous-calibration
> issue in C1, and new prior art (sequential whitening). Options A and B below are folded into it.

One page to decide what Phase 2 does next. Evidence: `phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`
(new), `FINALIZATION-RECORD.md` (Phase 1 and earlier Phase 2), `LEARNINGS-AND-RETIRED-DIRECTIONS.md`.

## Where things stand

| Area | State | Strength of evidence |
|---|---|---|
| Phase 1 (OmniST) | Complete, preprinted, C1 re-evaluated on five datasets (0.876 to 0.906) | Strong; preprint overstates relative to C1 |
| Neighbour attention | Equivalent output; memory win from N about 4,000 (7.2x), 16.7x at 8,000; training 2.6x | Solid for cost; equivalence only on random tokens |
| State-space block | Slower than GRU in every configuration tried; X2 dropped | Settled (negative) |
| Coverage at scale | Holds on real PeMS-BAY (0.92) and synthetic to N=2,000; N=4,000 at the band edge | Real evidence stops at 325 sensors |
| Usefulness of intervals | Beats persistence; **loses to seasonal-naive by about 21% in width** on real traffic | A genuine weakness |
| Geometry-aware calibration (WP1) | Not started; dense networks show no distance problem to fix (C2, V3) | Its case rests on the 30-station weather result and a not-yet-built sparse network |

## The two facts that matter most for the decision

1. **The intervals are wider than a trivial seasonal baseline on real traffic.** Any thesis chapter
   that calls the intervals useful must first fix or explain this. It also affects Phase 1's story.
2. **WP1's target effect has been seen in one 30-station network only.** Before building the
   geometry-aware method, the distance effect must replicate on a larger sparse network (WP0).

## Options

| Option | Next 2 to 4 weeks | Risk | What the thesis claims if it works |
|---|---|---|---|
| **A. Follow the plan, gate first** (recommended) | WP0: build the GHCN sparse network (300 to 1,500 stations), run V1b, add the local coordinate frame. Then run C2 on the sparse network. Add a seasonal-naive baseline to C1. | Medium. WP1 may lose its premise if the distance effect does not replicate | Geometry-aware calibration where distance matters, scale evidence to about 1,000 real stations, honest usefulness comparison |
| B. Re-centre Phase 2 on usefulness | Diagnose why intervals lose to seasonal-naive (error tail by station, horizon, time of day); try a seasonal-residual model or conformalised quantile regression | Medium | Calibrated intervals that beat strong simple baselines at unseen sensors |
| C. Scale-only thesis | WP3 to completion: published efficient-model comparison, OOM point, LargeST compute scaling | Low | Engineering study; low novelty |
| D. Switch to SafeTTA | See `../thesis/`; independent G6 check found label-free adaptation helps only below about 100 labels | Medium | Different thesis; Phase 1 becomes background |

A and B can run together: the GHCN data work and the seasonal-naive diagnosis do not compete for
the same compute.

## Kill-gates to fix before running (proposed; tighten only, never loosen)

- **G-A1 (WP0).** On the GHCN sparse network, over at least 20 region splits, coverage in the far
  distance tercile is at least 0.03 below the near tercile (as in the 30-station weather data).
  If not, WP1 drops to its fallback (characterisation).
- **G-B1.** After the diagnosis, the best variant's interval width on real PeMS-BAY is at most that of
  seasonal-naive at equal deployable coverage. If not, the thesis states the limitation and does not
  claim usefulness on traffic.

## Decisions only the author or supervisor can make

- Whether to post a revised preprint to match C1.
- Whether the scope in `phase2-omnist-scale/docs/RESEARCH-PLAN.md` is approved, and whether Option B
  is added to it.
- OmniST-Scale versus SafeTTA (scored a statistical tie in `../mtech-thesis-vetting/`).
