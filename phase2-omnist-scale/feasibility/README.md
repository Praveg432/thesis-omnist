# Feasibility tests for Phase 2 (OmniST v2 upgrades)

Two pre-registered rounds that tested proposed upgrades before any change to the Phase 2 plan. They were run on 26 Nov
2026 in a separate sandbox repository that read this repository without writing to it, then copied here unchanged
except for the import paths (the sandbox lived next to `thesis-omnist/`; here the code sits inside it). Results were
not re-run after the copy.

| File | Content |
|---|---|
| `PREREG.md`, `PREREG-2.md` | Pass rules, committed before each round's runs |
| `REPORT.md`, `REPORT-2.md` | Results and interpretation of each round |
| `v2lib.py` | Data preparation (read-only use of `phase1-omnist`), model variants, neighbour baselines |
| `run_feasibility.py`, `run_leads.py`, `tod_v1.py`, `memory_check.py` | Experiments of rounds 1 and 2 |
| `summarise.py`, `summarise2.py`, `summarise_stride.py` | Apply the pass rules; write `results/verdicts*.json` |
| `tests/` | 9 tests of the sandbox code |
| `results/` | Per-split results and verdicts |

## Provenance: sandbox commit history

The pre-registration timestamps below come from the sandbox repository (local; not published). Each pre-registration
commit precedes the code and results of its round.

| Commit | Time | Message |
|---|---|---|
| 1df2868 | 2026-11-26 12:04 | Pre-register OmniST v2 feasibility tests (before any run) |
| 889a7be | 2026-11-26 12:08 | Feasibility code: v2 model variants, neighbour baselines, forecast-time intervals; 6 tests |
| e88a4f9 | 2026-11-26 13:17 | Feasibility results and report: F2, F5, F4 pass; F1 fails; F3 passes on PeMS-BAY only; F4 gain not attributable to spatial parts |
| 99a9d73 | 2026-11-26 13:37 | Pre-register round 2: strengthen the Day-0 and time-of-day leads (before any run) |
| 06df2bc | 2026-11-26 13:39 | Round 2 code: attention ablations, PeMSD7-M, Day-0 intervals, thesis-pipeline time-of-day test; 3 tests |
| d1ef21a | 2026-11-26 14:39 | Exploratory (not pre-registered): training-stride option in the thesis-pipeline test |
| 34406fa | 2026-11-26 15:26 | Round 2 results and report: Day-0 lead replicated on two road networks; time-of-day hypothesis refuted; exploratory training-stride effect on PeMS-BAY |

## Reproduce

From this folder: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests`, then for example
`python3 run_feasibility.py pemsbay 0`, `python3 run_leads.py pemsd7 0`, `python3 tod_v1.py pemsbay_traffic control`,
and `python3 summarise.py`, `python3 summarise2.py`. The traffic speed series must be downloaded first
(`phase1-omnist/data/README.md`).
