#!/usr/bin/env python3
"""Overlay new stage-1 Lambda_b candidate diagnostics and make pilot scans.

The scan uses truth-matched forced Gamma candidates as its signal reference.
For each scalar it tests both one-sided directions at the requested relative
signal retention and reports the direction that removes most Zbb candidates.
These are exploratory same-sample scans, not approved cuts or yield estimates.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import mplhep as hep
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"analysis"/"studies"))
from observables_stage1 import BRANCHES as OBS_BRANCHES

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({"font.size": 11, "axes.labelsize": 12,
                     "axes.titlesize": 13, "legend.fontsize": 9,
                     "xtick.labelsize": 10, "ytick.labelsize": 10})

ONE_D = (
    "m_LamGam", "m_rec", "deltaE", "px_bal", "py_bal",
    "Estar_gamma", "Estar_gamma_rec", "E_same", "dca_Lam_gamma",
    "iso_R03_noLambda", "iso_R05_noLambda", "iso_delphes",
    "dm_gg_pi0", "n_photons_DR03", "lambda_pv_cos", "lambda_pv_dca",
)
TWO_D = (
    ("m_LamGam", "m_rec"),
    ("Estar_gamma", "m_LamGam"),
    ("iso_R03_noLambda", "E_same"),
    ("dca_Lam_gamma", "deltaE"),
    ("lambda_pv_cos", "lambda_flight_rxy_sig"),
)
LABELS = {
    "m_LamGam": r"$m(\Lambda\gamma)$ [GeV]",
    "m_rec": r"$m_{\rm rec}$ [GeV]",
    "deltaE": r"$\Delta E$ [GeV]",
    "px_bal": r"$p_x$ balance [GeV]",
    "py_bal": r"$p_y$ balance [GeV]",
    "Estar_gamma": r"$E^*_{\gamma}(\Lambda\gamma)$ [GeV]",
    "Estar_gamma_rec": r"$E^*_{\gamma}(p_{\rm rec})$ [GeV]",
    "E_same": r"$E_{\rm same}$ [GeV]",
    "dca_Lam_gamma": r"$\mathrm{DCA}_{\Lambda\gamma}$ proxy [mm]",
    "iso_R03_noLambda": r"$I_{0.3}^{\rm no\ \Lambda}$",
    "iso_R05_noLambda": r"$I_{0.5}^{\rm no\ \Lambda}$",
    "iso_delphes": "Delphes IsolationVar",
    "dm_gg_pi0": r"$|m(\gamma\gamma')-m(\pi^0)|$ [GeV]",
    "n_photons_DR03": r"$N_{\gamma}$ in $\Delta R<0.3$",
    "lambda_pv_cos": r"$\cos(\Lambda,\mathrm{PV}\to\mathrm{SV})$",
    "lambda_pv_dca": r"$\Lambda$ line DCA to PV [mm]",
    "lambda_flight_rxy_sig": r"$\Lambda$ transverse flight significance",
}


def values(table, name):
    if name not in table.column_names:
        return np.array([])
    return table[name].to_numpy().astype(float)


def valid(array):
    return np.isfinite(array) & (array > -998.)


def ranges(name, groups):
    if name == "m_LamGam":
        return 4.9, 6.3
    if name == "dm_gg_pi0":
        return 0., 0.4
    if name.startswith("iso_"):
        return 0., 2.
    if name == "n_photons_DR03":
        return -0.5, 10.5
    merged = np.concatenate([v[valid(v)] for v in groups if len(v)])
    if not len(merged):
        return 0., 1.
    lo, hi = np.quantile(merged, [.005, .995])
    pad = max((hi-lo)*.05, .01)
    return float(lo-pad), float(hi+pad)


def best_one_sided(signal, background, target):
    s = signal[valid(signal)]
    b = background[valid(background)]
    if len(s) < 2 or len(b) < 2:
        return None
    candidates = []
    for direction, threshold in (("<=", np.quantile(s, target)),
                                 (">=", np.quantile(s, 1.-target))):
        test = (lambda x: x <= threshold) if direction == "<=" else (lambda x: x >= threshold)
        retained_s = int(np.count_nonzero(test(s)))
        retained_b = int(np.count_nonzero(test(b)))
        candidates.append({"direction": direction, "threshold": float(threshold),
                           "signal_retention": retained_s/len(s),
                           "background_rejection": 1.-retained_b/len(b),
                           "signal_kept": retained_s, "signal_valid": len(s),
                           "background_kept": retained_b,
                           "background_valid": len(b)})
    return max(candidates, key=lambda row: row["background_rejection"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal", type=Path, required=True)
    parser.add_argument("--eta", type=Path, required=True)
    parser.add_argument("--zbb", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    s_all = pq.read_table(args.signal)
    truth = s_all["truth_matched"].to_numpy() == 1
    tables = {
        "Truth matched signal": s_all.filter(pa.array(truth)),
        "Other signal combinations": s_all.filter(pa.array(~truth)),
        "Eta sample as Gamma": pq.read_table(args.eta),
        "Generic Zbb": pq.read_table(args.zbb),
    }
    colors = ("#277DA1", "#F3722C", "#7A5195", "#43AA8B")
    result = {"inputs": {"signal": str(args.signal), "eta": str(args.eta),
                         "zbb": str(args.zbb)},
              "candidate_counts": {name: table.num_rows for name,table in tables.items()},
              "scan_definition": "Best of <= and >= thresholds trained and counted on these same samples; exploratory only",
              "scans": {}}
    for name in ONE_D:
        arrays = [values(table,name) for table in tables.values()]
        if not any(np.count_nonzero(valid(v)) for v in arrays):
            result["scans"][name] = {"available": False}
            fig,ax=plt.subplots(figsize=(8.5,5.5))
            ax.text(.5,.5,"IsolationVar is not persisted in these EDM4hep files",
                    transform=ax.transAxes,ha="center",va="center",fontsize=13)
            ax.set(xlabel=LABELS.get(name,name),ylabel="Candidates",
                   title=name,xlim=(0,1),ylim=(0,1))
            fig.tight_layout()
            fig.savefig(args.output_dir/f"overlay_{name}.png",dpi=150)
            plt.close(fig)
            continue
        lo,hi = ranges(name,arrays)
        bins = np.linspace(lo,hi,51) if name != "n_photons_DR03" else np.arange(-.5,11.5,1)
        fig,ax = plt.subplots(figsize=(8.5,5.5))
        for (label,_),array,color in zip(tables.items(),arrays,colors):
            selected=array[valid(array)]
            if len(selected):
                ax.hist(selected,bins=bins,histtype="step",
                        weights=np.full(len(selected),1./len(array)),
                        linewidth=1.7,label=f"{label} ({len(selected)})",color=color)
        ax.set(xlabel=LABELS.get(name,name),ylabel="Fraction of all candidates / bin",
               title=name)
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(args.output_dir/f"overlay_{name}.png",dpi=150)
        plt.close(fig)
        if name == "dm_gg_pi0":
            # Missing partners must pass a pi0 veto. A generic one-sided scan
            # on only valid masses would have a misleading denominator.
            result["scans"][name] = {"available": True,
                                      "note": "No-partner candidates require a separate pass category"}
            continue
        result["scans"][name] = {
            "available": True,
            "target_80pct": best_one_sided(arrays[0],arrays[3],.8),
            "target_50pct": best_one_sided(arrays[0],arrays[3],.5),
        }

    for xname,yname in TWO_D:
        fig,axes=plt.subplots(1,2,figsize=(11.2,4.8),sharex=True,sharey=True)
        xr=ranges(xname,[values(t,xname) for t in tables.values()])
        yr=ranges(yname,[values(t,yname) for t in tables.values()])
        for ax,label in zip(axes,("Truth matched signal","Generic Zbb")):
            x=values(tables[label],xname);y=values(tables[label],yname)
            mask=valid(x)&valid(y)
            ax.hist2d(x[mask],y[mask],bins=(40,40),range=(xr,yr),
                      norm=LogNorm(vmin=1),cmap="viridis")
            ax.set(xlabel=LABELS.get(xname,xname),
                   ylabel=LABELS.get(yname,yname),title=f"{label} ({mask.sum()})")
        fig.tight_layout()
        fig.savefig(args.output_dir/f"scatter_{xname}_vs_{yname}.png",dpi=150)
        plt.close(fig)
    for name in OBS_BRANCHES:
        if name in result["scans"]:
            continue
        signal_values=values(tables["Truth matched signal"],name)
        background_values=values(tables["Generic Zbb"],name)
        result["scans"][name] = {
            "available": bool(np.count_nonzero(valid(signal_values)) and
                              np.count_nonzero(valid(background_values))),
            "target_80pct": best_one_sided(signal_values,background_values,.8),
            "target_50pct": best_one_sided(signal_values,background_values,.5),
        }
    (args.output_dir/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# Exploratory one-variable scan", "",
           "Each row selects the better of a lower or upper cut on the same "
           "samples used to set the threshold. Fractions use valid "
           "candidate values; these are not cross-validated cuts.", "",
           "| Variable | Valid signal / Zbb | Zbb rejection at ~80% signal | Zbb rejection at ~50% signal |",
           "|---|---:|---:|---:|"]
    for name in OBS_BRANCHES:
        scan=result["scans"].get(name,{})
        def describe(row):
            return (f"{100*row['background_rejection']:.1f}% "
                    f"({row['direction']} {row['threshold']:.8g})") if row else "—"
        a=scan.get("target_80pct");b=scan.get("target_50pct")
        valid_count=f"{a['signal_valid']} / {a['background_valid']}" if a else "—"
        lines.append(f"| `{name}` | {valid_count} | {describe(a)} | {describe(b)} |")
    (args.output_dir/"scan_table.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines[:6]+[line for line in lines[6:] if
                           line.split("`")[1] in ONE_D]))


if __name__ == "__main__":
    main()
