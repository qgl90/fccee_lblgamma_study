#!/usr/bin/env python3
"""Freeze newly valid chunks between two catalogs of one Condor campaign."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--previous", type=Path, required=True)
    ap.add_argument("--current", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    previous = json.loads(args.previous.read_text())
    current = json.loads(args.current.read_text())
    for field in ("sample_name", "job_dir", "root_dir"):
        if previous[field] != current[field]:
            ap.error(f"Campaign field changed: {field}")
    old = {item["chunk_id"]: item for item in previous["chunks"]}
    new = {item["chunk_id"]: item for item in current["chunks"]}
    if len(old) != len(previous["chunks"]) or len(new) != len(current["chunks"]):
        ap.error("Duplicate chunk ID")
    if not set(old) <= set(new):
        ap.error(f"Current catalog drops {len(set(old)-set(new))} earlier chunks")
    changed = [chunk_id for chunk_id, item in old.items() if item != new[chunk_id]]
    if changed:
        ap.error(f"Earlier chunk records changed: {changed[:20]}")
    chunks = [item for item in current["chunks"] if item["chunk_id"] not in old]
    if not chunks:
        ap.error("No new valid chunks")
    result = dict(current)
    result.update({
        "chunks": chunks, "valid_chunks": len(chunks),
        "root_chunks_checked": len(chunks),
        "total_processed_events_in_valid_chunks": sum(x["events_processed"] for x in chunks),
        "total_candidate_bearing_output_events_in_valid_chunks": sum(
            x["candidate_bearing_output_events"] for x in chunks),
        "schema_counts": {key: sum(x["schema_sha256"] == key for x in chunks)
                          for key in sorted({x["schema_sha256"] for x in chunks})},
        "subset_only": True,
        "parent_catalog": str(args.current),
        "parent_catalog_sha256": digest(args.current),
        "previous_catalog": str(args.previous),
        "previous_catalog_sha256": digest(args.previous),
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        ap.error(f"Frozen output already exists: {args.output}")
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"new_valid_chunks": len(chunks),
                      "processed_events": result["total_processed_events_in_valid_chunks"],
                      "candidate_bearing_events": result[
                          "total_candidate_bearing_output_events_in_valid_chunks"]}, indent=2))


if __name__ == "__main__":
    main()
