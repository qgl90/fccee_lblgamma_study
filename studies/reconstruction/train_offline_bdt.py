#!/usr/bin/env python3
"""Train and score stage-1 candidate tables prepared by prepare_offline_bdt.py.

Signal is split by generated event_entry; Zbb is split by whole Condor chunk.
Only true physics signal and nonmatched inclusive Zbb train the binary model.
Every candidate, including rejected and diagnostic combinations, can later be
scored with --score-audit. The mass and helicity angle never enter the model.
"""

# Author: Renato Quagliani (rquaglia@cern.ch)

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import v3_plot_style  # noqa: F401 - LHCb-style labels and figure defaults
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score, roc_curve
import sklearn
import xgboost
from xgboost import XGBClassifier


FEATURES = []  # Loaded from the named JSON feature set or model manifest.
FEATURE_LABELS = {
    "proton_pt": "Proton pT [GeV]", "proton_eta": "Proton η",
    "pion_pt": "Pion pT [GeV]", "pion_eta": "Pion η",
    "gamma_E": "Photon E [GeV]", "gamma_eta": "Photon η",
    "lambda_pt": "Λ pT [GeV]", "lambda_eta": "Λ η",
    "lb_pt": "Λb pT [GeV]", "lb_eta": "Λb η",
    "proton_d0sig": "Proton |d0| significance",
    "pion_d0sig": "Pion |d0| significance",
    "lambda_d0_sig": "Λ d0 significance",
    "lambda_flight_rxy": "Λ transverse flight [mm]",
    "lambda_flight_rxy_sig": "Λ flight significance",
    "lambda_vertex_chi2": "Λ vertex χ²",
    "iso_R03_noLambda": "Photon isolation, ΔR=0.3",
    "iso_R05_noLambda": "Photon isolation, ΔR=0.5",
    "lambda_thrust_cos": "cos(Λ, thrust axis)",
    "gamma_thrust_cos": "cos(γ, thrust axis)",
    "m_rec": "Opposite-side recoil mass [GeV]",
    "Estar_gamma_rec": "Photon E* in recoil frame [GeV]",
    "proton_p": "Proton p [GeV]", "pion_p": "Pion p [GeV]",
    "lambda_p": "Λ p [GeV]", "lb_p": "Λb p [GeV]",
    "lambda_flight_xyz_sig": "Λ 3D flight significance",
    "iso_R03_all_energy": "Same-hemisphere cone energy, ΔR=0.3 [GeV]",
    "iso_R05_all_energy": "Same-hemisphere cone energy, ΔR=0.5 [GeV]",
    "iso_R05_charged_p": "Same-hemisphere charged cone |Σp|, ΔR=0.5 [GeV]",
    "iso_R05_neutral_energy": "Same-hemisphere neutral cone energy, ΔR=0.5 [GeV]",
    "lb_thrust_cos": "cos(Λb, thrust axis)",
    "z_partial_deltaE": "Candidate and recoil energy residual [GeV]",
    "z_partial_deltaP": "Candidate and recoil |Σp| [GeV]",
    "lb_E": "Λb candidate energy [GeV]",
    "lb_thrust_abs_cos": "|cos(Λb, thrust axis)|",
    "iso_R03_all_energy_over_gamma_E": "Photon R=0.3 activity ΣE/Eγ",
    "iso_R05_charged_n": "Photon R=0.5 charged multiplicity",
    "iso_R03_neutral_n": "Photon R=0.3 neutral multiplicity",
    "lambda0_iso_R05_charged_n_d0": "Λ R=0.5 charged objects with valid d0",
    "lambda0_iso_R05_charged_absd0_min": "Λ R=0.5 min |d0| [mm]",
    "lambda0_iso_R05_charged_absd0_max": "Λ R=0.5 max |d0| [mm]",
    "d_pi0": "Nearest same-hemisphere π⁰ mass distance [GeV]",
    "d_eta": "Nearest same-hemisphere η mass distance [GeV]",
    "min_pair": "Minimum same-hemisphere γγ mass [GeV]",
}


