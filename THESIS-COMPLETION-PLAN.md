# Thesis Completion Plan: Phase 2 (authoritative)

Candidate: Praveg Vashishtha (IITP006424) · Supervisor: Pankaj Chaswal · Hardware: Apple M4 Pro, one machine.

**Status.** Rewritten on 26 Nov 2026 around the lifecycle framing, after two pre-registered feasibility rounds
(`phase2-omnist-scale/feasibility/`). Replaces the earlier 26 Nov version. **Pending supervisor approval.** Acceptance
criteria are fixed now and may be tightened, never loosened; each step gets a dated pre-registration before its first
run, as for C1h, C1i and the feasibility rounds. Scale and alert details still come from
`phase2-omnist-scale/docs/RESEARCH-PLAN.md`.

Thesis title (submitted 17 Nov 2026): *Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor
Locations in Evolving Networks.* Semester 4 runs 16 Nov 2026 to 7 Feb 2027; week 3 starts 30 Nov.

---

## 0. Status

| Item | State |
|---|---|
| Phase 1 | Complete; progress report final (`SEM3-PROGRESS-REPORT.md`); verification `FINALIZATION-RECORD.md` Sections 20 and 21 |
| Feasibility of the proposed upgrades | Two pre-registered rounds, `phase2-omnist-scale/feasibility/REPORT.md` and `phase2-omnist-scale/feasibility/REPORT-2.md`; summary below |
| Open outside the repository | Supervisor approval of this scope and the title; the preprint decision; report submission by 30 Nov 2026 |

---

## 1. Framing: calibrated forecasting across a sensor's lifecycle

A sensor added to a running network passes through three stages: no history (Day 0), a short history (warm-up), and
a full history. Phase 2 asks whether one forecasting system can give **valid intervals at every stage, using only
information available at forecast time**, and what each stage costs in accuracy and width.

**What is claimed as new.** The calibrated transition from Day 0 to warm. Forecasting at unseen traffic sensors at
Day 0 is published: IGNNK (AAAI 2021), KITS (AAAI 2025), MoGERNN (Transportation Research Part C, 2025), and a 2026
cold-start meta-graph paper in *Sensors* (26(15):4995; abstract read, full text not). None of those found reports
forecast-time intervals across the transition. The architecture is not claimed as new.

**Wording kept out of the thesis** (refuted or untested): that the spatial branch beats a shared GRU for sensors with
history; that the attention provides the Day-0 gain; that the warm-up has no accuracy cost; that the interval gain
belongs to OmniST; any accuracy claim at 8,000 sensors.

## 2. Evidence the framing rests on (feasibility rounds, 26 Nov 2026)

| Finding | Evidence | Consequence |
|---|---|---|
| Masked-station training gives a Day-0 forecaster better than interpolating a shared GRU's neighbour forecasts, on road networks | 16.2% lower error on PeMS-BAY (10 splits), 10.3% on PeMSD7-M (10 splits); not on Delhi (1.2%, not significant) | Day 0 is a road-network result; Delhi is the negative control |
| The gain comes from masked training with neighbour pooling, not from the attention | A plain mean over neighbours keeps 14.7% and 9.9%; distance-biased attention adds about 2% on PeMS-BAY only | Freeze: masked training + neighbour pooling; attention optional |
| Day-0 intervals are close to valid | Coverage 0.879 and 0.880, interval score below the neighbour baseline on both road networks | Day-0 calibration works with Day-0 calibration stations; about 2 points under target |
| The spatial branch does not help sensors with history | Equal to the shared GRU on Delhi and PeMS-BAY; masked training costs between -2% and +1.3% | No warm-sensor claim; a small warm cost is reported |
| Seasonal residual + scale head fixes traffic intervals, for any backbone | Interval score 37% below seasonal-naive on PeMS-BAY (5 splits); a plain GRU with the same head is equal | Contribution D is a head and calibration result |
| Time of day is not the traffic fix | Adding it to the thesis model changes error by 0.1% and 0.7% | Dropped |
| The thesis traffic loaders train on one clock phase per day on PeMS-BAY | Overlapping training windows: 19% lower error, lower on 3 of 3 splits, interval just reaching zero (exploratory) | First step of Phase 2 |
| The relative-bias layer keeps the memory advantage | 10.4 times less than dense attention at N = 8,000, linear growth | Memory claim only |

