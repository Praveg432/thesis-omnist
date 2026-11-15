"""Split + Mondrian conformal utilities for NODE-exchangeable inductive calibration.

Protocol (the one under which the finite-sample guarantee actually applies to unseen nodes): nodes
are randomly partitioned into TRAIN / CALIBRATION / TEST. The model never sees calibration or test
nodes during training. At each forecast window, the conformal quantile is computed from the
calibration nodes' residuals and applied to the test nodes. Calibration and test nodes are
exchangeable (random node split), so per-window marginal coverage satisfies

    P(test node covered) ~ Beta(n_cal + 1 - l, l),   l = floor((n_cal + 1) * alpha)

(Vovk 2012; Angelopoulos & Bates 2023), with n_cal = number of calibration NODES.
"""
from __future__ import annotations
import numpy as np
from scipy import stats as ss


def split_qhat(resid: np.ndarray, alpha: float) -> float:
    n = len(resid)
    if n == 0:
        return float("inf")
    level = min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)
    return float(np.quantile(resid, level, method="higher"))


def beta_band(n_cal: int, alpha: float, confidence: float = 0.95):
    l = max(1, min(int(np.floor((n_cal + 1) * alpha)), n_cal))
    d = ss.beta(n_cal + 1 - l, l)
    return [float(d.ppf((1 - confidence) / 2)), float(d.ppf(1 - (1 - confidence) / 2))]


def group_ids(values: np.ndarray, edges: np.ndarray) -> np.ndarray:
    return np.searchsorted(edges, values, side="right")


def window_conformal(resid_cal, resid_test, alpha, grp_cal=None, grp_test=None, n_groups=3, min_group=10):
    """One window. Returns dict with marginal coverage/width, and (if groups given) per-group coverage
    for the GLOBAL quantile and for Mondrian (per-group) quantiles."""
    q = split_qhat(resid_cal, alpha)
    out = {"cov": float((resid_test <= q).mean()), "width": 2 * q}
    if grp_cal is not None:
        g_global, g_mond = {}, {}
        for g in range(n_groups):
            mt = grp_test == g
            if mt.sum() == 0:
                continue
            g_global[g] = float((resid_test[mt] <= q).mean())
            mc = grp_cal == g
            qg = split_qhat(resid_cal[mc], alpha) if mc.sum() >= min_group else q
            g_mond[g] = float((resid_test[mt] <= qg).mean())
        out["group_global"] = g_global
        out["group_mondrian"] = g_mond
    return out
