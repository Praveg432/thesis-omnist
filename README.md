# Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor Locations in Evolving Networks

**M.Tech Thesis — Department of Computer Science and Engineering, IIT Patna**
**Candidate:** Praveg Vashishtha
**Hardware envelope:** Apple M4 Pro (MPS, ~24 GB unified memory), single machine — no cluster
**Status:** title and abstract submitted and finalised 17 Nov 2026. Remaining work: [`THESIS-COMPLETION-PLAN.md`](THESIS-COMPLETION-PLAN.md), Section 0.

---

## Abstract

Sensor networks for air quality, traffic and weather are used to forecast conditions and to act on them. Two features of real deployments make this hard. The networks change: sensors fail, go offline and are installed at new sites, so forecasts are often needed at locations the model has never seen. And a single predicted value is not enough to act on. An operator needs an interval that contains the true value with a stated probability, and needs to know where that statement can be trusted.

This thesis studies uncertainty quantification for forecasting at sensor locations a model was not trained on, in networks whose layout changes. Its first part, now complete and released as a preprint, built and evaluated OmniST. OmniST is a forecaster that does not depend on a fixed network layout, so it can predict at a new sensor without being retrained, and it attaches split conformal prediction intervals to its forecasts at unseen sensors. On five real networks covering air quality, weather and traffic, with stations split at random into training, calibration and test sets many times over, average coverage at unseen sensors was between 87.6% and 90.6% for a 90% target when calibrated on errors from the evaluation period itself. Using only errors available at forecast time, averages were between 77.8% and 89.1%, lowest in the two air-quality networks, where error roughly doubled through the test year and simple baselines fell short alike. Calibrating instead on earlier years' errors from the same season, scaled by the forecast's magnitude, gave 90.2% and 89.0% in a pre-registered test on fresh station splits, and 90.8% on the weather network, which played no part in choosing the rule. The evaluation also showed the limits of an average. Coverage varied from split to split, and some individual stations were covered far less often than the target. A fall in coverage with distance from the training network, 1.4 points per station spacing in one sparse weather network, disappeared once a coordinate-encoding defect was corrected. And the cost of the model's attention grows with the square of the number of sensors.

The remaining work asks three open questions. First, where does coverage at a new site fail, and can calibration that accounts for the site's position relative to the existing network repair it without harming sites that are already well covered? Second, does the approach continue to hold, in coverage and in compute, as networks grow from hundreds toward thousands of sensors? Third, are the intervals useful as well as calibrated, judged against simple forecasting baselines and in decision tasks such as threshold alerts with a controlled miss rate? Early measurements bear on the last two. Restricting attention to each sensor's nearest neighbours reduced the attention layer's inference memory about seventeenfold at 8,000 sensors, with no gain below about a thousand. Replacing the recurrent time model with a state-space block brought no speed gain on this hardware. On real traffic data the intervals were narrower than those of a persistence forecast but wider than those of a seasonal one.

The expected contributions are an evaluation protocol for coverage at unseen sensors that uses only information available at forecast time, a characterisation of where and why that coverage fails, the methods tried to repair it together with their measured effect, and open, reproducible code. Each question is answered by measurement against criteria fixed in advance, so a negative answer is reported as a finding of the thesis. Coverage statements throughout are marginal and approximate, not guarantees for every sensor.

**Keywords:** spatiotemporal forecasting; uncertainty quantification; conformal prediction; inductive forecasting; sensor networks.

**Terminology.** Throughout, "calibrated coverage" means marginal coverage from split conformal prediction, with calibration on stations the model never saw. Stations are split at random into train, calibration and test sets, so a test station is exchangeable with the calibration stations. The exchangeable unit is the station, not the individual score: scores within a station are dependent and the conformal quantile pools them, so the coverage statement is approximate, and the approximation improves with the number of calibration stations (8 in the Delhi experiments, 3 in Beijing). It is checked empirically over many random splits. It is not a guarantee for every station and not a guarantee against arbitrary spatial dependence. See `phase2-omnist-scale/docs/RESEARCH-PLAN.md`, Section 1.

---

## The thesis in two phases

