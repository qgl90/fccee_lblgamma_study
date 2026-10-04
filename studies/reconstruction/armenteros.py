"""Reconstructed Armenteros-Podolanski variables for a fitted two-track V0.

alpha is (p_L(positive) - p_L(negative)) / (p_L(positive) + p_L(negative));
q_t is the momentum of either daughter transverse to the V0 flight direction
in GeV. Here ``proton`` and ``pion`` denote the selected mass hypothesis,
and ``lb_sign`` identifies whether the proton-hypothesis track is positive.
No generator information enters either variable or the optional cut.
"""

import numpy as np


PROTON_MASS_GEV = 0.9382720813
PION_MASS_GEV = 0.13957039


def from_three_momenta(proton, pion, lb_sign):
    """Return (charge-signed alpha, q_t) from arrays of fitted 3-vectors."""
    proton = np.asarray(proton, dtype=np.float64)
    pion = np.asarray(pion, dtype=np.float64)
    sign = np.asarray(lb_sign, dtype=np.float64)
    if proton.shape != pion.shape or proton.shape[-1] != 3:
        raise ValueError("Daughter momenta must have matching shape (..., 3)")
    parent = proton + pion
    p2 = np.sum(parent*parent, axis=-1)
    p = np.sqrt(p2)
    alpha = np.divide(sign*(np.sum(proton*proton, axis=-1)-
                            np.sum(pion*pion, axis=-1)), p2,
                      out=np.full_like(p, np.nan), where=p2 > 0)
    qt = np.divide(np.linalg.norm(np.cross(proton, pion), axis=-1), p,
                   out=np.full_like(p, np.nan), where=p > 0)
    return alpha, qt


def from_fitted_tuple(frame):
    """Recover the same variables from saved p, eta and fitted p-pi mass.

    The 3-vector opening angle follows from the invariant mass under the
    proton/pion hypotheses. This supports old tuples without saved px/py/pz.
    """
    pp = frame.proton_pt.to_numpy(dtype=np.float64) * np.cosh(
        frame.proton_eta.to_numpy(dtype=np.float64))
    pi = frame.pion_pt.to_numpy(dtype=np.float64) * np.cosh(
        frame.pion_eta.to_numpy(dtype=np.float64))
    ep = np.hypot(pp, PROTON_MASS_GEV)
    epi = np.hypot(pi, PION_MASS_GEV)
    pair_mass = frame.lambda_mass.to_numpy(dtype=np.float64)
    p2 = (ep+epi)**2-pair_mass**2
    # p_proton^2 - p_pion^2 = (p_proton-p_pion) dot p_V0.
    alpha = np.divide(frame.lb_sign.to_numpy(dtype=np.float64)*(pp**2-pi**2), p2,
                      out=np.full_like(pp, np.nan), where=p2 > 0)
    dot = ep*epi - (pair_mass**2-PROTON_MASS_GEV**2-PION_MASS_GEV**2)/2
    cross2 = np.maximum(pp**2*pi**2-dot**2, 0)
    qt = np.divide(np.sqrt(cross2), np.sqrt(np.maximum(p2, 0)),
                   out=np.full_like(pp, np.nan), where=p2 > 0)
    return alpha, qt


def passes(alpha, qt, *, max_qt_gev=None, min_abs_alpha=None):
    """Optional rectangular Armenteros selection; undefined values fail."""
    alpha = np.asarray(alpha)
    qt = np.asarray(qt)
    keep = np.isfinite(alpha) & np.isfinite(qt)
    if max_qt_gev is not None:
        keep &= qt <= max_qt_gev
    if min_abs_alpha is not None:
        keep &= np.abs(alpha) >= min_abs_alpha
    return keep


def passes_veto_box(alpha, qt, *, abs_alpha_min, abs_alpha_max,
                    qt_min_gev, qt_max_gev):
    """Keep candidates outside a rectangular K_S0-like Armenteros region."""
    alpha = np.asarray(alpha)
    qt = np.asarray(qt)
    valid = np.isfinite(alpha) & np.isfinite(qt)
    inside = ((np.abs(alpha) >= abs_alpha_min) &
              (np.abs(alpha) <= abs_alpha_max) &
              (qt >= qt_min_gev) & (qt <= qt_max_gev))
    return valid & ~inside