def split_signal(entry):
    # Candidate rows from the same generated event always share a partition.
    bucket = (entry.astype(np.uint64) * np.uint64(11400714819323198485)) % np.uint64(10)
    return np.where(bucket < 7, "train", np.where(bucket == 7, "validation", "test"))


def split_chunk(chunk_id):
    # Stable as newly completed chunks enter an updated catalog.
    return "train" if chunk_id % 10 < 7 else "validation" if chunk_id % 10 == 7 else "test"


def split_chunk_record(source_id, catalog_index, training_summary):
    """Keep historical catalog-order models reproducible during projection."""
    legacy = "catalog order" in training_summary.get("split", "")
    return split_chunk(catalog_index if legacy else source_id)


def feature_matrix(frame):
    x = frame[FEATURES].astype("float32").copy()
    return x.mask(~np.isfinite(x) | (x <= -998.))


def read(path):
    frame = pq.read_table(path, columns=FEATURES + ["event_entry", "truth_matched"],
                          use_threads=False).to_pandas(use_threads=False)
    if frame.empty:
        return frame
    if not set(FEATURES).issubset(frame.columns):
        raise ValueError(f"Missing model features in {path}")
    return frame


def score_files(model, paths, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        table = pq.read_table(path)
        if not table.num_rows:
            continue
        scores = model.predict_proba(feature_matrix(table.select(FEATURES).to_pandas()))[:, 1]
        scored = table.append_column("bdt_score", pa.array(scores.astype("float32")))
        pq.write_table(scored, output_dir / path.name, compression="zstd")


def plot_training(model, train, test, output_dir):
    score = model.predict_proba(feature_matrix(test))[:, 1]
    labels = test.class_id.to_numpy()
    fpr, tpr, _ = roc_curve(labels, score)
    auc = roc_auc_score(labels, score)
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.plot(tpr, 1/np.maximum(fpr, 1/max(1, (labels == 0).sum())), lw=2)
    ax.set(xlabel="Direct-signal candidate efficiency on held-out test",
           ylabel="Zbb candidate rejection (finite-MC capped)", yscale="log",
           title=f"Held-out ROC | AUC = {auc:.4f}")
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(output_dir / "test_roc.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 5.5))
    bins = np.linspace(0, 1, 51)
    for value, label, color in ((1, "Direct physics signal", "#2c6db2"),
                                (0, "Inclusive Zbb other", "#c44e52")):
        values = score[labels == value]
        ax.hist(values, bins, histtype="step", lw=2, color=color,
                weights=np.full(len(values), 1/max(1, len(values))),
                label=f"{label} | {len(values):,} candidates")
    ax.set(xlabel="BDT signal score", ylabel="Fraction per 0.02 bin", yscale="log",
           title="Held-out candidate score distribution")
    ax.legend(frameon=False)
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(output_dir / "test_scores.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for frame, partition, linestyle in ((train, "train", "-"),
                                         (test, "test", "--")):
        scores = model.predict_proba(feature_matrix(frame))[:, 1]
        for value, label, color in ((1, "Direct Physics", "#2c6db2"),
                                    (0, "Inclusive Zbb other", "#c44e52")):
            values = scores[frame.class_id.to_numpy() == value]
            ax.hist(values, bins=bins, histtype="step", lw=1.8,
                    ls=linestyle, color=color,
                    weights=np.full(len(values), 1/max(1, len(values))),
                    label=f"{label}, {partition} ({len(values):,})")
    ax.set(xlabel="BDT signal score", ylabel="Fraction per 0.02 bin", yscale="log",
           title="BDT response: training versus held-out test")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(output_dir / "train_test_scores.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 6))
    order = np.argsort(model.feature_importances_)
    ax.barh(np.asarray([FEATURE_LABELS.get(x, x) for x in FEATURES])[order],
            np.asarray(model.feature_importances_)[order])
    ax.set(xlabel="XGBoost split importance", title="Model inputs and importance")
    fig.tight_layout()
    fig.savefig(output_dir / "feature_importance.png", dpi=170)
    plt.close(fig)
    ncols = 4
    nrows = int(np.ceil(len(FEATURES)/ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(17, 3.2*nrows))
    for ax, feature in zip(np.ravel(axes), FEATURES):
        values = [test.loc[labels == cls, feature].to_numpy(dtype=float)
                  for cls in (1, 0)]
        valid = [x[np.isfinite(x) & (x > -998.)] for x in values]
        mixed = np.concatenate(valid)
        if len(mixed):
            lo, hi = np.quantile(mixed, [.01, .99])
            if lo == hi:
                hi = lo + 1
            edges = np.linspace(lo, hi, 35)
            for array, color, label in zip(valid, ("#2c6db2", "#c44e52"),
                                           ("Direct signal", "Inclusive Zbb")):
                counts, _ = np.histogram(array, edges)
                ax.stairs(counts/max(1, counts.sum()), edges, color=color,
                          label=label, lw=1.4)
        ax.set(xlabel=FEATURE_LABELS.get(feature, feature), ylabel="Fraction per bin")
        ax.grid(alpha=.15)
    for ax in np.ravel(axes)[len(FEATURES):]:
        ax.axis("off")
    handles, legend_labels = np.ravel(axes)[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Held-out model inputs | Physics MC versus inclusive Zbb", fontsize=17)
    fig.tight_layout(rect=(0, .025, 1, .975))
    fig.savefig(output_dir / "test_input_features.png", dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--max-train-background", type=int,
                    help="Optional training-only Zbb candidate cap; default uses every training chunk")
    ap.add_argument("--feature-config", type=Path,
                    default=Path("config/lb_bdt_features.json"))
    ap.add_argument("--feature-set", default="full",
                    help="Named ordered list in --feature-config")
    ap.add_argument("--score-audit", action="store_true")
    ap.add_argument("--io-workers", type=int, default=8,
                    help="Concurrent independent Parquet shard readers")
    ap.add_argument("--threads", type=int,
                    default=min(16, len(os.sched_getaffinity(0))),
                    help="XGBoost CPU threads for fitting and inference")
    args = ap.parse_args()
    if args.io_workers < 1 or args.threads < 1:
        ap.error("--io-workers and --threads must be positive")
    global FEATURES
    feature_config = json.loads(args.feature_config.read_text())
    if args.feature_set not in feature_config["feature_sets"]:
        ap.error(f"Unknown feature set {args.feature_set}; choose from "
                 f"{list(feature_config['feature_sets'])}")
    FEATURES = feature_config["feature_sets"][args.feature_set]
    if not isinstance(FEATURES, list) or not FEATURES or \
            len(FEATURES) != len(set(FEATURES)) or \
            not all(isinstance(name, str) and name for name in FEATURES):
        ap.error("Feature list must contain distinct, nonempty column names")
    forbidden = {"lb_mass", "lambda_mass", "cos_theta_p", "truth_matched",
                 "source_id", "event_entry", "candidate_slot",
                 "candidates_in_event", "lb_sign", "bdt_score", "sample"}
    unsafe = [name for name in FEATURES if name in forbidden or
              name.startswith(("truth_", "pass_")) or "_mc_" in name]
    if unsafe:
        ap.error(f"Truth, identity, target mass/angle, and cut flags cannot be BDT inputs: {unsafe}")
    manifest = json.loads((args.prepared_dir / "summary.json").read_text())
    if manifest["max_output_events_per_file"] is not None:
        raise ValueError("Pilot output has no processed-event denominator; use a full preparation")
    records = manifest["records"]
    if len(records) < 11:
        raise ValueError("Need at least ten Zbb chunks for disjoint train/validation/test")
    signal = read(args.prepared_dir / "signal_-1_selected.parquet")
    signal["split"] = split_signal(signal.event_entry.to_numpy())
    signal["class_id"] = np.where(signal.truth_matched == 1, 1, -1)
    def read_background(item):
        frame = read(args.prepared_dir / f"zbb_{item['source_id']}_selected.parquet")
        if frame.empty:
            return None
        frame["split"] = split_chunk(item["source_id"])
        frame["class_id"] = np.where(frame.truth_matched == 1, -1, 0)
        return frame
    with ThreadPoolExecutor(max_workers=args.io_workers) as pool:
        background = [frame for frame in pool.map(read_background, records[1:])
                      if frame is not None]
    background = pd.concat(background, ignore_index=True)
    train_signal = signal[(signal.split == "train") & (signal.class_id == 1)]
    train_background = background[(background.split == "train") & (background.class_id == 0)]
    if args.max_train_background is not None and \
            len(train_background) > args.max_train_background:
        train_background = train_background.sample(args.max_train_background, random_state=314159)
    train = pd.concat([train_signal, train_background], ignore_index=True)
    valid = pd.concat([signal[(signal.split == "validation") & (signal.class_id == 1)],
                       background[(background.split == "validation") & (background.class_id == 0)]],
                      ignore_index=True)
    test = pd.concat([signal[(signal.split == "test") & (signal.class_id == 1)],
                      background[(background.split == "test") & (background.class_id == 0)]],
                     ignore_index=True)
    for name, frame in (("train", train), ("validation", valid), ("test", test)):
        if set(frame.class_id) != {0, 1}:
            raise ValueError(f"{name} partition needs both classes")
    model = XGBClassifier(n_estimators=700, max_depth=3, learning_rate=.05,
                          subsample=.8, colsample_bytree=.8, min_child_weight=5,
                          tree_method="hist", objective="binary:logistic",
                          eval_metric="auc", early_stopping_rounds=40,
                          random_state=314159, n_jobs=args.threads)
    model.fit(feature_matrix(train), train.class_id,
              eval_set=[(feature_matrix(valid), valid.class_id)], verbose=False)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(args.output_dir / "bdt_model.json")
    # The preparation directory is appendable when later catalog snapshots
    # arrive. Pin the exact manifest used for this model in its own directory.
    frozen_manifest = args.output_dir / "prepared_manifest.json"
    manifest_bytes = (args.prepared_dir / "summary.json").read_bytes()
    if frozen_manifest.exists() and frozen_manifest.read_bytes() != manifest_bytes:
        raise ValueError("Model directory already pins another preparation")
    frozen_manifest.write_bytes(manifest_bytes)
    summary = {"command": sys.argv,
               "prepared_manifest": str(args.prepared_dir / "summary.json"),
               "frozen_prepared_manifest": str(frozen_manifest),
               "prepared_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
               "training_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "software": {"python": sys.version.split()[0],
                            "numpy": np.__version__,
                            "scikit_learn": sklearn.__version__,
                            "xgboost": xgboost.__version__},
               "scenario": manifest["scenario"], "features": FEATURES,
               "feature_labels": {feature: FEATURE_LABELS.get(feature, feature)
                                  for feature in FEATURES},
               "feature_set": args.feature_set,
               "feature_config": str(args.feature_config),
               "feature_config_sha256": hashlib.sha256(args.feature_config.read_bytes()).hexdigest(),
               "max_train_background": args.max_train_background,
               "parallelism": {"parquet_io_workers": args.io_workers,
                               "xgboost_threads": args.threads,
                               "cpu_affinity": len(os.sched_getaffinity(0))},
               "best_iteration": int(model.best_iteration),
               "counts": {name: {str(cls): int((frame.class_id == cls).sum()) for cls in (0, 1)}
                          for name, frame in (("train", train), ("validation", valid), ("test", test))},
               "auc": {name: float(roc_auc_score(frame.class_id,
                          model.predict_proba(feature_matrix(frame))[:, 1]))
                       for name, frame in (("train", train), ("validation", valid),
                                           ("test", test))},
               "split": "signal generated event hash; whole Zbb chunk by chunk_id modulo 10",
               "excluded_inputs": ["lb_mass", "lambda_mass", "cos_theta_p", "truth/ancestry",
                                   "source_id", "event_entry", "candidate multiplicity"],
               "mass_sculpting_check_required": True}
    (args.output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    plot_training(model, train, test, args.output_dir)
    paths = [args.prepared_dir / "signal_-1_selected.parquet"] + [
        args.prepared_dir / f"zbb_{item['source_id']}_selected.parquet"
        for item in records[1:]]
    score_files(model, paths, args.output_dir / "scored_selected")
    if args.score_audit:
        score_files(model, [path.with_name(path.name.replace("_selected.parquet", "_audit.parquet"))
                            for path in paths],
                    args.output_dir / "scored_stage1")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
