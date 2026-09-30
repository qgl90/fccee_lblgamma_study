#!/usr/bin/env python3
"""Plot event-level Gamma signal efficiency from the truth-diagnostic cutflow."""

import argparse
import csv
import json
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
import uproot

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({
    "font.size": 12, "axes.labelsize": 13, "axes.titlesize": 14,
    "xtick.labelsize": 10, "ytick.labelsize": 11,
    "legend.fontsize": 10,
})

STAGES = [
    ("raw_truth_candidate", "Reco match: raw objects"),
    ("selected_photon", "IDEA selected photon"),
    ("valid_pv", "Valid primary vertex"),
    ("event_tracks", "Event track prerequisites"),
    ("nonprimary_tracks", "Both tracks outside PV set"),
    ("daughter_d0", "Both daughter d0 ≥ 3σ"),
    ("vertex_fit_valid", "Valid secondary-vertex fit"),
    ("vertex_chi2", "Secondary-vertex χ² ≤ 9"),
    ("flight_distance", "SV flight Rxy ≥ 0.3 mm"),
    ("flight_significance", "SV flight significance ≥ 2"),
    ("lambda_mass_window", "Fitted-vertex Lambda mass window"),
    ("closest_mass_hypothesis", "Closest fitted-mass hypothesis"),
    ("lb_mass_window", "Lambda_b mass 4.9–6.3 GeV"),
    ("same_hemisphere", "Photon in Lambda thrust hemisphere"),
]


def wilson68(count, total):
    """68.3% Wilson half interval for binomial event counts."""
    if total == 0:
        return 0., 0.
    z = 1.
    p = count / total
    denominator = 1. + z * z / total
    center = (p + z * z / (2. * total)) / denominator
    half = z * np.sqrt(p * (1. - p) / total +
                       z * z / (4. * total * total)) / denominator
    return max(0., p - (center - half)), max(0., min(1., center + half) - p)


