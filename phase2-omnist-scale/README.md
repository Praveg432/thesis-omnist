# OmniST-Scale

**Scaling a topology-invariant spatiotemporal forecaster, with calibrated uncertainty at unseen
sensors, toward thousands of sensors.**

[![status](https://img.shields.io/badge/status-research%20(in%20progress)-orange.svg)]()
[![python](https://img.shields.io/badge/python-%E2%89%A53.10-blue.svg)]()
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> OmniST (arXiv:2611.04256) forecasts across sensor networks and produces conformal prediction
> intervals at locations it never saw during training. Its engine uses O(N^2) exact attention and a
> sequential GRU, and its coverage has been checked only up to 325 real sensors. OmniST-Scale works
> on the engine and on how the coverage behaves as the network grows.

Builds directly on the author's OmniST preprint. Runs on a single Apple M4 Pro (MPS).

---

## The gap

| OmniST today | OmniST-Scale target | State of the evidence |
|---|---|---|
| Exact attention, O(N^2) memory; the older "scalable" path loops in Python | O(N·k) neighbour attention | Implemented. Numerically equal to exact on random tokens (V2). **No memory or speed advantage measured yet.** |
| Sequential GRU temporal model | State-space temporal block | Implemented as a **sequential** scan, about **2x slower** than the GRU (T1). A parallel scan is planned. |
| Coverage checked to 325 real sensors | Coverage studied as N grows, with random station splits | Phase 1 re-evaluation done (C1). Larger real network and scaling study planned. |
| Conditional coverage only partly addressed | Geometry-aware calibration at new sites | **Not implemented.** Planned. Distance matters only in sparse networks (C2). |

## Status

This is the planned second phase of the thesis. What exists:

- **V1** (`experiments/V1_ssm_matches_omnist.py`): preliminary parity check, 3 seeds. Its gate was too
  permissive to be informative and it used training-station calibration. Kept as a record only;
  **superseded by V1b**.
- **V1b** (`experiments/V1b_parity_equivalence.py`): the corrected parity gate (disjoint calibration
  stations, paired equivalence test with margins fixed in advance, 10 seeds). **Not yet run in full.**
- **V2** (`experiments/V2_attention_equivalence.py`): equivalence of the neighbour attention to exact
  attention, shared weights, random tokens.
- **T1** (`experiments/T1_ssm_vs_gru_timing.py`): diagnostic timing of the state-space block against
  the GRU.

The work packages, acceptance criteria and fallbacks for the remainder are in
[`docs/RESEARCH-PLAN.md`](docs/RESEARCH-PLAN.md). Review-driven corrections are listed in
[`docs/VETTING-REPORT.md`](docs/VETTING-REPORT.md).

## Quick start

```bash
python3 -m pip install -e ".[dev]"      # core: numpy/scipy/sklearn
python3 -m pip install -e ".[torch]"    # + torch for the backbone (MPS)
pytest -q
python experiments/V2_attention_equivalence.py   # no training
python experiments/V1b_parity_equivalence.py quick   # smoke test, writes V1b_quick.json
```

## Reused (with attribution)

- **OmniST backbone** (`src/omnist_scale/omnist/`, ported from arXiv:2611.04256, MIT): coordinate
  tokenizer, k-NN attention, BiGRU, conformal calibration. The GRU and exact attention are the
  baselines.
- **Real Delhi PM2.5** (`data/real_delhi/`, public, same source as E-STGCN and OmniST).

## Repository layout

```
phase2-omnist-scale/
├── README.md, pyproject.toml, LICENSE, conftest.py
├── docs/RESEARCH-PLAN.md               # revised plan: work packages, acceptance criteria, fallbacks
├── docs/VETTING-REPORT.md              # what was run, what it shows, what the review corrected
├── src/omnist_scale/
│   ├── omnist/                         # ported OmniST backbone (attributed): the baseline
│   ├── ssm_temporal.py                 # diagonal state-space block (sequential scan today)
│   ├── fast_attention.py               # O(N·k) neighbour attention with a bounded neighbour cache
│   ├── scalable_model.py               # OmniST with swappable temporal / attention components
│   └── stats.py                        # confidence intervals and paired equivalence test
├── experiments/                        # V1 (superseded), V1b, V2, T1
├── data/real_delhi/                    # committed real data
└── tests/
```

`conformal.py` (geometry-aware calibration) is **planned** and does not exist yet.

## Honest scope
A systems and calibration contribution, not an accuracy record and not a new state-space model. A
large real network may not be usable; the plan has a stated fallback. Supersedes an earlier, retired
fusion idea (adaptive spatio-temporal conformal) that was a no-go on real data; it is not part of
this thesis.

## License
MIT. External-source content in docs rephrased for licensing compliance.
