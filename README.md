# Topology-Invariant Spatiotemporal Forecasting with Calibrated Uncertainty at Unseen Sensors, and Its Scaling to Large Networks

**M.Tech Thesis — Department of Computer Science and Engineering, IIT Patna**
**Candidate:** Praveg Vashishtha
**Hardware envelope:** Apple M4 Pro (MPS, ~24 GB unified memory), single machine — no cluster

---

## Abstract

Cities and states run on data from large sensor networks, such as air-quality monitors, traffic detectors, weather stations and power-grid meters, and they use that data to forecast what comes next and to act on it. Whether such a system is usable in the field comes down to two things.

The first is that the network never stays still. Sensors fail, drop offline for maintenance, or are installed in new places. A forecasting model has to keep working through all of that, and it often has to predict at a spot where no sensor has ever recorded anything, without being retrained each time the layout changes. The second is that a single predicted number is rarely enough to act on. A pollution advisory or a traffic decision needs a range the operator can trust: an interval calibrated to contain the true value with a stated probability. A forecast that looks confident but is quietly wrong is more dangerous than no forecast at all.

The first phase of this thesis built a forecaster that addresses both. We call it OmniST. It does not depend on how the sensor network is wired, and it attaches conformal prediction intervals with a stated coverage level to its predictions at locations it never trained on. We evaluated it on five real networks covering air quality, weather and traffic, using repeated random splits of the stations into training, calibration and test sets. With a target of 90%, the average coverage at unseen sensors came out between 87.6% and 90.6%. This phase is complete and has been released as a preprint, which has not been submitted for publication.

The evaluation also showed where the method is weak. Coverage varies from split to split and from station to station, so the average hides some badly covered sites. A new sensor placed far from the existing ones might be expected to fare worse, and in one sparse weather network it did: coverage fell by about 1.4 points for each additional typical station spacing. In the dense urban and traffic networks it did not, even when whole regions were held out. The engine also does not scale. Its attention grows with the square of the sensor count, its time model runs step by step, and its coverage has been checked on at most a few hundred real sensors.

The second phase takes these limits as its problem. When a sensor is placed at a new site, can its interval be calibrated using the geometry of that site, meaning its distance to the existing sensors and their local density, so that coverage holds where distance matters without harming networks where it does not? The work also asks whether the approach carries to larger networks, and it shows how an agency could use the intervals, through alerts whose miss rate for true exceedances is controlled.

The technical path has three parts. Attention that looks only at each sensor's nearest neighbours gave essentially the same output as the exact version in testing, and its memory advantage at large sensor counts is still to be measured. Calibration will be localised by site geometry, using a pool of scores built by holding out spatial blocks, together with an estimate of the coverage risk at each site that states its assumptions. Finally, the method will be packaged as a reusable PyTorch library. The coverage statement is marginal and approximate. It is not a guarantee for every station, and the thesis reports these limits alongside its results.

**Terminology.** In the title and throughout, "calibrated coverage" means marginal coverage from split conformal prediction, with calibration on stations the model never saw. Stations are split at random into train, calibration and test sets, so a test station is exchangeable with the calibration stations. The exchangeable unit is the station, not the individual score: scores within a station are dependent and the conformal quantile pools them, so the coverage statement is approximate, and the approximation improves with the number of calibration stations (8 in the Delhi experiments, 3 in Beijing). It is checked empirically over many random splits. It is not a guarantee for every station and not a guarantee against arbitrary spatial dependence. See `phase2-omnist-scale/docs/RESEARCH-PLAN.md`, Section 1.

---

## The thesis in two phases

| | **Phase 1 — OmniST** | **Phase 2 — OmniST-Scale** |
|---|---|---|
| Contribution | Design + validate a topology-invariant forecaster with calibrated (conformal) intervals at unseen sensors | Make that forecaster scale (sub-quadratic attention, time-parallel temporal block) and study how its coverage behaves as the network grows |
| Status | **Built and validated** (4 real datasets, 3 domains); stricter random-split re-evaluation (C1) done; released as preprint arXiv:2611.04256 (not submitted for publication) | **Planned.** Attention equivalence measured (V2). A preliminary parity check (V1) exists and is superseded by the stricter V1b, not yet run. Temporal block currently sequential. |
| Engine | coordinate tokenizer + k-NN attention (**exact O(N²)**) + **BiGRU** + inductive split/online conformal | **O(N·k)** attention + state-space temporal block + geometry-aware calibration (**not yet implemented**) |
| Coverage checked at | up to 325 real sensors (PeMS-BAY) | to be extended toward thousands if a usable real network is available |
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
- **What to decide next:** [`PROGRESSION-DECISION-BRIEF.md`](PROGRESSION-DECISION-BRIEF.md); background in
  [`LEARNINGS-AND-RETIRED-DIRECTIONS.md`](LEARNINGS-AND-RETIRED-DIRECTIONS.md).
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
