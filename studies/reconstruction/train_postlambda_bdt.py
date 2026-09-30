#!/usr/bin/env python3
"""Train a mass/angle-blind XGBoost BDT after the fitted-Lambda mass cut.

Train on truth-matched PHSP Lambda-gamma against inclusive Zbb combinations.
Split generic Zbb by source file and forced signal by event; reserve Lambda-eta
and wrong combinations for diagnostics. Choose score thresholds from validation
signal only, then report independent test performance and MC counting limits.
"""

import argparse
import json
import math
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "lblgamma-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score, roc_curve
from xgboost import XGBClassifier

from prepare_training_inputs import FEATURES, stable_split

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({"font.size":10,"axes.labelsize":11,"axes.titlesize":12,
                     "legend.fontsize":9,"xtick.labelsize":10,
                     "ytick.labelsize":10,"figure.autolayout":False})

FEATURE_SET = tuple(name for name in FEATURES if name not in
                    ("lambda_thrust_cos","neutral_thrust_cos")) + (
                        "lambda_thrust_abs","neutral_thrust_abs",
                        "hemisphere_product")
LABELS={1:"True PHSP signal",0:"Generic Zbb",2:"True Eta feed-down",-1:"Wrong combinations"}
COLORS={1:"#277DA1",0:"#43AA8B",2:"#7A5195",-1:"#F3722C"}


def model_matrix(frame):
    """Only declared reconstructed observables; missing sentinels become NaN."""
    absent=(set(FEATURE_SET)-{"lambda_thrust_abs","neutral_thrust_abs",
                             "hemisphere_product","lambda_thrust_cos",
                             "neutral_thrust_cos"})-set(frame.columns)
    absent |= {"lambda_thrust_cos","neutral_thrust_cos"}-set(frame.columns)
    if absent:
        raise KeyError(f"Missing model features: {sorted(absent)}")
    matrix=frame.loc[:,[name for name in FEATURE_SET if name in frame.columns]].astype("float32").copy()
    matrix["lambda_thrust_abs"]=np.abs(frame["lambda_thrust_cos"].to_numpy())
    matrix["neutral_thrust_abs"]=np.abs(frame["neutral_thrust_cos"].to_numpy())
    matrix["hemisphere_product"]=(frame["lambda_thrust_cos"].to_numpy()*
                                   frame["neutral_thrust_cos"].to_numpy())
    matrix=matrix.loc[:,list(FEATURE_SET)]
    matrix=matrix.mask(~np.isfinite(matrix) | (matrix<=-998.))
    return matrix


def split_masks(frame, pilot):
    sample=frame["sample_id"].astype(str).to_numpy()
    split=frame["split"].astype(str).to_numpy()
    source=frame["source_id"].to_numpy().astype(int)
    zbb_sources=sorted(int(x) for x in set(source[sample=="generic_zbb"]))
    if not pilot and len(zbb_sources)<5:
        raise ValueError("Need >=5 independent Zbb source files; use --pilot for a smoke test")
    if pilot:
        zbb_map={s:None for s in zbb_sources}
        assignment=split.copy()
    else:
        n=len(zbb_sources)
        n_train=max(1,int(round(.7*n)))
        n_val=max(1,int(round(.1*n)))
        if n_train+n_val>=n:
            n_train=n-2; n_val=1
        zbb_map={s:("train" if i<n_train else "validation" if i<n_train+n_val else "test")
                 for i,s in enumerate(zbb_sources)}
        assignment=split.copy()
        assignment[sample=="generic_zbb"]=[zbb_map[s] for s in source[sample=="generic_zbb"]]
    return assignment,zbb_map


def balance_weights(y):
    n1=np.count_nonzero(y==1); n0=np.count_nonzero(y==0)
    if min(n1,n0)<10:
        raise ValueError(f"Too few training candidates: signal={n1}, Zbb={n0}")
    return np.where(y==1,len(y)/(2*n1),len(y)/(2*n0))


