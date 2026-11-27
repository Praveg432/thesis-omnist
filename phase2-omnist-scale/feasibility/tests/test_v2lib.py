import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest
import torch

from v2lib import OmniSTv2, Variant, neighbours, station_split


def _inputs(B=2, W=10, N=12, seed=0):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(B, W, N, generator=g), torch.ones(B, N, dtype=torch.bool), torch.randn(B, W, 6, generator=g)


def _graph(N=12, B=2, k=8):
    xy = np.random.default_rng(0).uniform(0, 10, size=(N, 2))
    idx, feat = neighbours(xy, np.arange(N), np.arange(N), 1.0, k=k)
    return torch.as_tensor(idx)[None].expand(B, -1, -1), torch.as_tensor(feat)[None].expand(B, -1, -1, -1)


def test_zero_gate_makes_v2_identical_to_the_shared_gru_at_initialisation():
    torch.manual_seed(1)
    gru = OmniSTv2(Variant("gru", spatial=False), horizon=4)
    torch.manual_seed(1)
    v2 = OmniSTv2(Variant("v2", spatial=True), horizon=4)
    v2.inp.load_state_dict(gru.inp.state_dict()); v2.gru.load_state_dict(gru.gru.state_dict()); v2.head.load_state_dict(gru.head.state_dict())
    x, obs, tf = _inputs()
    ni, nf = _graph()
    assert torch.allclose(gru(x, obs, tf)[0], v2(x, obs, tf, ni, nf)[0], atol=1e-6)


def test_a_masked_station_forecast_does_not_depend_on_its_own_history():
    torch.manual_seed(2)
    v2 = OmniSTv2(Variant("v2", spatial=True), horizon=4)
    with torch.no_grad():
        v2.gate.fill_(1.0)
    x, obs, tf = _inputs()
    obs[:, 3] = False
    ni, nf = _graph()
    a = v2(x, obs, tf, ni, nf)[0][:, 3]
    x2 = x.clone(); x2[:, :, 3] += 100.0
    assert torch.allclose(a, v2(x2, obs, tf, ni, nf)[0][:, 3], atol=1e-5)


def test_neighbours_never_include_the_target_and_come_from_the_pool():
    xy = np.random.default_rng(3).uniform(0, 10, size=(30, 2))
    pool = np.arange(0, 30, 2)
    targets = np.arange(30)
    idx, feat = neighbours(xy, targets, pool, 1.0, k=8)
    assert all(t not in row for t, row in zip(targets, idx))
    assert set(idx.ravel()) <= set(pool)
    assert np.allclose(feat[..., 3], np.log1p(feat[..., 2]))


def test_relative_features_are_translation_invariant():
    xy = np.random.default_rng(4).uniform(0, 10, size=(20, 2))
    a = neighbours(xy, np.arange(20), np.arange(20), 1.0)[1]
    b = neighbours(xy + 500.0, np.arange(20), np.arange(20), 1.0)[1]
    assert np.allclose(a, b, atol=1e-5)


def test_residual_variant_refuses_day_zero_stations():
    v = OmniSTv2(Variant("res", spatial=False, residual=True), horizon=4)
    v.period_steps = 6
    x, obs, tf = _inputs(W=10)
    obs[:, 0] = False
    with pytest.raises(ValueError, match="Day 0"):
        v(x, obs, tf)


def test_station_split_matches_the_thesis_partition():
    train, cal, test = station_split(37, 0, 8, 8)
    perm = np.random.default_rng(1000).permutation(37)
    assert list(test) == sorted(perm[:8]) and list(cal) == sorted(perm[8:16])
    assert len(train) == 21 and not (set(train) & set(cal) | set(train) & set(test))
