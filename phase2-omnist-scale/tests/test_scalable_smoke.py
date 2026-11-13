"""Smoke tests: the SSM temporal block, O(N.k) attention, and the swappable model wire together and
behave as the vetting requires. Not the research eval (that is experiments/ at full seeds)."""
import numpy as np
import torch

from omnist_scale.omnist.omnist_model import ModelConfig
from omnist_scale.scalable_model import OmniSTScale
from omnist_scale.ssm_temporal import BidirectionalSSM
from omnist_scale.fast_attention import FastInductiveGAT
from omnist_scale.omnist.inductive_gat import InductiveGAT


def _coords(B, N):
    return torch.rand(B, N, 2) * torch.tensor([0.4, 0.6]) + torch.tensor([28.4, 76.8])


def test_all_four_variants_forward():
    cfg = ModelConfig(n_features=1, horizon=7, d_model=64)
    f = torch.randn(2, 20, 30, 1); c = _coords(2, 30); t = torch.rand(2, 20, 4)
    for temporal in ("gru", "ssm"):
        for attn in ("exact", "fast"):
            out = OmniSTScale(cfg, temporal=temporal, attention=attn)(f, c, t)
            assert out.shape == (2, 30, 7, 1), f"{temporal}+{attn} wrong shape {out.shape}"


def test_ssm_is_topology_invariant_shape():
    """SSM temporal block returns the same (B,T,N,d) for any N (per-node processing)."""
    ssm = BidirectionalSSM(d_model=32, d_state=8, n_layers=1)
    for N in (5, 20, 50):
        x = torch.randn(2, 15, N, 32)
        assert ssm(x).shape == (2, 15, N, 32)


def test_fast_attention_approximates_exact():
    """O(N.k) attention output is close to exact attention when they share weights (same math, only
    neighbour selection differs). Copy weights exact->fast and compare on the same input."""
    torch.manual_seed(0)
    d, H, k, N = 32, 4, 8, 60
    exact = InductiveGAT(d, H, k); fast = FastInductiveGAT(d, H, k)
    # share the learnable params so only neighbour SELECTION differs
    fast.q_proj.load_state_dict(exact.q_proj.state_dict())
    fast.k_proj.load_state_dict(exact.k_proj.state_dict())
    fast.v_proj.load_state_dict(exact.v_proj.state_dict())
    fast.out_proj.load_state_dict(exact.out_proj.state_dict())
    fast.dist_bias.load_state_dict(exact.dist_bias.state_dict())
    fast.norm.load_state_dict(exact.norm.state_dict())
    tokens = torch.randn(1, N, d); coords = _coords(1, N)
    with torch.no_grad():
        oe = exact(tokens, coords); of = fast(tokens, coords)
    cos = torch.nn.functional.cosine_similarity(oe.flatten(), of.flatten(), dim=0).item()
    assert cos > 0.95, f"fast attention should approximate exact (cosine {cos:.4f})"


def test_fast_attention_no_quadratic_blowup_large_n():
    """At larger N the fast path runs without forming an N^2 tensor (just a smoke that it completes)."""
    fast = FastInductiveGAT(d_model=32, n_heads=4, k_neighbors=8)
    tokens = torch.randn(1, 400, 32); coords = _coords(1, 400)
    out = fast(tokens, coords)
    assert out.shape == (1, 400, 32)
