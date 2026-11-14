"""Regression tests for defects found in review: neighbour-cache key collision, unbounded cache,
neighbour selection correctness, and the paired equivalence helper."""
import numpy as np
import pytest
import torch

from omnist_scale.fast_attention import FastInductiveGAT, knn_indices_ckdtree
from omnist_scale.stats import mean_ci, paired_equivalence


def _swapped_layouts():
    """Two different 8-sensor layouts with identical shape, coordinate sum and standard deviation
    (two nodes exchange their latitudes). Dyadic values keep the float sums exact."""
    a = torch.tensor([[[0.0, 0.0], [0.0, 0.125], [0.0, 0.25], [4.0, 4.0],
                       [4.0, 4.125], [4.0, 4.25], [8.0, 0.0], [8.0, 8.0]]])
    b = a.clone()
    b[0, 0, 0], b[0, 3, 0] = a[0, 3, 0].item(), a[0, 0, 0].item()
    return a, b


def test_cache_does_not_confuse_layouts_with_equal_sum_and_std():
    a, b = _swapped_layouts()
    assert float(a.sum()) == float(b.sum()) and float(a.std()) == float(b.std())
    layer = FastInductiveGAT(d_model=16, n_heads=2, k_neighbors=3)
    idx_a, _ = layer._knn(a, 3)
    idx_b, _ = layer._knn(b, 3)
    assert torch.equal(idx_a, knn_indices_ckdtree(a, 3))
    assert torch.equal(idx_b, knn_indices_ckdtree(b, 3))
    assert not torch.equal(idx_a, idx_b), "the two layouts must have different neighbours"


def test_cache_reuses_entry_for_identical_coordinates():
    a, _ = _swapped_layouts()
    layer = FastInductiveGAT(d_model=16, n_heads=2, k_neighbors=3)
    first = layer._knn(a, 3)
    second = layer._knn(a.clone(), 3)
    assert first[0] is second[0], "identical coordinates should hit the cache"


def test_cache_is_bounded_and_evicts_least_recently_used():
    layer = FastInductiveGAT(d_model=16, n_heads=2, k_neighbors=3, cache_size=3)
    gen = torch.Generator().manual_seed(0)
    layouts = [torch.rand(1, 10, 2, generator=gen) for _ in range(5)]
    for c in layouts:
        layer._knn(c, 3)
    assert len(layer._cache) == 3
    first_key = layer._coords_key(layouts[0], 3)
    assert first_key not in layer._cache, "oldest entry should have been evicted"


def _brute_force_knn(coords: np.ndarray, k: int) -> np.ndarray:
    lat0 = np.radians(coords[:, 0].mean())
    xy = np.stack([np.radians(coords[:, 1]) * np.cos(lat0), np.radians(coords[:, 0])], axis=1)
    d = np.linalg.norm(xy[:, None] - xy[None], axis=-1)
    np.fill_diagonal(d, np.inf)
    return np.argsort(d, axis=1)[:, :k]


def test_vectorised_neighbour_selection_matches_brute_force():
    gen = torch.Generator().manual_seed(1)
    coords = torch.rand(2, 60, 2, generator=gen) * torch.tensor([0.4, 0.6]) + torch.tensor([28.4, 76.8])
    got = knn_indices_ckdtree(coords, 6).numpy()
    for b in range(2):
        want = _brute_force_knn(coords[b].numpy().astype(np.float64), 6)
        assert (np.sort(got[b], axis=1) == np.sort(want, axis=1)).all()
        assert not (got[b] == np.arange(60)[:, None]).any(), "a node must not be its own neighbour"


def test_neighbour_selection_handles_duplicate_locations():
    coords = torch.tensor([[[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [2.0, 2.0], [3.0, 3.0], [4.0, 4.0]]])
    idx = knn_indices_ckdtree(coords, 3)[0].numpy()
    assert idx.shape == (6, 3)
    assert not (idx == np.arange(6)[:, None]).any()


def test_paired_equivalence_declares_equivalent_for_tiny_consistent_differences():
    res = paired_equivalence([0.001, -0.002, 0.0005, 0.001, -0.001, 0.0], margin=0.03)
    assert res["verdict"] == "equivalent"


def test_paired_equivalence_flags_above_when_interval_exceeds_margin():
    res = paired_equivalence([0.10, 0.11, 0.09, 0.12, 0.10], margin=0.03)
    assert res["verdict"] == "above"


def test_paired_equivalence_is_inconclusive_when_noisy_or_too_few_pairs():
    assert paired_equivalence([0.0, 0.08, -0.07, 0.05], margin=0.03)["verdict"] == "inconclusive"
    assert paired_equivalence([0.0], margin=0.03)["verdict"] == "inconclusive"


def test_paired_equivalence_rejects_nonpositive_margin():
    with pytest.raises(ValueError):
        paired_equivalence([0.0, 0.1], margin=0.0)


def test_paired_equivalence_flags_a_large_drop_not_just_a_large_rise():
    """A coverage drop of 0.1 against a 0.03 margin must be reported as 'below', not inconclusive."""
    res = paired_equivalence([-0.10, -0.11, -0.09, -0.12, -0.10], margin=0.03)
    assert res["verdict"] == "below"


def test_v1b_gate_fails_when_coverage_collapses():
    from omnist_scale.stats import parity_verdict
    mae = paired_equivalence([0.1, -0.2, 0.0, 0.1], margin=5.0)       # accuracy equivalent
    cov = paired_equivalence([-0.10, -0.11, -0.09, -0.12], margin=0.03)
    assert parity_verdict(mae, cov) == "NO-GO"


def test_v1b_gate_accepts_equivalent_or_better_accuracy_with_equivalent_coverage():
    from omnist_scale.stats import parity_verdict
    cov = paired_equivalence([0.001, -0.002, 0.0005, 0.001], margin=0.03)
    equivalent = paired_equivalence([0.1, -0.2, 0.0, 0.1], margin=5.0)
    better = paired_equivalence([-9.0, -9.5, -8.8, -9.2], margin=5.0)
    assert parity_verdict(equivalent, cov) == "GO"
    assert parity_verdict(better, cov) == "GO", "clearly lower error is non-inferior"


def test_v1b_gate_is_inconclusive_when_either_test_is():
    from omnist_scale.stats import parity_verdict
    cov = paired_equivalence([0.001, -0.002, 0.0005, 0.001], margin=0.03)
    noisy = paired_equivalence([3.0, -4.0, 6.0, -5.0], margin=5.0)
    assert parity_verdict(noisy, cov) == "INCONCLUSIVE"


def test_mean_ci_basic():
    res = mean_ci([1.0, 2.0, 3.0])
    assert res["mean"] == 2.0 and res["n"] == 3 and res["ci"][0] < 2.0 < res["ci"][1]
