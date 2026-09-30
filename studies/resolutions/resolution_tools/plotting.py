"""Reusable noninteractive 1D, scatter, efficiency, and resolution plots."""

import os
from pathlib import Path
import tempfile

_mpl_cache = Path(tempfile.gettempdir()) / "lblgamma-mplconfig"
_mpl_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_cache))
_font_cache = Path(tempfile.gettempdir()) / "lblgamma-cache"
_font_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(_font_cache))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np

from .fitting import GaussianFit, ResolutionBin, fit_gaussian_core

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "figure.figsize": (7, 5),
})


def _save(fig, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_1d(values, output, xlabel, title, fit: GaussianFit | None = None,
            bins: int = 60):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values) & (values > -900)]
    if len(values) == 0:
        raise ValueError("Cannot plot an empty distribution")
    if fit:
        limits = (fit.low, fit.high)
        bins = fit.bins
    else:
        limits = tuple(np.percentile(values, [0.5, 99.5]))
    fig, ax = plt.subplots(figsize=(7, 5))
    counts, edges, _ = ax.hist(values, bins=bins, range=limits,
                               histtype="step", linewidth=1.5, label="Data")
    if fit:
        x = np.linspace(fit.low, fit.high, 400)
        y = fit.amplitude * np.exp(-0.5 * ((x - fit.mean) / fit.sigma) ** 2)
        ax.plot(x, y, label=f"Gaussian core: $\\mu$={fit.mean:.4g}, $\\sigma$={fit.sigma:.4g}")
        ax.legend(frameon=False)
    ax.set(xlabel=xlabel, ylabel="Entries / bin", title=title)
    _save(fig, output)


def plot_scatter(x, y, output, xlabel, ylabel, title, max_points: int = 40_000,
                 identity: bool = False):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y) & (x > -900) & (y > -900)
    x, y = x[valid], y[valid]
    if len(x) > max_points:
        chosen = np.random.default_rng(12345).choice(len(x), max_points, replace=False)
        x, y = x[chosen], y[chosen]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(x, y, s=2, alpha=0.18, rasterized=True)
    if identity and len(x):
        upper = float(max(np.percentile(x, 99.5), np.percentile(y, 99.5)))
        ax.plot([0, upper], [0, upper], "k--", linewidth=1)
        ax.set(xlim=(0, upper), ylim=(0, upper))
    ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
    _save(fig, output)


def plot_resolution(bins: list[ResolutionBin], output, xlabel, ylabel, title,
                    reference=None, xscale="log", raw_x=None, raw_residual=None,
                    min_fit_entries=200, residual_label="Residual",
                    acceptance_boundary=None):
    """Show fitted widths with bin extents and entries on a twin y-axis.

    When raw arrays are supplied, also save a per-bin residual and Gaussian
    diagnostic next to the resolution figure.
    """
    valid = [row for row in bins if row.sigma is not None]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax_counts = ax.twinx()
    edges = [bins[0].low] + [row.high for row in bins]
    ax_counts.stairs([row.n for row in bins], edges, fill=True,
                     color="0.5", alpha=0.18, label="Residual entries / bin")
    ax_counts.set_ylabel("Residual entries / bin", color="0.35")
    ax_counts.tick_params(axis="y", colors="0.35")
    ax_counts.set_ylim(0, max(1, max(row.n for row in bins)) * 1.2)
    ax.set_zorder(ax_counts.get_zorder() + 1)
    ax.patch.set_visible(False)
    if valid:
        ax.errorbar([r.center for r in valid], [r.sigma for r in valid],
                    xerr=([r.center - r.low for r in valid],
                          [r.high - r.center for r in valid]),
                    yerr=[r.sigma_error for r in valid], fmt="o", ms=4,
                    capsize=2, color="C0", label="Gaussian core width")
    if reference:
        x = np.geomspace(bins[0].low, bins[-1].high, 300)
        ax.plot(x, reference(x), "--", label="IDEA card ECAL term")
    if acceptance_boundary is not None:
        for edge in (-acceptance_boundary, acceptance_boundary):
            ax.axvline(edge, color="0.3", linestyle=":", linewidth=1)
    ax.set(xscale=xscale, xlabel=xlabel, ylabel=ylabel, title=title)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    if valid or reference:
        ax.legend(frameon=False)
    _save(fig, output)
    if (raw_x is None) != (raw_residual is None):
        raise ValueError("raw_x and raw_residual must be supplied together")
    if raw_x is not None:
        output = Path(output)
        plot_fit_distributions(raw_x, raw_residual, bins,
                               output.with_name(output.stem + "_fit_distributions.png"),
                               xlabel, title, min_fit_entries, residual_label)


