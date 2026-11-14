"""omnist_scale: scalable, certified topology-invariant spatiotemporal forecasting.

Keeps OmniST's distribution-free inductive coverage guarantee while re-engineering the engine for
scale. Contributions (NEW, outside omnist/):
  ssm_temporal   - selective state-space (Mamba-style) temporal block: linear-time, parallel scan.
  fast_attention - O(N.k) spatial attention with a proven equivalence bound to exact attention.
  conformal      - PLANNED (not yet implemented): scalable conditional conformal. The V1/V2 gates use
                   standard split-conformal calibration inline.

Baseline (reused, attributed): omnist/ = the published OmniST backbone (GRU + exact attention).
"""
from . import omnist  # noqa: F401

__all__ = ["omnist"]
__version__ = "0.1.0"
