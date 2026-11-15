"""Tests for the code ported in the Nov-15 consolidation: chunked SSM scan (exploratory X2), the
conformal utilities, and the deployable-calibration helper used by V3."""
import os
import sys

import numpy as np
import torch

from omnist_scale.ssm_temporal import DiagonalSSM, BidirectionalSSM
from omnist_scale.conformal import split_qhat, beta_band, window_conformal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments"))


def test_chunked_scan_is_close_to_sequential_but_not_exact():
    """X2 audit: relative L2 difference is small, but the log-decay clamp means it is not identical.
    This test pins the measured behaviour so a future change that breaks it is noticed."""
    torch.manual_seed(0)
    seq = DiagonalSSM(32, 8, mode="sequential"); chk = DiagonalSSM(32, 8, mode="chunked")
    chk.load_state_dict(seq.state_dict())
    x = torch.randn(3, 70, 32)
    with torch.no_grad():
        a, b = seq(x), chk(x)
    rel = ((a - b).norm() / a.norm()).item()
    assert rel < 1e-3, f"chunked scan deviates from sequential: rel_l2={rel:.2e}"


def test_default_ssm_mode_is_sequential():
    assert DiagonalSSM(8, 4).mode == "sequential"
    out = BidirectionalSSM(8, 4, 1)(torch.randn(1, 5, 3, 8))
    assert out.shape == (1, 5, 3, 8)


def test_split_conformal_coverage_in_beta_band_over_random_node_splits():
    rng = np.random.default_rng(0)
    covs = []
    for _ in range(400):
        r = np.abs(rng.normal(size=220))
        q = split_qhat(r[:20], 0.10)
        covs.append((r[20:] <= q).mean())
    lo, hi = beta_band(20, 0.10)
    assert lo <= np.mean(covs) <= hi
    assert np.mean(covs) >= 0.89


def test_window_conformal_reports_group_coverages():
    rng = np.random.default_rng(1)
    rc, rt = np.abs(rng.normal(size=60)), np.abs(rng.normal(size=90))
    gc, gt = rng.integers(0, 3, 60), rng.integers(0, 3, 90)
    out = window_conformal(rc, rt, 0.10, gc, gt, min_group=5)
    assert 0.0 <= out["cov"] <= 1.0 and set(out["group_global"]) <= {0, 1, 2}


def test_deployable_calibration_valid_on_stationary_exchangeable_residuals():
    """With stationary, exchangeable residuals the chronological (past -> future) protocol must give
    coverage near the target; under non-stationarity it need not (that is the point of reporting it)."""
    from V3_coverage_at_scale import deployable_conformal
    rng = np.random.default_rng(2)
    nW, n_cal, n_te = 60, 40, 80
    covs = []
    for _ in range(40):
        Rc = np.abs(rng.normal(size=(nW, n_cal))); Rt = np.abs(rng.normal(size=(nW, n_te)))
        out = deployable_conformal(Rc, Rt, 0.10, rng.integers(0, 3, n_cal), rng.integers(0, 3, n_te))
        covs.append(out["cov"])
    assert 0.88 <= float(np.mean(covs)) <= 0.93


def test_deployable_calibration_undercovers_when_scale_grows_over_time():
    from V3_coverage_at_scale import deployable_conformal
    rng = np.random.default_rng(3)
    nW, n_cal, n_te = 60, 40, 80
    scale = np.linspace(1.0, 2.0, nW)[:, None]            # residual scale drifts upward
    Rc = np.abs(rng.normal(size=(nW, n_cal))) * scale; Rt = np.abs(rng.normal(size=(nW, n_te))) * scale
    out = deployable_conformal(Rc, Rt, 0.10, rng.integers(0, 3, n_cal), rng.integers(0, 3, n_te))
    assert out["cov"] < 0.88, "past-window calibration should under-cover when residual scale grows"
