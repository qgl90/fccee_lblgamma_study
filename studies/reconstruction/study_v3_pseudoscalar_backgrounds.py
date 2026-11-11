#!/usr/bin/env python3
"""Compare forced Lambda eta/pi0 one-photon backgrounds through a fixed v3 BDT.

Each input is a separately generated forced sample. Candidate construction,
offline cuts and BDT were already performed without MC identity. This script
uses ancestry only to classify selected rows and scales the forced-sample
rates with explicitly sourced branching-fraction scenarios.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2

import v3_plot_style  # noqa: F401


STAGES = ("audit", "offline_selected", "bdt_selected")
COLS = ("source_id", "event_entry", "candidate_slot", "lb_sign", "lb_mass",
        "cos_theta_p", "bdt_score", "proton_mc_parent_index", "pion_mc_parent_index",
        "proton_mc_parent_pdg", "pion_mc_parent_pdg",
        "proton_mc_grandparent_index", "pion_mc_grandparent_index",
        "proton_mc_grandparent_pdg", "pion_mc_grandparent_pdg",
        "photon_mc_parent_pdg", "photon_mc_grandparent_index",
        "photon_mc_grandparent_pdg")


def direct_partial(frame, meson_pdg):
    sign = frame.lb_sign
    lb = frame.proton_mc_grandparent_index
    return (frame.proton_mc_parent_index.ge(0) &
            frame.proton_mc_parent_index.eq(frame.pion_mc_parent_index) &
            frame.proton_mc_parent_pdg.eq(3122*sign) &
            frame.pion_mc_parent_pdg.eq(3122*sign) &
            lb.ge(0) & lb.eq(frame.pion_mc_grandparent_index) &
            lb.eq(frame.photon_mc_grandparent_index) &
            frame.proton_mc_grandparent_pdg.eq(5122*sign) &
            frame.pion_mc_grandparent_pdg.eq(5122*sign) &
            frame.photon_mc_grandparent_pdg.eq(5122*sign) &
            frame.photon_mc_parent_pdg.eq(meson_pdg))


def summarize(frame, mask, window, generated_decays):
    peak = frame.lb_mass.between(*window)
    result = {"candidate_rows": len(frame),
              "candidate_bearing_events": frame.event_entry.nunique(),
              "direct_partial_candidate_rows": int(mask.sum()),
              "direct_partial_events": frame.loc[mask, "event_entry"].nunique(),
              "wrong_or_unmatched_candidate_rows": int((~mask).sum()),
              "peak_candidate_rows": int(peak.sum()),
              "peak_candidate_events": frame.loc[peak, "event_entry"].nunique(),
              "peak_direct_partial_rows": int((peak & mask).sum()),
              "peak_direct_partial_events": frame.loc[peak & mask, "event_entry"].nunique(),
              "peak_wrong_or_unmatched_rows": int((peak & ~mask).sum())}
    result["candidate_rate_per_generated_decay_full_mass"] = len(frame)/generated_decays
    result["candidate_rate_per_generated_decay_peak"] = int(peak.sum())/generated_decays
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("eta_phsp", "eta_physics", "pi0_physics"), required=True)
    ap.add_argument("--stage2-manifest", type=Path, required=True)
    ap.add_argument("--generated-audit", type=Path, required=True)
    ap.add_argument("--branching-config", type=Path, default=Path("config/v3_pseudoscalar_branching_scenarios.json"))
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    manifest = json.loads(args.stage2_manifest.read_text())
    audit = json.loads(args.generated_audit.read_text())
    config = json.loads(args.branching_config.read_text())
    mode = config["modes"][args.mode]
    expected_mode = "eta" if args.mode.startswith("eta") else "pi0"
    if audit["mode"] != expected_mode or audit["processed_events"] != 100000 or \
            audit["generated_direct_decays"] < 100000:
        raise ValueError("Expected a complete 100k generated forced-mode audit")
    if manifest["record"]["events_processed"] != 100000 or manifest["max_output_events"] is not None:
        raise ValueError("Stage 2 is not a complete 100k run")
    if manifest.get("bdt_score_cut") is None:
        raise ValueError("Stage 2 manifest has no fixed BDT score")
    if "v3" not in str(Path(manifest["input"])):
        raise ValueError("Stage 1 input path must identify v3")
    window = config["signal_mass_window_gev"]
    stem = f"{manifest['sample']}_{manifest['source_id']}"
    root = args.stage2_manifest.parent
    tables = {}
    counts = {}
    for stage in STAGES:
        path = root / stage / f"{stem}.parquet"
        frame = pd.read_parquet(path, columns=list(COLS))
        if len(frame) != manifest["counts"][stage]:
            raise ValueError(f"{stage} row count differs from manifest")
        if frame.duplicated(["source_id", "event_entry", "candidate_slot"]).any():
            raise ValueError(f"{stage} has repeated candidate keys")
        mask = direct_partial(frame, mode["meson_pdg"])
        frame["direct_partial"] = mask
        tables[stage] = frame
        counts[stage] = summarize(frame, mask, window, audit["generated_direct_decays"])
    for parent, child in zip(STAGES[:-1], STAGES[1:]):
        p, c = counts[parent], counts[child]
        c["conditional_candidate_retention"] = c["candidate_rows"]/p["candidate_rows"]
        c["conditional_candidate_bearing_event_retention"] = (
            c["candidate_bearing_events"]/p["candidate_bearing_events"])
        c["conditional_direct_partial_retention"] = (
            c["direct_partial_candidate_rows"]/p["direct_partial_candidate_rows"]
            if p["direct_partial_candidate_rows"] else None)
        c["cumulative_candidate_retention_from_stage1"] = c["candidate_rows"]/counts["audit"]["candidate_rows"]
        c["cumulative_candidate_bearing_event_retention_from_stage1"] = (
            c["candidate_bearing_events"]/counts["audit"]["candidate_bearing_events"])
    factor = (config["N_Z"] * config["BR_Zbb"] * 2 * config["f_Lambdab_per_b"] *
              mode["BR_Lambdab_to_Lambda_meson"] * config["BR_Lambda_to_p_pi"] *
              mode["BR_meson_to_gamma_gamma"])
    final = counts["bdt_selected"]
    generated = audit["generated_direct_decays"]
    projection = {"factor_before_selection": factor,
                  "peak_candidates": factor*final["peak_candidate_rows"]/generated,
                  "peak_direct_partial": factor*final["peak_direct_partial_rows"]/generated,
                  "peak_wrong_or_unmatched": factor*final["peak_wrong_or_unmatched_rows"]/generated,
                  "full_mass_candidates": factor*final["candidate_rows"]/generated,
                  "peak_candidates_per_1e_minus_6_parent_br": (
                      factor*final["peak_candidate_rows"]/generated/
                      mode["BR_Lambdab_to_Lambda_meson"]*1e-6)}
    peak_count = final["peak_candidate_rows"]
    scale = factor/generated
    projection["peak_candidates_mc_95pct_poisson_interval"] = [
        (0.5*chi2.ppf(.025, 2*peak_count) if peak_count else 0.)*scale,
        0.5*chi2.ppf(.975, 2*(peak_count+1))*scale]
    if "BR_Lambdab_to_Lambda_meson_range" in mode:
        projection["peak_candidates_parent_br_range"] = [
            projection["peak_candidates"]*branch/mode["BR_Lambdab_to_Lambda_meson"]
            for branch in mode["BR_Lambdab_to_Lambda_meson_range"]]
    projection["mc_interval_scope"] = (
        "Approximate Poisson candidate-count interval; candidate correlations, parent branching-fraction, detector and model uncertainties excluded")
    result = {"mode": args.mode, "stage2_manifest": str(args.stage2_manifest),
              "generated_audit": str(args.generated_audit),
              "branching_config": str(args.branching_config),
              "generated_input_events": audit["processed_events"],
              "generated_direct_decays": generated,
              "generated_charge_counts": {"Lambda_b": audit["generated_lambda_b"],
                                           "anti_Lambda_b": audit["generated_anti_lambda_b"]},
              "reconstruction_hypothesis": "Lambda_b to Lambda gamma with one eta/pi0 daughter photon",
              "offline_scenario": manifest["scenario"],
              "bdt_score": manifest["bdt_score_cut"],
              "model_sha256": manifest["model_sha256"],
              "signal_peak_window_gev": window,
              "stages": counts, "branching_scenario": mode,
              "yield_formula": "N_Z*BR_Zbb*2*f_Lambdab*BR_mode*BR_Lambda_p_pi*BR_meson_gamma_gamma*candidate_rows/generated_direct_decays",
              "projected_candidates": projection}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    mass_bins = np.linspace(4.7, 6.5, 73)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for stage, label, color in (("audit", "Stage 1", "#4c78a8"),
                                ("offline_selected", "Offline", "#e09836"),
                                ("bdt_selected", "BDT", "#ba4148")):
        frame = tables[stage]
        ax.hist(frame.lb_mass, bins=mass_bins, histtype="step", label=label, color=color)
    ax.axvspan(*window, color="0.85", alpha=.5, label="Provisional signal peak")
    ax.set(xlabel=r"Reconstructed $m(\Lambda\gamma)$ [GeV]", ylabel="Candidate rows / 25 MeV",
           yscale="log", title=f"{args.mode}: one-photon reconstruction")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "mass_cutflow.png", dpi=180)
    plt.close(fig)
    frame = tables["bdt_selected"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for flag, label, color in ((True, "Direct partial", "#ba4148"),
                               (False, "Wrong/unmatched", "#4c78a8")):
        part = frame.loc[frame.direct_partial == flag]
        axes[0].hist(part.lb_mass, bins=mass_bins, histtype="step", label=label, color=color)
        axes[1].hist(part.cos_theta_p, bins=np.linspace(-1, 1, 21), histtype="step", label=label, color=color)
    axes[0].axvspan(*window, color="0.85", alpha=.5)
    axes[0].set(xlabel=r"Reconstructed $m(\Lambda\gamma)$ [GeV]", ylabel="BDT-selected candidates / 25 MeV", yscale="log")
    axes[1].set(xlabel=r"Reconstructed $\cos\theta_p$", ylabel="BDT-selected candidates / 0.1")
    axes[0].legend(frameon=False)
    fig.suptitle(f"{args.mode}: partial and wrong-combination components")
    fig.tight_layout()
    fig.savefig(args.output_dir / "post_bdt_mass_angle.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for flag, label, color in ((True, "Direct partial", "#ba4148"),
                               (False, "Wrong/unmatched", "#4c78a8")):
        part = frame.loc[frame.direct_partial == flag]
        ax.hist(part.lb_mass, bins=mass_bins, weights=np.full(len(part), factor/generated),
                histtype="step", label=label, color=color)
    ax.axvspan(*window, color="0.85", alpha=.5, label="Provisional signal peak")
    ax.set(xlabel=r"Reconstructed $m(\Lambda\gamma)$ [GeV]",
           ylabel="Projected candidates / 25 MeV",
           title=f"{args.mode}: branching-fraction scenario after fixed BDT")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "post_bdt_expected_mass.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"mode": args.mode, "stages": counts,
                      "projected_candidates": projection}, indent=2))


if __name__ == "__main__":
    main()
