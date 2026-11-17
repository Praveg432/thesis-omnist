"""Tests for the coordinate frame of the spatial embedding (the Delhi-constants defect)."""
import numpy as np
import pytest
import torch

from src.cc_hash import SpatialMLP, training_coordinate_frame
from src.omnist_model import ModelConfig, OmniST

WEATHER_LIKE = np.array([[32.6, -119.7], [38.0, -115.0], [44.5, -110.7], [40.1, -112.2]])


def test_shouldReproduceLegacyFormulaWhenUsingDefaultFrame():
    torch.manual_seed(0)
    mlp = SpatialMLP(d_model=16)
    coords = torch.tensor([[28.5, 77.0], [28.8, 77.3]])
    legacy_input = torch.stack([(coords[:, 0] - 28.6) / 0.2, (coords[:, 1] - 77.1) / 0.3], dim=-1)
    assert torch.allclose(mlp(coords), mlp.mlp(legacy_input), atol=1e-6)


def test_shouldKeepInputsSmallWhenFrameComesFromNonDelhiTrainingStations():
    center, scale = training_coordinate_frame(WEATHER_LIKE)
    normalised = (WEATHER_LIKE - np.array(center)) / np.array(scale)
    assert np.abs(normalised).max() < 3.0
    legacy = (WEATHER_LIKE - np.array([28.6, 77.1])) / np.array([0.2, 0.3])
    assert np.abs(legacy).max() > 100.0  # documents the defect: the legacy frame is far out of range


def test_shouldGiveSameEmbeddingWhenAllCoordinatesShiftAndFrameIsRecomputed():
    torch.manual_seed(1)
    shift = np.array([5.0, -40.0])
    c1, s1 = training_coordinate_frame(WEATHER_LIKE)
    c2, s2 = training_coordinate_frame(WEATHER_LIKE + shift)
    torch.manual_seed(2)
    a = SpatialMLP(8, center=c1, scale=s1)
    torch.manual_seed(2)
    b = SpatialMLP(8, center=c2, scale=s2)
    out_a = a(torch.tensor(WEATHER_LIKE, dtype=torch.float32))
    out_b = b(torch.tensor(WEATHER_LIKE + shift, dtype=torch.float32))
    assert torch.allclose(out_a, out_b, atol=1e-3)


def test_shouldSaveAndRestoreFrameWithStateDict():
    center, scale = training_coordinate_frame(WEATHER_LIKE)
    source = SpatialMLP(8, center=center, scale=scale)
    target = SpatialMLP(8)
    target.load_state_dict(source.state_dict())
    assert torch.allclose(target.center, torch.tensor(center, dtype=torch.float32))
    assert torch.allclose(target.scale, torch.tensor(scale, dtype=torch.float32))


def test_shouldPassFrameFromModelConfigToTokenizer():
    center, scale = training_coordinate_frame(WEATHER_LIKE)
    model = OmniST(ModelConfig(n_features=1, horizon=4, d_model=16, coord_center=center, coord_scale=scale))
    assert torch.allclose(model.tokenizer.spatial_emb.center, torch.tensor(center, dtype=torch.float32))


def test_shouldReturnLastObservedValueWhenResidualHeadIsZero():
    torch.manual_seed(0)
    model = OmniST(ModelConfig(n_features=1, horizon=3, d_model=16, residual_to_last=True))
    for p in model.prediction_head.parameters():
        torch.nn.init.zeros_(p)
    feats = torch.randn(2, 6, 4, 1)
    coords = torch.tensor(WEATHER_LIKE, dtype=torch.float32).unsqueeze(0).expand(2, -1, -1)
    out = model.eval()(feats, coords, torch.rand(2, 6, 4))
    assert torch.allclose(out, feats[:, -1].unsqueeze(2).expand(-1, -1, 3, -1))


def test_shouldRejectFrameFromFewerThanTwoTrainingStations():
    with pytest.raises(ValueError, match="at least two training stations"):
        training_coordinate_frame(np.array([[28.6, 77.1]]))


def test_shouldRejectNonPositiveScale():
    with pytest.raises(ValueError, match="positive scales"):
        SpatialMLP(8, center=(0.0, 0.0), scale=(1.0, 0.0))
