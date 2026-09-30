"""Gaussian core fits and binned detector-resolution extraction."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit


@dataclass(frozen=True)
class GaussianFit:
    n_total: int
    n_core: int
    amplitude: float
    mean: float
    sigma: float
    mean_error: float
    sigma_error: float
    chi2_ndf: float
    low: float
    high: float
    bins: int


@dataclass(frozen=True)
class ResolutionBin:
    low: float
    high: float
    center: float
    n: int
    mean: float | None
    sigma: float | None
    sigma_error: float | None
    chi2_ndf: float | None


def _gaussian(x, amplitude, mean, sigma):
    return amplitude * np.exp(-0.5 * ((x - mean) / sigma) ** 2)


def fit_gaussian_core(values, bins: int = 60, clip_sigma: float = 3.0,
                      min_entries: int = 100) -> GaussianFit:
    """Fit a Gaussian to a robust central window of a residual distribution."""
    data = np.asarray(values, dtype=float)
    data = data[np.isfinite(data) & (data > -900)]
    if len(data) < min_entries:
        raise ValueError(f"Need at least {min_entries} finite residuals")
    median = float(np.median(data))
    robust_sigma = 1.4826 * float(np.median(np.abs(data - median)))
    if robust_sigma <= 0:
        robust_sigma = float(np.std(data))
    if not np.isfinite(robust_sigma) or robust_sigma <= 0:
        raise ValueError("Residual distribution has no measurable width")
    low, high = median - clip_sigma * robust_sigma, median + clip_sigma * robust_sigma
    core = data[(data >= low) & (data <= high)]
    if len(core) < min_entries:
        raise ValueError("Too few entries in the Gaussian core window")
    counts, edges = np.histogram(core, bins=bins, range=(low, high))
    centers = 0.5 * (edges[:-1] + edges[1:])
    uncertainty = np.sqrt(np.maximum(counts, 1))
    bin_width = (high - low) / bins
    optimum, covariance = curve_fit(
        _gaussian, centers, counts,
        p0=(float(counts.max()), median, robust_sigma),
        sigma=uncertainty, absolute_sigma=True,
        bounds=([0., low, bin_width / 2], [np.inf, high, high - low]),
        maxfev=20_000,
    )
    errors = np.sqrt(np.diag(covariance))
    chi2 = np.sum(((counts - _gaussian(centers, *optimum)) / uncertainty) ** 2)
    return GaussianFit(
        n_total=len(data), n_core=len(core), amplitude=float(optimum[0]),
        mean=float(optimum[1]), sigma=float(optimum[2]),
        mean_error=float(errors[1]), sigma_error=float(errors[2]),
        chi2_ndf=float(chi2 / max(1, bins - 3)), low=low, high=high, bins=bins,
    )


def binned_gaussian_resolution(x, residual, edges,
                               min_entries: int = 200,
                               xscale: str = "log") -> list[ResolutionBin]:
    x = np.asarray(x, dtype=float)
    residual = np.asarray(residual, dtype=float)
    if x.shape != residual.shape:
        raise ValueError("x and residual must have the same shape")
    edges = np.asarray(edges, dtype=float)
    if not np.all(np.diff(edges) > 0):
        raise ValueError("bin edges must increase")
    if xscale not in ("log", "linear"):
        raise ValueError("xscale must be 'log' or 'linear'")
    out = []
    for i, (low, high) in enumerate(zip(edges[:-1], edges[1:])):
        mask = (x >= low) & ((x <= high) if i == len(edges) - 2 else (x < high))
        subset = residual[mask & np.isfinite(residual) & (residual > -900)]
        try:
            fit = fit_gaussian_core(subset, min_entries=min_entries)
        except (ValueError, RuntimeError):
            fit = None
        out.append(ResolutionBin(
            low=float(low), high=float(high),
            center=float(np.sqrt(low * high) if xscale == "log" else (low + high) / 2),
            n=len(subset), mean=fit.mean if fit else None,
            sigma=fit.sigma if fit else None,
            sigma_error=fit.sigma_error if fit else None,
            chi2_ndf=fit.chi2_ndf if fit else None,
        ))
    return out
