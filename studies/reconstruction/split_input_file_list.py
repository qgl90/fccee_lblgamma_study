#!/usr/bin/env python3
"""Split an ordered ROOT input manifest into balanced, contiguous lists."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-list", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--n-shards", type=int, default=600)
    args = parser.parse_args()
    if args.n_shards < 1:
        parser.error("--n-shards must be positive")

    files = [line.strip() for line in args.input_list.read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not files:
        parser.error("input list contains no file paths")
    if len(files) < args.n_shards:
        parser.error(f"{len(files)} files cannot populate {args.n_shards} nonempty shards")
    if len(files) != len(set(files)):
        parser.error("input list contains duplicate paths")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for shard in range(args.n_shards):
        start = shard * len(files) // args.n_shards
        stop = (shard + 1) * len(files) // args.n_shards
        target = args.output_dir / f"file_list_chunk{shard}.txt"
        target.write_text("\n".join(files[start:stop]) + "\n")

    sizes = [len((args.output_dir / f"file_list_chunk{i}.txt").read_text().splitlines())
             for i in range(args.n_shards)]
    print(f"Wrote {args.n_shards} lists for {len(files)} files to {args.output_dir}")
    print(f"files per chunk: min={min(sizes)}, max={max(sizes)}")


if __name__ == "__main__":
    main()