def draw(path, counts, denominator, conditional=False):
    fig, ax = plt.subplots(figsize=(10.5, 8.5))
    y = np.arange(len(STAGES))
    if conditional:
        totals = [denominator] + counts[:-1]
        values = [100. * n / d if d else 0. for n, d in zip(counts, totals)]
        errors = np.asarray([wilson68(n, d) for n, d in zip(counts, totals)]).T * 100
        ylabel = "Step retention [%]"
        title = "Signal survival at each reconstruction or selection step"
    else:
        values = [100. * n / denominator for n in counts]
        errors = np.asarray([wilson68(n, denominator) for n in counts]).T * 100
        ylabel = "Cumulative signal efficiency [%]"
        title = "At least one selected signal, per input event"
    bars = ax.barh(y, values, color="#177cab", alpha=0.85, height=0.7)
    ax.errorbar(values, y, xerr=errors, fmt="none", color="black",
                capsize=2, linewidth=1)
    for bar, n, value in zip(bars, counts, values):
        ax.text(value + 2.5, bar.get_y() + bar.get_height() / 2.,
                f"{n} ({value:.1f}%)", ha="left", va="center", fontsize=10)
    ax.set(yticks=y, yticklabels=[label for _, label in STAGES],
           xlabel=ylabel, title=title)
    ax.invert_yaxis()
    ax.set_xlim(0., max(100., max(values) * 1.17))
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    fig.text(0.01, 0.01, f"Denominator: {denominator} input events; a double-signal event counts once. "
             "Error bars: 68% Wilson binomial intervals.", fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def draw_raw_lambda_mass(csv_path, keep_events, output_path):
    """Show the truth daughters' reconstructed mass before the Lambda cut."""
    masses = []
    with csv_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if int(row["event_entry"]) in keep_events:
                masses.append(float(row["lambda_mass"]))
    values = np.asarray(masses)
    if values.size == 0:
        raise ValueError("No baseline truth candidates overlap the cutflow events")
    inside = int(np.count_nonzero((values >= 0.7) & (values <= 1.3)))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(values, bins=np.linspace(0.7, 4.5, 96), histtype="step",
            color="C0", linewidth=1.5, label="Truth-matched raw candidates")
    ax.axvspan(0.7, 1.3, color="C1", alpha=0.18, label="Selected Lambda mass range")
    ax.axvline(1.3, color="C1", linestyle="--", linewidth=1.2)
    ax.set(xlabel=r"Reconstructed $m(p\pi)$ [GeV]",
           ylabel="Truth-matched candidates / bin",
           title="Lambda mass before the broad mass selection")
    ax.text(0.98, 0.96,
            f"{inside}/{len(values)} candidate masses in 0.7–1.3 GeV\n"
            f"from {len(keep_events)} eligible signal events",
            transform=ax.transAxes, ha="right", va="top", fontsize=10,
            bbox={"boxstyle": "round", "facecolor": "white",
                  "edgecolor": "0.7", "alpha": 0.9})
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return {"raw_truth_candidate_rows_after_event_prerequisites": len(values),
            "raw_truth_candidate_masses_in_lambda_window": inside}


def draw_fitted_lambda_mass(values, output_path):
    values = np.asarray(values)
    inside = int(np.count_nonzero((values >= 0.7) & (values <= 1.3)))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(values, bins=np.linspace(0.5, 3.0, 100), histtype="step",
            color="C0", linewidth=1.5,
            label="True daughter assignment, fitted momenta")
    ax.axvspan(0.7, 1.3, color="C1", alpha=0.18,
               label="Selected Λ⁰ mass range")
    ax.set(xlabel=r"Fitted-vertex $m(p\pi)$ [GeV]",
           ylabel="Signal events / bin",
           title="Λ⁰ mass before the fitted-mass window")
    ax.text(0.98, 0.96, f"{inside}/{len(values)} events in 0.7–1.3 GeV",
            transform=ax.transAxes, ha="right", va="top", fontsize=10)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return {"fitted_signal_events_before_mass": len(values),
            "fitted_signal_events_in_mass_window": inside}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-events", type=int, default=1000)
    parser.add_argument("--selection-summary", type=Path,
                        help="Compare final truth-matched event count to the normal analysis")
    parser.add_argument("--baseline-truth-csv", type=Path,
                        help="Optional raw truth-candidate CSV for preselection Lambda mass plot")
    args = parser.parse_args()
    counts = {name: 0 for name, _ in STAGES}
    eligible_events = set()
    fitted_masses = []
    with uproot.open(str(args.input),
                     handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        generated_events = tree.num_entries
        for block in tree.iterate(["event_entry", "fitted_lambda_mass"] + list(counts),
                                  library="ak", step_size=200):
            flags = np.stack([np.asarray(block[name]) for name in counts], axis=1)
            if not np.all((flags == 0) | (flags == 1)):
                raise ValueError("Cutflow flags are not binary")
            if np.any(np.diff(flags, axis=1) > 0):
                raise ValueError("Cutflow stages are not cumulative per event")
            for name in counts:
                counts[name] += int(np.count_nonzero(np.asarray(block[name])))
            eligible_events.update(
                int(entry) for entry, passed in
                zip(block["event_entry"], block["event_tracks"]) if passed)
            fitted_masses.extend(
                float(mass) for mass, passed in
                zip(block["fitted_lambda_mass"], block["flight_significance"])
                if passed and mass > 0.)
    if generated_events != args.expected_events:
        raise ValueError(f"Expected {args.expected_events} events, got {generated_events}")
    if args.selection_summary:
        selected = json.loads(args.selection_summary.read_text())
        if selected["events_with_truth_matched_candidate"] != counts["same_hemisphere"]:
            raise ValueError("Final cutflow count disagrees with selected candidate output")
    values = list(counts.values())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    draw(args.output_dir / "selection_efficiency.png", values, generated_events)
    draw(args.output_dir / "selection_step_efficiency.png",
         values, generated_events, conditional=True)
    result = {
        "input": str(args.input),
        "definition": "event-level fraction: at least one selected Lambda_b to Lambda0 gamma signal; a double-signal event counts once",
        "generated_events": generated_events,
        "stages": [
            {"name": name, "label": label, "events": n,
             "cumulative_efficiency": n / generated_events,
             "conditional_efficiency": n / (generated_events if i == 0 else values[i-1])
             if (generated_events if i == 0 else values[i-1]) else 0.}
            for i, ((name, label), n) in enumerate(zip(STAGES, values))
        ],
        "acceptance_times_reconstruction": values[0] / generated_events,
        "selection_given_reco": values[-1] / values[0] if values[0] else 0.,
        "acceptance_times_reconstruction_times_selection":
            values[-1] / generated_events,
    }
    result["fitted_lambda_mass_diagnostic"] = draw_fitted_lambda_mass(
        fitted_masses, args.output_dir / "lambda_mass_before_selection.png")
    if args.baseline_truth_csv:
        result["lambda_mass_diagnostic"] = draw_raw_lambda_mass(
            args.baseline_truth_csv, eligible_events,
            args.output_dir / "lambda_mass_raw_before_selection.png")
    (args.output_dir / "selection_efficiency.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
