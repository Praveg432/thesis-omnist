# Title and Abstract for Initial Submission (draft, 15 Nov 2026)

Title and abstract for initial submission. **Applied on 15 Nov 2026** to `README.md`,
`MTECH-THESIS-PROPOSAL.md` and `SEM3-PROGRESS-REPORT.md` (and the report PDF). Subject to supervisor approval.

## Title

**Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor Locations in Evolving Networks**

## Abstract

Sensor networks for air quality, traffic and weather are used to forecast conditions and to act on them. Two features of real deployments make this hard. The networks change: sensors fail, go offline and are installed at new sites, so forecasts are often needed at locations the model has never seen. And a single predicted value is not enough to act on. An operator needs an interval that contains the true value with a stated probability, and needs to know where that statement can be trusted.

This thesis studies uncertainty quantification for forecasting at sensor locations a model was not trained on, in networks whose layout changes. Its first part, now complete and released as a preprint, built and evaluated OmniST. OmniST is a forecaster that does not depend on a fixed network layout, so it can predict at a new sensor without being retrained, and it attaches split conformal prediction intervals to its forecasts at unseen sensors. On five real networks covering air quality, weather and traffic, with stations split at random into training, calibration and test sets many times over, average coverage at unseen sensors was between 87.6% and 90.6% for a 90% target. The evaluation also showed the limits of an average. Coverage varied from split to split, and some individual stations were covered far less often than the target. It fell with distance from the training network in one sparse weather network, by about 1.4 points per typical station spacing, but not in the denser networks. And the cost of the model's attention grows with the square of the number of sensors.

The remaining work asks three open questions. First, where does coverage at a new site fail, and can calibration that accounts for the site's position relative to the existing network repair it without harming sites that are already well covered? Second, does the approach continue to hold, in coverage and in compute, as networks grow from hundreds toward thousands of sensors? Third, are the intervals useful as well as calibrated, judged against simple forecasting baselines and in decision tasks such as threshold alerts with a controlled miss rate? Early measurements bear on the last two. Restricting attention to each sensor's nearest neighbours reduced the attention layer's inference memory about seventeenfold at 8,000 sensors, with no gain below about a thousand. Replacing the recurrent time model with a state-space block brought no speed gain on this hardware. On real traffic data the intervals were narrower than those of a persistence forecast but wider than those of a seasonal one.

The expected contributions are an evaluation protocol for coverage at unseen sensors that uses only information available at forecast time, a characterisation of where and why that coverage fails, the methods tried to repair it together with their measured effect, and open, reproducible code. Each question is answered by measurement against criteria fixed in advance, so a negative answer is reported as a finding of the thesis. Coverage statements throughout are marginal and approximate, not guarantees for every sensor.

**Keywords:** spatiotemporal forecasting; uncertainty quantification; conformal prediction; inductive
forecasting; sensor networks.

---

## 1. Is the topic appropriate?

**Yes, for an M.Tech CSE thesis, with four conditions.**

- **It is a real research problem with completed evidence.** Phase 1 is built, evaluated on five real
  networks with repeated random splits, and documented with reproducible code and tests. Phase 2 has
  measured results, including negative ones.
- **Its scope fits the time and hardware.** Every experiment so far runs on one M4 Pro in minutes to
  hours.
- **Its contribution is evaluation-led.** The novelty is in how calibrated forecasting at unseen
  sensors behaves and where it fails, plus the methods tried to repair it. It is not a new theorem and
  not an accuracy record. The title and abstract are worded to match that.

Conditions:
1. **Supervisor approval** of the title and of the Phase 2 scope (both still pending).
2. **Institute rule on prior work.** Phase 1 is the candidate's own unpublished preprint
   (arXiv:2611.04256). Confirm that the manual allows including work already released as a preprint.
3. **The preprint's abstract claims more than the evaluation supports** (coverage at or above 90%
   under dropout and at 325 sensors; the random-split means are 87.6% to 90.6%). Either post a revised
   version or state the difference in the thesis. The draft abstract uses the random-split numbers.
4. **The third question carries the most risk to the story.** The intervals currently lose to a
   seasonal baseline on traffic. The thesis must report this whichever way it resolves.

## 2. How the wording stays acceptable if the plan changes

Rules applied:
- The title names the problem (uncertainty at unseen locations in changing networks), not a model,
  method, or result. No "calibrated", "certified", "scalable", "topology-invariant" or model name.
- Facts in the abstract are only results already measured and committed. They stay true whatever
  happens next.
- Remaining work is stated as questions, not deliverables. No method is promised: "calibration that
  accounts for the site's position" covers geometry-aware conformal, localised or weighted conformal,
  and any alternative.
- One sentence says negative answers are findings.

| If this happens | Title still fits? | Abstract still true? | What to change at final submission |
|---|---|---|---|
| Distance effect does not replicate on the large sparse network; geometry-aware calibration (WP1) fails | Yes | Yes (first question answered "no") | Report the characterisation |
| No usable real network above 325 sensors | Yes | Yes ("toward thousands" is a question) | State real evidence ends at 325 |
| Intervals never beat the seasonal baseline | Yes | Yes (already reported) | Report as a limitation |
| Phase 2 re-centres on usefulness (new interval method, conformalised quantile regression, seasonal-residual model) | Yes | Yes (third question) | Describe the method |
| OmniST backbone replaced by another forecaster | Yes (title names no model) | Yes (OmniST is the completed first part) | Add the new model |
| Scaling work dropped | Yes | Yes (one completed measurement) | Remove or shorten |
| Alerts or sensor placement added | Yes ("unseen sensor locations") | Yes | Add results |
| Phase 1 numbers revised by a new evaluation | Yes | Numbers must be updated | Re-run `tools/check_submission_text.py` |
| **Switch to SafeTTA or another unrelated topic** | **No** | **No** | **New title and abstract needed** |

The last row is deliberate. A title broad enough to also cover image test-time adaptation (for example
"Reliable Machine Learning under Distribution Shift") would be vague enough to invite rejection, and
would hide the completed Phase 1 work. If a switch is possible, decide it before submission.

## 3. Alternatives considered

| Title | Words | Trade-off |
|---|---|---|
| Previous (until 15 Nov): *Topology-Invariant Spatiotemporal Forecasting with Calibrated Uncertainty at Unseen Sensors, and Its Scaling to Large Networks* | 15 | Commits to scaling as a main outcome, and to calibration being achieved |
| *Topology-Invariant Spatiotemporal Forecasting with Calibrated Uncertainty at Unseen Sensors in Changing Networks* | 12 | Specific and close to Phase 1; commits to the architecture and to "calibrated" |
| **Adopted** (above) | 12 | Most robust; slightly less distinctive |

## 4. Checks run on this draft

See `tools/check_draft_abstract.py`: the same rules as `tools/check_submission_text.py` (title 10 to
15 words, no digits, symbols, acronyms, filler or "certified"; abstract at most 600 words, no em dash,
coverage range, weather slope and "five real networks" tied to the result files), plus the Phase 2
figures (memory ratio at 8,000 sensors, no gain below 1,000, traffic width ordering).

## 5. Status

- Done (15 Nov 2026): title and abstract replaced in `README.md`, `MTECH-THESIS-PROPOSAL.md` and
  `SEM3-PROGRESS-REPORT.md`; report PDF regenerated; `tools/check_submission_text.py` and
  `tools/check_draft_abstract.py` pass. Abstract expanded from 415 to 503 words (the keywords line adds
  11 more in the README and report).
- Outstanding: supervisor approval of the title and of the Phase 2 scope.
