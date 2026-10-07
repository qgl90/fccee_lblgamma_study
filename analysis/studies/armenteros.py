"""Lab-frame Armenteros-Podolanski variables for Lambda -> p pi.

No boost to the Lambda or Lb rest frame is required. The ellipse loci depend
only on the daughter masses and the V0 flight direction in the lab. Use this
after candidate building, never with truth fields as an input selection when
estimating efficiency.

Starting window (GeV/c), to be compared to the baseline on the same events:
    Lambda0 -> p pi- : alpha > 0.2 and qT < 0.12
    KS0 control      : |alpha| < 0.2 and 0.12 < qT < 0.22
Proton is the positive track for Lambda0. Mirror the alpha cut for anti-Lambda.
"""

from __future__ import annotations

import numpy as np

LAMBDA_ALPHA_MIN = 0.2
LAMBDA_QT_MAX = 0.12  # GeV/c; kinematic ceiling is ~0.101
KS_ALPHA_ABS_MAX = 0.2
KS_QT_MIN = 0.12


def armenteros_variables(p_pos, p_neg):
    """Return lab-frame (alpha, qT) for positive and negative daughters.

    p_pos, p_neg : shape (3,) or (N, 3), momenta in GeV/c.
    For Lambda0 -> p pi- pass the proton as p_pos.
    """
    p_pos = np.atleast_2d(np.asarray(p_pos, dtype=float))
    p_neg = np.atleast_2d(np.asarray(p_neg, dtype=float))
    if p_pos.shape[-1] != 3 or p_neg.shape != p_pos.shape:
        raise ValueError("p_pos and p_neg must have shape (3,) or (N, 3) and match")

    p_V = p_pos + p_neg
    p_V_mag = np.linalg.norm(p_V, axis=1, keepdims=True)
    hat = np.divide(p_V, p_V_mag, out=np.zeros_like(p_V), where=p_V_mag > 0)

    pL_pos = np.sum(p_pos * hat, axis=1)
    pL_neg = np.sum(p_neg * hat, axis=1)
    denom = pL_pos + pL_neg
    alpha = np.divide(
        pL_pos - pL_neg,
        denom,
        out=np.full(denom.shape, np.nan),
        where=np.abs(denom) > 0,
    )
    pT_vec = p_pos - pL_pos[:, None] * hat
    qT = np.linalg.norm(pT_vec, axis=1)
    qT = np.where(p_V_mag.ravel() > 0, qT, np.nan)
    return alpha, qT


def select_lambda(p_proton, p_pion, alpha_min=LAMBDA_ALPHA_MIN, qT_max=LAMBDA_QT_MAX):
    """Mask for Lambda0 -> p pi-. Vetoes the KS ellipse. Lab frame only."""
    alpha, qT = armenteros_variables(p_proton, p_pion)
    return (alpha > alpha_min) & (qT < qT_max) & np.isfinite(alpha) & np.isfinite(qT)


def select_antilambda(p_antiproton, p_pion, alpha_max=-LAMBDA_ALPHA_MIN, qT_max=LAMBDA_QT_MAX):
    """Mask for anti-Lambda0 -> anti-p pi+. Pass the negative track as p_pos argument order flipped:
    call armenteros with (pi+, anti-p) so alpha is negative for signal, or use this wrapper
    which expects p_neg = antiproton and p_pos = pion.
    """
    alpha, qT = armenteros_variables(p_pion, p_antiproton)
    return (alpha < alpha_max) & (qT < qT_max) & np.isfinite(alpha) & np.isfinite(qT)


def select_ks(p_pos, p_neg, alpha_abs_max=KS_ALPHA_ABS_MAX, qT_min=KS_QT_MIN, qT_max=0.22):
    """Mask for the KS0 -> pi+ pi- band, as a control sample."""
    alpha, qT = armenteros_variables(p_pos, p_neg)
    return (
        (np.abs(alpha) < alpha_abs_max)
        & (qT > qT_min)
        & (qT < qT_max)
        & np.isfinite(alpha)
        & np.isfinite(qT)
    )


def study_selection(p_proton, p_pion, alpha_min=LAMBDA_ALPHA_MIN, qT_max=LAMBDA_QT_MAX):
    """Counts for a selection study. Does not drop rows; mask is returned.

    Compare m(p pi) before and after the mask on the same candidates.
    Keep event_entry and candidate_slot if those columns exist upstream.
    """
    alpha, qT = armenteros_variables(p_proton, p_pion)
    finite = np.isfinite(alpha) & np.isfinite(qT)
    mask = (alpha > alpha_min) & (qT < qT_max) & finite
    n = int(finite.sum())
    n_pass = int(mask.sum())
    return {
        "n_input": int(len(alpha)),
        "n_finite": n,
        "n_pass": n_pass,
        "fraction_pass": (n_pass / n) if n else float("nan"),
        "alpha": alpha,
        "qT": qT,
        "mask": mask,
        "alpha_min": alpha_min,
        "qT_max": qT_max,
    }