def plot_fit_distributions(x, residual, bins: list[ResolutionBin], output,
                           xlabel, title, min_fit_entries=200,
                           residual_label="Residual"):
    """Show the actual residual histogram and fit in every truth-variable bin."""
    x = np.asarray(x, dtype=float)
    residual = np.asarray(residual, dtype=float)
    if x.shape != residual.shape:
        raise ValueError("x and residual must have the same shape")
    ncols = 4
    nrows = (len(bins) + ncols - 1) // ncols
    with plt.rc_context({"font.size": 10, "axes.titlesize": 10,
                         "axes.labelsize": 10, "xtick.labelsize": 8,
                         "ytick.labelsize": 8, "legend.fontsize": 8}):
        fig, axes = plt.subplots(nrows, ncols, figsize=(16, 3.1 * nrows))
        for i, row in enumerate(bins):
            ax = np.ravel(axes)[i]
            mask = ((x >= row.low) &
                    ((x <= row.high) if i == len(bins) - 1 else (x < row.high)) &
                    np.isfinite(residual) & (residual > -900))
            values = residual[mask]
            ax.set_title(f"{row.low:g}–{row.high:g}: N={len(values)}")
            try:
                fit = fit_gaussian_core(values, min_entries=min_fit_entries)
            except (ValueError, RuntimeError):
                fit = None
            if fit is not None:
                core = values[(values >= fit.low) & (values <= fit.high)]
                ax.hist(core, bins=fit.bins, range=(fit.low, fit.high),
                        histtype="step", color="C0", label="Fit-window data")
                grid = np.linspace(fit.low, fit.high, 250)
                curve = fit.amplitude * np.exp(-0.5 * ((grid - fit.mean) / fit.sigma) ** 2)
                ax.plot(grid, curve, color="C1", linewidth=1.5,
                        label="Gaussian fit")
                ax.text(0.98, 0.96,
                        rf"$\sigma={fit.sigma:.3g}$" + "\n" +
                        rf"$\chi^2/\mathrm{{ndf}}={fit.chi2_ndf:.2f}$" + "\n" +
                        f"Core N={fit.n_core}", transform=ax.transAxes,
                        ha="right", va="top", fontsize=8)
            elif len(values):
                limits = np.percentile(values, [0.5, 99.5])
                if limits[0] < limits[1]:
                    ax.hist(values, bins=40, range=limits,
                            histtype="step", color="C0")
                ax.text(0.98, 0.96, "No valid fit", transform=ax.transAxes,
                        ha="right", va="top", fontsize=8)
            else:
                ax.text(0.5, 0.5, "No entries", transform=ax.transAxes,
                        ha="center", va="center", fontsize=9)
            ax.grid(alpha=0.2)
            ax.set_xlabel(residual_label)
            ax.set_ylabel("Entries")
        for ax in np.ravel(axes)[len(bins):]:
            ax.set_visible(False)
        fig.suptitle(f"{title}: residuals by {xlabel}", fontsize=16)
        _save(fig, output)


