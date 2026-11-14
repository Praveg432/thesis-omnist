"""omnist_scale: scalable topology-invariant spatiotemporal forecasting with conformal calibration.

Aims to keep OmniST's conformal coverage behaviour while re-engineering the engine for scale. Contributions (NEW, outside omnist/):
  ssm_temporal   - diagonal state-space temporal block with an input-dependent step size. The scan
                   is currently SEQUENTIAL (about 2x slower than the GRU); a parallel scan is planned.
  fast_attention - O(N.k) spatial attention; numerical equivalence to exact attention is measured
                   (V2); a speed or memory advantage is not yet demonstrated.
  conformal      - PLANNED (not yet implemented): geometry-aware calibration at new sites. The V1/V2
                   gates use standard split-conformal calibration inline.

Baseline (reused, attributed): omnist/ = the published OmniST backbone (GRU + exact attention).
"""
from . import omnist  # noqa: F401

__all__ = ["omnist"]
__version__ = "0.1.0"
