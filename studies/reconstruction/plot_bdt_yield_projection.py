#!/usr/bin/env python3
"""Expected mass/angle after frozen BDT cuts, using only held-out test signal/Zbb.

The zero-background bins are MC upper limits, not predicted empty bins.
This is a candidate-count scenario with the editable all-b-baryon proxy.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from plot_yield_projection import draw_1d, draw_2d


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored",type=Path,required=True)
    ap.add_argument("--metrics",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--score-column",default="bdt_score")
    ap.add_argument("--method",default="BDT")
    args=ap.parse_args()
    metrics=json.loads(args.metrics.read_text())
    if metrics.get("pilot_event_split",False):
        raise ValueError("Yield plot requires file-held-out Zbb test")
    split_column="bdt_split" if args.score_column=="bdt_score" else "nn_split"
    columns=["class_id",split_column,args.score_column,"m_LamGam","cos_theta_p"]
    table=pq.read_table(args.scored,columns=columns)
    data={name:np.asarray(table[name].to_pylist()) for name in columns}
    label=data["class_id"].astype(int)
    split=data[split_column].astype(str)
    eligible=((np.isin(label,[0,1])&(split=="test"))|(label==2))
    weights=metrics["weights_per_candidate"]
    mass_bins=np.linspace(4.9,6.3,29)
    angle_bins=np.linspace(-1,1,11)
    summary={"input":str(args.scored),"metrics":str(args.metrics),
             "normalization":"test PHSP signal and independent Zbb files 8-9; all forced eta; candidates, not events",
             "weights_per_candidate":weights,"stages":{},
             "warning":"Zero Zbb survivors or cells mean no test MC support; upper count is approximately 3 at 95% CL."}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name in ("sig80","sig50"):
        score_cut=metrics["thresholds"][name]["score_cut"]
        mask=eligible&(data[args.score_column].astype(float)>=score_cut)
        title=f"Post-Λ + {args.method} {name} (validation score ≥ {score_cut:.3f})"
        counts={key:int(np.count_nonzero(mask&(label==cid)))
                for key,cid in (("signal",1),("zbb",0),("eta",2))}
        peak=(data["m_LamGam"].astype(float)>=5.4)&(data["m_LamGam"].astype(float)<5.9)
        peak_counts={key:int(np.count_nonzero(mask&peak&(label==cid)))
                     for key,cid in (("signal",1),("zbb",0),("eta",2))}
        summary["stages"][name]={
            "score_cut":score_cut,"mc_candidates":counts,"peak_mc_candidates":peak_counts,
            "expected_candidates":{k:counts[k]*weights[k] for k in counts},
            "peak_expected_candidates":{k:peak_counts[k]*weights[k] for k in peak_counts},
            "peak_zbb_zero_mc_approx_95pct_upper":
                3*weights["zbb"] if peak_counts["zbb"]==0 else None}
        note=("Independent-file test for signal and Zbb; forced η evaluation. "
              "Λb share=1 upper proxy; empty bins unresolved")
        prefix=args.method.lower()
        draw_1d(data,label,mask,weights,mass_bins,"m_LamGam",
                r"$m(\Lambda\gamma)$ [GeV]",title,
                args.output_dir/f"{prefix}_{name}_mass.png",note)
        draw_1d(data,label,mask,weights,angle_bins,"cos_theta_p",
                r"$\cos\theta_p$ (reconstructed)",title,
                args.output_dir/f"{prefix}_{name}_costheta.png",note)
        draw_2d(data,label,mask,weights,mass_bins,angle_bins,title,
                args.output_dir/f"{prefix}_{name}_mass_costheta.png")
    (args.output_dir/f"{args.method.lower()}_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary["stages"],indent=2))


if __name__=="__main__":main()