def plot_roc(y,score,output):
    fpr,tpr,_=roc_curve(y,score)
    fig,ax=plt.subplots(figsize=(7.5,5.8))
    ax.plot(tpr,1/np.maximum(fpr,1/max(1,np.count_nonzero(y==0))),color=COLORS[1],lw=2)
    ax.set(xlabel="Signal efficiency relative to post-Λ sample",
           ylabel="Generic Zbb rejection factor (finite-MC capped)",
           yscale="log",xlim=(0,1),title=f"Independent test ROC; AUC={roc_auc_score(y,score):.4f}")
    ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(output,dpi=170);plt.close(fig)


def plot_scores(frame,assignment,output):
    fig,ax=plt.subplots(figsize=(9,5.8))
    score=frame["bdt_score"].to_numpy()
    label=frame["class_id"].to_numpy()
    sample=frame["sample_id"].astype(str).to_numpy()
    for cid in (1,0,2,-1):
        mask=(label==cid)
        if cid in (1,0):mask &= assignment=="test"
        if cid==-1:mask &= sample=="signal_gamma"
        if not mask.any():continue
        ax.hist(score[mask],bins=np.linspace(0,1,51),histtype="step",lw=1.8,
                weights=np.full(mask.sum(),1/mask.sum()),label=f"{LABELS[cid]} ({mask.sum()})",
                color=COLORS[cid])
    ax.set(xlabel="BDT score",ylabel="Fraction of class / bin",yscale="log",
           ylim=(1e-4,1),title="Held-out score distributions; Eta and wrong combinations diagnostic")
    ax.legend(frameon=False)
    fig.tight_layout();fig.savefig(output,dpi=170);plt.close(fig)


def plot_mass_angle(frame,assignment,threshold,output,lb_mass_range):
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    sample=frame["sample_id"].astype(str).to_numpy()
    labels=frame["class_id"].to_numpy()
    score=frame["bdt_score"].to_numpy()
    for row,(cid,name) in enumerate(((1,"PHSP signal"),(0,"generic Zbb"))):
        base=(labels==cid)&(assignment=="test")
        for col,(feature,bins,xlabel) in enumerate((
            ("lb_mass",np.linspace(*lb_mass_range,29),r"$m(\Lambda\gamma)$ [GeV]"),
            ("cos_theta_p",np.linspace(-1,1,21),r"$\cos\theta_p$"))):
            ax=axes[row,col]
            for sub,label,style in ((base,"post-Λ", "-"),(base&(score>=threshold),"BDT kept","--")):
                vals=frame.loc[sub,feature].to_numpy()
                if len(vals):
                    ax.hist(vals,bins=bins,weights=np.full(len(vals),1/len(vals)),
                            histtype="step",lw=1.6,linestyle=style,
                            color=COLORS[cid],label=f"{label} ({len(vals)})")
            ax.set(xlabel=xlabel,ylabel="Shape / bin",title=name,ylim=(0,None))
            ax.legend(frameon=False)
    fig.suptitle(f"Mass and angle checks at validation-selected score ≥ {threshold:.3f}")
    fig.tight_layout(rect=(0,0,1,.95));fig.savefig(output,dpi=170);plt.close(fig)


def plot_importance(model,output):
    gain=model.get_booster().get_score(importance_type="gain")
    # XGBoost 3 may serialize DataFrame columns as f0, f1, ... even though
    # the model matrix was named. Map positions back to the declared schema.
    values={name:gain.get(name,gain.get(f"f{index}",0.))
            for index,name in enumerate(FEATURE_SET)}
    items=sorted(((value,name) for name,value in values.items()),reverse=True)[:18]
    fig,ax=plt.subplots(figsize=(9,6.5))
    ax.barh([name for _,name in items[::-1]],[value for value,_ in items[::-1]],
            color="#277DA1")
    ax.set(xlabel="Average XGBoost split gain",title="Top reconstructed inputs")
    fig.subplots_adjust(left=.37,right=.97,bottom=.12,top=.91)
    fig.savefig(output,dpi=170);plt.close(fig)


