"""Offline effective calorimeter geometry and hypothetical photon pointing.

Lengths are mm; angles passed to smear_direction are radians. MC truth only
defines the synthetic measurement. Displacements use that measurement and PV.
"""

from dataclasses import dataclass
import numpy as np


def unit(vectors):
    vectors = np.asarray(vectors, dtype=float)
    length = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return np.divide(vectors, length, out=np.full_like(vectors, np.nan),
                     where=np.isfinite(length) & (length > 0))


@dataclass(frozen=True)
class CalorimeterSurface:
    barrel_radius_mm: float
    endcap_abs_z_mm: float
    endcap_inner_radius_mm: float
    endcap_outer_radius_mm: float

    def __post_init__(self):
        values = np.array(list(vars(self).values()))
        if not np.all(np.isfinite(values)) or not (
            self.barrel_radius_mm > 0 and self.endcap_abs_z_mm > 0 and
            0 <= self.endcap_inner_radius_mm < self.endcap_outer_radius_mm <=
            self.barrel_radius_mm
        ):
            raise ValueError("Invalid finite-cylinder/annular-endcap dimensions")

    def intersect_from_origin(self, momentum):
        """First surface crossing. Region 0=invalid/hole/gap, 1=barrel, 2=endcap.

        The barrel is bounded by the endcap planes. A ray through the beam
        hole or an endcap gap cannot be reassigned to a later barrel crossing.
        """
        direction = unit(momentum)
        transverse = np.linalg.norm(direction[..., :2], axis=-1)
        z = np.abs(direction[..., 2])
        barrel_t = np.divide(self.barrel_radius_mm, transverse,
                             out=np.full_like(z, np.inf), where=transverse > 0)
        endcap_t = np.divide(self.endcap_abs_z_mm, z,
                             out=np.full_like(z, np.inf), where=z > 0)
        barrel = barrel_t <= endcap_t
        distance = np.minimum(barrel_t, endcap_t)
        with np.errstate(invalid="ignore"):
            hit = direction * distance[..., None]
        radius = np.linalg.norm(hit[..., :2], axis=-1)
        endcap = (~barrel & (radius >= self.endcap_inner_radius_mm - 1e-9) &
                  (radius <= self.endcap_outer_radius_mm + 1e-9))
        valid = np.all(np.isfinite(hit), axis=-1) & (barrel | endcap)
        region = np.where(valid, np.where(barrel, 1, 2), 0)
        return np.where(valid[..., None], hit, np.nan), region


def smear_direction(true_momentum, sigma_rad, standard_normals):
    """Two Gaussian local angular components mapped to a unit direction.

    Reuse standard_normals across resolution hypotheses for paired comparisons.
    One pair should be generated per unique photon, not per candidate reuse.
    """
    if not np.isfinite(sigma_rad) or sigma_rad < 0:
        raise ValueError("sigma_rad must be finite and nonnegative")
    direction = unit(true_momentum)
    reference = np.zeros_like(direction)
    reference[..., 2] = 1
    polar = np.abs(direction[..., 2]) > .9
    reference[polar] = [1, 0, 0]
    tangent1 = unit(np.cross(reference, direction))
    tangent2 = np.cross(direction, tangent1)
    normals = np.asarray(standard_normals, dtype=float)
    if normals.shape != direction.shape[:-1] + (2,):
        raise ValueError("Need two standard normal draws per photon")
    delta = sigma_rad * (normals[..., 0, None] * tangent1 +
                         normals[..., 1, None] * tangent2)
    angle = np.linalg.norm(delta, axis=-1)
    return np.cos(angle)[..., None] * direction + np.sinc(angle / np.pi)[..., None] * delta


def photon_impact_parameters(hit, direction, pv):
    """Unsigned 3D and transverse distances from PV to the photon line.

    These are line impact parameters, not a decay length along the photon.
    A significance would additionally require a position/direction covariance.
    """
    n = unit(direction)
    delta = np.asarray(hit, dtype=float) - np.asarray(pv, dtype=float)
    ip3d = np.linalg.norm(np.cross(delta, n), axis=-1)
    nt = np.linalg.norm(n[..., :2], axis=-1)
    numerator = np.abs(delta[..., 0] * n[..., 1] - delta[..., 1] * n[..., 0])
    ipxy = np.divide(numerator, nt, out=np.full_like(nt, np.nan), where=nt > 0)
    return ip3d, ipxy