---

## 3. Steps, criteria and fallbacks

### S0. Training-window fix (week 3; affects every traffic number)
- **Work.** Pre-registered test of the traffic loaders' training stride (overlapping windows instead of one per day) on
  all 6 C1 splits of PeMS-BAY and PeMSD7-M, through the thesis pipeline.
- **Accept.** PeMS-BAY error lower, paired 95% interval below 0; coverage within 0.02 of 0.90.
- **If accepted.** The fix becomes the default for all Phase 2 traffic runs; the Phase 1 traffic accuracy and width
  figures are re-run and reported next to the originals, which are kept. Phase 1 coverage conclusions are expected to stand.
- **Fallback.** Report the effect size with its interval; keep the original loaders.

### B. The lifecycle curve (headline; weeks 3 to 6)
- **Model.** Masked-station training extended to **partial histories** (each training station's input window truncated
  at random, from none to full), with neighbour pooling; the distance-biased attention as an ablation. All-or-nothing
  masking, as tested so far, does not train a warm-up.
- **Axes.** Model input history in steps up to the window: PeMS-BAY 0 to 24 hours, PeMSD7-M 0 to 4 hours, Delhi 0 to 60
  days. Calibration history in days, 0 to 60: Day-0 calibration on Day-0 calibration stations, then own-data split
  conformal, generalized hierarchical conformal [22] and adaptive conformal inference as the sensor's errors accumulate.
- **Networks.** PeMS-BAY and PeMSD7-M; Delhi as the negative control; at least 20 splits each.
- **Accept.** On the road networks: Day-0 error at least 5% below the shared GRU with neighbour interpolation; at full
  history error at most 1.01 times the shared GRU's; coverage within 0.03 of 0.90 at every point of both axes; width at
  60 days of calibration at least 5% below Day 0.
- **Fallback.** The curves as measured, with the stage at which the system stops being valid or useful.

