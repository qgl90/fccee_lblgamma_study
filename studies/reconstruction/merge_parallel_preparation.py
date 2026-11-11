#!/usr/bin/env python3
"""Merge disjoint, completed Stage-2 preparation partitions for --resume.

The parent preparation is subsequently resumed against the full frozen
catalog; that step independently rebuilds all cutflow counters from the
candidate audit tables and checks the ROOT event denominators.
"""

# Author: Renato Quagliani (rquaglia@cern.ch)

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import pyarrow.parquet as pq


def metadata(path):
    info = pq.read_metadata(path)
    return info.num_rows, info.schema.to_arrow_schema()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--worker-root", type=Path, required=True)
    ap.add_argument("--prepared-dir", type=Path, required=True)
    args = ap.parse_args()
    catalog = json.loads(args.catalog.read_text())
    expected = {item["chunk_id"]: item for item in catalog["chunks"]}
    workers = sorted(path for path in args.worker_root.glob("part_*") if path.is_dir())
    if not workers:
        ap.error("No partition directories found")
    identity_path = args.prepared_dir / "preparation_identity.json"
    if not identity_path.exists():
        ap.error(f"Missing parent preparation identity: {identity_path}")
    identity = json.loads(identity_path.read_text())
    found = {}
    for worker in workers:
        summary_path = worker / "summary.json"
        if not summary_path.exists():
            ap.error(f"Worker is incomplete: {worker}")
        if json.loads((worker / "preparation_identity.json").read_text()) != identity:
            ap.error(f"Different preparation identity: {worker}")
        summary = json.loads(summary_path.read_text())
        for record in summary["records"][1:]:
            chunk_id = record["source_id"]
            if chunk_id not in expected or chunk_id in found:
                ap.error(f"Unexpected or repeated chunk {chunk_id}")
            item = expected[chunk_id]
            if record["path"] != item["root"] or \
                    record["events_processed"] != item["events_processed"] or \
                    record["root_bytes"] != item["root_bytes"]:
                ap.error(f"Catalog/source mismatch for chunk {chunk_id}")
            for kind, stage in (("audit", "stage1"), ("selected", "selected")):
                source = worker / f"zbb_{chunk_id}_{kind}.parquet"
                if not source.exists() or metadata(source)[0] != record["stages"][stage]["candidates"]:
                    ap.error(f"Incomplete {kind} table for chunk {chunk_id}")
            found[chunk_id] = worker
    if set(found) != set(expected):
        ap.error(f"Partitions cover {len(found)}/{len(expected)} catalog chunks")
    copied = 0
    retained = 0
    for chunk_id, worker in sorted(found.items()):
        sources = [worker / f"zbb_{chunk_id}_{kind}.parquet"
                   for kind in ("audit", "selected")]
        targets = [args.prepared_dir / source.name for source in sources]
        if all(target.exists() and metadata(target) == metadata(source)
               for source, target in zip(sources, targets)):
            retained += 1
            continue
        for source, target in zip(sources, targets):
            temporary = target.with_suffix(".parquet.tmp")
            shutil.copy2(source, temporary)
            temporary.replace(target)
        copied += 1
    result = {"catalog": str(args.catalog),
              "catalog_sha256": hashlib.sha256(args.catalog.read_bytes()).hexdigest(),
              "prepared_dir": str(args.prepared_dir),
              "workers": [str(worker) for worker in workers],
              "chunk_ids": sorted(found), "copied_chunks": copied,
              "retained_matching_chunks": retained,
              "next_step": "rerun prepare_offline_bdt.py against full catalog with --resume"}
    (args.prepared_dir / "parallel_merge_manifest.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in
                      ("copied_chunks", "retained_matching_chunks", "next_step")}, indent=2))


if __name__ == "__main__":
    main()
