#!/usr/bin/env python3
"""Fixed-score Armenteros K_S veto and post-BDT ancestry audit for v3.

The box uses saved reconstructed alpha and qT only. MC ancestry labels are
read after the score selection and used only to evaluate its effect.
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
from scipy.stats import chi2

from train_offline_bdt import split_chunk_record, split_signal
from project_offline_bdt import SIGNAL_FACTOR, BACKGROUND_FACTOR
import v3_plot_style  # noqa: F401


COLUMNS = ["source_id", "event_entry", "candidate_slot", "truth_matched",
           "bdt_score", "arm_alpha", "arm_qt", "lb_mass", "cos_theta_p",
           "proton_mc_pdg", "pion_mc_pdg", "photon_mc_pdg",
           "proton_mc_parent_pdg", "pion_mc_parent_pdg",
           "photon_mc_parent_pdg", "proton_mc_parent_index",
           "pion_mc_parent_index", "photon_mc_grandparent_pdg"]
KEY = ["source_id", "event_entry", "candidate_slot"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_survivors(path, score):
    frame = pq.read_table(path, columns=COLUMNS, use_threads=False).to_pandas()
    return frame.loc[frame.bdt_score >= score].copy()


def ancestry(frame):
    p, pi = frame.proton_mc_pdg.abs(), frame.pion_mc_pdg.abs()
    common = ((frame.proton_mc_parent_index >= 0) &
              (frame.proton_mc_parent_index == frame.pion_mc_parent_index))
    ks = common & p.eq(211) & pi.eq(211) & frame.proton_mc_parent_pdg.abs().eq(310) & frame.pion_mc_parent_pdg.abs().eq(310)
    lam = common & p.eq(2212) & pi.eq(211) & frame.proton_mc_parent_pdg.abs().eq(3122) & frame.pion_mc_parent_pdg.abs().eq(3122)
    category = np.full(len(frame), "Other or unmatched pair", dtype=object)
    category[p.eq(2212) & pi.eq(211)] = "p/pi identities, other ancestry"
    category[lam] = "True Lambda pair"
    category[ks] = "Kshort pi/pi assigned p/pi"
    frame["pair_origin"] = category
    mother = frame.photon_mc_parent_pdg.abs()
    photon = np.full(len(frame), "Other or unmatched photon", dtype=object)
    photon[mother.eq(111)] = "pi0 photon"
    photon[mother.eq(221)] = "eta photon"
    photon[mother.eq(5122)] = "direct Lambda_b photon"
    frame["photon_origin"] = photon
    return frame


def counts(frame, keep):
    selected = frame.loc[keep]
    return {"candidates": int(len(selected)),
            "events": int(selected[["source_id", "event_entry"]].drop_duplicates().shape[0])}


def interval(n, factor):
    return [float(factor * (.5 * chi2.ppf(.025, 2*n) if n else 0)),
            float(factor * .5 * chi2.ppf(.975, 2*(n+1)))]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--projection-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--box", nargs=4, type=float, metavar=("ALPHA_MIN", "ALPHA_MAX", "QT_MIN", "QT_MAX"),
                    default=(.70, .75, .09, .11))
    args = ap.parse_args()
    model, projection = args.model_dir, args.projection_dir / "projection.json"
    manifest_path = model / "prepared_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    training = json.loads((model / "training_summary.json").read_text())
    projected = json.loads(projection.read_text())
    if manifest["scenario"] != projected["scenario"]:
        raise ValueError("Model and projection scenarios differ")
    score = float(projected["validation_choice"]["score"])
    records = manifest["records"][1:]
    paths = [model / "scored_selected" / f"zbb_{r['source_id']}_selected.parquet" for r in records]
    if not all(p.exists() for p in paths):
        raise ValueError("Missing frozen scored shard")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        parts = list(pool.map(lambda p: read_survivors(p, score), paths))
    zbb = pd.concat(parts, ignore_index=True)
    signal = read_survivors(model / "scored_selected" / "signal_-1_selected.parquet", score)
    if zbb.duplicated(KEY).any() or signal.duplicated(KEY).any():
        raise ValueError("Duplicate candidate key")
    zbb = ancestry(zbb)
    signal = ancestry(signal)
    zbb["partition"] = [split_chunk_record(int(source), 0, training) for source in zbb.source_id]
    signal["partition"] = split_signal(signal.event_entry.to_numpy())
    test_signal = int(((signal.partition == "test") & (signal.truth_matched == 1)).sum())
    test_zbb = int(((zbb.partition == "test") & (zbb.truth_matched != 1)).sum())
    expected = projected["independent_test"]
    if (test_signal != expected["signal"]["candidates"] or
            test_zbb != expected["zbb"]["candidates"]):
        raise ValueError("Fixed-score test counts disagree with frozen projection")
    a0, a1, q0, q1 = args.box
    if not (0 <= a0 < a1 <= 1 and 0 <= q0 < q1):
        raise ValueError("Invalid Armenteros box")
    for frame in (signal, zbb):
        valid = np.isfinite(frame.arm_alpha) & np.isfinite(frame.arm_qt)
        frame["pass_arm"] = valid & ~((frame.arm_alpha.abs() >= a0) &
                                     (frame.arm_alpha.abs() <= a1) &
                                     (frame.arm_qt >= q0) & (frame.arm_qt <= q1))
    denom = {"all": manifest["events_processed"],
             "test": {"signal": projected["signal_generated_events_by_split"]["test"],
                      "zbb": projected["zbb_processed_events_by_split"]["test"]}}
    result = {"scenario": manifest["scenario"], "fixed_score": score,
              "veto_box": {"abs_alpha_min": a0, "abs_alpha_max": a1,
                           "qt_min_gev": q0, "qt_max_gev": q1},
              "definition": "veto if abs(saved reconstructed arm_alpha) in interval AND saved reconstructed arm_qt in interval",
              "model_manifest_sha256": sha(manifest_path),
              "training_summary_sha256": sha(model / "training_summary.json"),
              "projection_sha256": sha(projection),
              "zbb_scored_shards": len(paths), "denominators_input_events": denom,
              "partitions": {}, "candidate_truth_is_diagnostic_only": True,
              "reference_cut_changed": False}
    for part in ("all", "validation", "test"):
        s = signal if part == "all" else signal.loc[signal.partition == part]
        z = zbb if part == "all" else zbb.loc[zbb.partition == part]
        groups = {"direct_signal": s.loc[s.truth_matched == 1],
                  "signal_wrong_combination": s.loc[s.truth_matched != 1],
                  "zbb_other": z.loc[z.truth_matched != 1],
                  "zbb_direct": z.loc[z.truth_matched == 1]}
        groups["zbb_kshort_fake"] = groups["zbb_other"].loc[
            groups["zbb_other"].pair_origin == "Kshort pi/pi assigned p/pi"]
        rows = {key: {"before": counts(f, np.ones(len(f), dtype=bool)),
                      "after": counts(f, f.pass_arm),
                      "conditional_candidate_retention": float(f.pass_arm.mean()) if len(f) else None}
                for key, f in groups.items()}
        if part in denom:
            ns, nb = denom[part]["signal"], denom[part]["zbb"]
            for stage in ("before", "after"):
                sig = rows["direct_signal"][stage]["candidates"]
                bg = rows["zbb_other"][stage]["candidates"]
                sy, by = SIGNAL_FACTOR * sig / ns, BACKGROUND_FACTOR * bg / nb
                rows[stage + "_expected"] = {"signal": sy, "zbb_other": by,
                    "zbb_95pct_interval": interval(bg, BACKGROUND_FACTOR / nb),
                    "central_purity": sy/(sy+by) if sy+by else None}
        rows["zbb_pair_origin_before"] = groups["zbb_other"].pair_origin.value_counts().to_dict()
        rows["zbb_pair_origin_after"] = groups["zbb_other"].loc[groups["zbb_other"].pass_arm].pair_origin.value_counts().to_dict()
        rows["zbb_photon_origin_before"] = groups["zbb_other"].photon_origin.value_counts().to_dict()
        rows["zbb_photon_origin_after"] = groups["zbb_other"].loc[groups["zbb_other"].pass_arm].photon_origin.value_counts().to_dict()
        result["partitions"][part] = rows
    args.output_dir.mkdir(parents=True, exist_ok=True)
    keep_cols = KEY + ["partition", "truth_matched", "bdt_score", "lb_mass", "cos_theta_p",
                       "arm_alpha", "arm_qt", "pass_arm", "pair_origin", "photon_origin"]
    signal[keep_cols].to_parquet(args.output_dir / "signal_post_bdt_armenteros.parquet", index=False)
    zbb[keep_cols].to_parquet(args.output_dir / "zbb_post_bdt_armenteros_truth_audit.parquet", index=False)
    (args.output_dir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    sources = [(signal.loc[signal.truth_matched == 1], "Direct signal", "#2670a8"),
               (zbb.loc[(zbb.truth_matched != 1) & (zbb.pair_origin == "Kshort pi/pi assigned p/pi")], "True Kshort fake", "#ba4148"),
               (zbb.loc[(zbb.truth_matched != 1) & (zbb.pair_origin != "Kshort pi/pi assigned p/pi")], "Other Zbb", "#db9533")]
    for ax, field, edges, label in ((axes[0], "arm_alpha", np.linspace(-1, 1, 81), r"$\alpha$"),
                                   (axes[1], "arm_qt", np.linspace(0, .3, 81), r"$q_T$ [GeV]")):
        for frame, name, color in sources:
            h, _ = np.histogram(frame[field], edges)
            ax.stairs(h / max(1, h.sum()), edges, label=f"{name} ({len(frame)})", color=color)
        ax.set(xlabel=label, ylabel="Candidate fraction / bin")
        ax.grid(alpha=.2)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle(f"After fixed v3 BDT score ≥ {score:.6f}; truth categories for audit")
    fig.tight_layout()
    fig.savefig(args.output_dir / "armenteros_post_bdt_1d.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 6))
    for frame, name, color in sources[:2]:
        ax.scatter(frame.arm_alpha, frame.arm_qt, s=8 if name == "Direct signal" else 45,
                   alpha=.18 if name == "Direct signal" else .9, label=name, color=color)
    for x in (a0, -a1):
        ax.add_patch(plt.Rectangle((x, q0), a1-a0, q1-q0, fill=False,
                                   edgecolor="black", lw=2, ls="--"))
    ax.set(xlabel=r"$\alpha$", ylabel=r"$q_T$ [GeV]", xlim=(-1, 1), ylim=(0, .3),
           title="Exploratory reconstructed Kshort veto box")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "armenteros_post_bdt_plane.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    names = ("direct_signal", "zbb_other", "zbb_kshort_fake")
    labels = ("Direct signal", "Zbb nonmatched", "True Kshort fake")
    colors = ("#2670a8", "#db9533", "#ba4148")
    x = np.arange(3)
    for i, part in enumerate(("validation", "test")):
        values = [result["partitions"][part][key]["conditional_candidate_retention"]
                  for key in names]
        ax.bar(x + (i-.5)*.34, values, width=.32, color=colors,
               alpha=1 if part == "test" else .55,
               hatch="" if part == "test" else "//")
    ax.set(xticks=x, xticklabels=labels, ylabel="Fraction kept after Armenteros veto",
           ylim=(0, 1), title="Fixed BDT score, same selected candidates")
    ax.grid(axis="y", alpha=.2)
    fig.text(.5, .01, "Hatched: validation; solid: test. Colour: truth category (evaluation only).",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .03, 1, 1))
    fig.savefig(args.output_dir / "armenteros_post_bdt_retention.png", dpi=170)
    plt.close(fig)
    print(json.dumps({p: {k: v for k, v in d.items() if k in ("direct_signal", "zbb_other", "zbb_kshort_fake", "zbb_pair_origin_before", "zbb_pair_origin_after")}
                      for p, d in result["partitions"].items()}, indent=2))


if __name__ == "__main__":
    main()
