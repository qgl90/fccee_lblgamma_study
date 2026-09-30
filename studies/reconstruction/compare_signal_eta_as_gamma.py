#!/usr/bin/env python3
"""Compare gamma signal with eta events reconstructed under the gamma hypothesis.

The two Parquet files must come from the same lb2lambda_gamma_reco.py selection.
The eta label below is diagnostic MC ancestry only; it never affects selection.
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
import pyarrow.parquet as pq

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({
    "font.size": 12, "axes.labelsize": 13, "axes.titlesize": 14,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 10,
})


def columns(path, names):
    table = pq.read_table(path, columns=names)
    return {name: table[name].to_numpy(zero_copy_only=False) for name in names}


ETA_ANCESTRY_COLUMNS = [
    "lb_sign", "proton_mc_pdg", "pion_mc_pdg", "proton_mc_parent_pdg",
    "pion_mc_parent_pdg", "proton_mc_parent_index", "pion_mc_parent_index",
    "proton_mc_grandparent_pdg", "proton_mc_grandparent_index",
    "pion_mc_grandparent_index", "photon_mc_pdg",
    "photon_mc_parent_pdg", "photon_mc_grandparent_pdg",
    "photon_mc_grandparent_index",
]


def true_partial_eta_mask(eta):
    """Truth label for Λ⁰ plus one photon from its sibling η daughter."""
    q = eta["lb_sign"]
    true_lambda = (
        (eta["proton_mc_pdg"] == q * 2212) &
        (eta["pion_mc_pdg"] == -q * 211) &
        (eta["proton_mc_parent_pdg"] == q * 3122) &
        (eta["pion_mc_parent_pdg"] == q * 3122) &
        (eta["proton_mc_parent_index"] >= 0) &
        (eta["proton_mc_parent_index"] == eta["pion_mc_parent_index"]) &
        (eta["proton_mc_grandparent_pdg"] == q * 5122) &
        (eta["proton_mc_grandparent_index"] >= 0) &
        (eta["proton_mc_grandparent_index"] ==
         eta["pion_mc_grandparent_index"]))
    eta_photon = (
        (eta["photon_mc_pdg"] == 22) &
        (eta["photon_mc_parent_pdg"] == 221) &
        (eta["photon_mc_grandparent_pdg"] == q * 5122) &
        (eta["photon_mc_grandparent_index"] ==
         eta["proton_mc_grandparent_index"]))
    return true_lambda & eta_photon


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal", type=Path, required=True)
    parser.add_argument("--eta-as-gamma", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    signal = columns(args.signal, ["lb_mass", "truth_matched"])
    eta = columns(args.eta_as_gamma,
                  ["lb_mass", "truth_matched"] + ETA_ANCESTRY_COLUMNS)
    true_partial_eta = true_partial_eta_mask(eta)
    if np.any(eta["truth_matched"] == 1):
        raise ValueError("Eta-as-gamma sample contains a direct-gamma truth match")
    if not np.all((signal["lb_mass"] >= 4.9) & (signal["lb_mass"] <= 6.3)):
        raise ValueError("Signal candidate outside final fit range")
    if not np.all((eta["lb_mass"] >= 4.9) & (eta["lb_mass"] <= 6.3)):
        raise ValueError("Eta candidate outside final fit range")

    edges = np.linspace(4.9, 6.3, 71)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for values, label, color in (
        (signal["lb_mass"][signal["truth_matched"] == 1],
         r"Truth-matched $\Lambda_b\to\Lambda^0\gamma$", "C0"),
        (eta["lb_mass"][true_partial_eta],
         r"True $\Lambda_b\to\Lambda^0\eta$, one $\gamma$ used", "C1"),
        (eta["lb_mass"][~true_partial_eta],
         r"Other $\eta$-sample combinations", "C2"),
    ):
        ax.stairs(np.histogram(values, edges)[0], edges, label=label,
                  color=color, linewidth=1.5)
    ax.set(xlabel=r"Reconstructed $m(p\pi\gamma)$ [GeV]",
           ylabel="Candidates / 20 MeV",
           title=r"Same $\Lambda^0\gamma$ selection on signal and $\Lambda^0\eta$ samples")
    ax.set_xlim(4.9, 6.3)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "signal_vs_eta_as_gamma.png", dpi=160,
                bbox_inches="tight")
    plt.close(fig)

    result = {
        "signal_file": str(args.signal),
        "eta_as_gamma_file": str(args.eta_as_gamma),
        "fit_range_gev": [4.9, 6.3],
        "signal_candidates": len(signal["lb_mass"]),
        "signal_truth_matched": int(np.count_nonzero(signal["truth_matched"])),
        "eta_as_gamma_candidates": len(eta["lb_mass"]),
        "eta_true_partial_candidates": int(np.count_nonzero(true_partial_eta)),
        "eta_other_combinations": int(np.count_nonzero(~true_partial_eta)),
        "normalization": "Raw candidate counts in first 1000 events of each sample; no branching fraction or production-rate scaling",
    }
    (args.output_dir / "signal_vs_eta_as_gamma.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
