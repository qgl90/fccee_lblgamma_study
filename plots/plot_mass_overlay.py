#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import ROOT


@dataclass(frozen=True)
class Sample:
    name: str
    path: str
    scale: float


def _parse_triplets(value: str) -> list[Sample]:
    value = (value or "").strip()
    if not value:
        return []
    out: list[Sample] = []
    for entry in value.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("|")
        if len(parts) != 3:
            raise ValueError(f"Bad entry '{entry}', expected name|path|scale")
        name, path, scale_s = parts
        out.append(Sample(name=name, path=path, scale=float(scale_s)))
    return out


def _parse_pair(value: str) -> tuple[str, float]:
    parts = value.split("|")
    if len(parts) != 2:
        raise ValueError("Bad --signal, expected path|scale")
    return parts[0], float(parts[1])


def _hist_from_tree(
    file_path: str,
    tree_name: str,
    branch: str,
    nbins: int,
    xmin: float,
    xmax: float,
    hist_name: str,
) -> ROOT.TH1:
    f = ROOT.TFile.Open(file_path)
    if not f or f.IsZombie():
        raise RuntimeError(f"Failed to open ROOT file: {file_path}")
    t = f.Get(tree_name)
    if not t:
        raise RuntimeError(f"Tree '{tree_name}' not found in: {file_path}")

    h = ROOT.TH1F(hist_name, "", nbins, xmin, xmax)
    h.Sumw2()
    # Keep file alive by attaching histogram to gROOT
    h.SetDirectory(0)
    draw_expr = f"{branch}>>{hist_name}"
    n = t.Draw(draw_expr, "", "goff")
    if n < 0:
        raise RuntimeError(f"Failed to draw '{branch}' from {file_path}")
    f.Close()
    return h


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--tree", default="events")
    ap.add_argument("--branch", default="lb_reco_m")
    ap.add_argument("--nbins", type=int, default=120)
    ap.add_argument("--xmin", type=float, default=4.8)
    ap.add_argument("--xmax", type=float, default=6.4)
    ap.add_argument("--normalize", choices=["none", "area"], default="none")
    ap.add_argument("--signal", required=True, help="path|scale")
    ap.add_argument("--backgrounds", default="", help="name|path|scale;name|path|scale;...")
    args = ap.parse_args()

    ROOT.gROOT.SetBatch(True)

    out_png = Path(args.out)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    sig_path, sig_scale = _parse_pair(args.signal)
    bgs = _parse_triplets(args.backgrounds)

    hs_signal = _hist_from_tree(
        sig_path, args.tree, args.branch, args.nbins, args.xmin, args.xmax, "h_signal"
    )
    hs_signal.Scale(sig_scale)

    h_bgs: list[tuple[Sample, ROOT.TH1]] = []
    for i, bg in enumerate(bgs):
        h = _hist_from_tree(
            bg.path,
            args.tree,
            args.branch,
            args.nbins,
            args.xmin,
            args.xmax,
            f"h_bg_{i}",
        )
        h.Scale(bg.scale)
        h_bgs.append((bg, h))

    if args.normalize == "area":
        for _, h in h_bgs:
            if h.Integral() > 0:
                h.Scale(1.0 / h.Integral())
        if hs_signal.Integral() > 0:
            hs_signal.Scale(1.0 / hs_signal.Integral())

    c = ROOT.TCanvas("c", "c", 900, 700)
    c.SetLeftMargin(0.12)
    c.SetBottomMargin(0.12)

    stack = ROOT.THStack("stack", "")
    legend = ROOT.TLegend(0.62, 0.65, 0.88, 0.88)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)

    # Backgrounds as filled stack
    colors = [ROOT.kAzure + 1, ROOT.kGreen + 2, ROOT.kOrange + 7, ROOT.kMagenta - 2, ROOT.kGray + 1]
    for i, (bg, h) in enumerate(h_bgs):
        h.SetFillColor(colors[i % len(colors)])
        h.SetLineColor(ROOT.kBlack)
        stack.Add(h)
        legend.AddEntry(h, bg.name, "f")

    if len(h_bgs) > 0:
        stack.Draw("hist")
        stack.GetXaxis().SetTitle(args.branch)
        stack.GetYaxis().SetTitle("Events")
        stack.SetMinimum(0)
    else:
        hs_signal.Draw("hist")
        hs_signal.GetXaxis().SetTitle(args.branch)
        hs_signal.GetYaxis().SetTitle("Events")
        hs_signal.SetMinimum(0)

    # Signal as line
    hs_signal.SetLineColor(ROOT.kRed)
    hs_signal.SetLineWidth(3)
    hs_signal.SetFillStyle(0)
    if len(h_bgs) > 0:
        hs_signal.Draw("hist same")
        legend.AddEntry(hs_signal, "signal", "l")
    else:
        legend.AddEntry(hs_signal, "signal", "l")

    legend.Draw()
    c.SaveAs(str(out_png))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
