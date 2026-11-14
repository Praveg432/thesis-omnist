# OmniST-Scale

**A scalable, certified topology-invariant spatiotemporal forecaster — keeping OmniST's coverage
guarantee while making its engine run at the thousands-of-sensors regime it could not reach.**

[![status](https://img.shields.io/badge/status-research%20(vetting%20phase)-orange.svg)]()
[![python](https://img.shields.io/badge/python-%E2%89%A53.10-blue.svg)]()
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> OmniST (arXiv:2611.04256) forecasts across sensor networks with a **distribution-free coverage
> guarantee at unseen locations, preserved as sensors are added/removed** — but its engine is
> **O(N²) spatial attention + O(T) sequential GRU**, and its coverage is certified only to **325 real
> sensors**. OmniST-Scale keeps that exact guarantee and **re-engineers the engine to be
> sub-quadratic in nodes and parallel in time, and certifies coverage at scale** — the gate OmniST's
> own limitations section names as open.

Builds directly on the author's published OmniST. Runs on a single Apple M4 Pro (MPS).

---

## The gap (from OmniST's own stated limitations)

| OmniST today | OmniST-Scale target |
|--------------|---------------------|
| Spatial attention O(N²) memory (exact); "scalable" path is a per-batch Python loop | **Genuine O(N·k)** vectorized attention with a *proven equivalence bound* to exact |
| Temporal backbone = sequential **GRU** (O(T), not parallelizable over time) | **Selective state-space (Mamba-style) block** — linear-time, parallel scan (and finally earns the "ST-SSM" name) |
| Coverage certified only to **325 real sensors** | **Certified coverage at thousands of nodes** (+ scalable conditional conformal, tightening OmniST's partial Mondrian fix) |

The novelty is **certified coverage *at scale*** — not raw speed (scalable ST-GNNs exist) and not a
new backbone (SSMs exist). It is the combination: a topology-invariant forecaster that stays
distribution-free-coverage-valid at unseen nodes while scaling sub-quadratically.

## Status: vetting phase (make-or-break first)

Before committing, the load-bearing assumption is kill-gated (`experiments/`, `docs/RESEARCH-PLAN.md`):

- **V1 (the make-or-break):** does an **SSM temporal block + O(N·k) attention** match OmniST's
  accuracy *and* inductive coverage on real Delhi, while scaling better? If it can't match the
  guarantee, the scale-up is moot — stop.
- V2: equivalence bound of O(N·k) attention vs exact (cosine similarity + coverage parity).
- V3: coverage holds as N grows (scaling ladder) on real + large synthetic-real networks.
- V4: does the SSM *earn its keep* (the MambaOut-analog kill-gate) — crossover N/T where it wins.

## Quick start

```bash
python3 -m pip install -e ".[dev]"      # core: numpy/scipy/sklearn
python3 -m pip install -e ".[torch]"    # + torch for the backbone (MPS)
pytest -q
python experiments/V1_ssm_matches_omnist.py      # the make-or-break
```

## Reused (with attribution)

- **OmniST backbone** (`src/omnist_scale/omnist/`, ported from arXiv:2611.04256, MIT): coordinate
  tokenizer + k-NN GAT + BiGRU + split/online conformal. The GRU and exact-attention are the
  *baselines to beat*; the SSM block and O(N·k) attention are this project's contributions.
- **Real Delhi PM2.5** (`data/real_delhi/`, public, same as E-STGCN/OmniST).

## Repository layout

```
omnist-scale/
├── README.md, pyproject.toml, LICENSE, conftest.py
├── docs/RESEARCH-PLAN.md               # problem, 3 optimization fronts, vetting, timeline, risks
├── src/omnist_scale/
│   ├── omnist/                         # ported OmniST backbone (attributed) — the baseline
│   ├── ssm_temporal.py                 # selective state-space temporal block (NEW)
│   ├── fast_attention.py               # O(N·k) spatial attention + equivalence bound (NEW)
│   └── conformal.py                    # split + scalable conditional conformal (NEW/ported)
├── experiments/                        # V1-V4 vetting (+ results/)
├── data/real_delhi/                    # committed real data
└── tests/
```

## Honest scope
A systems + trustworthy-ML contribution: certified coverage at scale, not a SOTA-accuracy claim or a
new SSM. The MambaOut analog is a real risk (a gated-conv/GRU may match the SSM at small T/N) — V4 is
the kill-gate for it. Certifying coverage at *thousands of real sensors* needs a real dataset that
size (a data gate, not an architecture gate). Supersedes an earlier, retired fusion idea
(adaptive spatio-temporal conformal) that was a no-go on real data; it is not part of this thesis.

## License
MIT. External-source content in docs rephrased for licensing compliance.
