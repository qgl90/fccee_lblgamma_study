#!/usr/bin/env python3
"""Holdout check of one-variable background rejection on training inputs.

Thresholds and directions use only the event-grouped train split. Report
performance on the untouched test split for direct Gamma signal, generic Zbb,
and the specific Eta feed-down. Missing values fail an ordinary scalar cut;
partner-photon variables are omitted because no-partner must instead pass a
dedicated pi0 veto. This is not a multivariate model or a physical yield fit.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

PARTNER_FIELDS={"dm_gg_pi0","E_gamma2","dr_gg"}


def finite_values(table,name):
    return np.asarray([np.nan if v is None else float(v)
                       for v in table[name].to_pylist()])


def pass_cut(values,direction,threshold):
    finite=np.isfinite(values)
    return finite & ((values<=threshold) if direction=="<=" else
                     (values>=threshold))


def choose_cut(values,classes,splits,target):
    signal_train=(classes==1)&(splits=="train")
    bkg_train=(classes==0)&(splits=="train")
    available=np.isfinite(values[signal_train])
    valid_fraction=available.mean() if len(available) else 0.
    if (not len(values[signal_train]) or not len(values[bkg_train])
            or valid_fraction<target):
        return None
    q=target/valid_fraction
    signal_values=values[signal_train & np.isfinite(values)]
    options=[]
    for direction,quantile in (("<=",q),(">=",1.-q)):
        threshold=float(np.quantile(signal_values,quantile))
        keep_s=pass_cut(values[signal_train],direction,threshold)
        keep_b=pass_cut(values[bkg_train],direction,threshold)
        options.append({"direction":direction,"threshold":threshold,
                        "train_signal_retention":float(keep_s.mean()),
                        "train_zbb_rejection":float(1.-keep_b.mean())})
    return max(options,key=lambda row:row["train_zbb_rejection"])


def evaluate(values,classes,splits,cut):
    if cut is None:
        return None
    result=dict(cut)
    for label,class_id in (("signal",1),("zbb",0),("eta",2)):
        mask=(classes==class_id)&(splits=="test")
        selected=pass_cut(values[mask],cut["direction"],cut["threshold"])
        result[f"test_{label}_total"]=int(mask.sum())
        result[f"test_{label}_kept"]=int(selected.sum())
        result[f"test_{label}_retention"]=(float(selected.mean())
                                            if mask.any() else None)
    result["test_zbb_rejection"]=(1.-result["test_zbb_retention"]
                                   if result["test_zbb_retention"] is not None else None)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    table=pq.read_table(args.input)
    classes=table["class_id"].to_numpy()
    splits=np.asarray(table["split"].to_pylist())
    features=[name for name in table.column_names if name not in
              {"sample_id","source_id","event_entry","candidate_slot",
               "candidates_in_event","event_group","split","class_id",
               "class_name","training_eligible","candidate_weight"}
              and not name.startswith("has_")]
    summary={"input":str(args.input),"denominator":"all candidates of each class in test split; missing scalar values fail cuts",
             "partner_fields_omitted":sorted(PARTNER_FIELDS),"scans":{}}
    for name in features:
        vals=finite_values(table,name)
        entry={"missing_fraction":float(np.mean(~np.isfinite(vals)))}
        if name in PARTNER_FIELDS:
            entry["note"]="Use dedicated pi0 veto with no-partner pass state"
        else:
            for target in (.8,.5):
                entry[f"target_{int(target*100)}pct"]=evaluate(
                    vals,classes,splits,choose_cut(vals,classes,splits,target))
        summary["scans"][name]=entry
    # A missing partner passes a resolved-pi0 veto; it is not an invalid
    # candidate. This fixed physics window is evaluated without tuning.
    pi0_distance=finite_values(table,"dm_gg_pi0")
    veto_pass=(~np.isfinite(pi0_distance)) | (pi0_distance>=0.020)
    pi0_veto={"window_gev":0.020,"no_partner_passes":True}
    for label,class_id in (("signal",1),("zbb",0),("eta",2)):
        mask=(classes==class_id)&(splits=="test")
        pi0_veto[f"test_{label}_total"]=int(mask.sum())
        pi0_veto[f"test_{label}_kept"]=int(np.count_nonzero(veto_pass[mask]))
    summary["fixed_pi0_veto_20mev"]=pi0_veto
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,indent=2)+"\n")
    lines=["# Held-out one-variable check", "",
           "Thresholds and directions use training events only. Results below "
           "use test events and include invalid values as failures.", "",
           "| Variable | Missing | 80% train: test signal kept | 80% train: test Zbb rejection | 80% train: test η kept | 50% train: test signal kept | 50% train: test Zbb rejection |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for name,entry in summary["scans"].items():
        row80=entry.get("target_80pct")
        row50=entry.get("target_50pct")
        if row80 is None or row50 is None:
            continue
        percentage=lambda x: f"{100*x:.1f}%" if x is not None else "—"
        kept=lambda row,label: (f"{row[f'test_{label}_kept']}/{row[f'test_{label}_total']} "
                                f"({percentage(row[f'test_{label}_retention'])})")
        rejected=lambda row: (f"{row['test_zbb_total']-row['test_zbb_kept']}/"
                              f"{row['test_zbb_total']} "
                              f"({percentage(row['test_zbb_rejection'])})")
        lines.append(f"| `{name}` | {percentage(entry['missing_fraction'])} | "
                     f"{kept(row80,'signal')} | {rejected(row80)} | "
                     f"{kept(row80,'eta')} | {kept(row50,'signal')} | "
                     f"{rejected(row50)} |")
    markdown=args.output.with_suffix(".md")
    lines.extend(["", "Fixed resolved π⁰ veto (no partner passes; "
                  "reject $|m_{\\gamma\\gamma}-m_{\\pi^0}|<20$ MeV): "
                  f"test signal {pi0_veto['test_signal_kept']}/{pi0_veto['test_signal_total']}, "
                  f"test Zbb {pi0_veto['test_zbb_kept']}/{pi0_veto['test_zbb_total']}, "
                  f"test η {pi0_veto['test_eta_kept']}/{pi0_veto['test_eta_total']}."])
    markdown.write_text("\n".join(lines)+"\n")
    print("\n".join(lines))


if __name__=="__main__":
    main()
