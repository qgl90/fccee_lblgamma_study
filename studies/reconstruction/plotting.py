"""Small reusable histogram plots for event-vector reconstruction ntuples."""

import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({
    "font.size": 12,
    "axes.labelsize": 13,
    "axes.titlesize": 14,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
})


def mass_overlay(edges, all_counts, matched_counts, path, xlabel, title,
                 annotation=None):
    """Plot all combinations and truth-matched ones with separate count axes."""
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax_match = ax.twinx()
    ax.stairs(all_counts, edges, color="C0", linewidth=1.4,
              label="All combinations")
    ax_match.stairs(matched_counts, edges, color="C1", linewidth=1.6,
                    label="Truth-matched signal")
    ax.set(xlabel=xlabel, ylabel="All combinations / bin", title=title)
    ax_match.set_ylabel("Truth-matched candidates / bin", color="C1")
    ax_match.tick_params(axis="y", colors="C1")
    ax.set_ylim(bottom=0)
    ax_match.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    handles, labels = ax.get_legend_handles_labels()
    other_handles, other_labels = ax_match.get_legend_handles_labels()
    ax.legend(handles + other_handles, labels + other_labels,
              frameon=False, loc="upper right")
    if annotation:
        ax.text(0.02, 0.96, annotation, transform=ax.transAxes,
                ha="left", va="top", fontsize=10,
                bbox={"boxstyle": "round", "facecolor": "white",
                      "edgecolor": "0.7", "alpha": 0.9})
    fig.tight_layout(pad=1.4)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def candidate_multiplicity(values, path, label="Uncut"):
    """Plot the candidate count per input event, including zero-candidate events."""
    values = np.asarray(values, dtype=int)
    upper = max(10, int(values.max(initial=0)) + 1)
    edges = np.linspace(0, upper, 60)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(values, bins=edges, histtype="step", linewidth=1.5)
    ax.set(xlabel=r"$\Lambda_b$ combinations / event", ylabel="Events / bin",
           title=f"{label} candidate multiplicity")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def matched_mass_scatter(lb_mass, lambda_mass, path, title, xlim=None, ylim=None):
    """Show whether the matched Lambda_b high-mass tail follows Lambda0 mass."""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(lb_mass, lambda_mass, s=10, alpha=0.45, rasterized=True)
    ax.axhline(1.115683, color="C1", linestyle="--", linewidth=1.2,
               label=r"PDG $m(\Lambda^0)$")
    ax.set(xlabel=r"Reconstructed $m(p\pi\gamma)$ [GeV]",
           ylabel=r"Reconstructed $m(p\pi)$ [GeV]", title=title)
    ax.set_xlim(*(xlim or (0, None)))
    ax.set_ylim(*(ylim or (0, None)))
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def flight_overlay(edges, all_counts, truth_counts, threshold, path):
    """Plot reconstructed Lambda0 transverse flight distances, in mm."""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    other = ax.twinx()
    ax.stairs(all_counts, edges, color="C0", label="All retained Lambda candidates")
    other.stairs(truth_counts, edges, color="C1", label="Truth-matched Lambda")
    ax.axvline(threshold, color="black", linestyle="--", linewidth=1.2,
               label="Configured minimum")
    ax.set_xscale("log")
    ax.set(xlabel=r"Reconstructed $\Lambda^0$ flight $R_{xy}$ from PV [mm]",
           ylabel="All Lambda candidates / bin",
           title="Selected Lambda vertex displacement")
    other.set_ylabel("Truth-matched Lambda / bin", color="C1")
    other.tick_params(axis="y", colors="C1")
    ax.set_ylim(bottom=0)
    other.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    handles, labels = ax.get_legend_handles_labels()
    extra, extra_labels = other.get_legend_handles_labels()
    ax.legend(handles + extra, labels + extra_labels, frameon=False)
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
