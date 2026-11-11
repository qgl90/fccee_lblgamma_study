#!/usr/bin/env python3
"""Require the generated EDM4hep events tree to contain the requested count."""

import sys

import ROOT

path, expected_text = sys.argv[1:]
expected = int(expected_text)
root_file = ROOT.TFile.Open(path)
if not root_file or root_file.IsZombie():
    raise RuntimeError(f"Cannot open EDM4hep file: {path}")
events = root_file.Get("events")
if not events:
    raise RuntimeError(f"Missing events tree: {path}")
actual = events.GetEntries()
root_file.Close()
if actual != expected:
    raise RuntimeError(f"Expected {expected} events in {path}, found {actual}")
print(f"Validated {actual} events in {path}")
