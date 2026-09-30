#!/usr/bin/env python3
"""Stream candidate Parquet files from Zbb shards into one table."""

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq


def merge(paths, output):
    if not paths:
        raise ValueError("No input Parquet files found")
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = None
    rows = 0
    try:
        for path in paths:
            parquet = pq.ParquetFile(path)
            if writer is None:
                writer = pq.ParquetWriter(output, parquet.schema_arrow,
                                          compression="zstd")
            elif not parquet.schema_arrow.equals(writer.schema, check_metadata=False):
                raise ValueError(f"Schema mismatch in {path}")
            for batch in parquet.iter_batches(batch_size=100_000):
                writer.write_batch(batch)
                rows += batch.num_rows
    finally:
        if writer is not None:
            writer.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    selected = sorted(args.input_dir.glob("shard_*/zbb_file_*_selected.parquet"))
    rejected = sorted(args.input_dir.glob("shard_*/zbb_file_*_rejected.parquet"))
    if not selected or len(selected) != len(rejected):
        raise ValueError(f"Expected paired selected/rejected tables; found {len(selected)} and {len(rejected)}")
    summary = {
        "input_dir": str(args.input_dir),
        "source_files": len(selected),
        "selected_candidates": merge(selected, args.output_dir / "zbb_selected.parquet"),
        "rejected_candidates": merge(rejected, args.output_dir / "zbb_rejected.parquet"),
        "selected_output": str(args.output_dir / "zbb_selected.parquet"),
        "rejected_output": str(args.output_dir / "zbb_rejected.parquet"),
    }
    (args.output_dir / "merge_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
