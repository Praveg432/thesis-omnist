"""OmniST-Scale model: the SAME OmniST architecture with swappable scalable components.

Keeps the ported OmniST baseline (omnist/omnist_model.py) untouched as the reference, and assembles a
variant where the temporal backbone and/or spatial attention can be swapped:
  temporal = "gru"  (baseline BiGRU)  | "ssm"  (BidirectionalSSM, this project)
  attention = "exact" (baseline GAT)  | "fast" (FastInductiveGAT O(N·k), this project)

Everything else (coordinate tokenizer, prediction head, forward contract) is identical to OmniST, so
accuracy/coverage differences are attributable to the swapped component -- the clean ablation V1/V4
need.
"""
from __future__ import annotations
import torch
import torch.nn as nn

from .omnist.cc_hash import CCHashTokenizer
from .omnist.inductive_gat import InductiveGAT
from .omnist.temporal import BidirectionalGRU
from .omnist.omnist_model import ModelConfig
from .ssm_temporal import BidirectionalSSM
from .fast_attention import FastInductiveGAT


class OmniSTScale(nn.Module):
    def __init__(self, config: ModelConfig, temporal: str = "gru", attention: str = "exact",
                 d_state: int = 16):
        super().__init__()
        self.config = config
        self.temporal_kind = temporal
        self.attention_kind = attention

        self.tokenizer = CCHashTokenizer(
            n_features=config.n_features, d_model=config.d_model,
            spatial_hidden=config.spatial_hidden, n_temporal_harmonics=config.n_temporal_harmonics)

        if attention == "exact":
            self.gat_layers = nn.ModuleList([
                InductiveGAT(config.d_model, config.n_gat_heads, config.k_neighbors, config.dropout)
                for _ in range(config.n_gat_layers)])
        elif attention == "fast":
            self.gat_layers = nn.ModuleList([
                FastInductiveGAT(config.d_model, config.n_gat_heads, config.k_neighbors, config.dropout)
                for _ in range(config.n_gat_layers)])
        else:
            raise ValueError(f"attention must be 'exact' or 'fast', got {attention}")

        if temporal == "gru":
            self.temporal = BidirectionalGRU(config.d_model, config.n_temporal_layers, config.temporal_dropout)
        elif temporal == "ssm":
            self.temporal = BidirectionalSSM(config.d_model, d_state=d_state,
                                             n_layers=config.n_temporal_layers, dropout=config.temporal_dropout)
        else:
            raise ValueError(f"temporal must be 'gru' or 'ssm', got {temporal}")

        self.prediction_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_model), nn.GELU(), nn.Dropout(config.dropout),
            nn.Linear(config.d_model, config.horizon * config.n_features))

    def forward(self, features: torch.Tensor, coords: torch.Tensor, timestamps: torch.Tensor):
        B, T, N, F = features.shape
        tokens = self.tokenizer(features, coords, timestamps)             # (B,T,N,d)
        for gat in self.gat_layers:
            tokens = torch.stack([gat(tokens[:, t], coords) for t in range(T)], dim=1)
        tokens = self.temporal(tokens)                                    # (B,T,N,d)
        out = self.prediction_head(tokens[:, -1])                         # (B,N,H*F)
        return out.view(B, N, self.config.horizon, self.config.n_features)

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
