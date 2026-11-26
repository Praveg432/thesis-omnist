# Thesis Completion Plan: Phase 2 (authoritative)

Candidate: Praveg Vashishtha (IITP006424) · Supervisor: Pankaj Chaswal · Hardware: Apple M4 Pro, one machine.

**Status of this plan.** Rewritten on 26 Nov 2026 from the evidence in `FINALIZATION-RECORD.md` Sections 11 to 21. It
replaces the 16 Nov version and the work-package timeline in `phase2-omnist-scale/docs/RESEARCH-PLAN.md`
(acceptance details for scale and alerts are still taken from that file). **Pending supervisor approval** of the
scope. Acceptance criteria below are fixed now; they may be tightened, never loosened, and each contribution gets
a dated pre-registration file before its first run, as was done for C1h and C1i.

Thesis title (submitted 17 Nov 2026): *Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor
Locations in Evolving Networks.* Dates: Semester 4 runs 16 Nov 2026 to 7 Feb 2027; week 3 starts 30 Nov.

---

## 0. Status and action register

### Phase 1 (OmniST): complete

| Item | State |
|---|---|
| Forecaster, five real networks, protocol C1 | Done; preprint arXiv:2611.04256 |
| Forecast-time calibration (C1b to C1j) | Done. Two pre-registered rounds. Seasonal rule confirmed on air quality and weather (0.890 to 0.913); expanding calibration on traffic (0.881, 0.891); station-level conformal confirmed on traffic |
| Coordinate defect | Found, fixed (option, default unchanged), effect measured |
| Distance effect (C2, C3) | Re-run with the corrected frame: the weather effect does not reproduce |
| Verification | Seven checks, `FINALIZATION-RECORD.md` Section 20; progress report final |
| Evidence limits closed | Traffic extended to 20 splits; Phase 2 re-run with the corrected frame (unchanged); V1b run (attention GO, state-space NO-GO); Section 21 |
| Not re-run, labelled original-protocol in the report | Dropout robustness, drift handling, 7-sensor run, E-STGCN, IGNNK and interpolator comparisons. Scheduled below (E1) |

### Decisions outside the repository

1. Supervisor approval of this scope and of the title. **Open.**
2. Whether and when to post a revised preprint (correction text in `FINALIZATION-RECORD.md`, Section 19). Proposed: after the
   Phase 2 confirmation of contribution A, around week 5.
3. Submission of the Semester 3 report, window 20 to 30 Nov 2026.

---

## 1. What the evidence changes

| Finding | Effect on the plan |
|---|---|
| The forecast-time shortfall on air quality is a calibration problem with too little history, repaired by earlier years' errors scaled by the forecast, at +25% to +60% width (C1f, C1h, C1i) | Contribution A is half done. What remains is per-station coverage, width, and generality |
| Traffic needs no seasonal rule; station-level conformal repairs per-station coverage at +25% to +31% width (C1g) | A is evaluated per network type, not with one rule |
| The weather distance effect was produced by the coordinate defect (C2n: slope -0.2 points per spacing, interval includes zero) | Contribution C is now a properly powered test of whether distance matters, most likely ending as a characterisation. Not a method to build |
| OmniST beats persistence and seasonal-naive on interval score on air quality and weather; not on traffic (PeMSD7-M MAE 3.79 against 3.63; PeMS-BAY width 33% above seasonal-naive) | Contribution D concentrates on traffic |
| Neighbour attention cuts inference memory 7 to 17 times from 4,000 sensors; state-space block 2 times slower, dropped | Scale work is measurement, not invention |
| Phase 2 real-network inputs were inside the intended coordinate range (at most 0.47; synthetic at most 1.9), so V3 and V3b were not distorted by the defect | No re-run needed; a corrected-frame run is a robustness check (E2) |
| Online rule selection fails with one earlier year (Beijing 0.868) | Not a default; needs several earlier years |

---

## 2. Contributions, criteria and fallbacks

**Spine.** Valid and useful intervals at a new sensor from the day it is installed, evaluated with information
available at forecast time only.

### A. Per-station coverage at forecast time (protected)
Already shown: mean coverage at target on all networks with a network-type-specific rule. Remaining problem: some
stations stay under-covered (weather 13% below 0.80; pooled traffic 6% to 12%) and the repair costs width.
- **Work.** (A1) Combine station-level conformal with the seasonal scaled scores on air quality and weather.
  (A2) Test the second-moment variant for per-station spread. (A3) Measure how the width cost falls with the number of
  calibration stations on the large GHCN network (E3), where 300 or more calibration stations are available.
- **Accept** on every network, over at least 20 fresh splits: mean coverage within 0.02 of 0.90; at most 5% of
  stations below 0.80; width at most 30% above the Phase 1 fixed rule for that network type.
- **Fallback.** Report the width against worst-station coverage curve and which networks cannot meet both.

### B. A new sensor's first weeks (protected)
- **Work.** Coverage and width as the sensor accumulates its own data, 0 to 60 days: cold start (other stations only),
  then own-data split conformal, generalized hierarchical conformal [22], adaptive conformal inference.
- **Accept.** Coverage within 0.03 of 0.90 at every history length; at least 5% narrower at 60 days than at 0 days on
  4 of 6 networks, paired over splits.
- **Fallback.** Curves of coverage and width against history, with the finding that own data does not help where it does not.

### C. Does position matter? (gated, probably a characterisation)
- **Gate G0.** On the large GHCN network (E3), with the corrected frame and at least 20 region splits, the farthest
  tercile of test stations is at least 0.03 below the nearest. If G0 fails, no geometry-aware method is built.
- **If G0 passes.** Geometry-aware calibration [16], [17] against sequential whitening [10] and cluster-aware
  calibration [18]. Accept: far tercile within 0.03 of 0.90, mean within 0.02, width at most +10%, not worse than whitening.
