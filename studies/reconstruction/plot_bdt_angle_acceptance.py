#!/usr/bin/env python3
"""Generated-cos(theta_p) acceptance before/after BDT for PHSP and HELAMP.

PHSP uses only the signal test-event hash, matching the training split.
HELAMP is independent of training and uses all generated decays. Plot the
generated and selected counts on the second axis to expose sparse bins.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_training_inputs import stable_split
from study_cos_theta_p import generated_angles

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({"font.size":10,"axes.labelsize":11,"axes.titlesize":12,
                     "legend.fontsize":8,"xtick.labelsize":10,"ytick.labelsize":10,
                     "figure.autolayout":False})


def panel(ax,name,generated,selected,thresholds,bins,score_column,method):
    truth=np.asarray([r[3] for r in generated],dtype=float)
    denominator=np.histogram(truth,bins)[0]
    if np.any(denominator==0):
        raise ValueError(f"Empty generated angular bin in {name}")
    centers=(bins[:-1]+bins[1:])/2
    widths=np.diff(bins)/2
    selected_truth=selected["truth_cos_theta_p"].to_numpy(dtype=float)
    stage_masks=[("Post-Λ",np.ones(len(selected),dtype=bool),"#277DA1")]
    for label,key,color in (("BDT ~80%","sig80","#E76F51"),
                            ("BDT ~50%","sig50","#7A5195")):
        stage_masks.append((label.replace("BDT",method),
                            selected[score_column].to_numpy()>=thresholds[key],color))
    counts={"generated":denominator.tolist()}
    for label,mask,color in stage_masks:
        numerator=np.histogram(selected_truth[mask],bins)[0]
        if np.any(numerator>denominator):
            raise ValueError(f"Numerator exceeds generated in {name}: {label}")
        efficiency=numerator/denominator
        error=np.sqrt(efficiency*(1-efficiency)/denominator)
        ax.errorbar(centers,efficiency,xerr=widths,yerr=error,fmt="o-",capsize=2,
                    markersize=4,linewidth=1,color=color,label=f"{label} ({mask.sum()})")
        counts[label]={"selected":numerator.tolist(),"efficiency":efficiency.tolist()}
    ax.set(xlabel=r"Generated $\cos\theta_p$",ylabel="Selected / generated decays",
           xlim=(-1,1),ylim=(0,1),title=name)
    aux=ax.twinx()
    aux.stairs(denominator,bins,color="0.65",linewidth=1.1,label="Generated")
    aux.set(ylabel="Generated decays / bin",ylim=(0,1.35*max(denominator)))
    ax.legend(loc="upper center",frameon=False)
    return counts


def validate_physics_decay_content(generated, selected):
    """Check HELAMP selected decays by angle and charge without row-index joins.

    A multithreaded FCCAnalyses snapshot can reorder its event rows relative to
    the input EDM4hep tree. The truth angle belongs to the selected decay, so
    a unique angle/charge match still validates the generated denominator.
    """
    used=set()
    by_sign={sign:sorted((angle,i) for i,(_,_,s,angle) in enumerate(generated)
                          if s==sign) for sign in (-1,1)}
    import bisect
    for row in selected.itertuples():
        angle=float(row.truth_cos_theta_p)
        sign=int(row.lb_sign)
        options=by_sign[sign]
        at=bisect.bisect_left(options,(angle,-1))
        neighbors=options[max(0,at-2):min(len(options),at+3)]
        viable=[(abs(value-angle),index) for value,index in neighbors
                if index not in used]
        if not viable:
            raise ValueError("HELAMP truth angle has no unused generated decay")
        distance,index=min(viable)
        if distance>2e-4:
            raise ValueError(f"HELAMP selected decay cannot match generated content: {distance}")
        used.add(index)
    return len(used)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phsp-mc",type=Path,required=True)
    ap.add_argument("--phsp-events",type=int,required=True)
    ap.add_argument("--scored",type=Path,required=True)
    ap.add_argument("--metrics",type=Path,required=True)
    ap.add_argument("--physics-mc",type=Path,required=True)
    ap.add_argument("--physics-events",type=int,required=True)
    ap.add_argument("--physics-scored",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--score-column",default="bdt_score")
    ap.add_argument("--method",default="BDT")
    args=ap.parse_args()
    metrics=json.loads(args.metrics.read_text())
    thresholds={name:row["score_cut"] for name,row in metrics["thresholds"].items()}
    phsp=pq.read_table(args.scored).to_pandas()
    split_column="bdt_split" if args.score_column=="bdt_score" else "nn_split"
    phsp=phsp.loc[(phsp.class_id==1)&(phsp[split_column]=="test")].copy()
    sources=np.unique(phsp.source_id.to_numpy())
    if len(sources)!=1:raise ValueError("Need one forced PHSP source ID")
    source=int(sources[0])
    phsp_gen=[r for r in generated_angles(args.phsp_mc,args.phsp_events)
              if stable_split(f"signal_gamma:{source}:{r[0]}")=="test"]
    physics=pq.read_table(args.physics_scored).to_pandas()
    physics_gen=generated_angles(args.physics_mc,args.physics_events)
    validated_physics=validate_physics_decay_content(physics_gen,physics)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    bins=np.linspace(-1,1,11)
    fig,axes=plt.subplots(1,2,figsize=(14,5.5),sharey=True)
    result={"phsp_test":panel(axes[0],"PHSP: held-out signal events",phsp_gen,
                              phsp,thresholds,bins,args.score_column,args.method),
            "physics":panel(axes[1],"HELAMP: independent angular model",physics_gen,
                            physics,thresholds,bins,args.score_column,args.method)}
    fig.suptitle(f"Acceptance × reconstruction × post-Λ/{args.method} selection vs generated angle")
    fig.subplots_adjust(left=.07,right=.92,bottom=.16,top=.86,wspace=.28)
    prefix=args.method.lower()
    fig.savefig(args.output_dir/f"{prefix}_angle_acceptance.png",dpi=170)
    plt.close(fig)
    result["bin_edges"]=bins.tolist()
    result["denominators"]={"phsp_test_generated_decays":len(phsp_gen),
                            "physics_generated_decays":len(physics_gen),
                            "physics_selected_content_validated":validated_physics}
    result["physics_match_note"]=("Selected HELAMP decays are joined to generated "
        "decays by unique truth angle and charge because multithreaded snapshot "
        "event_entry does not preserve the input EDM4hep entry ordering.")
    (args.output_dir/f"{prefix}_angle_acceptance.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result["denominators"],indent=2))


if __name__=="__main__":main()
