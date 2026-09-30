#!/usr/bin/env python3
"""Split generated signal losses into reconstructed daughters and selections."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import awkward as ak
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import uproot

from check_charge_efficiency import generated_chains

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({"font.size": 11, "axes.labelsize": 12,
                     "axes.titlesize": 14, "xtick.labelsize": 10,
                     "ytick.labelsize": 10, "legend.fontsize": 10})

FIELDS = [
    "Particle/Particle.generatorStatus",
    "ReconstructedParticles/ReconstructedParticles.type",
    "ReconstructedParticles/ReconstructedParticles.charge",
    "ReconstructedParticles/ReconstructedParticles.tracks_begin",
    "ReconstructedParticles/ReconstructedParticles.tracks_end",
    "MCRecoAssociations#0/MCRecoAssociations#0.index",
    "MCRecoAssociations#1/MCRecoAssociations#1.index",
    "Photon#0/Photon#0.index",
]

STAGES = [
    ("generated", "Generated pπγ chain"),
    ("proton_track", "Proton or antiproton track"),
    ("both_tracks", "Both charged tracks"),
    ("three_objects", "Both tracks and photon"),
    ("selected_photon", "IDEA selected photon"),
    ("valid_pv", "Valid reconstructed PV"),
    ("nonprimary_tracks", "Both tracks outside PV set"),
    ("daughter_d0", "Both daughter d0 ≥ 3σ"),
    ("vertex_fit_valid", "Valid Λ0 vertex fit"),
    ("vertex_chi2", "SV χ² ≤ 9"),
    ("flight_distance", "SV flight Rxy ≥ 0.3 mm"),
    ("flight_significance", "SV flight significance ≥ 2"),
    ("lambda_mass_window", "Fitted Λ0 mass window"),
    ("closest_mass_hypothesis", "Closest fitted mass hypothesis"),
    ("lb_mass_window", "Λb fit mass interval"),
    ("same_hemisphere", "Photon in Λ0 thrust hemisphere"),
]
PLOT_STAGES = [stage for stage in STAGES if stage[0] in {
    "generated", "proton_track", "both_tracks", "three_objects",
    "selected_photon", "valid_pv", "nonprimary_tracks", "daughter_d0",
    "vertex_chi2", "lambda_mass_window", "same_hemisphere"}]


def component_flags(path, chains):
    counts = {label: Counter() for label in ("Lambda_b", "anti_Lambda_b")}
    event_flags = {label: {"three_objects": np.zeros(len(chains), dtype=bool),
                           "selected_photon": np.zeros(len(chains), dtype=bool)}
                   for label in counts}
    with uproot.open(str(path),
                     handler=uproot.source.file.MemmapSource) as root:
        arrays = root["events"].arrays(FIELDS, entry_stop=len(chains), library="ak")
    unpacked = [arrays[name] for name in FIELDS]
    for event_index, items in enumerate(zip(*unpacked)):
        status, reco_type, charge, track_begin, track_end, assoc_reco, assoc_mc, selected = (
            ak.to_list(item) for item in items)
        pairs = [(int(r), int(m)) for r, m in zip(assoc_reco, assoc_mc)
                 if 0 <= r < len(reco_type) and 0 <= m < len(status)]
        by_mc = {}
        for r, m in pairs:
            by_mc.setdefault(m, []).append(r)
        n_reco = Counter(r for r, _ in pairs)
        n_mc = Counter(m for _, m in pairs)
        unique = {m: r for r, m in pairs
                  if n_reco[r] == 1 and n_mc[m] == 1 and status[m] == 1}
        selected = set(selected)
        for chain in chains[event_index]:
            sign = chain["sign"]
            label = "Lambda_b" if sign > 0 else "anti_Lambda_b"
            counter = counts[label]
            counter["generated"] += 1
            p = unique.get(chain["proton"], -1)
            pi = unique.get(chain["pion"], -1)
            photon_indices = [unique.get(mc_index, -1)
                              for mc_index in chain["photons"]]
            if any(mc_index in by_mc for mc_index in chain["photons"]):
                counter["photon_any_association"] += 1
            if any(reco_type[r] == 22 and charge[r] == 0
                   for mc_index in chain["photons"]
                   for r in by_mc.get(mc_index, [])):
                counter["photon_any_usable_reco"] += 1
            proton_track = p >= 0 and charge[p] * sign > 0.5 and track_end[p] > track_begin[p]
            pion_track = pi >= 0 and charge[pi] * sign < -0.5 and track_end[pi] > track_begin[pi]
            if chain["proton"] in by_mc:
                counter["proton_any_association"] += 1
            if chain["pion"] in by_mc:
                counter["pion_any_association"] += 1
            if any(charge[r] * sign > 0.5 and track_end[r] > track_begin[r]
                   for r in by_mc.get(chain["proton"], [])):
                counter["proton_any_usable_track"] += 1
            if any(charge[r] * sign < -0.5 and track_end[r] > track_begin[r]
                   for r in by_mc.get(chain["pion"], [])):
                counter["pion_any_usable_track"] += 1
            usable_photons = [g for g in photon_indices if
                              g >= 0 and reco_type[g] == 22 and charge[g] == 0]
            photon = bool(usable_photons)
            if proton_track:
                counter["proton_track"] += 1
            if pion_track:
                counter["pion_track_marginal"] += 1
            if photon:
                counter["photon_marginal"] += 1
            if proton_track and pion_track:
                counter["both_tracks"] += 1
                if photon:
                    counter["three_objects"] += 1
                    event_flags[label]["three_objects"][event_index] = True
                    if any(g in selected for g in usable_photons):
                        counter["selected_photon"] += 1
                        event_flags[label]["selected_photon"][event_index] = True
    return counts, event_flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mc", type=Path, required=True)
    parser.add_argument("--cutflow", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with uproot.open(str(args.cutflow),
                     handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        n_events = tree.num_entries
        names = [f"{prefix}{name}" for prefix in ("positive_", "negative_")
                 for name in (["raw_truth_candidate", "selected_photon"] +
                              [stage for stage, _ in STAGES[5:]])]
        names += ["positive_true_vertex_chi2", "negative_true_vertex_chi2"]
        cutflow = tree.arrays(names, library="np")
    chains = generated_chains(args.mc, n_events)
    counts, event_flags = component_flags(args.mc, chains)
    for label, prefix in (("Lambda_b", "positive_"),
                          ("anti_Lambda_b", "negative_")):
        for name, _ in STAGES[5:]:
            counts[label][name] = int(np.count_nonzero(cutflow[prefix + name]))
        if counts[label]["three_objects"] != int(np.count_nonzero(
                cutflow[prefix + "raw_truth_candidate"])):
            different = np.flatnonzero(event_flags[label]["three_objects"] !=
                                       cutflow[prefix + "raw_truth_candidate"].astype(bool))
            raise ValueError(f"Component and FCCAnalyses raw-match counts disagree for {label}: "
                             f"components={counts[label]['three_objects']}, "
                             f"cutflow={np.count_nonzero(cutflow[prefix + 'raw_truth_candidate'])}, "
                             f"different_events={different.tolist()[:10]}")
        if counts[label]["selected_photon"] != int(np.count_nonzero(
                cutflow[prefix + "selected_photon"])):
            raise ValueError(f"Component and FCCAnalyses photon counts disagree for {label}")
        values = [counts[label][name] for name, _ in STAGES]
        if any(next_count > prior for prior, next_count in zip(values, values[1:])):
            raise ValueError(f"Non-cumulative signal stages for {label}")

    total = Counter(counts["Lambda_b"]) + Counter(counts["anti_Lambda_b"])
    chi2_values = np.concatenate([
        cutflow[prefix + "true_vertex_chi2"][
            cutflow[prefix + "vertex_fit_valid"] == 1]
        for prefix in ("positive_", "negative_")])
    if len(chi2_values) != total["vertex_fit_valid"]:
        raise ValueError("Valid vertex count differs from χ² values")
    chi2_scan = {str(bound): int(np.count_nonzero(chi2_values <= bound))
                 for bound in (4, 9, 16, 25, 50, 100)}
    if chi2_scan["9"] != total["vertex_chi2"]:
        raise ValueError("χ² ≤ 9 scan disagrees with cutflow")
    result = {
        "generated_events": n_events,
        "generated_direct_signal_decays": total["generated"],
        "reconstructible_definition": "unique bidirectional MC-reco links to both charged tracks and one type-22 photon; includes detector acceptance and reconstruction, not generator-only geometric acceptance",
        "charge_counts": {label: dict(value) for label, value in counts.items()},
        "total_counts": dict(total),
        "vertex_chi2_scan": {
            "valid_true_vertices": len(chi2_values),
            "passing_by_max_chi2": chi2_scan,
            "median": float(np.median(chi2_values)),
            "q90": float(np.quantile(chi2_values, 0.9)),
        },
        "stages": [
            {"name": name, "label": label, "decays": total[name],
             "cumulative_efficiency": total[name] / total["generated"],
             "conditional_efficiency": total[name] /
                 (total[STAGES[i - 1][0]] if i else total["generated"])
                 if (total[STAGES[i - 1][0]] if i else total["generated"]) else 0.}
            for i, (name, label) in enumerate(STAGES)
        ],
    }
    (args.output_dir / "signal_loss_audit.json").write_text(
        json.dumps(result, indent=2) + "\n")

    fig, ax = plt.subplots(figsize=(10.5, 7))
    y = np.arange(len(PLOT_STAGES))
    values = [100 * total[name] / total["generated"] for name, _ in PLOT_STAGES]
    ax.barh(y, values, color="#177cab", alpha=0.85)
    for i, (value, (name, _)) in enumerate(zip(values, PLOT_STAGES)):
        ax.text(value + 1.5, i, str(total[name]), va="center", fontsize=9)
    ax.set(yticks=y, yticklabels=[label for _, label in PLOT_STAGES],
           xlabel="Generated direct signal decays retained [%]",
           title="Where Λb→Λ0(pπ)γ signal decays are lost",
           xlim=(0, 110))
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(args.output_dir / "signal_loss_audit.png", dpi=160,
                bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(chi2_values, bins=np.linspace(0, 100, 101), histtype="step",
            linewidth=1.5, color="C0", label="True Λ0 pairs before χ² cut")
    ax.axvline(9, color="C1", linestyle="--", linewidth=1.5,
               label="Current χ² ≤ 9")
    ax.set(xlabel="Two-track SV χ² / ndf", ylabel="Generated signal decays / bin",
           title="Fitted true Λ0 vertex quality", xlim=(0, 100))
    ax.set_yscale("log")
    ax.set_ylim(bottom=0.8)
    ax.text(0.98, 0.96, f"{int(np.count_nonzero(chi2_values > 100))} entries above 100",
            transform=ax.transAxes, ha="right", va="top", fontsize=10)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "true_vertex_chi2.png", dpi=160,
                bbox_inches="tight")
    plt.close(fig)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