def plot_resolution_comparison(series: dict[str, list[ResolutionBin]], output,
                               xlabel, ylabel, title, xscale="linear",
                               acceptance_boundary=None):
    """Overlay Gaussian core widths for samples fitted in the same bins."""
    fig, ax = plt.subplots(figsize=(8.3, 5.5))
    markers = ["o", "s", "^", "D", "v"]
    for i, (label, rows) in enumerate(series.items()):
        valid = [row for row in rows if row.sigma is not None]
        if not valid:
            continue
        ax.errorbar([r.center for r in valid], [r.sigma for r in valid],
                    xerr=([r.center - r.low for r in valid],
                          [r.high - r.center for r in valid]),
                    yerr=[r.sigma_error for r in valid],
                    fmt=markers[i % len(markers)], ms=4, capsize=2,
                    label=label, alpha=0.85)
    ax.set(xscale=xscale, xlabel=xlabel, ylabel=ylabel, title=title)
    if acceptance_boundary is not None:
        for edge in (-acceptance_boundary, acceptance_boundary):
            ax.axvline(edge, color="0.3", linestyle=":", linewidth=1)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=10)
    _save(fig, output)


def _wilson(k, n):
    p = k / n
    denom = 1 + 1 / n
    center = (p + 1 / (2 * n)) / denom
    half = np.sqrt(p * (1 - p) / n + 1 / (4 * n * n)) / denom
    return p, max(0., p - (center - half)), max(0., (center + half) - p)


def plot_efficiency(x, flag_sets: dict[str, np.ndarray], edges, output,
                    xlabel, title, xscale="log", acceptance_boundary=None):
    x = np.asarray(x, dtype=float)
    edges = np.asarray(edges, dtype=float)
    centers = (np.sqrt(edges[:-1] * edges[1:]) if xscale == "log"
               else 0.5 * (edges[:-1] + edges[1:]))
    fig, ax = plt.subplots(figsize=(7, 5))
    ax_counts = ax.twinx()
    totals = np.histogram(x[np.isfinite(x)], edges)[0]
    ax_counts.stairs(totals, edges, fill=True, color="0.5", alpha=0.18)
    ax_counts.set_ylabel("Counts / bin (fill: generated; dash: matched)", color="0.35")
    ax_counts.tick_params(axis="y", colors="0.35")
    ax_counts.set_ylim(0, max(1, totals.max()) * 1.2)
    ax.set_zorder(ax_counts.get_zorder() + 1)
    ax.patch.set_visible(False)
    for i_set, (label, flags) in enumerate(flag_sets.items()):
        flags = np.asarray(flags, dtype=bool)
        if flags.shape != x.shape:
            raise ValueError(f"Efficiency flags for {label} do not match x")
        matched_counts = np.histogram(x[flags & np.isfinite(x)], edges)[0]
        ax_counts.stairs(matched_counts, edges, color=f"C{i_set}",
                         linestyle="--", alpha=0.5, linewidth=1)
        xs, ys, lower, upper, xlow, xhigh = [], [], [], [], [], []
        for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
            mask = (x >= lo) & ((x <= hi) if i == len(centers) - 1 else (x < hi))
            n = int(mask.sum())
            if not n:
                continue
            p, dn, up = _wilson(int(flags[mask].sum()), n)
            xs.append(centers[i]); ys.append(p); lower.append(dn); upper.append(up)
            xlow.append(centers[i] - lo); xhigh.append(hi - centers[i])
        ax.errorbar(xs, ys, xerr=[xlow, xhigh], yerr=[lower, upper], fmt="o-", ms=4,
                    capsize=2, label=label)
    ax.set(xscale=xscale, ylim=(-0.04, 1.04), xlabel=xlabel,
           ylabel="Fraction of generated particles", title=title)
    if acceptance_boundary is not None:
        for edge in (-acceptance_boundary, acceptance_boundary):
            ax.axvline(edge, color="0.3", linestyle=":", linewidth=1)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    _save(fig, output)


