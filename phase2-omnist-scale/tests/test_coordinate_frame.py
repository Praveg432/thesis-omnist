"""The Phase 2 copy of the tokenizer must keep the same coordinate-frame behaviour as Phase 1."""
import numpy as np
import torch

from omnist_scale.omnist.cc_hash import SpatialMLP, training_coordinate_frame
from omnist_scale.omnist.omnist_model import ModelConfig
from omnist_scale.scalable_model import OmniSTScale

WEATHER_LIKE = np.array([[32.6, -119.7], [38.0, -115.0], [44.5, -110.7], [40.1, -112.2]])


def test_shouldReproduceLegacyFormulaWhenUsingDefaultFrame():
    torch.manual_seed(0)
    mlp = SpatialMLP(d_model=16)
    coords = torch.tensor([[28.5, 77.0], [28.8, 77.3]])
    legacy_input = torch.stack([(coords[:, 0] - 28.6) / 0.2, (coords[:, 1] - 77.1) / 0.3], dim=-1)
    assert torch.allclose(mlp(coords), mlp.mlp(legacy_input), atol=1e-6)


def test_shouldPassFrameToScalableModelTokenizer():
    center, scale = training_coordinate_frame(WEATHER_LIKE)
    model = OmniSTScale(ModelConfig(n_features=1, horizon=4, d_model=16, coord_center=center, coord_scale=scale))
    assert torch.allclose(model.tokenizer.spatial_emb.center, torch.tensor(center, dtype=torch.float32))