def generated_split_denominator(frame,manifest,split_name):
    """Hash generated event IDs with the same stable rule as signal candidates."""
    n=manifest["input_events"]["signal_gamma"]
    source=int(frame.loc[frame.sample_id=="signal_gamma","source_id"].iloc[0])
    return sum(stable_split(f"signal_gamma:{source}:{entry}")==split_name
               for entry in range(n))


def physics_check(path,model,thresholds,input_events,lambda_pdg,lambda_half_window,lb_mass_range):
    data=pq.read_table(path).to_pandas()
    mask=((data["truth_matched"].to_numpy()==1)
          & (np.abs(data["lambda_mass"]-lambda_pdg)<lambda_half_window)
          & data["lb_mass"].between(*lb_mass_range).to_numpy())
    selected=data.loc[mask].copy()
    selected["bdt_score"]=model.predict_proba(model_matrix(selected))[:,1]
    result={"input":str(path),"input_events":input_events,
            "matched_postlambda_candidates":len(selected),
            "matched_postlambda_event_efficiency":selected["event_entry"].nunique()/input_events,
            "thresholds":{name:{"matched_candidates":int((selected.bdt_score>=value).sum()),
                                 "event_efficiency":selected.loc[selected.bdt_score>=value,"event_entry"].nunique()/input_events}
                          for name,value in thresholds.items()}}
    return result,selected


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input",type=Path,required=True,
                    help="candidate_audit_postlambda.parquet")
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--yield-config",type=Path,default=Path("config/yield_projection.json"))
    ap.add_argument("--physics",type=Path)
    ap.add_argument("--physics-input-events",type=int)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--pilot",action="store_true",help="Allow event-level split of one Zbb file for code smoke only")
    args=ap.parse_args()
    frame=pq.read_table(args.input).to_pandas()
    manifest=json.loads(args.manifest.read_text())
    config=json.loads(args.yield_config.read_text())
    lb_mass_range=manifest.get("lb_mass_range_gev",[4.9,6.3])
    lambda_half_window=manifest.get("lambda_mass_half_window_gev",.010)
    lambda_pdg=manifest.get("lambda_pdg_gev",1.115683)
    required={"sample_id","source_id","event_group","split","class_id","lb_mass","cos_theta_p"}
    if required-set(frame):raise KeyError(f"Missing columns: {required-set(frame)}")
    if not np.all(frame.lb_mass.between(*lb_mass_range)&
                  (np.abs(frame.lambda_mass-lambda_pdg)<lambda_half_window)):
        raise ValueError("Input is not post-Λ preselection")
    assignment,zbb_map=split_masks(frame,args.pilot)
    y_all=frame.class_id.to_numpy().astype(int)
    matrix=model_matrix(frame)
    train=np.isin(y_all,[0,1])&(assignment=="train")
    val=np.isin(y_all,[0,1])&(assignment=="validation")
    test=np.isin(y_all,[0,1])&(assignment=="test")
    for name,mask in (("train",train),("validation",val),("test",test)):
        if np.unique(y_all[mask]).size!=2:
            raise ValueError(f"{name} split does not contain both classes")
    model=XGBClassifier(n_estimators=600,max_depth=3,learning_rate=.045,
                        min_child_weight=20,subsample=.8,colsample_bytree=.85,
                        reg_lambda=8,objective="binary:logistic",eval_metric="auc",
                        tree_method="hist",n_jobs=8,random_state=314159,
                        early_stopping_rounds=35)
    model.fit(matrix.loc[train],y_all[train],sample_weight=balance_weights(y_all[train]),
              eval_set=[(matrix.loc[val],y_all[val])],
              sample_weight_eval_set=[balance_weights(y_all[val])],verbose=False)
    score=model.predict_proba(matrix)[:,1]
    frame["bdt_score"]=score
    frame["bdt_split"]=assignment
    val_sig=score[val&(y_all==1)]
    thresholds={f"sig{int(100*target)}":float(np.quantile(val_sig,1-target))
                for target in (.99,.95,.9,.8,.7,.5,.3,.1)}
    test_sig=(test&(y_all==1))
    test_zbb=(test&(y_all==0))
    eta=(y_all==2)
    wrong=(y_all==-1)&(frame.sample_id.to_numpy()=="signal_gamma")
    n_sig_den=generated_split_denominator(frame,manifest,"test")
    n_zbb_den=(len([s for s,x in zbb_map.items() if x=="test"])*
               manifest["input_events"]["generic_zbb"]//max(1,len(zbb_map))
               if not args.pilot else int(round(.15*manifest["input_events"]["generic_zbb"])))
    n_eta_den=manifest["input_events"]["specific_eta"]
    n_zbb=config["n_z"]*config["br_z_to_bb"]
    n_lb=2*n_zbb*config["f_b_baryon_per_b_at_z"]*config["lambda_b_share_of_b_baryons"]
    w_sig=n_lb*config["br_lb_to_lambda_gamma"]*config["br_lambda_to_p_pi"]/n_sig_den
    w_zbb=n_zbb/n_zbb_den
    w_eta=(n_lb*config["br_lb_to_lambda_eta"]*config["br_lambda_to_p_pi"]*
           config["br_eta_to_gamma_gamma"]/n_eta_den)
    peak=(frame.lb_mass.to_numpy()>=5.4)&(frame.lb_mass.to_numpy()<5.9)
    threshold_rows={}
    for name,cut in thresholds.items():
        passing=score>=cut
        counts={"test_signal":int(np.count_nonzero(test_sig&passing)),
                "test_zbb":int(np.count_nonzero(test_zbb&passing)),
                "eta":int(np.count_nonzero(eta&passing)),
                "signal_wrong":int(np.count_nonzero(wrong&passing)),
                "peak_test_signal":int(np.count_nonzero(test_sig&passing&peak)),
                "peak_test_zbb":int(np.count_nonzero(test_zbb&passing&peak)),
                "peak_eta":int(np.count_nonzero(eta&passing&peak))}
        expected={"signal":counts["peak_test_signal"]*w_sig,
                  "zbb":counts["peak_test_zbb"]*w_zbb,
                  "eta":counts["peak_eta"]*w_eta}
        upper_zbb=(counts["peak_test_zbb"]+3 if counts["peak_test_zbb"]==0 else
                   counts["peak_test_zbb"]+1.96*math.sqrt(counts["peak_test_zbb"])) * w_zbb
        central_purity=(expected["signal"]/(sum(expected.values())) if sum(expected.values()) else None)
        upper_bg_purity=(expected["signal"]/(expected["signal"]+upper_zbb+expected["eta"])
                         if expected["signal"]+upper_zbb+expected["eta"] else None)
        threshold_rows[name]={"score_cut":cut,"counts":counts,
                              "test_signal_relative_efficiency":counts["test_signal"]/max(1,np.count_nonzero(test_sig)),
                              "test_zbb_relative_efficiency":counts["test_zbb"]/max(1,np.count_nonzero(test_zbb)),
                              "peak_expected":expected,
                              "peak_central_purity":central_purity,
                              "peak_purity_with_conservative_zbb_count":upper_bg_purity,
                              "peak_zbb_count_upper_approx_95pct":upper_zbb/w_zbb}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    model.save_model(args.output_dir/"bdt_model.json")
    frame.to_parquet(args.output_dir/"scored_candidates.parquet",index=False)
    plot_roc(y_all[test],score[test],args.output_dir/"test_roc.png")
    plot_scores(frame,assignment,args.output_dir/"test_scores.png")
    plot_mass_angle(frame,assignment,thresholds["sig50"],args.output_dir/"mass_angle_sculpting_sig50.png",lb_mass_range)
    plot_importance(model,args.output_dir/"feature_gain.png")
    physics=None
    if args.physics:
        if not args.physics_input_events or args.physics_input_events<=0:
            raise ValueError("Supply --physics-input-events")
        physics,physics_selected=physics_check(args.physics,model,thresholds,args.physics_input_events,
                                               lambda_pdg,lambda_half_window,lb_mass_range)
        physics_selected.to_parquet(args.output_dir/"physics_scored_candidates.parquet",index=False)
    result={"input":str(args.input),"manifest":str(args.manifest),
            "pilot_event_split":args.pilot,"zbb_source_split":zbb_map,
            "model":"XGBoost depth-3 gradient boosted trees, fixed hyperparameters with validation early stopping",
            "best_iteration":int(model.best_iteration),"features":list(FEATURE_SET),
            "split_counts":{name:{str(cid):int(np.count_nonzero(mask&(y_all==cid))) for cid in (1,0)}
                            for name,mask in (("train",train),("validation",val),("test",test))},
            "test_auc":float(roc_auc_score(y_all[test],score[test])),
            "denominators":{"test_signal_generated_events":n_sig_den,
                            "test_zbb_generated_events":n_zbb_den,
                            "eta_generated_events":n_eta_den},
            "weights_per_candidate":{"signal":w_sig,"zbb":w_zbb,"eta":w_eta},
            "baseline_peak_mc":{"test_signal":int(np.count_nonzero(test_sig&peak)),
                                "test_zbb":int(np.count_nonzero(test_zbb&peak)),
                                "eta":int(np.count_nonzero(eta&peak))},
            "thresholds":threshold_rows,"physics_check":physics,
            "cautions":["Score cuts are chosen from validation signal only; test sources are independent for Zbb unless pilot mode.",
                        "Purity is a scenario projection using the all-b-baryon Lambda_b upper proxy.",
                        "Zero test Zbb survivors are bounded by three MC events at about 95% CL, not treated as zero physical background.",
                        "No mass or cos(theta_p) input is used; inspect saved shape plots for sculpting."]}
    (args.output_dir/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# Post-Λ-mass BDT review", "",
           f"Test AUC: **{result['test_auc']:.4f}**; best iteration {model.best_iteration}.",
           f"Zbb source assignment: `{zbb_map}`.","",
           "| Validation target | Score | Test signal kept | Test Zbb kept | Peak signal / Zbb / Eta MC | Purity with Zbb upper* |",
           "|---|---:|---:|---:|---:|---:|"]
    for name,row in threshold_rows.items():
        c=row["counts"]
        purity=row["peak_purity_with_conservative_zbb_count"]
        if purity is None:
            purity_text="undefined"
        else:
            purity_text=f"{100*purity:.3f}%"
        lines.append(f"| {name} | {row['score_cut']:.4f} | {c['test_signal']} | {c['test_zbb']} | "
                     f"{c['peak_test_signal']} / {c['peak_test_zbb']} / {c['peak_eta']} | "
                     f"{purity_text} |")
    lines += ["", f"Peak means 5.4–5.9 GeV diagnostic interval; candidate interval is {lb_mass_range[0]}–{lb_mass_range[1]} GeV.",
              "Projected purities use the editable yield config; they are not sensitivity results.",
              "* Uses the approximate 95% upper Zbb count, including three events when none survive; the Lambda_b yield itself is an upper proxy, so this is not a guaranteed purity floor.",
              "The score, all original labels, mass, angle, source, and event keys are retained in scored_candidates.parquet."]
    if physics:
        lines += ["",f"Physics HELAMP smoke: {physics['matched_postlambda_candidates']} matched post-Λ candidates from {physics['input_events']} input events."]
    (args.output_dir/"metrics.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"test_auc":result["test_auc"],"split_counts":result["split_counts"],
                      "baseline_peak_mc":result["baseline_peak_mc"],"thresholds":threshold_rows},indent=2))


if __name__=="__main__":
    main()
