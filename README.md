# Certified Topology-Invariant Spatiotemporal Forecasting with Trustworthy Uncertainty at Unseen Sensors, and Its Scaling to Large Networks

**M.Tech Thesis — Department of Computer Science and Engineering, IIT Patna**
**Candidate:** Praveg Vashishtha
**Hardware envelope:** Apple M4 Pro (MPS, ~24 GB unified memory), single machine — no cluster

---

## Abstract

Cities and states now run on data from large sensor networks — air-quality monitors, traffic
detectors, weather stations, power-grid meters — and they use that data to forecast what comes next
and act on it. Whether such a system is usable in the field comes down to two things.

The first is that the network never stays still. Sensors fail, drop offline for maintenance, or get
installed in new places. A forecasting model has to keep working through all of that, and it often
has to predict at a spot where no sensor has ever recorded anything, without being retrained each
time the layout changes. The second is that a single predicted number is rarely enough to act on. A
pollution advisory or a traffic decision needs a range the operator can actually trust — an interval
guaranteed to hold the true value with a known probability. A forecast that looks confident but is
quietly wrong is more dangerous than no forecast at all.

The first phase of this thesis designed a forecaster that delivers both. We call it OmniST: it does
not care how the sensor network is wired, it attaches a distribution-free coverage guarantee to its
predictions at locations it never trained on, and it keeps that guarantee when the network changes.
We validated it on four real datasets across air quality, traffic, and weather, and have released it
as a preprint. Building and validating that method is the first contribution of the thesis.

That first phase also surfaced a hard limit, and the second phase is built to remove it. OmniST does
not scale. Its spatial computation grows with the square of the sensor count, its temporal model runs
step by step and cannot be sped up across time, and its guarantee has only been certified up to a few
hundred real sensors. That is exactly the wrong ceiling, because the places where a resilient,
trustable forecaster matters most — city-wide and national monitoring grids — have thousands of
sensors, not hundreds. So the second problem the thesis takes on is to make a certified,
topology-independent forecaster run efficiently at the scale of thousands of sensors without
weakening the guarantee that is the whole point of it.

The timing matters. Sensing networks are expanding quickly, and when a forecaster breaks as sensors
come and go, or reports confidence it cannot stand behind, the cost lands on public-safety and
resource decisions. Making the model merely faster is neither the real difficulty nor anything new.
The difficulty is holding a finite-sample statistical guarantee steady while the engine underneath it
is rebuilt and the network keeps growing.

The technical path is clear. The quadratic spatial step is replaced by one that looks only at each
sensor's nearest neighbours — provably the same answer, far less memory — bringing large networks
within reach of ordinary hardware. The slow sequential time model gives way to a modern state-space
block that handles long sequences in linear time and in parallel. Most important, the
conformal-prediction layer that produces the guarantee is reworked so it stays valid as the network
scales, and so the guarantee holds more evenly from sensor to sensor rather than only on average.

Early runs on real air-quality data back the idea: the rebuilt engine matches the original model's
accuracy, keeps its coverage guarantee, and the nearest-neighbour attention gives numerically the
same output as the exact version. The thesis delivers a forecaster that is certified, trustworthy,
and scalable across large real networks — useful wherever environmental, traffic, and infrastructure
monitoring has to keep working as the sensors on the ground change.

---

## The thesis in two phases

| | **Phase 1 — OmniST** | **Phase 2 — OmniST-Scale** |
|---|---|---|
| Contribution | Design + validate a topology-invariant forecaster with a certified inductive coverage guarantee at unseen sensors | Re-engineer that forecaster to be sub-quadratic in nodes and parallel in time, and certify the guarantee holds at scale |
| Status | **Built and validated** (4 real datasets, 3 domains); released as preprint arXiv:2611.04256 (not submitted for publication) | **V1 / V2 executed (GO)**; V3 (coverage-at-scale) and V4 (SSM crossover) pending |
| Engine | coordinate tokenizer + k-NN attention (**exact O(N²)**) + **BiGRU** + inductive split/online conformal | **O(N·k)** attention + **selective state-space (SSM)** temporal block + **scalable conditional conformal** |
| Certified scale | 325 real sensors (PeMS-BAY) | coverage certified as N grows toward thousands |
| Folder | [`phase1-omnist/`](phase1-omnist/) | [`phase2-omnist-scale/`](phase2-omnist-scale/) |

Both phases are thesis work. OmniST is a **preprint, not a publication** — it has not been submitted
to any venue — so building it is examined as the thesis's first contribution, not treated as external
prior art. Phase 2 builds directly on it.

## Where to start

- **The framing:** [`MTECH-THESIS-PROPOSAL.md`](MTECH-THESIS-PROPOSAL.md) — title, abstract, problem,
  two-phase plan, gates, risks, contributions (committee-facing).
- **The narrative + timeline:** [`THESIS-OVERVIEW.md`](THESIS-OVERVIEW.md) — what is done vs pending,
  mapped to the thesis timeline.
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

# Phase 2 (OmniST-Scale)
cd ../phase2-omnist-scale && python3 -m pip install -e ".[dev]" && pytest -q
python experiments/V1_ssm_matches_omnist.py          # parity make-or-break (real Delhi) -> GO
python experiments/V2_attention_equivalence.py       # O(N.k) == exact -> GO
```

## License

MIT — see [`LICENSE`](LICENSE).

*External-source content in docs was rephrased for compliance with licensing restrictions. Novelty
verdicts rest on literature as of November 2026 and must be re-scanned before submission.*
