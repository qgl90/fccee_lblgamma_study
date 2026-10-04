#!/usr/bin/env python3
"""Resume a frozen Zcc/Zss v3 catalog through offline cuts and a fixed BDT.

One process handles each ROOT chunk at a time. A complete chunk directory is
published atomically and holds all Stage 1 candidate rows, offline survivors,
BDT survivors, and a hash-checked manifest. Truth is carried for diagnosis only.
"""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import uuid

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

import prepare_offline_bdt as preparation


WINDOW = (5.4, 5.9)
_MODEL = None
_FEATURES = None
_CFG = None
_SCENARIO = None
_SCORE = None


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def init_worker(model_path, features, cfg, scenario, score):
    global _MODEL, _FEATURES, _CFG, _SCENARIO, _SCORE
    from xgboost import XGBClassifier
    _MODEL = XGBClassifier(n_jobs=1)
    _MODEL.load_model(model_path)
    _MODEL.set_params(n_jobs=1)
    _FEATURES = features
    _CFG = cfg
    _SCENARIO = scenario
    _SCORE = score


def table_counts(table):
    if table.num_rows == 0:
        return {"candidate_rows": 0, "candidate_bearing_events": 0,
                "direct_signal_rows": 0, "nonmatched_rows": 0,
                "peak_candidate_rows": 0, "peak_direct_signal_rows": 0,
                "peak_nonmatched_rows": 0, "peak_candidate_bearing_events": 0}
    mass = table["lb_mass"].to_numpy(zero_copy_only=False)
    truth = table["truth_matched"].to_numpy(zero_copy_only=False) == 1
    events = table["event_entry"].to_numpy(zero_copy_only=False)
    peak = (mass >= WINDOW[0]) & (mass <= WINDOW[1])
    return {"candidate_rows": int(table.num_rows),
            "candidate_bearing_events": int(np.unique(events).size),
            "direct_signal_rows": int(truth.sum()),
            "nonmatched_rows": int((~truth).sum()),
            "peak_candidate_rows": int(peak.sum()),
            "peak_direct_signal_rows": int((peak & truth).sum()),
            "peak_nonmatched_rows": int((peak & ~truth).sum()),
            "peak_candidate_bearing_events": int(np.unique(events[peak]).size)}


def check_existing(path, source, run_identity):
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        if path.exists():
            raise ValueError(f"Incomplete published chunk directory: {path}")
        return None
    manifest = json.loads(manifest_path.read_text())
    if manifest["source"] != source or manifest["run_identity"] != run_identity:
        raise ValueError(f"Published chunk has another input/scenario: {path}")
    for name, info in manifest["tables"].items():
        target = path / f"{name}.parquet"
        if (not target.is_file() or target.stat().st_size != info["bytes"] or
                pq.read_metadata(target).num_rows != info["rows"] or
                digest(target) != info["sha256"]):
            raise ValueError(f"Published table changed or incomplete: {target}")
    return manifest


