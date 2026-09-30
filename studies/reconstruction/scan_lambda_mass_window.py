#!/usr/bin/env python3
"""Scan a post-reconstruction Lambda0 mass cut on signal and generic Zbb.

The builder keeps the broad 0.7–1.3 GeV window. This script applies an
additional symmetric window to candidate-level Parquet tables. Truth fields
are used only to report retention and the origin of surviving combinations.
"""

import argparse
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
import pyarrow as pa
import pyarrow.parquet as pq

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({"font.size": 12, "axes.labelsize": 12,
                     "axes.titlesize": 13, "legend.fontsize": 10})

WINDOWS_MEV = (5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200, 300)


def true_lambda_mask(table):
    """Diagnostic for a correct signed pπ pair from the same generated Λ0."""
    p = table["proton_mc_parent_index"].to_numpy()
    pi = table["pion_mc_parent_index"].to_numpy()
    parent_pdg = table["proton_mc_parent_pdg"].to_numpy()
    correct_mass = table["mass_hypothesis_correct"].to_numpy() == 1
    return (p >= 0) & (p == pi) & (np.abs(parent_pdg) == 3122) & correct_mass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal", type=Path, required=True)
    parser.add_argument("--zbb", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--apply-window-mev", type=float, default=10.)
    parser.add_argument("--lambda-mass-gev", type=float, default=1.115683)
    args = parser.parse_args()
    if args.apply_window_mev <= 0:
        raise ValueError("Window half-width must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    signal = pq.read_table(args.signal)
    zbb = pq.read_table(args.zbb)
    s = signal.to_pydict()
    b = zbb.to_pydict()
    s_delta = np.abs(np.asarray(s["lambda_mass"]) - args.lambda_mass_gev) * 1000
    b_delta = np.abs(np.asarray(b["lambda_mass"]) - args.lambda_mass_gev) * 1000
    truth = np.asarray(s["truth_matched"]) == 1
    true_lambda = true_lambda_mask(zbb)
    b_entries = np.asarray(b["event_entry"])
    scan = []
    for width in WINDOWS_MEV:
        s_keep = s_delta <= width
        b_keep = b_delta <= width
        row = {
            "half_window_mev": width,
            "signal_truth_matched": int(np.count_nonzero(s_keep & truth)),
            "signal_other_combinations": int(np.count_nonzero(s_keep & ~truth)),
            "zbb_candidates": int(np.count_nonzero(b_keep)),
            "zbb_events_with_candidate": int(len(np.unique(b_entries[b_keep]))),
            "zbb_candidates_with_true_lambda": int(np.count_nonzero(
                b_keep & true_lambda)),
        }
        row["signal_truth_retention"] = row["signal_truth_matched"] / int(truth.sum())
        row["zbb_candidate_retention"] = row["zbb_candidates"] / len(b_delta)
        scan.append(row)

    s_keep = s_delta <= args.apply_window_mev
    b_keep = b_delta <= args.apply_window_mev
    signal_output = args.output_dir / "signal_lambda_window.parquet"
    zbb_output = args.output_dir / "zbb_lambda_window.parquet"
    pq.write_table(signal.filter(pa.array(s_keep)), signal_output, compression="zstd")
    pq.write_table(zbb.filter(pa.array(b_keep)), zbb_output, compression="zstd")
    result = {
        "mass_reference_gev": args.lambda_mass_gev,
        "selection": "abs(fitted lambda_mass - mass_reference) <= half_window",
        "signal_input": str(args.signal), "zbb_input": str(args.zbb),
        "baseline": {
            "signal_truth_matched": int(truth.sum()),
            "signal_other_combinations": int((~truth).sum()),
            "zbb_candidates": len(b_delta),
            "zbb_events_with_candidate": int(len(np.unique(b_entries))),
            "zbb_candidates_with_true_lambda": int(true_lambda.sum()),
        },
        "applied_half_window_mev": args.apply_window_mev,
        "applied": {
            "signal_truth_matched": int(np.count_nonzero(s_keep & truth)),
            "signal_other_combinations": int(np.count_nonzero(s_keep & ~truth)),
            "zbb_candidates": int(np.count_nonzero(b_keep)),
            "zbb_events_with_candidate": int(len(np.unique(b_entries[b_keep]))),
            "zbb_candidates_with_true_lambda": int(np.count_nonzero(
                b_keep & true_lambda)),
        },
        "scan": scan,
        "signal_output": str(signal_output), "zbb_output": str(zbb_output),
    }
    (args.output_dir / "lambda_mass_scan.json").write_text(
        json.dumps(result, indent=2) + "\n")

    fig, ax = plt.subplots(figsize=(9, 5.8))
    ax.hist(s_delta[truth], bins=np.linspace(0, 100, 51), histtype="step",
            label="Truth-matched signal")
    ax.hist(s_delta[~truth], bins=np.linspace(0, 100, 51), histtype="step",
            label="Other signal-sample combinations")
    ax.hist(b_delta, bins=np.linspace(0, 100, 51), histtype="step",
            label="Generic Zbb candidates")
    ax.axvline(args.apply_window_mev, linestyle="--", color="0.4",
               label=f"±{args.apply_window_mev:g} MeV working point")
    ax.set(xlabel=r"$|m(p\pi)-m(\Lambda^0)|$ [MeV]",
           ylabel="Candidates / 2 MeV", yscale="log",
           title="Fitted-vertex Λ⁰ mass distance")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "lambda_mass_distributions.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    ax.plot([row["half_window_mev"] for row in scan],
            [row["signal_truth_retention"] for row in scan],
            marker="o", label="Truth-matched signal retention")
    ax.plot([row["half_window_mev"] for row in scan],
            [row["zbb_candidate_retention"] for row in scan],
            marker="s", label="Generic Zbb candidate retention")
    ax.axvline(args.apply_window_mev, linestyle="--", color="0.4")
    ax.set(xlabel="Λ⁰ mass half-window [MeV]", ylabel="Fraction of baseline candidates",
           xlim=(0, max(WINDOWS_MEV)), ylim=(0, 1.05),
           title="Post-reconstruction Λ⁰ mass-window scan")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "lambda_mass_retention.png", dpi=160)
    plt.close(fig)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
