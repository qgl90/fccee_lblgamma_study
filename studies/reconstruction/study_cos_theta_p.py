#!/usr/bin/env python3
"""Study Lambda_b helicity-angle response and selection on a PHSP sample.

Generated direct Lambda_b/anti-Lambda_b decays provide the denominator even
when no candidate is reconstructed. Truth-matched selected candidates provide
the numerator and reconstructed-minus-true angle residual. Every efficiency
is per generated decay; the eta-as-gamma plot, if supplied, is shape only.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import awkward as ak
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pyarrow.parquet as pq
import uproot

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_charge_efficiency import generated_chains

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({"font.size": 12, "axes.labelsize": 12,
                     "axes.titlesize": 14, "legend.fontsize": 10})

MC_FIELDS = [
    "Particle/Particle.momentum.x", "Particle/Particle.momentum.y",
    "Particle/Particle.momentum.z", "Particle/Particle.mass",
]
ANGULAR_STAGES = (
    ("raw_truth_candidate", "Reconstructed p, π, γ"),
    ("selected_photon", "Selected photon"),
    ("daughter_d0", "PV and daughter displacement"),
    ("vertex_chi2", "Secondary vertex χ²"),
    ("same_hemisphere", "Final selection"),
)


def four(momentum, mass):
    """(E,px,py,pz) in GeV, using the MC mass field."""
    spatial = np.asarray(momentum, dtype=float)
    return np.r_[np.hypot(np.linalg.norm(spatial), mass), spatial]


def boost(vector, beta):
    """Apply the same Lorentz boost as TLorentzVector::Boost(beta)."""
    beta2 = float(np.dot(beta, beta))
    if not 0 <= beta2 < 1:
        return np.full(4, np.nan)
    if beta2 == 0:
        return vector.copy()
    gamma = 1. / np.sqrt(1. - beta2)
    dot = float(np.dot(beta, vector[1:]))
    spatial = vector[1:] + ((gamma - 1.) * dot / beta2 +
                            gamma * vector[0]) * beta
    return np.r_[gamma * (vector[0] + dot), spatial]


def helicity_cos(parent, lam, proton):
    """cos between (anti)proton and -parent, in the Lambda rest frame."""
    beta = -lam[1:] / lam[0]
    parent_rest = boost(parent, beta)[1:]
    proton_rest = boost(proton, beta)[1:]
    denominator = np.linalg.norm(parent_rest) * np.linalg.norm(proton_rest)
    return float(np.clip(-np.dot(parent_rest, proton_rest) / denominator,
                         -1., 1.)) if denominator > 0 else np.nan


def generated_angles(path, n_events):
    chains = generated_chains(path, n_events)
    with uproot.open(str(path),
                     handler=uproot.source.file.MemmapSource) as root:
        arrays = root["events"].arrays(MC_FIELDS, entry_stop=n_events,
                                       library="ak")
    rows = []
    for event, chain_list in enumerate(chains):
        x, y, z, mass = (ak.to_numpy(arrays[name][event]) for name in MC_FIELDS)
        def particle(index):
            return four((x[index], y[index], z[index]), mass[index])
        for chain in chain_list:
            value = helicity_cos(particle(chain["lb"]),
                                 particle(chain["lambda"]),
                                 particle(chain["proton"]))
            if not np.isfinite(value):
                raise ValueError(f"Undefined generated angle at event {event}")
            rows.append((event, chain["lb"], chain["sign"], value))
    return rows


def selected_candidates(path):
    columns = ["event_entry", "candidate_slot", "truth_matched",
               "lb_mc_index", "lb_sign", "lb_mass", "cos_theta_p",
               "truth_cos_theta_p"]
    table = pq.read_table(path, columns=columns).to_pydict()
    return [{name: table[name][i] for name in columns}
            for i in range(len(table["event_entry"]))]


def efficiency_plot(generated, selected, outdir, bins):
    values = np.asarray([row[3] for row in generated])
    selected_values = np.asarray([row["truth_cos_theta_p"] for row in selected])
    gen, _ = np.histogram(values, bins)
    sel, _ = np.histogram(selected_values, bins)
    if np.any(sel > gen):
        raise ValueError("Selected candidates exceed generated decays in a bin")
    center = (bins[:-1] + bins[1:]) / 2
    efficiency = np.divide(sel, gen, out=np.zeros_like(sel, dtype=float),
                           where=gen > 0)
    error = np.divide(np.sqrt(sel * (1. - efficiency)), gen,
                      out=np.zeros_like(efficiency), where=gen > 0)
    fig, ax = plt.subplots(figsize=(9, 5.8))
    ax.errorbar(center, efficiency, xerr=np.diff(bins) / 2, yerr=error,
                fmt="o", color="C0", capsize=2, label="Selected / generated")
    ax.set(xlabel=r"Generated $\cos\theta_p$", ylabel="Selection efficiency",
           xlim=(-1, 1), ylim=(0, 1),
           title=r"$\Lambda_b\to\Lambda^0\gamma$ efficiency vs $\cos\theta_p$")
    ax2 = ax.twinx()
    ax2.step(bins, np.r_[gen, gen[-1]], where="post", color="0.55",
             label="Generated direct decays")
    ax2.step(bins, np.r_[sel, sel[-1]], where="post", color="C1",
             label="Selected truth matched")
    ax2.set(ylabel="Decays / bin", ylim=(0, max(gen) * 1.35))
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, frameon=False,
              loc="lower center")
    fig.tight_layout()
    fig.savefig(outdir / "cos_theta_p_efficiency.png", dpi=160)
    plt.close(fig)
    return gen, sel


def resolution_plot(selected, outdir, bins):
    truth = np.asarray([row["truth_cos_theta_p"] for row in selected])
    reco = np.asarray([row["cos_theta_p"] for row in selected])
    residual = reco - truth
    if np.any(~np.isfinite(residual)) or np.any(np.abs(reco) > 1.00001):
        raise ValueError("Invalid selected reconstructed angle")
    center = (bins[:-1] + bins[1:]) / 2
    count, _ = np.histogram(truth, bins)
    width = []
    bias = []
    for low, high in zip(bins[:-1], bins[1:]):
        values = residual[(truth >= low) & (truth < high if high < 1 else truth <= high)]
        width.append(float((np.quantile(values, .84) - np.quantile(values, .16)) / 2)
                     if len(values) >= 8 else np.nan)
        bias.append(float(np.median(values)) if len(values) >= 8 else np.nan)
    fig, ax = plt.subplots(figsize=(9, 5.8))
    ax.errorbar(center, width, xerr=np.diff(bins) / 2, fmt="o", capsize=2,
                label="Half-width of central 68%", color="C0")
    ax.set(xlabel=r"Generated $\cos\theta_p$",
           ylabel=r"Resolution in $\cos\theta_p$ (absolute)",
           xlim=(-1, 1),
           title=r"Truth-matched $\cos\theta_p$ response")
    ax.set_ylim(bottom=0)
    finite_widths = np.asarray(width)[np.isfinite(width)]
    ax.set_ylim(top=float(np.max(finite_widths) * 1.35)
                if len(finite_widths) else 1.)
    ax2 = ax.twinx()
    ax2.step(bins, np.r_[count, count[-1]], where="post", color="0.55",
             label="Matched candidates / bin")
    ax2.set(ylabel="Matched candidates / bin", ylim=(0, max(count) * 1.35))
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, frameon=False,
              loc="upper left")
    fig.tight_layout()
    fig.savefig(outdir / "cos_theta_p_resolution.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.hist(residual, bins=np.linspace(-.5, .5, 81), histtype="step",
            label="Selected truth matched")
    ax.set(xlabel=r"Reconstructed $\cos\theta_p$ − generated $\cos\theta_p$",
           ylabel="Candidates / bin", title="Helicity-angle residual")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outdir / "cos_theta_p_residual.png", dpi=160)
    plt.close(fig)

    # Expose every distribution behind the binned width, including tails.
    fig, axes = plt.subplots(2, 5, figsize=(16, 6.5), sharex=True,
                             sharey=True)
    for i, ax in enumerate(axes.flat):
        low, high = bins[i:i + 2]
        mask = (truth >= low) & (truth < high if high < 1 else truth <= high)
        ax.hist(residual[mask], bins=np.linspace(-.12, .12, 49),
                histtype="step", color="C0")
        ax.axvline(0, color="0.5", linewidth=1)
        ax.set_title(f"{low:+.1f} to {high:+.1f}; N={int(mask.sum())}",
                     fontsize=11)
        ax.set_ylim(bottom=0)
    fig.supxlabel(r"Reconstructed $\cos\theta_p$ − generated $\cos\theta_p$")
    fig.supylabel("Candidates / bin")
    fig.tight_layout()
    fig.savefig(outdir / "cos_theta_p_residual_by_bin.png", dpi=160)
    plt.close(fig)
    return np.asarray(width), np.asarray(bias), residual


def charge_plot(generated, selected, outdir, bins):
    center = (bins[:-1] + bins[1:]) / 2
    fig, ax = plt.subplots(figsize=(9, 5.8))
    for sign, label, color in ((1, r"$\Lambda_b$", "C0"),
                               (-1, r"$\overline{\Lambda}_b$", "C1")):
        gen, _ = np.histogram([r[3] for r in generated if r[2] == sign], bins)
        sel, _ = np.histogram([r["truth_cos_theta_p"] for r in selected
                               if r["lb_sign"] == sign], bins)
        efficiency = np.divide(sel, gen, out=np.zeros_like(sel, dtype=float),
                               where=gen > 0)
        error = np.divide(np.sqrt(sel * (1. - efficiency)), gen,
                          out=np.zeros_like(efficiency), where=gen > 0)
        ax.errorbar(center, efficiency, xerr=np.diff(bins) / 2, yerr=error,
                    fmt="o", capsize=2, color=color, label=label)
    ax.set(xlabel=r"Generated $\cos\theta_p$", ylabel="Selection efficiency",
           xlim=(-1, 1), ylim=(0, 1),
           title="Charge-separated helicity-angle efficiency")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outdir / "cos_theta_p_efficiency_by_charge.png", dpi=160)
    plt.close(fig)


def staged_efficiency_plot(generated, cutflow_path, outdir, bins):
    """Use sign-specific event flags; require one generated decay per sign/event."""
    keys = [(event, sign) for event, _, sign, _ in generated]
    if len(set(keys)) != len(keys):
        raise ValueError("Stage flags cannot disambiguate two decays of the same sign/event")
    names = [f"{prefix}{stage}" for prefix in ("positive_", "negative_")
             for stage, _ in ANGULAR_STAGES]
    with uproot.open(str(cutflow_path),
                     handler=uproot.source.file.MemmapSource) as root:
        flags = root["events"].arrays(["event_entry"] + names, library="np")
    indexed = {int(entry): i for i, entry in enumerate(flags["event_entry"])}
    if not all(event in indexed for event, _, _, _ in generated):
        raise ValueError("Cutflow does not cover all generated event entries")
    truth = np.asarray([row[3] for row in generated])
    denominator, _ = np.histogram(truth, bins)
    centers = (bins[:-1] + bins[1:]) / 2
    stage_counts = {}
    fig, ax = plt.subplots(figsize=(9.5, 6))
    for name, label in ANGULAR_STAGES:
        accepted = np.asarray([
            bool(flags[("positive_" if sign > 0 else "negative_") + name]
                       [indexed[event]])
            for event, _, sign, _ in generated])
        counts, _ = np.histogram(truth[accepted], bins)
        stage_counts[name] = counts.tolist()
        efficiency = np.divide(counts, denominator,
                               out=np.zeros_like(counts, dtype=float),
                               where=denominator > 0)
        ax.plot(centers, efficiency, marker="o", label=label)
    ax.set(xlabel=r"Generated $\cos\theta_p$", ylabel="Cumulative efficiency",
           xlim=(-1, 1), ylim=(0, 1),
           title="Selection stages versus generated helicity angle")
    ax.legend(frameon=False, fontsize=9, ncol=2)
    fig.tight_layout()
    fig.savefig(outdir / "cos_theta_p_staged_efficiency.png", dpi=160)
    plt.close(fig)
    return stage_counts


def mass_angle_plot(signal, eta_path, outdir):
    matched = [r for r in signal if r["truth_matched"] == 1]
    fig, ax = plt.subplots(figsize=(8.8, 6))
    ax.hist2d([r["lb_mass"] for r in matched],
              [r["cos_theta_p"] for r in matched],
              bins=(35, 20), range=((4.9, 6.3), (-1, 1)), cmap="viridis")
    ax.set(xlabel=r"Reconstructed $m(\Lambda_b)$ [GeV]",
           ylabel=r"Reconstructed $\cos\theta_p$",
           title="Truth-matched signal candidates")
    fig.tight_layout()
    fig.savefig(outdir / "mass_vs_cos_theta_p.png", dpi=160)
    plt.close(fig)
    other = [r for r in signal if r["truth_matched"] != 1]
    fig, ax = plt.subplots(figsize=(8.8, 6))
    ax.hist2d([r["lb_mass"] for r in other],
              [r["cos_theta_p"] for r in other],
              bins=(35, 20), range=((4.9, 6.3), (-1, 1)), cmap="viridis")
    ax.set(xlabel=r"Reconstructed $m(\Lambda_b)$ [GeV]",
           ylabel=r"Reconstructed $\cos\theta_p$",
           title="Other combinations in forced signal sample")
    fig.tight_layout()
    fig.savefig(outdir / "signal_other_mass_vs_cos_theta_p.png", dpi=160)
    plt.close(fig)
    if eta_path is None:
        return {"all": 0, "true_partial": 0, "other": 0}
    eta = pq.read_table(eta_path).to_pydict()
    n_eta = len(eta["cos_theta_p"])
    # A true partial candidate has the right signed Lambda0 daughter pair
    # and a photon whose eta mother shares that Lambda0's Lambda_b parent.
    # This is a plotting label only; the one-photon builder never sees it.
    partial = np.asarray(eta["mass_hypothesis_correct"]) == 1
    partial &= np.asarray(eta["proton_mc_parent_index"]) == np.asarray(
        eta["pion_mc_parent_index"])
    partial &= np.asarray(eta["proton_mc_grandparent_index"]) == np.asarray(
        eta["photon_mc_grandparent_index"])
    partial &= np.asarray(eta["proton_mc_grandparent_pdg"]) == (
        5122 * np.asarray(eta["lb_sign"]))
    partial &= np.asarray(eta["photon_mc_parent_pdg"]) == 221
    partial &= np.asarray(eta["photon_mc_grandparent_index"]) >= 0
    eta_angle = np.asarray(eta["cos_theta_p"])
    fig, ax = plt.subplots(figsize=(8.8, 6))
    ax.hist2d(np.asarray(eta["lb_mass"])[partial], eta_angle[partial],
              bins=(35, 20), range=((4.9, 6.3), (-1, 1)), cmap="viridis")
    ax.set(xlabel=r"Reconstructed $m(\Lambda_b)$ [GeV]",
           ylabel=r"Reconstructed $\cos\theta_p$",
           title="True partial η→γγ reconstructed as Λγ")
    fig.tight_layout()
    fig.savefig(outdir / "eta_partial_mass_vs_cos_theta_p.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    bins = np.linspace(-1, 1, 21)
    ax.hist([r["cos_theta_p"] for r in matched], bins=bins, histtype="step",
            density=True, label="Truth-matched direct γ")
    ax.hist(eta_angle[partial], bins=bins, histtype="step", density=True,
            label="True partial η→γγ")
    ax.hist(eta_angle[~partial], bins=bins, histtype="step", density=True,
            label="Other η-sample combinations")
    ax.set(xlabel=r"Reconstructed $\cos\theta_p$",
           ylabel="Unit-normalized candidates / bin",
           title="Forced-sample angular shapes (no physical normalization)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outdir / "signal_eta_cos_theta_p_shapes.png", dpi=160)
    plt.close(fig)
    return {"all": n_eta, "true_partial": int(partial.sum()),
            "other": int((~partial).sum())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mc", type=Path, required=True)
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--cutflow", type=Path)
    parser.add_argument("--eta-as-gamma", type=Path)
    parser.add_argument("--events", type=int, default=1000)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.events <= 0:
        raise ValueError("--events must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    generated = generated_angles(args.mc, args.events)
    # The reconstruction can contain more events than the requested
    # generated-denominator range; keep the exact same input-event subset.
    rows = [row for row in selected_candidates(args.selected)
            if int(row["event_entry"]) < args.events]
    matched = [r for r in rows if r["truth_matched"] == 1]
    generated_by_key = {(event, lb): (sign, angle)
                        for event, lb, sign, angle in generated}
    if len(generated_by_key) != len(generated):
        raise ValueError("Duplicate generated Lambda_b keys")
    seen = set()
    for row in matched:
        key = (int(row["event_entry"]), int(row["lb_mc_index"]))
        if key in seen or key not in generated_by_key:
            raise ValueError(f"Duplicate or unknown matched decay {key}")
        seen.add(key)
        sign, angle = generated_by_key[key]
        if sign != row["lb_sign"] or abs(angle - row["truth_cos_theta_p"]) > 2e-4:
            raise ValueError(f"Charge or C++/Python angle disagreement at {key}")
    bins = np.linspace(-1., 1., 11)
    gen, sel = efficiency_plot(generated, matched, args.output_dir, bins)
    charge_plot(generated, matched, args.output_dir, bins)
    stage_counts = (staged_efficiency_plot(generated, args.cutflow,
                                          args.output_dir, bins)
                    if args.cutflow else {})
    if stage_counts and stage_counts["same_hemisphere"] != sel.tolist():
        raise ValueError("Final sign-specific cutflow and matched candidates disagree by angle bin")
    width, bias, residual = resolution_plot(matched, args.output_dir, bins)
    eta_counts = mass_angle_plot(rows, args.eta_as_gamma, args.output_dir)
    result = {
        "definition": "(anti)proton versus negative Lambda_b momentum in Lambda rest frame",
        "generated_direct_decays": len(generated),
        "selected_truth_matched": len(matched),
        "efficiency": len(matched) / len(generated),
        "selected_by_sign": {
            "Lambda_b": sum(r["lb_sign"] == 1 for r in matched),
            "anti_Lambda_b": sum(r["lb_sign"] == -1 for r in matched),
        },
        "bin_edges": bins.tolist(), "generated_per_bin": gen.tolist(),
        "selected_per_bin": sel.tolist(),
        "stage_counts_per_bin": stage_counts,
        "resolution_68_halfwidth_per_bin": width.tolist(),
        "residual_median_per_bin": bias.tolist(),
        "residual_median_all": float(np.median(residual)),
        "residual_68_halfwidth_all": float((np.quantile(residual, .84) -
                                            np.quantile(residual, .16)) / 2),
        "eta_as_gamma_candidates": eta_counts,
    }
    (args.output_dir / "cos_theta_p_summary.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
