#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def _set_or_add(lines: list[str], key: str, value: str) -> list[str]:
    key_prefix = f"{key} ="
    out: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(key_prefix):
            out.append(f"{key} = {value}\n")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"\n{key} = {value}\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--nevents", required=True, type=int)
    ap.add_argument("--seed", required=True, type=int)
    args = ap.parse_args()

    text = args.input.read_text()
    lines = [l if l.endswith("\n") else f"{l}\n" for l in text.splitlines()]

    lines = _set_or_add(lines, "Main:numberOfEvents", str(args.nevents))
    # Pythia8 RNG seed settings (safe even if already present)
    lines = _set_or_add(lines, "Random:setSeed", "on")
    lines = _set_or_add(lines, "Random:seed", str(args.seed))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

