#!/usr/bin/env python3
"""Make the first track and photon detector-response plots."""

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np

from resolution_tools import (
    binned_gaussian_resolution, load_sample,
    plot_1d, plot_efficiency, plot_resolution, plot_scatter,
)


def _write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def _good(*arrays):
    mask = np.ones(len(arrays[0]), dtype=bool)
    for array in arrays:
        mask &= np.isfinite(array) & (array > -900)
    return mask


def _ecal_relative(E):
    """Card ECalResolutionFormula in percent, valid for |eta| <= 3.

    Both barrel (|eta| <= 0.88) and endcap (0.88 < |eta| <= 3)
    use the same absolute-energy sigma in GeV.
    """
    E = np.asarray(E, dtype=float)
    return 100 * np.sqrt(E**2 * 0.005**2 + E * 0.03**2 + 0.002**2) / E


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(
        "outputs/analysis/studies/Lb2LambdaGamma_resolutions_12000events_from500k.root"))
    parser.add_argument("--output-dir", type=Path, default=Path(
        "outputs/plots/resolutions/Lb2LambdaGamma"))
    parser.add_argument("--target-pairs", type=int, default=200_000,
                        help="Maximum matched tracks and photons retained separately")
    parser.add_argument("--chunk-events", type=int, default=1_000)
    parser.add_argument("--min-fit-entries", type=int, default=200)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sample = load_sample(args.input, args.target_pairs, args.chunk_events)
    print(f"Read {sample.events_read} events: {len(sample.track_pt)} matched tracks, "
          f"{len(sample.gamma_e)} matched photons", flush=True)

    tracks = _good(sample.track_p, sample.track_pt, sample.track_eta,
                   sample.track_reco_pt, sample.track_dp_rel,
                   sample.track_dpt_rel, sample.track_dqoverpt)
    photons = _good(sample.gamma_e, sample.gamma_eta,
                    sample.gamma_reco_e, sample.gamma_dE_rel)
    tpt = sample.track_pt[tracks]
    tp = sample.track_p[tracks]
    t_eta = sample.track_eta[tracks]
    rpt = sample.track_reco_pt[tracks]
    t_res = 100 * sample.track_dpt_rel[tracks]
    p_res = 100 * sample.track_dp_rel[tracks]
    q_res = sample.track_dqoverpt[tracks]
    ge = sample.gamma_e[photons]
    g_eta = sample.gamma_eta[photons]
    re = sample.gamma_reco_e[photons]
    g_res = 100 * sample.gamma_dE_rel[photons]
    selected = sample.gamma_selected[photons] == 1

    track_edges = np.geomspace(0.1, 60, 17)
    p_edges = np.geomspace(0.1, 100, 16)
    eta_edges = np.linspace(-3.2, 3.2, 33)
    gamma_eta_edges = np.linspace(-3.5, 3.5, 29)
    gamma_edges = np.geomspace(0.2, 60, 17)
    track_bins = binned_gaussian_resolution(tpt, t_res, track_edges, args.min_fit_entries)
    eta_track = tpt >= 0.1
    track_eta_bins = binned_gaussian_resolution(
        t_eta[eta_track], t_res[eta_track], eta_edges,
        args.min_fit_entries, xscale="linear")
    p_eta_bins = binned_gaussian_resolution(
        t_eta[eta_track], p_res[eta_track], eta_edges,
        args.min_fit_entries, xscale="linear")
    p_bins = binned_gaussian_resolution(tp, p_res, p_edges, args.min_fit_entries)
    q_bins = binned_gaussian_resolution(tpt, q_res, track_edges, args.min_fit_entries)
    ecal_acceptance = np.abs(g_eta) <= 3.0
    gamma_bins = binned_gaussian_resolution(
        ge[ecal_acceptance], g_res[ecal_acceptance],
        gamma_edges, args.min_fit_entries)
    selected_bins = binned_gaussian_resolution(
        ge[selected & ecal_acceptance], g_res[selected & ecal_acceptance],
        gamma_edges, args.min_fit_entries)
    gamma_eta_bins = binned_gaussian_resolution(
        g_eta, g_res, gamma_eta_edges, args.min_fit_entries, xscale="linear")
    selected_eta_bins = binned_gaussian_resolution(
        g_eta[selected], g_res[selected], gamma_eta_edges,
        args.min_fit_entries, xscale="linear")

    out = args.output_dir
    plot_1d(t_res, out / "track_dpt_rel_1d.png",
            r"$100\Delta p_T/p_T$ [%]", "Charged-particle response (all pT)")
    plot_scatter(tpt, rpt, out / "track_pt_scatter.png",
                 "Truth pT [GeV]", "Reco pT [GeV]", "Matched charged particles", identity=True)
    plot_resolution(track_bins, out / "track_resolution_vs_pt.png",
                    "Truth pT [GeV]", r"Gaussian $\sigma(\Delta p_T/p_T)$ [%]",
                    "Charged-particle momentum resolution",
                    raw_x=tpt, raw_residual=t_res,
                    min_fit_entries=args.min_fit_entries,
                    residual_label=r"$100\Delta p_T/p_T$ [%]")
    plot_resolution(track_eta_bins, out / "track_resolution_vs_eta.png",
                    r"Truth $\eta$", r"Gaussian $\sigma(\Delta p_T/p_T)$ [%]",
                    "Charged-particle transverse-momentum resolution",
                    xscale="linear", raw_x=t_eta[eta_track],
                    raw_residual=t_res[eta_track],
                    min_fit_entries=args.min_fit_entries,
                    residual_label=r"$100\Delta p_T/p_T$ [%]",
                    acceptance_boundary=2.56)
    plot_resolution(p_eta_bins, out / "track_dp_resolution_vs_eta.png",
                    r"Truth $\eta$", r"Gaussian $\sigma(\Delta p/p)$ [%]",
                    "Charged-particle momentum resolution versus angle",
                    xscale="linear", raw_x=t_eta[eta_track],
                    raw_residual=p_res[eta_track],
                    min_fit_entries=args.min_fit_entries,
                    residual_label=r"$100\Delta p/p$ [%]",
                    acceptance_boundary=2.56)
    plot_resolution(p_bins, out / "track_dp_resolution_vs_p.png",
                    "Truth p [GeV]", r"Gaussian $\sigma(\Delta p/p)$ [%]",
                    "Charged-particle momentum resolution",
                    raw_x=tp, raw_residual=p_res,
                    min_fit_entries=args.min_fit_entries,
                    residual_label=r"$100\Delta p/p$ [%]")
    plot_resolution(q_bins, out / "track_qoverpt_resolution_vs_pt.png",
                    "Truth pT [GeV]", "Gaussian sigma of delta(q/pT) [1/GeV]",
                    "Charged-particle curvature resolution",
                    raw_x=tpt, raw_residual=q_res,
                    min_fit_entries=args.min_fit_entries,
                    residual_label=r"$\Delta(q/p_T)$ [1/GeV]")
    plot_1d(g_res, out / "photon_dE_rel_1d.png",
            r"$100\Delta E/E$ [%]", "Photon energy response (all energies)")
    plot_scatter(ge, re, out / "photon_energy_scatter.png",
                 "Truth E [GeV]", "Reco E [GeV]", "Matched photons", identity=True)
    plot_resolution(gamma_bins, out / "photon_resolution_vs_energy.png",
                    "Truth E [GeV]", r"Gaussian $\sigma(\Delta E/E)$ [%]",
                    "Raw reconstructed-photon energy resolution", _ecal_relative,
                    raw_x=ge[ecal_acceptance], raw_residual=g_res[ecal_acceptance],
                    min_fit_entries=args.min_fit_entries,
                    residual_label=r"$100\Delta E/E$ [%]")
    plot_resolution(selected_bins, out / "selected_photon_resolution_vs_energy.png",
                    "Truth E [GeV]", r"Gaussian $\sigma(\Delta E/E)$ [%]",
                    "PhotonEfficiency-selected energy resolution", _ecal_relative,
                    raw_x=ge[selected & ecal_acceptance],
                    raw_residual=g_res[selected & ecal_acceptance],
                    min_fit_entries=args.min_fit_entries,
                    residual_label=r"$100\Delta E/E$ [%]")
    for slug, rows, mask, title in [
        ("photon_resolution_vs_eta", gamma_eta_bins, np.ones(len(ge), dtype=bool),
         "Raw reconstructed-photon energy resolution"),
        ("selected_photon_resolution_vs_eta", selected_eta_bins, selected,
         "PhotonEfficiency-selected energy resolution"),
    ]:
        plot_resolution(rows, out / (slug + ".png"), r"Truth $\eta$",
                        r"Gaussian $\sigma(\Delta E/E)$ [%]", title,
                        xscale="linear", raw_x=g_eta[mask],
                        raw_residual=g_res[mask],
                        min_fit_entries=args.min_fit_entries,
                        residual_label=r"$100\Delta E/E$ [%]",
                        acceptance_boundary=3.0)

    track_acceptance = (sample.track_truth_pt > 0) & (
        np.abs(sample.track_truth_eta) <= 2.56)
    gamma_acceptance = (sample.gamma_truth_e > 0) & (
        np.abs(sample.gamma_truth_eta) <= 3.0)
    plot_efficiency(sample.track_truth_pt[track_acceptance],
                    {"Matched track": sample.track_truth_matched[track_acceptance]},
                    track_edges, out / "track_match_fraction_vs_pt.png",
                    "Truth pT [GeV]", "Track match fraction within IDEA eta acceptance")
    plot_efficiency(sample.gamma_truth_e[gamma_acceptance],
                    {"Raw matched photon": sample.gamma_truth_matched[gamma_acceptance],
                     "PhotonEfficiency selected": sample.gamma_truth_selected[gamma_acceptance]},
                    gamma_edges, out / "photon_match_fraction_vs_energy.png",
                    "Truth E [GeV]", "Photon match fraction within IDEA eta acceptance")
    plot_efficiency(sample.track_truth_eta[sample.track_truth_pt >= 0.1],
                    {"Matched track": sample.track_truth_matched[
                        sample.track_truth_pt >= 0.1]},
                    eta_edges, out / "track_match_fraction_vs_eta.png",
                    r"Truth $\eta$", "Track match fraction: truth pT >= 0.1 GeV",
                    xscale="linear", acceptance_boundary=2.56)
    plot_efficiency(sample.gamma_truth_eta[sample.gamma_truth_e >= 2.0],
                    {"Raw matched photon": sample.gamma_truth_matched[
                        sample.gamma_truth_e >= 2.0],
                     "PhotonEfficiency selected": sample.gamma_truth_selected[
                        sample.gamma_truth_e >= 2.0]},
                    gamma_eta_edges, out / "photon_match_fraction_vs_eta.png",
                    r"Truth $\eta$", "Photon match fraction: truth E >= 2 GeV",
                    xscale="linear", acceptance_boundary=3.0)

    for name, rows in [
        ("track_resolution_vs_pt.csv", track_bins),
        ("track_resolution_vs_eta.csv", track_eta_bins),
        ("track_dp_resolution_vs_eta.csv", p_eta_bins),
        ("track_dp_resolution_vs_p.csv", p_bins),
        ("track_qoverpt_resolution_vs_pt.csv", q_bins),
        ("photon_resolution_vs_energy.csv", gamma_bins),
        ("selected_photon_resolution_vs_energy.csv", selected_bins),
        ("photon_resolution_vs_eta.csv", gamma_eta_bins),
        ("selected_photon_resolution_vs_eta.csv", selected_eta_bins),
    ]:
        _write_csv(out / name, rows)

    summary = {
        "input": str(args.input), "events_read": sample.events_read,
        "target_pairs": args.target_pairs,
        "min_fit_entries": args.min_fit_entries,
        "truth_tracks": len(sample.track_truth_pt),
        "matched_tracks_retained": len(sample.track_pt),
        "truth_photons": len(sample.gamma_truth_e),
        "matched_photons_retained": len(sample.gamma_e),
        "resolution_method": "Gaussian core fits within truth-variable bins; see CSV tables",
        "relative_resolution_unit": "percent (100 times the relative residual)",
        "ecal_card_relative_percent": "100*sqrt(E^2*0.005^2 + E*0.03^2 + 0.002^2)/E, |eta|<=3; same expression in barrel and endcap",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(f"Wrote plots, fit tables, and summary to {out}")


if __name__ == "__main__":
    main()
