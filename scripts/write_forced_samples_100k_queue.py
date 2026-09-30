#!/usr/bin/env python3
"""Write Condor's chunk queue from the canonical generation config."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("config/config.yaml"),
        help="YAML workflow configuration (default: config/config.yaml)",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("work/condor/forced_samples_100k.queue"),
        help="queue file passed to condor_submit",
    )
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text())
    production = config["preselection_generation"]
    total_events = int(production["events"])
    chunks = int(production["chunks"])
    if total_events <= 0 or chunks <= 0 or total_events % chunks:
        parser.error("preselection_generation.events must divide evenly by chunks")

    rows = []
    chunk_events = total_events // chunks
    for sample, settings in production["samples"].items():
        seed_base = int(settings["seed"])
        for chunk in range(chunks):
            rows.append(
                f"{sample} {chunk} {seed_base + chunk} {chunk_events} {total_events}"
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(rows) + "\n")
    print(
        f"Wrote {len(rows)} jobs ({chunks} chunks/sample, "
        f"{chunk_events} events/chunk) to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
