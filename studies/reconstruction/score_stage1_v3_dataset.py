#!/usr/bin/env python3
"""Apply the frozen v3 offline selection and BDT to one Stage-1 ROOT file.

The full Stage-1 candidate schema is flattened and joined by the exact
(source_id, event_entry, candidate_slot) key.  Truth is carried only as a
diagnostic label; selection and scoring use reconstructed quantities.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq
from xgboost import XGBClassifier

import materialize_stage2_candidates as materialize
import prepare_offline_bdt as preparation
import train_offline_bdt as training


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--source-id", type=int, default=0)
    ap.add_argument("--sample", default="dataset",
                    help="Short source label, used only in output file names")
    ap.add_argument("--config", type=Path,
                    default=Path("config/lb_offline_selections.json"))
    ap.add_argument("--projection", type=Path,
                    help="Optional validation-fixed projection.json for a BDT cut")
    ap.add_argument("--max-output-events", type=int,
                    help="Development check: cap candidate-bearing ROOT events")
    args = ap.parse_args()
    if not args.sample.isidentifier():
        ap.error("--sample must be an identifier")
    if args.max_output_events is not None and args.max_output_events < 1:
        ap.error("--max-output-events must be positive")
    model_summary = json.loads((args.model_dir / "training_summary.json").read_text())
    prepared_manifest_path = Path(model_summary.get(
        "frozen_prepared_manifest", model_summary["prepared_manifest"]))
    if sha(prepared_manifest_path) != model_summary["prepared_manifest_sha256"]:
        raise ValueError("Trained model's preparation manifest has changed")
    prepared_manifest = json.loads(prepared_manifest_path.read_text())
    scenario = model_summary["scenario"]
    cfg = json.loads(args.config.read_text())
    preparation.validate_config(cfg, scenario)
    if sha(args.config) != prepared_manifest["config_sha256"]:
        raise ValueError("Offline config differs from model preparation")
    threshold = None
    if args.projection:
        projection = json.loads(args.projection.read_text())
        if Path(projection["training_summary"]).resolve() != (
                args.model_dir / "training_summary.json").resolve():
            raise ValueError("Projection uses another trained model")
        choice = projection.get("validation_choice")
        if not choice or not np.isfinite(choice.get("score", np.nan)):
            raise ValueError("Projection has no validation-fixed BDT cut")
        threshold = float(choice["score"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.sample}_{args.source_id}"
    prepared_dir = args.output_dir / "prepared"
    prepared_dir.mkdir(exist_ok=True)
    scan = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    record = preparation.process_file(args.input, args.sample, args.source_id,
        cfg, scenario, prepared_dir, args.max_output_events, scan)
    training.FEATURES = model_summary["features"]
    model = XGBClassifier()
    model.load_model(args.model_dir / "bdt_model.json")
    scored_dir = args.output_dir / "scored_audit"
    training.score_files(model, [prepared_dir / f"{stem}_audit.parquet"], scored_dir)
    flat_dir = args.output_dir / "flat"
    flat_dir.mkdir(exist_ok=True)
    flat_path = flat_dir / f"{stem}.parquet"
    command = [sys.executable, "studies/reconstruction/flatten_candidates.py",
               "--input", str(args.input), "--mode", "gamma",
               "--source-id", str(args.source_id), "--output", str(flat_path)]
    if args.max_output_events is not None:
        command += ["--max-events", str(args.max_output_events)]
    subprocess.run(command, check=True)
    full = materialize.attach(pq.read_table(flat_path),
                              pq.read_table(scored_dir / f"{stem}_audit.parquet"))
    selected = full.filter(full["pass_selected"])
    outputs = {"audit": full, "offline_selected": selected}
    if threshold is not None:
        outputs["bdt_selected"] = selected.filter(
            pc.greater_equal(selected["bdt_score"], threshold))
    counts = {}
    for name, table in outputs.items():
        target = args.output_dir / name / f"{stem}.parquet"
        target.parent.mkdir(exist_ok=True)
        metadata = dict(table.schema.metadata or {})
        metadata.update({b"stage1_input": str(args.input).encode(),
                         b"bdt_model": str(args.model_dir / "bdt_model.json").encode(),
                         b"offline_scenario": scenario.encode()})
        if threshold is not None:
            metadata[b"bdt_score_cut"] = repr(threshold).encode()
        pq.write_table(table.replace_schema_metadata(metadata), target,
                       compression="zstd")
        counts[name] = table.num_rows
    manifest = {"command": sys.argv, "input": str(args.input),
                "input_bytes": args.input.stat().st_size,
                "model_summary": str(args.model_dir / "training_summary.json"),
                "model_summary_sha256": sha(args.model_dir / "training_summary.json"),
                "model_sha256": sha(args.model_dir / "bdt_model.json"),
                "config": str(args.config), "config_sha256": sha(args.config),
                "scenario": scenario, "projection": str(args.projection) if args.projection else None,
                "bdt_score_cut": threshold, "source_id": args.source_id,
                "sample": args.sample, "record": record, "counts": counts,
                "max_output_events": args.max_output_events,
                "candidate_key": ["source_id", "event_entry", "candidate_slot"]}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"counts": counts, "events_processed": record["events_processed"],
                      "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