def plot_efficiency_comparison(samples, edges, output, xlabel, title,
                               xscale="linear", min_denominator=30,
                               acceptance_boundary=None):
    """Compare matching fractions for different generated populations."""
    edges = np.asarray(edges, dtype=float)
    fig, ax = plt.subplots(figsize=(8.3, 5.5))
    ax_counts = ax.twinx()
    ax_counts.set_ylabel("Counts / bin (solid: generated; dash: matched)", color="0.35")
    ax_counts.tick_params(axis="y", colors="0.35")
    ax.set_zorder(ax_counts.get_zorder() + 1)
    ax.patch.set_visible(False)
    markers = ["o", "s", "^", "D", "v"]
    rows = []
    for i, (label, (x, matched)) in enumerate(samples.items()):
        x = np.asarray(x, dtype=float)
        matched = np.asarray(matched, dtype=bool)
        if x.shape != matched.shape:
            raise ValueError(f"Generated values and match flags differ for {label}")
        centers, values, low_errors, high_errors, xlow, xhigh = [], [], [], [], [], []
        total = np.histogram(x[np.isfinite(x)], edges)[0]
        ax_counts.stairs(total, edges, color=f"C{i}", alpha=0.35, linewidth=1)
        found = np.histogram(x[matched & np.isfinite(x)], edges)[0]
        ax_counts.stairs(found, edges, color=f"C{i}", linestyle="--",
                         alpha=0.55, linewidth=1)
        for j, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
            mask = np.isfinite(x) & (x >= lo) & (
                (x <= hi) if j == len(edges) - 2 else (x < hi))
            n = int(mask.sum())
            if n == 0:
                continue
            k = int(matched[mask].sum())
            p, lower, upper = _wilson(k, n)
            center = float(np.sqrt(lo * hi) if xscale == "log" else (lo + hi) / 2)
            if n >= min_denominator:
                centers.append(center)
                values.append(100 * p)
                low_errors.append(100 * lower)
                high_errors.append(100 * upper)
                xlow.append(center - lo)
                xhigh.append(hi - center)
            rows.append({"sample": label, "low": float(lo), "high": float(hi),
                         "n": n, "matched": k, "fraction_percent": 100 * p,
                         "error_low_percent": 100 * lower,
                         "error_high_percent": 100 * upper,
                         "plotted": n >= min_denominator})
        ax.errorbar(centers, values, xerr=[xlow, xhigh], yerr=[low_errors, high_errors],
                    fmt=markers[i % len(markers)] + "-", ms=4, capsize=2,
                    label=label, alpha=0.85)
    ax.set(xscale=xscale, ylim=(-3, 103), xlabel=xlabel,
           ylabel="Unique match fraction [%]", title=title)
    if acceptance_boundary is not None:
        for edge in (-acceptance_boundary, acceptance_boundary):
            ax.axvline(edge, color="0.3", linestyle=":", linewidth=1)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=10)
    _save(fig, output)
    return rows


def plot_efficiency_map(x, y, matched, xedges, yedges, output, xlabel,
                        ylabel, title, xscale="log", min_denominator=20):
    """Matched/total in two truth-coordinate dimensions; sparse cells are blank."""
    total, _, _ = np.histogram2d(x, y, bins=(xedges, yedges))
    found, _, _ = np.histogram2d(np.asarray(x)[matched], np.asarray(y)[matched],
                                 bins=(xedges, yedges))
    fraction = np.full_like(total, np.nan)
    np.divide(found, total, out=fraction, where=total >= min_denominator)
    fraction[total < min_denominator] = np.nan
    fig, ax = plt.subplots(figsize=(8, 5.5))
    mesh = ax.pcolormesh(xedges, yedges, fraction.T, vmin=0, vmax=1,
                         cmap="viridis", shading="flat")
    fig.colorbar(mesh, ax=ax, label="Matched / generated")
    ax.set(xscale=xscale, xlabel=xlabel, ylabel=ylabel, title=title)
    _save(fig, output)
