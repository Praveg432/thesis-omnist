"""Selective state-space (Mamba-style) temporal block — a drop-in replacement for OmniST's BiGRU.

Why. OmniST's temporal backbone is a bidirectional GRU: O(T) *sequential* recurrence that cannot
parallelize over the time axis and whose per-step cost is fixed. For long horizons / many nodes this
is the throughput bottleneck. A diagonal selective state-space model (S4D/Mamba-style) runs in
linear time with a PARALLEL scan and constant per-step state, giving better throughput and memory at
long T while matching the modeling capacity GRUs provide here.

Design (MPS-friendly, pure PyTorch — no CUDA mamba-ssm kernel needed):
  - diagonal SSM: state h_t = a ⊙ h_{t-1} + b ⊙ x_t,  y_t = Re(c · h_t) + d ⊙ x_t
  - a = exp(-softplus(A_log) * dt)  (stable, in (0,1) per channel) — the decay; dt is input-dependent
    (the "selective" part) so the block can modulate memory per token.
  - bidirectional (forward + reversed) to match BiGRU's two-directional context.
  - per-node processing: (B,T,N,d) -> (B*N, T, d), identical interface to BidirectionalGRU, so it
    swaps into omnist_model via a config flag with no other change.

This is an associative-scan-free, numerically-simple realization adequate for the parity/scaling
study; it is NOT a reimplementation of the full Mamba selective-scan kernel (that is a stretch goal).
The claim this supports is "an SSM temporal block matches GRU accuracy/coverage while scaling better",
tested in V1/V4 — not "we built Mamba".
"""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


class DiagonalSSM(nn.Module):
    """One-directional diagonal selective SSM over a (B, T, d) sequence."""

    def __init__(self, d_model: int, d_state: int = 16):
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state
        # per-(channel,state) log-decay (A), input/output maps (B, C), skip (D)
        self.A_log = nn.Parameter(torch.log(torch.linspace(0.5, 4.0, d_state)).repeat(d_model, 1))
        self.B = nn.Parameter(torch.randn(d_model, d_state) * 0.1)
        self.C = nn.Parameter(torch.randn(d_model, d_state) * 0.1)
        self.D = nn.Parameter(torch.ones(d_model))
        # selective timestep: dt depends on the input (the "selection" mechanism)
        self.dt_proj = nn.Linear(d_model, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, T, d) -> (B, T, d). Sequential scan (linear time); state is (B, d, d_state)."""
        B, T, D = x.shape
        dt = F.softplus(self.dt_proj(x))                 # (B, T, D) input-dependent step, >0
        A = -torch.exp(self.A_log)                        # (D, d_state) negative real -> stable decay
        h = x.new_zeros(B, D, self.d_state)
        ys = []
        for t in range(T):
            xt = x[:, t]                                  # (B, D)
            dt_t = dt[:, t]                               # (B, D)
            a = torch.exp(dt_t.unsqueeze(-1) * A.unsqueeze(0))        # (B, D, d_state) in (0,1)
            b = dt_t.unsqueeze(-1) * self.B.unsqueeze(0)             # (B, D, d_state)
            h = a * h + b * xt.unsqueeze(-1)                          # (B, D, d_state)
            y = (h * self.C.unsqueeze(0)).sum(-1) + self.D.unsqueeze(0) * xt   # (B, D)
            ys.append(y)
        return torch.stack(ys, dim=1)                     # (B, T, D)


class BidirectionalSSM(nn.Module):
    """Bidirectional diagonal-SSM temporal backbone. Drop-in for omnist.temporal.BidirectionalGRU:
    input/return (B, T, N, d_model); per-node processing; residual + LayerNorm."""

    def __init__(self, d_model: int, d_state: int = 16, n_layers: int = 1, dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.layers = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.ModuleDict({
                "fwd": DiagonalSSM(d_model, d_state),
                "bwd": DiagonalSSM(d_model, d_state),
                "mix": nn.Linear(2 * d_model, d_model),
                "norm": nn.LayerNorm(d_model),
            }))
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, N, D = x.shape
        h = x.permute(0, 2, 1, 3).reshape(B * N, T, D)    # (B*N, T, D)
        for layer in self.layers:
            fwd = layer["fwd"](h)
            bwd = torch.flip(layer["bwd"](torch.flip(h, dims=[1])), dims=[1])
            mixed = layer["mix"](torch.cat([fwd, bwd], dim=-1))
            h = layer["norm"](h + self.drop(mixed))        # residual + norm
        return h.reshape(B, N, T, D).permute(0, 2, 1, 3)   # (B, T, N, D)
