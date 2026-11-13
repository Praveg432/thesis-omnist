"""OmniST backbone — ported (attributed) from the author's published OmniST project.

Source: OmniST, Praveg Vashishtha, arXiv:2611.04256 (github.com/Praveg432/OmniST), MIT.
Ported verbatim (only import rewrites) as the BASELINE for OmniST-Scale. Topology-invariant
forecaster: coordinate tokenizer (cc_hash) + inductive k-NN GAT (inductive_gat) + per-node
bidirectional GRU (temporal), assembled in omnist_model.OmniST.

In OmniST-Scale, the GRU temporal backbone and the exact O(N^2) attention are the BASELINES to beat;
this project's contributions are the drop-in SSM temporal block (ssm_temporal.py) and the O(N.k)
spatial attention (fast_attention.py), evaluated for accuracy/coverage parity + scaling.
"""
from .omnist_model import OmniST, ModelConfig  # noqa: F401
from .cc_hash import CCHashTokenizer  # noqa: F401
from .inductive_gat import InductiveGAT  # noqa: F401
from .temporal import BidirectionalGRU  # noqa: F401

__all__ = ["OmniST", "ModelConfig", "CCHashTokenizer", "InductiveGAT", "BidirectionalGRU"]
