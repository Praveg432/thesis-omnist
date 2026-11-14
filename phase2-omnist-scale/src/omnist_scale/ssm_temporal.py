"""Selective state-space (Mamba-style) temporal block — a drop-in replacement for OmniST's BiGRU.

Purpose. OmniST's temporal backbone is a bidirectional GRU. A diagonal state-space model (S4D-style,
with an input-dependent step size) is a candidate replacement that could be evaluated for accuracy
parity and, once a parallel scan is implemented, for time-parallel throughput.

Current implementation (what the code actually does):
  - diagonal SSM: state h_t = a ⊙ h_{t-1} + b ⊙ x_t,  y_t = sum(c ⊙ h_t) + d ⊙ x_t
  - a = exp(dt * A) with A < 0, so a is in (0,1); dt = softplus(Linear(x_t)) is input-dependent.
    Only dt is input-dependent. B and C are fixed parameters, so this is a partial version of
    Mamba's selection mechanism, not the full one.
  - the recurrence is evaluated by a SEQUENTIAL Python loop over t. It is NOT parallel over time.
    Measured on an M4 Pro (B=4, N=37, d=64, 2 layers): about 2x slower than the BiGRU at T = 60, 240
    and 960, with the same linear growth in T. No throughput advantage over the GRU exists yet.
  - bidirectional (forward + reversed) to match BiGRU's two-directional context.
  - per-node processing: (B,T,N,d) -> (B*N, T, d), identical interface to BidirectionalGRU, so it
    swaps into omnist_model via a config flag with no other change.

Planned (Semester 4): replace the loop with a parallel prefix scan (the recurrence h_t = a_t h_{t-1}
+ b_t is associative), verify numerical equality with this sequential version, and measure
throughput and memory against the GRU. Until that is done, the only supportable claim is accuracy
parity, not speed. This is NOT a reimplementation of Mamba's selective-scan kernel.
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
        """x: (B, T, d) -> (B, T, d). Sequential scan (O(T) steps, not parallel); state (B, d, d_state)."""
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
