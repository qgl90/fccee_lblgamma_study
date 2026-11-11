#!/usr/bin/env python3
"""Copy verified Stage 2 candidate pairs from compatible preparations.

This repairs interrupted incremental preparations without rerunning ROOT
extraction. Run prepare_offline_bdt.py --resume afterward: it rechecks ROOT
counters, candidate coverage, and rebuilds the complete cutflow summary.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import shutil
from pathlib import Path

import pyarrow.parquet as pq


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair(directory, chunk_id):
    paths = [directory / f"zbb_{chunk_id}_{kind}.parquet"
             for kind in ("audit", "selected")]
    if not all(path.is_file() for path in paths):
        return None
    try:
        metadata = [pq.read_metadata(path) for path in paths]
    except (OSError, ValueError):
        return None
    if any(item.num_rows <= 0 for item in metadata):
        return None
    return paths, [(item.num_rows, item.schema.to_arrow_schema())
                   for item in metadata]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--prepared-dir", type=Path, required=True)
    ap.add_argument("--source-dir", type=Path, action="append", required=True)
    ap.add_argument("--execute", action="store_true",
                    help="Copy missing pairs; default only checks and reports")
    args = ap.parse_args()
    catalog = json.loads(args.catalog.read_text())
    chunk_ids = [item["chunk_id"] for item in catalog["chunks"]]
    if len(chunk_ids) != len(set(chunk_ids)):
        ap.error("Catalog has repeated chunk IDs")
    identity_path = args.prepared_dir / "preparation_identity.json"
    if not identity_path.is_file():
        ap.error(f"Missing preparation identity: {identity_path}")
    identity = json.loads(identity_path.read_text())
    sources = []
    for directory in args.source_dir:
        source_identity = directory / "preparation_identity.json"
        if not source_identity.is_file() or json.loads(source_identity.read_text()) != identity:
            ap.error(f"Preparation identity differs or is missing: {directory}")
        sources.append(directory)

    existing = 0
    to_copy = []
    unavailable = []
    for chunk_id in chunk_ids:
        target = pair(args.prepared_dir, chunk_id)
        candidates = [(source, pair(source, chunk_id)) for source in sources]
        candidates = [(source, value) for source, value in candidates if value]
        if target:
            if candidates and any(value[1] != target[1] for _, value in candidates):
                ap.error(f"Conflicting candidate pair for chunk {chunk_id}")
            existing += 1
        elif candidates:
            reference = candidates[0][1][1]
            if any(value[1] != reference for _, value in candidates[1:]):
                ap.error(f"Conflicting source pairs for chunk {chunk_id}")
            to_copy.append((chunk_id, candidates[0][1][0]))
        else:
            unavailable.append(chunk_id)

    result = {"catalog": str(args.catalog), "catalog_sha256": digest(args.catalog),
              "prepared_dir": str(args.prepared_dir),
              "source_dirs": [str(source) for source in sources],
              "catalog_chunks": len(chunk_ids), "already_prepared": existing,
              "copied": 0, "available_to_copy": len(to_copy),
              "copied_chunk_ids": [],
              "unavailable_chunk_ids": unavailable}
    if args.execute:
        for chunk_id, paths in to_copy:
            for source in paths:
                target = args.prepared_dir / source.name
                temporary = target.with_suffix(".parquet.tmp")
                shutil.copy2(source, temporary)
                temporary.replace(target)
            if pair(args.prepared_dir, chunk_id)[1] != pair(paths[0].parent, chunk_id)[1]:
                raise ValueError(f"Copied pair failed metadata check: {chunk_id}")
            result["copied"] += 1
            result["copied_chunk_ids"].append(chunk_id)
            if result["copied"] % 25 == 0:
                print(f"Copied {result['copied']}/{len(to_copy)} candidate pairs",
                      flush=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        manifest = args.prepared_dir / f"consolidation_{stamp}.json"
        result["manifest"] = str(manifest)
        manifest.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
