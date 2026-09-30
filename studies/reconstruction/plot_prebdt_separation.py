#!/usr/bin/env python3
"""Pre-BDT candidate overlays after the unchanged Lambda-gamma stage-1 selection.

Each curve is divided by all candidates in its labelled class, including
entries outside the displayed range and missing values. The forced samples
are deliberately not yield-normalized to inclusive Zbb. No threshold is
learned or applied by this script.
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
plt.rcParams.update({"font.size": 11, "axes.labelsize": 12,
                     "axes.titlesize": 13, "legend.fontsize": 10,
                     "xtick.labelsize": 10, "ytick.labelsize": 10})

CLASSES = (
    ("True $\\Lambda_b\\to\\Lambda\\gamma$", "signal_gamma", 1, "#277DA1"),
    ("Signal wrong combinations", "signal_gamma", -1, "#F3722C"),
    ("True $\\Lambda\\eta$ feed-down", "specific_eta", 2, "#7A5195"),
    ("$Z\\to b\\bar b$ combinations", "generic_zbb", 0, "#43AA8B"),
)


def spec(name, label, low, high, *, log=False, discrete=False, note=""):
    return {"name": name, "label": label, "low": low, "high": high,
            "log": log, "discrete": discrete, "note": note}


PANELS = {
    "mass_kinematics": (
        spec("m_LamGam", r"$m(\Lambda\gamma)$ [GeV]", 4.9, 6.3),
        spec("lambda_mass", r"Fitted $m(p\pi)$ [GeV]", 0.7, 1.3),
        spec("lb_pt", r"$p_T(\Lambda\gamma)$ [GeV]", 0., 45.),
        spec("photon_reco_energy", r"$E_\gamma$ [GeV]", 2., 42.),
    ),
    "isolation": (
        spec("iso_R03_noLambda", r"$I_{0.3}^{\mathrm{no}\,\Lambda}$", 0., 3.),
        spec("iso_R05_noLambda", r"$I_{0.5}^{\mathrm{no}\,\Lambda}$", 0., 4.),
        spec("iso_charged", r"Charged $I_{0.3}^{\mathrm{no}\,\Lambda}$", 0., 3.),
        spec("n_photons_DR03", r"Other photons, $\Delta R<0.3$", 0., 6., discrete=True),
    ),
    "recoil": (
        spec("m_rec", r"$m(p_Z-p_{\rm other})$ [GeV]", 0., 75.),
        spec("deltaE", r"$E_{\Lambda\gamma}+E_{\rm other}-E_{\rm CM}$ [GeV]", -65., 5.),
        spec("E_same", r"Leftover signal-side energy [GeV]", 0., 52.),
        spec("Estar_gamma_rec", r"$E^*_{\gamma}(p_{\rm rec})$ [GeV]", 0., 20.),
    ),
    "lambda_topology": (
        spec("lambda_flight_rxy", r"$R_{xy}({\rm PV}\to{\rm SV}_\Lambda)$ [mm]", .3, 2000., log=True),
        spec("lambda_flight_rxy_sig", r"$R_{xy}/\sigma_{R_{xy}}$", 2., 8000., log=True),
        spec("lambda_vertex_chi2", r"Fitted $\Lambda$ SV $\chi^2$", 0., 9.),
        spec("lambda_pv_dca", r"Fitted $\Lambda$ line DCA to PV [mm]", 0., 3.),
    ),
    "daughter_displacement": (
        spec("proton_d0sig", r"Proton $|d_0|/\sigma_{d_0}$", 3., 1000., log=True),
        spec("pion_d0sig", r"Pion $|d_0|/\sigma_{d_0}$", 3., 2500., log=True),
        spec("lambda_flight_xyz", r"$L_{xyz}({\rm PV}\to{\rm SV}_\Lambda)$ [mm]", .3, 2500., log=True),
        spec("lambda_pv_cos", r"$\cos(\vec{p}_\Lambda,{\rm PV}\to{\rm SV}_\Lambda)$", .95, 1.00001,
             note="Diagnostic only: no PV-pointing cut."),
    ),
    "photon_pairing": (
        spec("dm_gg_pi0", r"$|m(\gamma\gamma')-m_{\pi^0}|$ [GeV]", 0., .5,
             note="No partner is absent from bars and remains in denominator."),
        spec("n_photons_DR05", r"Other photons, $\Delta R<0.5$", 0., 6., discrete=True),
        spec("iso_neutral", r"Neutral $I_{0.3}^{\mathrm{no}\,\Lambda}$", 0., 3.),
        spec("dca_Lam_gamma", r"$\Lambda$--$\gamma$ line DCA proxy [mm]", 0., 2.,
             note="Photon ray is assumed from PV; not a measured photon vertex."),
    ),
}


def masks(table):
    samples = np.asarray(table["sample_id"].to_pylist())
    labels = table["class_id"].to_numpy()
    return [(title, (samples == sample) & (labels == class_id), color)
            for title, sample, class_id, color in CLASSES]


def make_panel(table, groups, title, specs, output):
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 7.3))
    for ax, item in zip(axes.flat, specs):
        values = table[item["name"]].to_numpy().astype(float)
        if item["discrete"]:
            bins = np.arange(item["low"] - .5, item["high"] + .5, 1.)
        elif item["log"]:
            bins = np.geomspace(item["low"], item["high"], 42)
            ax.set_xscale("log")
        else:
            bins = np.linspace(item["low"], item["high"], 47)
        for label, mask, color in groups:
            selected = values[mask]
            valid = np.isfinite(selected) & (selected > -998.)
            if selected.size:
                ax.hist(selected[valid], bins=bins,
                        weights=np.full(valid.sum(), 1. / selected.size),
                        histtype="step", linewidth=1.5, color=color,
                        label=f"{label} ({selected.size:,})")
        ax.set(xlabel=item["label"], ylabel="Fraction of class / bin", ylim=(0, None))
        if item["note"]:
            ax.text(.98, .96, item["note"], transform=ax.transAxes,
                    ha="right", va="top", fontsize=7.5,
                    bbox={"facecolor": "white", "alpha": .8, "edgecolor": "none"})
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.suptitle(title, y=.99, fontsize=17)
    fig.legend(handles, labels, loc="upper center", ncol=2,
               bbox_to_anchor=(.5, .955), frameon=False)
    fig.text(.5, .012,
             "Same stage-1 candidate selection; each class normalized to its own full candidate count; no BDT cut",
             ha="center", fontsize=10)
    fig.tight_layout(rect=(0, .035, 1, .875), h_pad=1.1, w_pad=1.2)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="candidate_audit.parquet from prepare_training_inputs.py")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    columns = ["sample_id", "class_id"] + [item["name"] for group in
              PANELS.values() for item in group]
    table = pq.read_table(args.input, columns=list(dict.fromkeys(columns)))
    groups = masks(table)
    titles = {
        "mass_kinematics": "Mass and candidate kinematics",
        "isolation": "Candidate-photon isolation after removing Lambda daughters",
        "recoil": "Z-pole recoil and opposite/same hemisphere energy",
        "lambda_topology": "Fitted Lambda displacement and vertex quality",
        "daughter_displacement": "Daughter-track displacement and Lambda geometry",
        "photon_pairing": "Other photons and photon-origin diagnostic",
    }
    for name, specs in PANELS.items():
        make_panel(table, groups, titles[name], specs,
                   args.output_dir / f"{name}.png")
    summary = {"input": str(args.input), "candidate_rows": table.num_rows,
               "categories": {title: int(mask.sum()) for title, mask, _ in groups},
               "normalization": "each class divided by its full selected-candidate count; missing and out-of-range entries remain in denominator",
               "applied_selection": "unchanged stage-1 reconstruction only; no observable or BDT cut",
               "panels": {name: [item["name"] for item in specs]
                          for name, specs in PANELS.items()}}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