| | **Phase 1 — OmniST** | **Phase 2 — OmniST-Scale** |
|---|---|---|
| Contribution | Design + validate a topology-invariant forecaster with calibrated (conformal) intervals at unseen sensors | Answer three open questions: where coverage at new sites fails and whether it can be repaired, whether the approach holds as networks grow, and whether the intervals are useful against simple baselines |
| Status | **Built and validated** (4 real datasets, 3 domains); stricter random-split re-evaluation (C1) done; released as preprint arXiv:2611.04256 (not submitted for publication) | **In progress.** Measured: attention equivalence (V2), memory and time against N and T (V4), coverage against N and interval width against baselines (V3, V3b). V1b not yet run. See [`CONSOLIDATED-FINDINGS.md`](phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md). |
| Engine | coordinate tokenizer + k-NN attention (**exact O(N²)**) + **BiGRU** + inductive split/online conformal | **O(N·k)** neighbour attention (measured); calibration that accounts for site position (**not yet implemented**); state-space block tried and dropped (no speed gain) |
| Coverage checked at | up to 325 real sensors (PeMS-BAY) | 325 real sensors with real coordinates; synthetic to 4,000; real networks toward thousands if a usable one is available |
| Folder | [`phase1-omnist/`](phase1-omnist/) | [`phase2-omnist-scale/`](phase2-omnist-scale/) |

Both phases are thesis work. OmniST is a **preprint, not a publication** — it has not been submitted
to any venue — so building it is examined as the thesis's first contribution, not treated as external
prior art. Phase 2 builds directly on it.

## Where to start

- **The framing:** [`MTECH-THESIS-PROPOSAL.md`](MTECH-THESIS-PROPOSAL.md) — title, abstract, problem,
  two-phase plan, gates, risks, contributions (committee-facing).
- **The narrative + timeline:** [`THESIS-OVERVIEW.md`](THESIS-OVERVIEW.md) — what is done vs pending,
  mapped to the thesis timeline.
- **Latest Phase 2 measurements (15 Nov):**
  [`phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md`](phase2-omnist-scale/docs/CONSOLIDATED-FINDINGS.md).
- **Plan to completion (12 weeks, from 16 Nov 2026):** [`THESIS-COMPLETION-PLAN.md`](THESIS-COMPLETION-PLAN.md).
- **What to decide next:** [`PROGRESSION-DECISION-BRIEF.md`](PROGRESSION-DECISION-BRIEF.md); background in
  [`LEARNINGS.md`](LEARNINGS.md).
- **Claim → evidence:** [`EXPERIMENTS-INDEX.md`](EXPERIMENTS-INDEX.md) — every claim in the abstract
  traced to the script that produces it and the committed result file, marked executed or pending.
- **Phase 1 details:** [`phase1-omnist/README.md`](phase1-omnist/README.md) and
  [`phase1-omnist/FINDINGS-AND-IMPACT.md`](phase1-omnist/FINDINGS-AND-IMPACT.md).
- **Phase 2 details:** [`phase2-omnist-scale/README.md`](phase2-omnist-scale/README.md) and
  [`phase2-omnist-scale/docs/VETTING-REPORT.md`](phase2-omnist-scale/docs/VETTING-REPORT.md).

## Repository layout

```
thesis-omnist/
├── README.md                     # this file (title + abstract + map)
├── MTECH-THESIS-PROPOSAL.md       # committee-facing proposal (two-phase)
├── THESIS-OVERVIEW.md             # narrative, done-vs-pending, timeline
├── EXPERIMENTS-INDEX.md           # abstract claim -> script -> result file
├── LICENSE
├── phase1-omnist/                 # Phase 1: OmniST (full repo — src, experiments, results, data, paper, tests)
└── phase2-omnist-scale/           # Phase 2: OmniST-Scale (src, experiments V1/V2, results, data, tests)
```

Each phase keeps its own `pyproject.toml`, tests, and data loaders so it runs standalone. Phase 2
carries a frozen copy of the OmniST backbone it compares against (`phase2-omnist-scale/src/omnist_scale/omnist/`)
so the scale-up experiments are reproducible without reaching into Phase 1.

## Reproduce

```bash
# Phase 1 (OmniST)
cd phase1-omnist && python3 -m pip install -r requirements.txt && pytest -q
python experiments/06_inductive_conformal.py        # headline inductive coverage (real Delhi)
python experiments/B1_multidomain_v2.py             # cross-domain coverage (4 real datasets)
python experiments/C1_rigorous_inductive_eval.py delhi_air_quality   # random disjoint-station re-evaluation

# Phase 2 (OmniST-Scale)
cd ../phase2-omnist-scale && python3 -m pip install -e ".[dev]" && pytest -q
python experiments/V2_attention_equivalence.py       # neighbour attention vs exact (no training)
python experiments/V1b_parity_equivalence.py quick   # corrected parity gate, smoke test only
```

## License

MIT — see [`LICENSE`](LICENSE).

*External-source content in docs was rephrased for compliance with licensing restrictions. Novelty
verdicts rest on literature as of November 2026 and must be re-scanned before submission.*
