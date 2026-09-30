#!/usr/bin/env python3
"""Score new independent Winter2023 Zbb files with frozen BDT and NN models.

No model fit, feature choice, or score threshold uses these extension files.
Save one row per post-Lambda candidate and a finite-MC peak-background limit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME",str(Path(tempfile.gettempdir())/"lblgamma-cache"))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL","2")

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import chi2
import tensorflow as tf
from xgboost import XGBClassifier

import nn_preprocessing  # Required for deserializing the frozen Processor.
from prepare_training_inputs import annotate
from train_postlambda_bdt import model_matrix


def count_passing(frame,score_column,cut):
    passed=frame[score_column].to_numpy()>=cut
    peak=frame.lb_mass.between(5.4,5.9,inclusive="left").to_numpy()
    return {"all":int(passed.sum()),"peak":int(np.count_nonzero(passed&peak)),
            "all_unique_events":int(frame.loc[passed,"event_group"].nunique()),
            "peak_unique_events":int(frame.loc[passed&peak,"event_group"].nunique())}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs",type=Path,nargs="+",required=True)
    ap.add_argument("--bdt-model",type=Path,required=True)
    ap.add_argument("--bdt-metrics",type=Path,required=True)
    ap.add_argument("--bdt-scored",type=Path,required=True)
    ap.add_argument("--nn-dir",type=Path,required=True)
    ap.add_argument("--yield-config",type=Path,default=Path("config/yield_projection.json"))
    ap.add_argument("--events-per-file",type=int,default=100000)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    if args.events_per_file<=0 or len(set(args.inputs))!=len(args.inputs):
        raise ValueError("Need positive denominator and unique input files")
    bdt_metrics=json.loads(args.bdt_metrics.read_text())
    nn_metrics=json.loads((args.nn_dir/"metrics.json").read_text())
    config=json.loads(args.yield_config.read_text())
    tf.config.threading.set_intra_op_parallelism_threads(8)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    model=XGBClassifier()
    model.load_model(args.bdt_model)
    nn=tf.keras.models.load_model(args.nn_dir/nn_metrics["selected_variant"]/"model.keras")
    processor=joblib.load(args.nn_dir/nn_metrics["selected_variant"]/"processor.joblib")
    rows=[];sources=set();inputs=[]
    for path in args.inputs:
        table=pq.read_table(path)
        source=np.unique(table["source_id"].to_numpy())
        if len(source)!=1 or int(source[0]) in sources:
            raise ValueError(f"Repeated or ambiguous source_id in {path}: {source}")
        sid=int(source[0]);sources.add(sid)
        if str(sid) in bdt_metrics["zbb_source_split"]:
            raise ValueError(f"Source {sid} was already used in BDT training/test")
        audit=annotate(table,"generic_zbb",sid).to_pandas()
        post=audit.loc[(audit.class_id==0)&
                       (audit.lambda_mass.sub(1.115683).abs()<.010)&
                       (audit.lb_mass.between(4.9,6.3))].copy()
        matrix=model_matrix(post)
        post["bdt_score"]=model.predict_proba(matrix)[:,1]
        post["nn_score"]=nn.predict(processor.transform(matrix),batch_size=2048,verbose=0).reshape(-1)
        rows.append(post)
        inputs.append({"path":str(path),"source_id":sid,
                       "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                       "stage1_candidates":len(audit),
                       "postlambda_background_candidates":len(post),
                       "excluded_direct_truth_matches":int(np.count_nonzero(audit.class_id==-1))})
        print(json.dumps(inputs[-1]),flush=True)
    extension=pd.concat(rows,ignore_index=True)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    extension.to_parquet(args.output_dir/"extension_scored_candidates.parquet",index=False)
    original=pq.read_table(args.bdt_scored,columns=["class_id","bdt_split",
        "bdt_score","lb_mass","event_group"]).to_pandas()
    original=original.loc[(original.class_id==0)&(original.bdt_split=="test")]
    nn_original=pq.read_table(args.nn_dir/"scored_candidates.parquet",columns=[
        "class_id","nn_split","nn_score","lb_mass","event_group"]).to_pandas()
    nn_original=nn_original.loc[(nn_original.class_id==0)&(nn_original.nn_split=="test")]
    if len(original)!=len(nn_original):
        raise ValueError("Original BDT/NN test background row count mismatch")
    n_original_events=int(bdt_metrics["denominators"]["test_zbb_generated_events"])
    n_extension_events=len(args.inputs)*args.events_per_file
    n_total_events=n_original_events+n_extension_events
    n_zbb=config["n_z"]*config["br_z_to_bb"]
    weight=n_zbb/n_total_events
    methods={}
    for method,metrics,baseline,score_column in (
        ("bdt",bdt_metrics,original,"bdt_score"),
        ("nn",nn_metrics,nn_original,"nn_score")):
        method_rows={}
        for name in ("sig95","sig90","sig80","sig50"):
            cut=metrics["thresholds"][name]["score_cut"]
            a=count_passing(baseline,score_column,cut)
            b=count_passing(extension,score_column,cut)
            n_peak=a["peak"]+b["peak"]
            # Exact one-sided 95% upper for a Poisson count with no subtraction.
            upper_count=float(chi2.ppf(.95,2*(n_peak+1))/2)
            sig=metrics["thresholds"][name]["peak_expected"]["signal"]
            eta=metrics["thresholds"][name]["peak_expected"]["eta"]
            projected_upper=upper_count*weight
            method_rows[name]={"score_cut":cut,"original_test_counts":a,
                "extension_counts":b,"combined_test_counts":{
                    "all":a["all"]+b["all"],"peak":n_peak,
                    "all_unique_events":a["all_unique_events"]+b["all_unique_events"],
                    "peak_unique_events":a["peak_unique_events"]+b["peak_unique_events"]},
                "peak_zbb_expected_central":n_peak*weight,
                "peak_zbb_expected_95pct_upper":projected_upper,
                "peak_signal_expected_upper_proxy":sig,
                "peak_eta_expected":eta,
                "peak_purity_with_zbb_count_upper_and_signal_production_upper_proxy":
                    sig/(sig+eta+projected_upper)}
        methods[method]=method_rows
    summary={"inputs":inputs,"original_test_generated_zbb_events":n_original_events,
             "extension_generated_zbb_events":n_extension_events,
             "combined_independent_test_generated_zbb_events":n_total_events,
             "postlambda_extension_background_candidates":len(extension),
             "peak_mass_window_gev":[5.4,5.9],"weight_per_combined_test_zbb_candidate":weight,
             "methods":methods,
             "interpretation":"Frozen selections on new independent sources. Candidate-count Poisson upper is one-sided 95%; check unique-event counts for candidate clustering. Projected ratios still use an all-b-baryon Lambda_b upper proxy and are not physical purity confidence bounds."}
    (args.output_dir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({"combined_test_events":n_total_events,
                      "postlambda_extension_candidates":len(extension),
                      "sig80":{k:v["sig80"] for k,v in methods.items()}},indent=2))


if __name__=="__main__":main()
