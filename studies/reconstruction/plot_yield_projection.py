#!/usr/bin/env python3
"""Project Lambda-gamma candidate yields at successive, explicitly provisional cuts.

Reads the existing candidate audit, so this does not alter FCCAnalyses selection.
Forced signal/eta rows enter only when their full decay chain is truth matched.
Each inclusive Zbb candidate enters as background. The outputs are candidate
counts, not event counts, and carry finite-MC errors. No fit or toy is done.
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
from matplotlib.colors import LogNorm
import mplhep as hep
import numpy as np
import pyarrow.parquet as pq

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({"font.size": 10, "axes.labelsize": 11,
                     "axes.titlesize": 12, "legend.fontsize": 9,
                     "figure.autolayout": False})

COMPONENTS = (
    ("signal", 1, r"$\Lambda_b\to\Lambda\gamma$", "#277DA1"),
    ("zbb", 0, r"Inclusive $Z\to b\bar b$", "#43AA8B"),
    ("eta", 2, r"$\Lambda_b\to\Lambda\eta(\gamma\gamma)$", "#7A5195"),
)


def weights(config):
    """One candidate weight per simulated event denominator, including both b signs."""
    n_zbb = config["n_z"] * config["br_z_to_bb"]
    n_lb = (2 * n_zbb * config["f_b_baryon_per_b_at_z"] *
            config["lambda_b_share_of_b_baryons"])
    den = config["input_events"]
    return {
        "signal": n_lb * config["br_lb_to_lambda_gamma"] *
                  config["br_lambda_to_p_pi"] / den["signal_gamma"],
        "eta": n_lb * config["br_lb_to_lambda_eta"] *
               config["br_lambda_to_p_pi"] * config["br_eta_to_gamma_gamma"] /
               den["specific_eta"],
        "zbb": n_zbb / den["generic_zbb"],
    }


def finite(values):
    return np.isfinite(values) & (values > -998.)


def stage_masks(data, config):
    """Cumulative candidate masks; the stored ntuple remains at preselection."""
    cut = config["offline_cuts"]
    mass = data["lambda_mass"]
    stage = np.ones(len(mass), dtype=bool)
    result = [("preselection", "Stage-1 baseline", stage.copy(),
               "Existing Λγ reconstruction; 4.9 < m(Λγ) < 6.3 GeV")]
    stage &= finite(mass) & (np.abs(mass-config["lambda_mass_pdg_gev"]) <
                             cut["lambda_mass_half_width_gev"])
    result.append(("lambda_mass", "Fitted Λ mass", stage.copy(),
                   "Previous + |m(pπ)-mΛ| < 10 MeV"))
    iso = data["iso_R03_noLambda"]
    stage &= finite(iso) & (iso <= cut["iso_R03_noLambda_max"])
    result.append(("lambda_iso", "Λ mass + photon isolation", stage.copy(),
                   "Previous + iso_R03_noLambda ≤ 0.211"))
    same = data["E_same"]
    stage &= finite(same) & (same <= cut["E_same_max_gev"])
    result.append(("lambda_iso_roe", "Λ mass + isolation + Z-side activity",
                   stage.copy(), "Previous + E_same ≤ 19.35 GeV"))
    return result


def sample_hist(values, mask, bins, weight):
    counts = np.histogram(values[mask & finite(values)], bins=bins)[0]
    return counts, counts * weight, np.sqrt(counts) * weight


def draw_1d(data, class_id, mask, weights_by_name, bins, column, label, title,
            output, annotation):
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    values = data[column]
    maximum = 0.
    for key, cid, legend, color in COMPONENTS:
        counts, expected, error = sample_hist(values, mask & (class_id == cid),
                                               bins, weights_by_name[key])
        ax.stairs(expected, bins, label=f"{legend} ({int(counts.sum())} MC)",
                  color=color, linewidth=2)
        centers = (bins[1:]+bins[:-1])/2
        occupied = counts > 0
        ax.errorbar(centers[occupied], expected[occupied], yerr=error[occupied],
                    fmt="none", ecolor=color, alpha=.55, linewidth=.8)
        maximum = max(maximum, expected.max(initial=0))
    ax.set_yscale("log")
    ax.set_ylim(.5, max(1., maximum*3.))
    ax.set_xlim(bins[0], bins[-1])
    ax.set_xlabel(label)
    ax.set_ylabel("Expected candidates / bin")
    ax.set_title(title)
    ax.legend(loc="upper right", frameon=False)
    fig.text(.16, .055, annotation.replace("\n", "  •  "),
             fontsize=8, ha="left")
    fig.text(.16, .025, "Empty MC bins are unresolved, not zero expected background",
             fontsize=8, ha="left")
    fig.subplots_adjust(left=.16, right=.96, bottom=.20, top=.91)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def draw_2d(data, class_id, mask, weights_by_name, mass_bins, angle_bins,
            title, output):
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharex=True, sharey=True)
    fig.set_layout_engine(None)
    mass, angle = data["m_LamGam"], data["cos_theta_p"]
    hists = []
    for key, cid, _, _ in COMPONENTS:
        selected = mask & (class_id == cid) & finite(mass) & finite(angle)
        h = np.histogram2d(mass[selected], angle[selected],
                           bins=(mass_bins, angle_bins))[0]
        hists.append(h * weights_by_name[key])
    positives = np.concatenate([h[h > 0] for h in hists])
    norm = LogNorm(vmin=max(1., positives.min(initial=1.)),
                   vmax=max(10., positives.max(initial=10.)))
    for ax, (key, _, label, _), h in zip(axes, COMPONENTS, hists):
        image = ax.pcolormesh(mass_bins, angle_bins, np.ma.masked_where(h.T <= 0, h.T),
                              norm=norm, cmap="viridis", shading="flat")
        ax.set_title(label)
        ax.set_xlabel(r"$m(\Lambda\gamma)$ [GeV]")
    axes[0].set_ylabel(r"$\cos\theta_p$")
    cax = fig.add_axes([.91, .20, .018, .57])
    fig.colorbar(image, cax=cax, label="Expected candidates / 2D bin")
    fig.suptitle(title + " — blank cells have zero MC support", y=.99)
    fig.subplots_adjust(left=.07, right=.87, bottom=.16, top=.86, wspace=.08)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/yield_projection.json"))
    parser.add_argument("--input-manifest", type=Path,
                        help="Override simulated-event denominators from prepare_bdt_dataset.py")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.input_manifest:
        manifest=json.loads(args.input_manifest.read_text())
        config["input_events"]=manifest["input_events"]
    for key, n in config["input_events"].items():
        if n <= 0:
            raise ValueError(f"Non-positive simulated event denominator: {key}")
    if not 0 < config["lambda_b_share_of_b_baryons"] <= 1:
        raise ValueError("lambda_b_share_of_b_baryons must lie in (0,1]")
    columns = ["class_id", "m_LamGam", "cos_theta_p", "lambda_mass",
               "iso_R03_noLambda", "E_same", "event_group"]
    table = pq.read_table(args.input, columns=columns)
    data = {name: np.asarray(table[name].to_pylist()) for name in columns}
    class_id = data["class_id"].astype(int)
    weights_by_name = weights(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"resolved_config.json").write_text(json.dumps(config,indent=2)+"\n")
    mass_bins = np.linspace(4.9, 6.3, 29)
    angle_bins = np.linspace(-1., 1., 11)
    summary = {"input": str(args.input), "config": str(args.config),
               "weights_per_simulated_candidate": weights_by_name,
               "normalization": "expected candidate counts at configured n_z; truth-matched forced decays plus inclusive Zbb candidates",
               "stages": {},
               "warnings": [
                   "0.084 is the Z-pole ALL b-baryon fraction; share=1 is a Lambda_b upper-envelope proxy.",
                   "Forced PHSP signal gives no physical polarization shape in cos(theta_p).",
                   "One Zbb MC candidate carries a very large weight; empty/low-statistic bins cannot support a sensitivity fit.",
                   "Offline cuts are exploratory and their thresholds were inspected on these samples; validate on independent files before toys."
               ]}
    stage_rows = []
    for stage_id, title, stage, cuts in stage_masks(data, config):
        row = {"cuts": cuts, "components": {}}
        for key, cid, _, _ in COMPONENTS:
            selected = stage & (class_id == cid)
            peak = selected & (data["m_LamGam"] >= 5.4) & (data["m_LamGam"] < 5.9)
            n, n_peak = int(selected.sum()), int(peak.sum())
            row["components"][key] = {
                "mc_candidates": n,
                "unique_mc_events": len(set(data["event_group"][selected])),
                "event_efficiency_from_input":
                    len(set(data["event_group"][selected])) /
                    config["input_events"][{"signal":"signal_gamma",
                                             "eta":"specific_eta",
                                             "zbb":"generic_zbb"}[key]],
                "expected_candidates": n * weights_by_name[key],
                "expected_mc_stat_error": np.sqrt(n) * weights_by_name[key],
                "mass_5p4_5p9_mc_candidates": n_peak,
                "mass_5p4_5p9_expected": n_peak * weights_by_name[key],
                "mass_5p4_5p9_mc_stat_error": np.sqrt(n_peak) * weights_by_name[key],
                "mass_5p4_5p9_zero_mc_95pct_upper":
                    3.0 * weights_by_name[key] if n_peak == 0 else None,
            }
        summary["stages"][stage_id] = row
        stage_rows.append((stage_id, row))
        note = (f"{cuts}\n"
                f"$N_Z$={config['n_z']:.1e}; $f_{{b\\to baryon}}$={config['f_b_baryon_per_b_at_z']:.3f}, "
                "Λb share=1 proxy")
        draw_1d(data, class_id, stage, weights_by_name, mass_bins, "m_LamGam",
                r"$m(\Lambda\gamma)$ [GeV]", title,
                args.output_dir/f"{stage_id}_mass.png", note)
        draw_1d(data, class_id, stage, weights_by_name, angle_bins, "cos_theta_p",
                r"$\cos\theta_p$ (reconstructed)", title,
                args.output_dir/f"{stage_id}_costheta.png", note)
        draw_2d(data, class_id, stage, weights_by_name, mass_bins, angle_bins,
                title, args.output_dir/f"{stage_id}_mass_costheta.png")
    (args.output_dir/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    lines = ["# Projected candidate yields", "",
             "Scenario: N(Z)={:.2e}; Z→bb={:.4f}; f(b→all b baryons)={:.3f}; Λb share={:.2f}.".format(
                 config["n_z"],config["br_z_to_bb"],
                 config["f_b_baryon_per_b_at_z"],config["lambda_b_share_of_b_baryons"]),
             "The Λb share=1 choice is an upper-envelope proxy, not a measured Λb production fraction.",
             "Counts below are **candidates**, not distinct events. Errors are MC counting errors only.",
             "", "| Stage | Signal MC / expected | Zbb MC / expected | Eta MC / expected |",
             "|---|---:|---:|---:|"]
    for stage_id, row in stage_rows:
        cells=[]
        for key in ("signal","zbb","eta"):
            item=row["components"][key]
            cells.append(f"{item['mc_candidates']:,} / {item['expected_candidates']:,.0f} ± {item['expected_mc_stat_error']:,.0f}")
        lines.append("| {} | {} |".format(stage_id," | ".join(cells)))
    lines += ["", "Signal acceptance × reconstruction × stage selection, measured as distinct matched events / 10,000 generated forced-signal events:", ""]
    for stage_id, row in stage_rows:
        item = row["components"]["signal"]
        lines.append(f"- `{stage_id}`: {item['unique_mc_events']:,}/10,000 = {100*item['event_efficiency_from_input']:.2f}%")
    lines += ["", "Conditional candidate retention relative to the preceding stage:", "",
              "| Stage | Signal | Zbb | Eta |", "|---|---:|---:|---:|"]
    previous = None
    for stage_id, row in stage_rows:
        if previous is None:
            previous = row
            continue
        ratios = []
        for key in ("signal", "zbb", "eta"):
            n = row["components"][key]["mc_candidates"]
            den = previous["components"][key]["mc_candidates"]
            ratios.append(f"{n}/{den} = {100*n/den:.1f}%" if den else "undefined")
        lines.append("| {} | {} |".format(stage_id, " | ".join(ratios)))
        previous = row
    lines += ["", "In the 5.4–5.9 GeV diagnostic mass interval:", "",
              "| Stage | Signal MC | Zbb MC | Eta MC |", "|---|---:|---:|---:|"]
    for stage_id,row in stage_rows:
        vals=[str(row["components"][key]["mass_5p4_5p9_mc_candidates"])
              for key in ("signal","zbb","eta")]
        lines.append("| {} | {} |".format(stage_id," | ".join(vals)))
    lines += ["", "## Interpretation", "",
              "- Forced γ and η samples are phase space and their truth-matched candidates are weighted by physical decay branching fractions.",
              "- Zbb is scaled by N(Z) × B(Z→bb) / N(generated Zbb). The forced samples are scaled by twice the Zbb yield times the b-baryon fraction, Λb share, and decay branching fractions.",
              "- The offline thresholds are illustrative; the current stage-1 FCCAnalyses snapshot has none of these new cuts.",
              "- At the last stage only a handful of generic Zbb MC candidates remain. The projected background shape and toy sensitivity are not trustworthy yet; process more independent Winter2023 Zbb files.",
              "- PHSP signal does not predict the polarization-dependent cosθp shape; use a physics decay model before sensitivity toys.",
              "- The 5.4–5.9 GeV interval is a diagnostic display, not a new candidate cut; the final fit range remains 4.9–6.3 GeV."]
    (args.output_dir/"summary.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"weights":weights_by_name,
                      "stages":{s:{k:v["mc_candidates"] for k,v in row["components"].items()}
                                for s,row in stage_rows}},indent=2))


if __name__ == "__main__":
    main()
