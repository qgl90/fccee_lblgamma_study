"""Reusable data loading, fitting, and plotting for detector resolutions."""

from .fitting import GaussianFit, ResolutionBin, binned_gaussian_resolution, fit_gaussian_core
from .io import ResolutionSample, load_sample
from .plotting import plot_1d, plot_efficiency, plot_efficiency_comparison, plot_efficiency_map, plot_fit_distributions, plot_resolution, plot_resolution_comparison, plot_scatter

__all__ = [
    "GaussianFit", "ResolutionBin", "ResolutionSample", "binned_gaussian_resolution",
    "fit_gaussian_core", "load_sample", "plot_1d", "plot_efficiency",
    "plot_efficiency_comparison", "plot_efficiency_map",
    "plot_fit_distributions", "plot_resolution", "plot_resolution_comparison", "plot_scatter",
]