def process_chunk(source, sample, parent, run_identity, max_output_events):
    import train_offline_bdt as training
    chunk_id = source["chunk_id"]
    target = Path(parent) / "chunks" / f"chunk_{chunk_id}"
    previous = check_existing(target, source, run_identity)
    if previous is not None:
        return previous
    temporary = Path(parent) / "work" / f"chunk_{chunk_id}_{uuid.uuid4().hex}"
    temporary.mkdir(parents=True)
    root_path = Path(source["root"])
    if root_path.stat().st_size != source["root_bytes"]:
        raise ValueError(f"ROOT size changed for chunk {chunk_id}")
    scan = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    stage1 = preparation.process_file(root_path, sample, chunk_id, _CFG,
                                      _SCENARIO, temporary, max_output_events, scan)
    if max_output_events is None and (stage1["events_processed"] != source["events_processed"] or
                                     stage1["root_output_events"] != source["candidate_bearing_output_events"]):
        raise ValueError(f"ROOT counters changed for chunk {chunk_id}")
    stem = f"{sample}_{chunk_id}"
    audit_path = temporary / f"{stem}_audit.parquet"
    selected_path = temporary / f"{stem}_selected.parquet"
    audit = pq.read_table(audit_path)
    selected = pq.read_table(selected_path) if selected_path.exists() else audit.slice(0, 0)
    if selected.num_rows != stage1["stages"]["selected"]["candidates"]:
        raise ValueError(f"Offline row count changed for chunk {chunk_id}")
    keys = ("source_id", "event_entry", "candidate_slot")
    for name, table in (("audit", audit), ("selected", selected)):
        rows = list(zip(*(table[key].to_pylist() for key in keys)))
        if len(rows) != len(set(rows)):
            raise ValueError(f"Repeated {name} candidate key in chunk {chunk_id}")
    if selected.num_rows:
        training.FEATURES = _FEATURES
        score = _MODEL.predict_proba(
            training.feature_matrix(selected.select(_FEATURES).to_pandas()))[:, 1]
        selected = selected.append_column("bdt_score", pa.array(score.astype("float32")))
    else:
        selected = selected.append_column("bdt_score", pa.array([], type=pa.float32()))
    bdt = selected.filter(pc.greater_equal(selected["bdt_score"], _SCORE))
    tables = {"audit": audit, "offline_selected": selected, "bdt_selected": bdt}
    information = {}
    for name, table in tables.items():
        path = temporary / f"{name}.parquet"
        pq.write_table(table, path, compression="zstd")
        information[name] = {"rows": table.num_rows, "bytes": path.stat().st_size,
                             "sha256": digest(path)}
    manifest = {"sample": sample, "source": source,
                "run_identity": run_identity, "stage1_record": stage1,
                "stage_counts": {name: table_counts(table) for name, table in tables.items()},
                "tables": information,
                "max_output_events": max_output_events}
    (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    audit_path.unlink()
    if selected_path.exists():
        selected_path.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ValueError(f"Chunk appeared during processing: {target}")
    os.replace(temporary, target)
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--projection", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--max-chunks", type=int, help="Development trial only")
    ap.add_argument("--max-output-events", type=int, help="Development trial cap per ROOT chunk")
    args = ap.parse_args()
    if args.workers < 1 or (args.max_chunks is not None and args.max_chunks < 1) or \
            (args.max_output_events is not None and args.max_output_events < 1):
        ap.error("Worker count and trial limits must be positive")
    if args.max_chunks is not None and args.max_output_events is None:
        ap.error("A development subset must cap output events")
    catalog = json.loads(args.catalog.read_text())
    sample = {"p8_ee_Zcc_ecm91": "zcc", "p8_ee_Zss_ecm91": "zss"}.get(
        catalog["sample_name"])
    if sample is None:
        ap.error("Catalog must identify Zcc or Zss")
    if catalog["invalid_chunks"] or len(catalog["chunks"]) != catalog["valid_chunks"]:
        ap.error("Catalog has invalid or inconsistent chunks")
    if len(catalog["schema_counts"]) != 1 or next(iter(catalog["schema_counts"])) != \
            "8be4dbee92339c54fba50c760b61bb1e045a3f2bf246f524516cbfbe359d1eb7":
        ap.error("Catalog is not the frozen v3 Stage 1 schema")
    model_summary_path = args.model_dir / "training_summary.json"
    model_summary = json.loads(model_summary_path.read_text())
    model_path = args.model_dir / "bdt_model.json"
    projection = json.loads(args.projection.read_text())
    if Path(projection["training_summary"]).resolve() != model_summary_path.resolve():
        ap.error("Projection identifies another BDT model")
    score = float(projection["validation_choice"]["score"])
    cfg_path = Path("config/lb_offline_selections.json")
    cfg = json.loads(cfg_path.read_text())
    scenario = model_summary["scenario"]
    preparation.validate_config(cfg, scenario)
    prepared_path = Path(model_summary["frozen_prepared_manifest"])
    if digest(prepared_path) != model_summary["prepared_manifest_sha256"]:
        ap.error("Frozen BDT preparation manifest changed")
    prepared = json.loads(prepared_path.read_text())
    if digest(cfg_path) != prepared["config_sha256"]:
        ap.error("Offline config differs from trained model")
    identity = {"catalog_sha256": digest(args.catalog), "model_sha256": digest(model_path),
                "projection_sha256": digest(args.projection), "config_sha256": digest(cfg_path),
                "runner_sha256": digest(Path(__file__)),
                "preparation_sha256": digest(Path(preparation.__file__)),
                "scenario": scenario, "score_cut": score,
                "mass_window_gev": list(WINDOW),
                "max_output_events": args.max_output_events}
    root = args.output_dir
    root.mkdir(parents=True, exist_ok=True)
    identity_path = root / "run_identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError("Output directory contains another catalog/model/score scenario")
    if not identity_path.exists():
        identity_path.write_text(json.dumps(identity, indent=2) + "\n")
    chunks = catalog["chunks"][:args.max_chunks]
    manifests = []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=init_worker,
            initargs=(str(model_path), model_summary["features"], cfg, scenario, score)) as pool:
        futures = {pool.submit(process_chunk, source, sample, str(root), identity,
                               args.max_output_events): source["chunk_id"] for source in chunks}
        for completed, future in enumerate(as_completed(futures), 1):
            manifest = future.result()
            manifests.append(manifest)
            if completed % 25 == 0 or completed == len(chunks):
                print(f"{sample}: complete {completed}/{len(chunks)} chunks", flush=True)
    manifests.sort(key=lambda item: item["source"]["chunk_id"])
    combined = {name: {key: sum(item["stage_counts"][name][key] for item in manifests)
                       for key in manifests[0]["stage_counts"][name]}
                for name in ("audit", "offline_selected", "bdt_selected")}
    summary = {"sample": sample, "catalog": str(args.catalog), "run_identity": identity,
               "input_chunks": len(chunks),
               "processed_input_events": sum(item["stage1_record"]["events_processed"] or 0
                                             for item in manifests),
               "candidate_bearing_stage1_events_in_root": sum(
                   item["stage1_record"]["root_output_events"] for item in manifests),
               "read_stage1_output_events": sum(
                   item["stage1_record"]["read_output_events"] for item in manifests),
               "stage_counts": combined,
               "complete_catalog": args.max_chunks is None and args.max_output_events is None and
                                   len(chunks) == catalog["valid_chunks"]}
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