- **If G0 fails (the expected case).** The result is a powered negative: the 95% interval of the distance slope on a
  network 10 to 50 times larger than the 30-station one, which is a thesis result.

### D. Are the intervals useful? (protected on traffic)
- **Done** on air quality and weather (interval score below persistence and seasonal-naive, C1h).
- **Work.** Traffic: a forecaster that predicts the residual from the seasonal-naive forecast, locally scaled scores,
  a quantile head; diagnosis of the PeMS-BAY width gap by horizon, time of day and station.
- **Accept.** On PeMSD7-M and PeMS-BAY, interval score below both persistence and seasonal-naive under the same
  calibration rule, paired 95% interval below zero, coverage within 0.02 of 0.90.
- **Fallback.** State that on traffic the learned model does not beat a seasonal baseline, with the diagnosis.

### E. Scale and the remaining Phase 1 comparisons
- **E1.** Phase 1 comparisons under the forecast-time rules: dropout robustness, drift handling, the 7-sensor run,
  E-STGCN, IGNNK (official code), interpolators. Accept: each claim restated or withdrawn with the new numbers.
- **E2.** Done 26 Nov: V1b (attention GO, state-space NO-GO) and the corrected-frame V3 on real PeMS-BAY (unchanged).
  Remaining: corrected-frame V3b, only if D changes the traffic model.
- **E3.** Large sparse network from GHCN-Daily (300 to 1,500 stations after quality filtering) for A, C and coverage
  against N; LargeST (8,600 sensors) for compute scaling only.
- **Accept.** From `phase2-omnist-scale/docs/RESEARCH-PLAN.md` WP3: at least 5 times lower peak memory than exact
  attention at N of 2,000 or more; neighbour-set agreement at least 0.99; coverage within 0.02 of 0.90 at every size
  evaluated, at least 10 splits per size. Replicated sensors are never used to claim coverage.
- **Fallback.** Restrict the claim to equivalence; if no real network above 325 sensors is usable, state evidence to 325.

### F. Alerts with a controlled miss rate (cut candidate)
Conformal risk control [19] at one air-quality network with published thresholds fixed in advance. Accept: mean miss rate
at or below target plus 0.02 over random splits, false-alarm rate against a threshold-on-point-forecast baseline.

### G. Package and thesis (protected)
Pip-installable PyTorch package with fit, calibrate, predict, tests and an example that reproduces one headline table in
a fresh environment; thesis in the IIT Patna format, at least 30 verified references.

**Dropped:** the state-space block, a separate coverage-risk estimate (the distance effect it targeted is not
established), sensor placement, cross-city transfer, online rule selection as a default.

---

## 3. Schedule (week 3 starts 30 Nov 2026)

| Week | Dates | Work | Exit check |
|---|---|---|---|
| 3 | 30 Nov to 6 Dec | Submit the Semester 3 report. Pre-register A and G0. Build the GHCN large network (E3). LargeST usability check | Network built with a quality report |
| 4 | 7 to 13 Dec | G0 test (C) on the large network. A1 and A2 on air quality and weather | G0 pass or fail recorded; A pre-registered runs complete |
| 5 | 14 to 20 Dec | A on traffic and the large network (A3). Decide on the preprint revision | A accepted or fallback declared |
| 6 | 21 to 27 Dec | B design, pre-registration and first runs. Start thesis chapters 1 to 3 | B first curves |
| 7 | 28 Dec to 3 Jan | B complete. D on traffic: seasonal-residual forecaster, diagnosis | B accepted or fallback |
| 8 | 4 to 10 Jan | D confirmation. E3 coverage against N. C method only if G0 passed | D accepted or fallback |
| 9 | 11 to 17 Jan | E1 comparisons. LargeST compute scaling. F alerts if on schedule | E accepted; F decision |
| 10 | 18 to 24 Jan | Reproducibility pass in a fresh environment. Chapters 4 to 6 | Headline table reproduces |
| 11 | 25 to 31 Jan | Chapters 7 to 9. Supervisor review | Draft complete |
| 12 | 1 to 7 Feb | Revisions, formatting, slides | Submission-ready 7 Feb 2027 |

**Cut order if time runs short:** F, then LargeST compute scaling, then E1 breadth, then C's method (if G0 passed).
A, B, D-on-traffic and the writing are protected.

## 4. Risks

- **GHCN data quality.** Too many gaps would shrink the large network; fallback is a smaller curated set, and the C and
  coverage-against-N claims then rest on that size.
- **Width.** Every repair costs width. If A cannot meet the +30% limit on a network type, that is reported as the trade-off.
- **Small traffic samples.** Traffic series cover weeks to months, so multi-year rules do not apply; confirmations use
  20 splits and are stated as such.
- **Selection after the fact.** The seasonal rule was chosen on C1f before being confirmed. From now on a rule is
  fixed in a dated pre-registration before its confirmation run.
- **Fast-moving area.** Re-scan the prior art at the start of week 3 and before submission.
- **Single-machine compute.** Runs are queued in the background; a week's work is not planned above about 40 machine-hours.

## 5. Evidence base

| Question | Where |
|---|---|
| Phase 1 numbers and verification | `SEM3-PROGRESS-REPORT.md`; `FINALIZATION-RECORD.md` Sections 9 to 21 |
| Pre-registrations | `PRE-REGISTRATION-C1H.md`, `PRE-REGISTRATION-C1I.md` |
| Experiments and result files | `EXPERIMENTS-INDEX.md` |
| Phase 2 measurements | `phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md` |
| Scale and alert acceptance details, novelty assessment | `phase2-omnist-scale/docs/RESEARCH-PLAN.md` |
