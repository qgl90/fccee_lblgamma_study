#!/usr/bin/env python3
"""Audit Zss candidate ancestry after the frozen v3 BDT and veto sequence.

Every cut is reconstructed-only. Truth identifies the origin of surviving
track pairs and photons after selection; it never determines retention.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from study_v3_post_bdt_armenteros import ancestry
from study_v3_post_bdt_veto_sequence import stages, STAGES
import v3_plot_style  # noqa: F401


COLUMNS = ("source_id", "event_entry", "candidate_slot", "truth_matched",
           "bdt_score", "lb_mass", "arm_alpha", "arm_qt", "pass_pi0",
           "pass_eta", "proton_mc_pdg", "pion_mc_pdg", "photon_mc_pdg",
           "proton_mc_parent_pdg", "pion_mc_parent_pdg",
           "proton_mc_parent_index", "pion_mc_parent_index",
           "proton_mc_grandparent_pdg", "photon_mc_index",
           "photon_mc_parent_index", "photon_mc_parent_pdg",
           "photon_mc_grandparent_pdg")
PAIR_ORDER = ("Kshort pi/pi assigned p/pi", "True Lambda pair",
              "p/pi identities, other ancestry", "Other or unmatched pair")
PHOTON_ORDER = ("pi0 photon", "eta photon", "direct Lambda_b photon",
                "Other or unmatched photon")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_one(path):
    return pq.read_table(path, columns=list(COLUMNS)).to_pandas()


def categories(frame, column, order):
    counts = frame[column].value_counts().to_dict()
    return {key: int(counts.get(key, 0)) for key in order}


def top_abs_pdg(frame, column, limit=12):
    return {str(int(k)): int(v) for k, v in
            frame[column].abs().value_counts().head(limit).items()}


def figure(result, key, order, outpath):
    labels = ("BDT", "+ Arm.", "+ pi0", "+ eta")
    values = np.array([[result[stage][key][label] for label in order]
                       for stage in STAGES], dtype=int)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    bottom = np.zeros(len(STAGES), dtype=int)
    colors = ("#bb4e50", "#3175a8", "#c99b45", "#777777")
    display = {"Kshort pi/pi assigned p/pi": r"$K^0_S\to\pi\pi$ assigned $p\pi$",
               "True Lambda pair": r"True $\Lambda\to p\pi$ pair",
               "p/pi identities, other ancestry": r"$p/\pi$ identities, other ancestry",
               "Other or unmatched pair": "Other or unmatched pair",
               "pi0 photon": r"$\pi^0$ photon", "eta photon": r"$\eta$ photon",
               "direct Lambda_b photon": r"Direct $\Lambda_b$ photon",
               "Other or unmatched photon": "Other or unmatched photon"}
    for j, label in enumerate(order):
        ax.bar(labels, values[:, j], bottom=bottom, label=display[label],
               color=colors[j], width=.65)
        bottom += values[:, j]
    ax.set(ylabel="Raw nonmatched Zss candidate rows, 5.4–5.9 GeV",
           title=("Track-pair truth origin" if key == "pair_origin" else
                  "Selected-photon truth origin") + " after reconstructed cuts")
    ax.tick_params(axis="x", length=0)
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=.2)
    ax.legend(frameon=False, fontsize=9, ncol=2)
    fig.tight_layout()
    fig.savefig(outpath, dpi=180)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zss-summary", type=Path, required=True)
    ap.add_argument("--projection", type=Path, required=True)
    ap.add_argument("--config", type=Path,
                    default=Path("config/v3_post_bdt_veto_sequence.json"))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    if args.workers < 1:
        ap.error("workers must be positive")
    summary = json.loads(args.zss_summary.read_text())
    projection = json.loads(args.projection.read_text())
    cfg = json.loads(args.config.read_text())
    score = float(projection["validation_choice"]["score"])
    if (summary["sample"] != "zss" or not summary["complete_catalog"] or
            summary["run_identity"]["score_cut"] != score or
            summary["run_identity"]["model_sha256"] != projection["model_sha256"]):
        raise ValueError("Zss output is not the complete frozen BDT sample")
    paths = sorted(args.zss_summary.parent.glob("chunks/chunk_*/bdt_selected.parquet"))
    if len(paths) != summary["input_chunks"]:
        raise ValueError("Missing Zss BDT chunk table")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        frame = pd.concat(pool.map(read_one, paths), ignore_index=True)
    if len(frame) != summary["stage_counts"]["bdt_selected"]["candidate_rows"]:
        raise ValueError("BDT candidate rows disagree with complete summary")
    if frame.duplicated(["source_id", "event_entry", "candidate_slot"]).any():
        raise ValueError("Repeated candidate key")
    if (frame.bdt_score < score).any():
        raise ValueError("BDT table has a score below the frozen cut")
    frame = ancestry(frame.loc[frame.truth_matched != 1].copy())
    mask_by_stage = stages(frame, cfg["armenteros_reject_box"])
    peak = frame.lb_mass.between(*cfg["mass_window_gev"])
    weight = cfg["N_Z"] * cfg["branching_fractions"]["Zss"] / summary["processed_input_events"]
    results = {}
    for stage in STAGES:
        subset = frame.loc[mask_by_stage[stage] & peak].copy()
        ks = subset.pair_origin.eq("Kshort pi/pi assigned p/pi")
        pair_parent = subset.loc[(subset.proton_mc_parent_index >= 0) &
                                 (subset.proton_mc_parent_index == subset.pion_mc_parent_index),
                                 "proton_mc_parent_pdg"].abs().value_counts().head(12)
        lam = subset.pair_origin.eq("True Lambda pair")
        other_gamma = subset.photon_origin.eq("Other or unmatched photon")
        results[stage] = {
            "candidate_rows": int(len(subset)),
            "candidate_bearing_events": int(subset[["source_id", "event_entry"]]
                                            .drop_duplicates().shape[0]),
            "expected_candidates": float(len(subset) * weight),
            "pair_origin": categories(subset, "pair_origin", PAIR_ORDER),
            "photon_origin": categories(subset, "photon_origin", PHOTON_ORDER),
            "kshort_pair_by_photon_origin": categories(subset.loc[ks],
                                                         "photon_origin", PHOTON_ORDER),
            "same_parent_track_pair_abs_pdg_top12": {
                str(int(k)): int(v) for k, v in pair_parent.items()},
            "true_lambda_parent_abs_pdg_top12": top_abs_pdg(
                subset.loc[lam], "proton_mc_grandparent_pdg"),
            "selected_photon_abs_parent_pdg_top12": top_abs_pdg(
                subset, "photon_mc_parent_pdg"),
            "other_photon_abs_parent_pdg_top12": top_abs_pdg(
                subset.loc[other_gamma], "photon_mc_parent_pdg"),
            "other_photon_no_mc_match": int((subset.loc[other_gamma,
                                                        "photon_mc_index"] < 0).sum()),
            "pair_by_photon_origin": {
                pair: categories(subset.loc[subset.pair_origin.eq(pair)],
                                 "photon_origin", PHOTON_ORDER)
                for pair in PAIR_ORDER},
        }
    output = {"zss_summary": str(args.zss_summary),
              "zss_summary_sha256": digest(args.zss_summary),
              "projection": str(args.projection),
              "projection_sha256": digest(args.projection),
              "config": str(args.config), "config_sha256": digest(args.config),
              "input_chunks": len(paths),
              "processed_input_events": summary["processed_input_events"],
              "score_cut": score, "candidate_weight": weight,
              "mass_window_gev": cfg["mass_window_gev"],
              "truth_use": "Ancestry labels only after reconstructed BDT and veto cuts",
              "stages": results}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "zss_ancestry.json").write_text(json.dumps(output, indent=2) + "\n")
    figure(results, "pair_origin", PAIR_ORDER,
           args.output_dir / "zss_peak_pair_origin.png")
    figure(results, "photon_origin", PHOTON_ORDER,
           args.output_dir / "zss_peak_photon_origin.png")
    print(json.dumps({stage: {"candidate_rows": row["candidate_rows"],
                              "pair_origin": row["pair_origin"]}
                      for stage, row in results.items()}, indent=2))


if __name__ == "__main__":
    main()
