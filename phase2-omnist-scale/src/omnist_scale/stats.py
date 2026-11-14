"""Small statistics helpers for the Phase 2 gates (pure functions, no I/O)."""
from __future__ import annotations

import numpy as np
from scipy import stats as ss


def mean_ci(values, level: float = 0.95) -> dict:
    """Mean with a two-sided t confidence interval. Needs at least 2 values for an interval."""
    v = np.asarray([x for x in values if x == x], dtype=float)
    n = len(v)
    if n == 0:
        return {"mean": None, "ci": [None, None], "n": 0}
    if n == 1:
        return {"mean": round(float(v[0]), 4), "ci": [None, None], "n": 1}
    m = float(v.mean())
    half = float(ss.t.ppf(0.5 + level / 2.0, n - 1)) * float(v.std(ddof=1)) / np.sqrt(n)
    return {"mean": round(m, 4), "ci": [round(m - half, 4), round(m + half, 4)], "n": n}


def paired_equivalence(diffs, margin: float, level: float = 0.90) -> dict:
    """Equivalence of two methods from PAIRED differences (method - baseline).

    The methods are declared equivalent within +/- margin when the two-sided `level` confidence
    interval of the mean difference lies strictly inside (-margin, +margin). With level = 0.90 this
    is the two one-sided tests (TOST) procedure at alpha = 0.05.

    Returns verdict "equivalent", "worse" (interval entirely above +margin, i.e. the method is
    worse by more than the margin when diffs are errors), or "inconclusive" (interval straddles a
    margin: more paired observations are needed). Fewer than 2 pairs is always "inconclusive".
    """
    d = np.asarray(diffs, dtype=float)
    n = len(d)
    if margin <= 0:
        raise ValueError(f"margin must be positive, got {margin}")
    if n < 2:
        return {"verdict": "inconclusive", "n": n, "margin": margin,
                "reason": "need at least 2 paired observations"}
    m = float(d.mean())
    half = float(ss.t.ppf(0.5 + level / 2.0, n - 1)) * float(d.std(ddof=1)) / np.sqrt(n)
    lo, hi = m - half, m + half
    if lo > -margin and hi < margin:
        verdict = "equivalent"
    elif lo > margin:
        verdict = "worse"
    else:
        verdict = "inconclusive"
    return {"verdict": verdict, "n": n, "margin": round(float(margin), 6), "level": level,
            "mean_diff": round(m, 6), "ci": [round(lo, 6), round(hi, 6)]}
