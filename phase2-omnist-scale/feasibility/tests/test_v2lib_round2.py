import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from v2lib import OmniSTv2, Variant, neighbours


def _setup(seed=0, B=2, W=8, N=12):
    g = torch.Generator().manual_seed(seed)
    x, tf = torch.randn(B, W, N, generator=g), torch.randn(B, W, 6, generator=g)
    xy = np.random.default_rng(seed).uniform(0, 10, size=(N, 2))
    idx, feat = neighbours(xy, np.arange(N), np.arange(N), 1.0)
    return x, torch.ones(B, N, dtype=torch.bool), tf, torch.as_tensor(idx)[None].expand(B, -1, -1), torch.as_tensor(feat)[None].expand(B, -1, -1, -1)


def test_default_attention_path_is_unchanged_from_round_one():
    """Round-1 results used attention with the distance bias; 'learned' must be that path."""
    assert Variant("v2", True).attention == "learned"


def test_mean_ablation_ignores_distances_and_query():
    torch.manual_seed(1)
    m = OmniSTv2(Variant("mean", True, attention="mean"), horizon=3)
    x, obs, tf, ni, nf = _setup()
    h = m.encode(x, obs, tf)
    a = m.spatial_context(h, ni, nf)
    b = m.spatial_context(h, ni, nf * 100.0)  # changing distances changes nothing
    assert torch.allclose(a, b)


def test_nobias_ablation_ignores_distances_but_learned_does_not():
    torch.manual_seed(2)
    nb = OmniSTv2(Variant("nb", True, attention="nobias"), horizon=3)
    torch.manual_seed(2)
    lb = OmniSTv2(Variant("lb", True, attention="learned"), horizon=3)
    x, obs, tf, ni, nf = _setup()
    h = nb.encode(x, obs, tf)
    assert torch.allclose(nb.spatial_context(h, ni, nf), nb.spatial_context(h, ni, nf * 3.0))
    assert not torch.allclose(lb.spatial_context(h, ni, nf), lb.spatial_context(h, ni, nf * 3.0))