### D. Useful intervals (weeks 6 to 7)
- **Work.** Seasonal-residual + scale head as a backbone-agnostic forecasting head, with the seasonal value passed as an
  explicit input (PeMSD7-M's daily period of 288 steps exceeds its window). At Day 0 the seasonal value is taken from
  neighbours. PeMS-BAY and PeMSD7-M, 20 splits each, after S0.
- **Accept.** Interval score below both seasonal-naive and persistence under the same forecast-time rule, paired 95%
  interval below 0, coverage within 0.02 of 0.90, on both networks; reported for OmniST and the shared GRU.
- **Fallback.** State where the learned model does not beat a seasonal baseline, with a diagnosis by horizon and time of day.

### A. Per-station coverage (week 7)
- **Work.** Station-level conformal on the scale-head scores, at full history and along the lifecycle curve.
- **Accept.** At most 5% of stations below 0.80 coverage, mean within 0.02 of 0.90, width at most 30% above the pooled
  rule, on every network over at least 20 splits.
- **Fallback.** Width against worst-station coverage, and which networks cannot meet both.

### C. Does position matter? (gated; week 8)
Gate G0 on a 300 to 1,500 station GHCN network with the corrected coordinate frame: farthest tercile at least 0.03 below
the nearest over 20 or more region splits. A geometry-aware method is built only if G0 passes; otherwise a powered
characterisation (expected, since the weather effect did not survive the coordinate correction).

### E. Scale and remaining comparisons (weeks 8 to 9)
Coverage and error against N up to the largest usable real network (GHCN; LargeST for compute only); the Phase 1
comparisons (dropout, drift, 7-sensor run, E-STGCN, IGNNK official code, interpolators) under the forecast-time rules;
the headline results repeated with the shared GRU as backbone. Acceptance as in `phase2-omnist-scale/docs/RESEARCH-PLAN.md` WP3.

### F. Alerts (cut candidate) and G. package and thesis (protected)
F: conformal risk control at one air-quality network. G: installable package reproducing one headline table in a fresh
environment; thesis in the IIT Patna format with at least 30 verified references.

**Dropped:** tuning the distance-biased attention to beat the GRU on warm sensors; the time-of-day input as a fix; the
state-space block; a separate coverage-risk estimate; sensor placement; cross-city transfer; online rule selection as a default.

---

## 4. Schedule (week 3 starts 30 Nov 2026)

| Week | Dates | Work | Exit check |
|---|---|---|---|
| 3 | 30 Nov to 6 Dec | Submit the Semester 3 report. Pre-register S0 and B. Run S0. Implement partial-history masking | S0 verdict; B pre-registered |
| 4 | 7 to 13 Dec | B: model-history axis on PeMS-BAY and PeMSD7-M | Day-0 to full-history curves |
| 5 | 14 to 20 Dec | B: calibration-history axis; Delhi control. Preprint decision | B accepted or fallback |
| 6 | 21 to 27 Dec | D pre-registered and run. Start chapters 1 to 3 | D first results |
| 7 | 28 Dec to 3 Jan | D confirmation; A on the scale-head scores | D and A accepted or fallback |
| 8 | 4 to 10 Jan | GHCN network; gate G0 (C); coverage against N (E) | G0 recorded |
| 9 | 11 to 17 Jan | E comparisons; LargeST compute; F if on schedule | E accepted; F decision |
| 10 | 18 to 24 Jan | Reproducibility pass in a fresh environment; chapters 4 to 6 | Headline table reproduces |
| 11 | 25 to 31 Jan | Chapters 7 to 9; supervisor review | Draft complete |
| 12 | 1 to 7 Feb | Revisions, formatting, slides | Submission-ready 7 Feb 2027 |

**Cut order:** F, then LargeST compute, then E breadth, then C's method. S0, B, D, A and the writing are protected.

## 5. Risks

- **Partial-history masking may not train a smooth warm-up.** The fallback reports the measured curve; the Day-0 result
  stands on its own.
- **Day-0 coverage is about 2 points under target.** If it stays there, the thesis reports it and tests station-level
  or adaptive calibration as the repair.
- **Air quality.** No Day-0 advantage was found on Delhi; the lifecycle claim is scoped to road networks unless a
  second air-quality network changes that.
- **Traffic samples.** Traffic series cover weeks to months; rules that use earlier years do not apply there.
- **Width.** Every repair costs width; reported as a trade-off.
- **Prior art moves fast.** Re-scan cold-start and inductive forecasting at the start of week 3 and before submission.
- **Compute.** About 40 machine-hours a week on one machine; runs are queued in the background.

## 6. Evidence base

| Question | Where |
|---|---|
| Phase 1 numbers and verification | `SEM3-PROGRESS-REPORT.md`; `FINALIZATION-RECORD.md` Sections 9 to 22 |
| Pre-registrations | `PRE-REGISTRATION-C1H.md`, `PRE-REGISTRATION-C1I.md`, `phase2-omnist-scale/feasibility/PREREG.md`, `phase2-omnist-scale/feasibility/PREREG-2.md` |
| Feasibility results | `phase2-omnist-scale/feasibility/REPORT.md`, `phase2-omnist-scale/feasibility/REPORT-2.md` |
| Experiments and result files | `EXPERIMENTS-INDEX.md` |
| Phase 2 measurements | `phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md` |
| Scale and alert criteria, novelty assessment | `phase2-omnist-scale/docs/RESEARCH-PLAN.md` |
