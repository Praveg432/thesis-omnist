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

    def __init__(self, d_model: int, d_state: int = 16, mode: str = "sequential", chunk: int = 16):
        super().__init__()
        assert mode in ("sequential", "chunked")
        self.mode = mode          # "chunked" = exploratory X2 scan (see _forward_chunked); default unchanged
        self.chunk = chunk
        self.d_model = d_model
        self.d_state = d_state
        # per-(channel,state) log-decay (A), input/output maps (B, C), skip (D)
        self.A_log = nn.Parameter(torch.log(torch.linspace(0.5, 4.0, d_state)).repeat(d_model, 1))
        self.B = nn.Parameter(torch.randn(d_model, d_state) * 0.1)
        self.C = nn.Parameter(torch.randn(d_model, d_state) * 0.1)
        self.D = nn.Parameter(torch.ones(d_model))
        # selective timestep: dt depends on the input (the "selection" mechanism)
        self.dt_proj = nn.Linear(d_model, d_model)

    def _forward_chunked(self, x: torch.Tensor) -> torch.Tensor:
        """EXPLORATORY (plan item X2). Chunked closed-form scan. Within a chunk of length C,
            h_t = exp(L_t) * (h_0 + cumsum_s exp(-L_s) u_s),  L = cumsum(dt*A),  u = dt*B*x,
        evaluated with cumsum (parallel inside the chunk); Python loops over T/C chunks, not T steps.
        The per-step log-decay is clamped to >= -4 so exp(-L) stays finite in fp32 for C <= 16, which
        makes this NOT identical to the sequential scan under very strong decay.
        Measured outcome (see docs/CONSOLIDATED-FINDINGS.md, V4): relative L2 difference from the
        sequential scan about 6e-5 for T = 16 to 500, but max absolute difference up to 7.8e-3, and it
        is NOT faster than the BiGRU (1.77x slower forward+backward at T = 960 on MPS). It therefore
        does not meet the X2 acceptance criteria (equal within 1e-4; no slower than the GRU at
        T >= 240)."""
        B, T, D = x.shape
        S = self.d_state
        dt = F.softplus(self.dt_proj(x))                                      # (B,T,D)
        A = -torch.exp(self.A_log)                                            # (D,S)
        h = x.new_zeros(B, D, S)
        ys = []
        for s0 in range(0, T, self.chunk):
            xc = x[:, s0:s0 + self.chunk]; dtc = dt[:, s0:s0 + self.chunk]    # (B,C,D)
            la = (dtc.unsqueeze(-1) * A.view(1, 1, D, S)).clamp(min=-4.0)     # (B,C,D,S) log decay
            u = dtc.unsqueeze(-1) * self.B.view(1, 1, D, S) * xc.unsqueeze(-1)
            L = torch.cumsum(la, dim=1)
            hs = torch.exp(L) * (h.unsqueeze(1) + torch.cumsum(torch.exp(-L) * u, dim=1))
            h = hs[:, -1]
            ys.append((hs * self.C.view(1, 1, D, S)).sum(-1) + self.D.view(1, 1, D) * xc)
        return torch.cat(ys, dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, T, d) -> (B, T, d). Sequential scan (O(T) steps, not parallel); state (B, d, d_state)."""
        if self.mode == "chunked":
            return self._forward_chunked(x)
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

    def __init__(self, d_model: int, d_state: int = 16, n_layers: int = 1, dropout: float = 0.1,
                 mode: str = "sequential"):
        super().__init__()
        self.d_model = d_model
        self.layers = nn.ModuleList()
        for _ in range(n_layers):
            self.layers.append(nn.ModuleDict({
                "fwd": DiagonalSSM(d_model, d_state, mode=mode),
                "bwd": DiagonalSSM(d_model, d_state, mode=mode),
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
