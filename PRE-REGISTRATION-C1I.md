# Pre-registration: second confirmation round (experiments C1i, C1j and C1g on PeMS-BAY)

Written and committed on 17 Nov 2026 **before** any of these runs. Thresholds may be tightened later, never
loosened. Results go to `FINALIZATION-RECORD.md`, Section 18, whatever they show.

## What this round answers

The C1h review left four gaps: (1) the rule was not tested on traffic; (2) Delhi has few scored windows, so
per-split estimates are noisy; (3) the rule widens intervals and is worse than the same-year rule on weather;
(4) station-level conformal was measured on one traffic network only.

## Methods, fixed now

- **Known-at-origin history.** A window's errors may be used for a forecast issued at origin o only if that
  window's whole target period ends on or before o. This allows overlapping forecast origins without leakage.
- **Weekly forecast origins (gap 2).** Delhi, Beijing and weather are scored with a new forecast origin every
  7 days instead of every horizon length (30 or 15 days). Same models and training as C1h.
- **Phase-matched rule for traffic (gap 1).** The traffic series cover weeks, not years, so the analogue of
  "same season in earlier years" is "same time of day on earlier days": errors of earlier, fully observed windows
  whose origin lies within 60 minutes (circular, 24-hour period) of the current origin's time of day, scaled by
  the forecast's mean absolute value exactly as in C1h. Fallback to all earlier windows if fewer than 2 match.
- **Online rule selection (gap 3).** At each forecast origin, choose among five fixed candidate rules the one
  with the lowest mean interval score on the calibration stations over earlier scored windows whose targets are
  already observed; before any such window exists, use the C1h rule. Candidates: same-year; all earlier windows;
  all earlier windows scaled; earlier years same season (45 days) scaled (the C1h rule); same-year scaled.
- **Station-level conformal on PeMS-BAY (gap 4).** Hierarchical conformal with 45 calibration stations, 6 splits,
  as in C1g.

## Data

- C1i: fresh station splits not used before: Delhi and Beijing splits 30 to 49, weather splits 20 to 39; test years
  as in C1h.
- C1j: PeMSD7-M and PeMS-BAY, splits 0 to 5, single test period (the rule was never chosen on traffic).

## Hypotheses and pass rules

| ID | Hypothesis | Pass if |
|---|---|---|
| H5 | The phase-matched rule gives nominal coverage on traffic | Mean coverage within 0.02 of 0.90 on PeMSD7-M and PeMS-BAY |
| H6 | The C1h rule's coverage holds with weekly origins, more precisely | Mean coverage within 0.02 of 0.90 on Delhi, Beijing and weather, and the 95% interval over splits on Delhi narrower than in C1h (0.018 wide) |
| H7 | Online selection keeps coverage and recovers efficiency | Mean coverage within 0.02 of 0.90 on Delhi, Beijing and weather; on weather mean interval score below the C1h rule (paired 95% interval below 0); on Delhi and Beijing mean interval score not above the C1h rule by more than 2% |
| H8 | Station-level conformal helps on a second traffic network | On PeMS-BAY: mean coverage at least 0.90 and share of stations below 0.80 lower than pooled conformal |

Each hypothesis is reported as pass or fail with its numbers.
