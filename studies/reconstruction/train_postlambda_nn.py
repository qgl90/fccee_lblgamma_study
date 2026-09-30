#!/usr/bin/env python3
"""Train and audit dense neural nets after the existing fitted-Lambda window.

Truth-matched PHSP signal and inclusive Winter2023 Zbb train the classifier.
Zbb source files 8-9 and PHSP test events are untouched until model choice and
thresholds are frozen on validation. Eta and wrong combinations are diagnostics.
No fit mass, helicity angle, ancestry, event ID, or source ID enters the net.
"""

import argparse
import json
import math
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"lblgamma-mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME",str(Path(tempfile.gettempdir())/"lblgamma-cache"))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL","2")
os.environ.setdefault("OMP_NUM_THREADS","8")

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score, roc_curve
import tensorflow as tf

from nn_preprocessing import Processor
from train_postlambda_bdt import FEATURE_SET, model_matrix

plt.style.use(hep.style.LHCb2)
plt.rcParams.update({"font.size":10,"axes.labelsize":11,"legend.fontsize":9})

# This list is frozen from training-only BDT split gains and physics definitions.
# The third variant checks whether the two strongest closure inputs dominate.
CORE_FEATURES=(
    "E_same","deltaE","hemisphere_product","lb_pt",
    "iso_R05_noLambda_E","iso_R05_noLambda","iso_R03_noLambda",
    "deltaP","iso_R03_noLambda_E","iso_R02","lambda_flight_rxy",
    "iso_neutral","n_photons_DR05","cos_rec_sig","lambda_mass",
    "photon_reco_energy","lambda_flight_rxy_sig","lambda_vertex_chi2",
    "proton_d0sig","pion_d0sig","lambda_pv_dca","m_rec",
    "Estar_gamma_rec",
)
VARIANTS={
    "compact":CORE_FEATURES,
    "all_reco":FEATURE_SET,
    "no_closure":tuple(x for x in CORE_FEATURES if x not in {"E_same","deltaE"}),
}
TARGETS=(.99,.95,.90,.80,.70,.50,.30)
COLORS={1:"#277DA1",0:"#43AA8B",2:"#7A5195",-1:"#F3722C"}
FEATURE_GROUPS={
    "Z closure / ROE":("E_same","m_same","deltaE","px_bal","py_bal",
                       "pz_bal","deltaP","m_rec","m_rec_all","cos_rec_sig",
                       "Estar_gamma_rec","roe_n_same","roe_n_other"),
    "Photon isolation / partner":("iso_R02","iso_R03","iso_R05",
                       "iso_R03_noLambda","iso_R05_noLambda",
                       "iso_R03_noLambda_E","iso_R05_noLambda_E",
                       "iso_charged","iso_neutral","n_photons_DR03",
                       "n_photons_DR05","dm_gg_pi0","E_gamma2","dr_gg"),
    "Fitted Lambda topology":("lambda_mass","lambda_vertex_chi2",
                       "lambda_flight_rxy","lambda_flight_rxy_sig",
                       "proton_d0sig","pion_d0sig","lambda_pv_dca"),
    "Kinematics / hemisphere":("lb_pt","photon_reco_energy",
                       "lambda_thrust_abs","neutral_thrust_abs",
                       "hemisphere_product"),
}


def check_input(frame,manifest,bdt_metrics):
    expected={"signal_gamma":manifest["input_events"]["signal_gamma"],
              "specific_eta":manifest["input_events"]["specific_eta"],
              "generic_zbb":manifest["input_events"]["generic_zbb"]}
    if bdt_metrics["pilot_event_split"] or len(bdt_metrics["zbb_source_split"])<5:
        raise ValueError("Need the independent-file BDT baseline, not pilot mode")
    if (frame["lb_mass"].lt(4.9)|frame["lb_mass"].gt(6.3)|
        frame["lambda_mass"].sub(1.115683).abs().ge(.010)).any():
        raise ValueError("Input is not the frozen post-Lambda selection")
    if not all(n>0 for n in expected.values()):
        raise ValueError("Invalid generated-event denominator")
    assignment=np.asarray([
        bdt_metrics["zbb_source_split"][str(int(source))]
        if sample=="generic_zbb" else split
        for source,sample,split in zip(frame.source_id,frame.sample_id,frame.split)
    ])
    y=frame.class_id.to_numpy(dtype=int)
    # Confirm exactly the same candidate partition as the BDT comparison.
    for partition in ("train","validation","test"):
        for label in (0,1):
            actual=int(np.count_nonzero((assignment==partition)&(y==label)))
            baseline=bdt_metrics["split_counts"][partition][str(label)]
            if actual!=baseline:
                raise ValueError(f"Split mismatch {partition}/{label}: {actual} vs {baseline}")
    event_split=frame.loc[frame.class_id==1].groupby("event_group")["split"].nunique()
    if not event_split.empty and event_split.max()>1:
        raise ValueError("PHSP event leakage across splits")
    return assignment,y


def build_net(n_inputs,seed):
    tf.keras.utils.set_random_seed(seed)
    net=tf.keras.Sequential([
        tf.keras.layers.Input(shape=(n_inputs,)),
        tf.keras.layers.Dense(64,activation="relu",kernel_regularizer=tf.keras.regularizers.l2(1e-3)),
        tf.keras.layers.Dropout(.15),
        tf.keras.layers.Dense(32,activation="relu",kernel_regularizer=tf.keras.regularizers.l2(1e-3)),
        tf.keras.layers.Dropout(.10),
        tf.keras.layers.Dense(1,activation="sigmoid"),
    ])
    net.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=8e-4),
                loss="binary_crossentropy",
                metrics=[tf.keras.metrics.AUC(name="auc")])
    return net


def train_variant(name,names,matrix,y,assignment,output_dir,epochs):
    train=(assignment=="train")&np.isin(y,[0,1])
    validation=(assignment=="validation")&np.isin(y,[0,1])
    processor=Processor(names).fit(matrix.loc[train])
    x_train=processor.transform(matrix.loc[train]);x_val=processor.transform(matrix.loc[validation])
    y_train=y[train].astype("float32");y_val=y[validation].astype("float32")
    n_signal=np.count_nonzero(y_train==1);n_bg=np.count_nonzero(y_train==0)
    weights=np.where(y_train==1,len(y_train)/(2*n_signal),len(y_train)/(2*n_bg)).astype("float32")
    net=build_net(x_train.shape[1],314159+len(names))
    callbacks=[tf.keras.callbacks.EarlyStopping(monitor="val_auc",mode="max",
                patience=15,min_delta=2e-4,restore_best_weights=True)]
    history=net.fit(x_train,y_train,sample_weight=weights,
                    validation_data=(x_val,y_val),epochs=epochs,batch_size=384,
                    callbacks=callbacks,verbose=0,shuffle=True)
    score=net.predict(x_val,batch_size=2048,verbose=0).reshape(-1)
    auc=float(roc_auc_score(y_val,score))
    val_sig=score[y_val==1];val_bg=score[y_val==0]
    cut=float(np.quantile(val_sig,.2))
    row={"variant":name,"features":list(names),"validation_auc":auc,
         "train_signal":int(n_signal),"train_zbb":int(n_bg),
         "validation_signal":int(np.count_nonzero(y_val==1)),
         "validation_zbb":int(np.count_nonzero(y_val==0)),
         "validation_zbb_at_sig80":int(np.count_nonzero(val_bg>=cut)),
         "epochs":len(history.history["loss"]),
         "best_val_auc_keras":float(max(history.history["val_auc"])),
         "input_dim":int(x_train.shape[1])}
    variant_dir=output_dir/name
    variant_dir.mkdir(parents=True,exist_ok=True)
    net.save(variant_dir/"model.keras")
    joblib.dump(processor,variant_dir/"processor.joblib")
    (variant_dir/"validation.json").write_text(json.dumps(row,indent=2)+"\n")
    return row,net,processor


def score_all(net,processor,matrix):
    return net.predict(processor.transform(matrix),batch_size=2048,verbose=0).reshape(-1)


def plot_scores(frame,assignment,path):
    score=frame.nn_score.to_numpy()
    label=frame.class_id.to_numpy()
    sample=frame.sample_id.to_numpy()
    fig,ax=plt.subplots(figsize=(9,5.8))
    for cid,name in ((1,"True PHSP signal"),(0,"Generic Zbb"),
                     (2,"True eta feed-down"),(-1,"Wrong signal combinations")):
        mask=(label==cid)
        if cid in (0,1):mask &= assignment=="test"
        if cid==-1:mask &= sample=="signal_gamma"
        if not mask.any():continue
        ax.hist(score[mask],bins=np.linspace(0,1,51),histtype="step",lw=1.8,
                weights=np.full(mask.sum(),1/mask.sum()),color=COLORS[cid],
                label=f"{name} ({mask.sum()})")
    ax.set(xlabel="NN score",ylabel="Fraction of class / bin",yscale="log",
           ylim=(1e-4,1),title="Held-out NN scores; eta and wrong combinations diagnostic")
    ax.legend(frameon=False)
    fig.tight_layout();fig.savefig(path,dpi=170);plt.close(fig)


def plot_roc_compare(y,score,bdt_score,path):
    fig,ax=plt.subplots(figsize=(7.5,5.8))
    n_bg=np.count_nonzero(y==0)
    for values,name,color in ((score,"NN","#277DA1"),(bdt_score,"BDT baseline","#F3722C")):
        fpr,tpr,_=roc_curve(y,values)
        ax.plot(tpr,1/np.maximum(fpr,1/n_bg),lw=2,color=color,
                label=f"{name}: AUC {roc_auc_score(y,values):.4f}")
    ax.set(xlabel="Signal retention / post-Λ candidates",
           ylabel="Zbb rejection (finite-MC capped)",xlim=(.5,1),yscale="log",
           title="Same independent-file test; 1,655 Zbb candidates")
    ax.legend(frameon=False);ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(path,dpi=170);plt.close(fig)


def plot_mass_angle(frame,assignment,cut,path):
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    score=frame.nn_score.to_numpy();y=frame.class_id.to_numpy()
    for row,(cid,name) in enumerate(((1,"PHSP signal"),(0,"generic Zbb"))):
        base=(y==cid)&(assignment=="test")
        for col,(feature,bins,label) in enumerate((
            ("lb_mass",np.linspace(4.9,6.3,29),r"$m(\Lambda\gamma)$ [GeV]"),
            ("cos_theta_p",np.linspace(-1,1,21),r"$\cos\theta_p$"))):
            ax=axes[row,col]
            for sel,title,style in ((base,"post-Λ","-"),(base&(score>=cut),"NN kept","--")):
                values=frame.loc[sel,feature].to_numpy()
                if len(values):
                    ax.hist(values,bins=bins,weights=np.full(len(values),1/len(values)),
                            histtype="step",linestyle=style,lw=1.6,
                            color=COLORS[cid],label=f"{title} ({len(values)})")
            ax.set(xlabel=label,ylabel="Shape / bin",title=name,ylim=(0,None))
            ax.legend(frameon=False)
    fig.suptitle(f"Mass and angle after frozen NN score ≥ {cut:.3f}")
    fig.tight_layout(rect=(0,0,1,.95));fig.savefig(path,dpi=170);plt.close(fig)


def group_permutation(net,processor,matrix,y,assignment,output_dir):
    """Validation-only group permutation; shared shuffle preserves group structure."""
    validation=(assignment=="validation")&np.isin(y,[0,1])
    source=matrix.loc[validation].copy()
    truth=y[validation]
    baseline=net.predict(processor.transform(source),batch_size=2048,verbose=0).reshape(-1)
    auc=float(roc_auc_score(truth,baseline))
    rng=np.random.default_rng(314159)
    rows=[]
    for group,names in FEATURE_GROUPS.items():
        present=[name for name in names if name in processor.names]
        shuffled=source.copy()
        order=rng.permutation(len(shuffled))
        shuffled.loc[:,present]=source.iloc[order][present].to_numpy()
        score=net.predict(processor.transform(shuffled),batch_size=2048,verbose=0).reshape(-1)
        rows.append({"group":group,"features":present,
                     "validation_auc_permuted":float(roc_auc_score(truth,score)),
                     "delta_auc":float(auc-roc_auc_score(truth,score))})
    rows.sort(key=lambda r:r["delta_auc"],reverse=True)
    result={"validation_auc_unpermuted":auc,"groups":rows,
            "note":"Whole-group row permutation on validation only; breaks cross-group correlations and is descriptive, not causal."}
    (output_dir/"feature_group_permutation.json").write_text(json.dumps(result,indent=2)+"\n")
    fig,ax=plt.subplots(figsize=(8,5.2))
    ax.barh([r["group"] for r in rows[::-1]],[r["delta_auc"] for r in rows[::-1]],
            color="#277DA1")
    ax.set(xlabel="Validation AUC decrease after group permutation",
           title="NN input group importance; validation data only")
    fig.subplots_adjust(left=.32,right=.97,bottom=.16,top=.90)
    fig.savefig(output_dir/"feature_group_permutation.png",dpi=170)
    plt.close(fig)
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--bdt-metrics",type=Path,required=True)
    ap.add_argument("--bdt-scored",type=Path,required=True)
    ap.add_argument("--physics",type=Path,required=True)
    ap.add_argument("--physics-input-events",type=int,default=10000)
    ap.add_argument("--yield-config",type=Path,default=Path("config/yield_projection.json"))
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--epochs",type=int,default=120)
    args=ap.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    tf.config.threading.set_intra_op_parallelism_threads(8)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    frame=pq.read_table(args.input).to_pandas()
    manifest=json.loads(args.manifest.read_text())
    bdt=json.loads(args.bdt_metrics.read_text())
    config=json.loads(args.yield_config.read_text())
    assignment,y=check_input(frame,manifest,bdt)
    matrix=model_matrix(frame)
    trained=[]
    for name,names in VARIANTS.items():
        row,net,processor=train_variant(name,names,matrix,y,assignment,
                                         args.output_dir,args.epochs)
        trained.append(row)
        print(json.dumps({k:row[k] for k in ("variant","validation_auc",
                            "validation_zbb_at_sig80","epochs")}),flush=True)
        del net,processor
        tf.keras.backend.clear_session()
    # Validation decides; the independent test is evaluated only once below.
    chosen=max(trained,key=lambda r:(r["validation_auc"],
                                      -r["validation_zbb_at_sig80"]))
    chosen_dir=args.output_dir/chosen["variant"]
    net=tf.keras.models.load_model(chosen_dir/"model.keras")
    processor=joblib.load(chosen_dir/"processor.joblib")
    score=score_all(net,processor,matrix)
    importance=group_permutation(net,processor,matrix,y,assignment,args.output_dir)
    frame["nn_score"]=score
    frame["nn_split"]=assignment
    validation=(assignment=="validation")&(y==1)
    thresholds={f"sig{int(100*t)}":float(np.quantile(score[validation],1-t))
                for t in TARGETS}
    test_sig=(assignment=="test")&(y==1)
    test_bg=(assignment=="test")&(y==0)
    eta=y==2
    wrong=(y==-1)&(frame.sample_id.to_numpy()=="signal_gamma")
    peak=frame.lb_mass.between(5.4,5.9,inclusive="left").to_numpy()
    n_sig_den=bdt["denominators"]["test_signal_generated_events"]
    n_bg_den=bdt["denominators"]["test_zbb_generated_events"]
    n_eta_den=manifest["input_events"]["specific_eta"]
    n_zbb=config["n_z"]*config["br_z_to_bb"]
    n_lb=2*n_zbb*config["f_b_baryon_per_b_at_z"]*config["lambda_b_share_of_b_baryons"]
    weights={
        "signal":n_lb*config["br_lb_to_lambda_gamma"]*config["br_lambda_to_p_pi"]/n_sig_den,
        "zbb":n_zbb/n_bg_den,
        "eta":n_lb*config["br_lb_to_lambda_eta"]*config["br_lambda_to_p_pi"]*
               config["br_eta_to_gamma_gamma"]/n_eta_den,
    }
    if any(abs(weights[k]-bdt["weights_per_candidate"][k])>1e-6 for k in weights):
        raise ValueError("NN and BDT projection weights differ")
    baseline=pq.read_table(args.bdt_scored,columns=["sample_id","source_id",
        "event_entry","candidate_slot","bdt_score"]).to_pandas()
    keys=["sample_id","source_id","event_entry","candidate_slot"]
    pair=frame[keys].merge(baseline,on=keys,how="left",validate="one_to_one",sort=False)
    if pair.bdt_score.isna().any() or len(pair)!=len(frame):
        raise ValueError("BDT and NN candidate keys do not align")
    bdt_score=pair.bdt_score.to_numpy()
    rows={}
    for name,cut in thresholds.items():
        passing=score>=cut
        counts={
            "test_signal":int(np.count_nonzero(test_sig&passing)),
            "test_zbb":int(np.count_nonzero(test_bg&passing)),
            "eta":int(np.count_nonzero(eta&passing)),
            "signal_wrong":int(np.count_nonzero(wrong&passing)),
            "peak_test_signal":int(np.count_nonzero(test_sig&passing&peak)),
            "peak_test_zbb":int(np.count_nonzero(test_bg&passing&peak)),
            "peak_eta":int(np.count_nonzero(eta&passing&peak)),
        }
        peak_expected={"signal":counts["peak_test_signal"]*weights["signal"],
                       "zbb":counts["peak_test_zbb"]*weights["zbb"],
                       "eta":counts["peak_eta"]*weights["eta"]}
        upper_bg_count=(3. if counts["peak_test_zbb"]==0 else
                        counts["peak_test_zbb"]+1.96*math.sqrt(counts["peak_test_zbb"]))
        denom=peak_expected["signal"]+peak_expected["eta"]+upper_bg_count*weights["zbb"]
        rows[name]={"score_cut":cut,"counts":counts,
                    "test_signal_relative_efficiency":counts["test_signal"]/int(test_sig.sum()),
                    "test_zbb_relative_efficiency":counts["test_zbb"]/int(test_bg.sum()),
                    "peak_expected":peak_expected,
                    "peak_zbb_count_upper_approx_95pct":upper_bg_count,
                    "peak_purity_with_conservative_zbb_count":peak_expected["signal"]/denom}
    frame.to_parquet(args.output_dir/"scored_candidates.parquet",index=False)
    physics=pq.read_table(args.physics).to_pandas()
    p_mask=(physics.truth_matched.to_numpy()==1)&(
        physics.lambda_mass.sub(1.115683).abs().to_numpy()<.010)
    physics=physics.loc[p_mask].copy()
    physics["nn_score"]=score_all(net,processor,model_matrix(physics))
    physics.to_parquet(args.output_dir/"physics_scored_candidates.parquet",index=False)
    physics_summary={"input":str(args.physics),"input_events":args.physics_input_events,
        "matched_postlambda_candidates":len(physics),
        "thresholds":{name:{"matched_candidates":int((physics.nn_score>=cut).sum()),
                              "event_efficiency":physics.loc[physics.nn_score>=cut,"event_entry"].nunique()/args.physics_input_events}
                      for name,cut in thresholds.items()}}
    plot_scores(frame,assignment,args.output_dir/"test_scores.png")
    plot_roc_compare(y[(test_sig|test_bg)],score[(test_sig|test_bg)],
                     bdt_score[(test_sig|test_bg)],args.output_dir/"test_roc_vs_bdt.png")
    plot_mass_angle(frame,assignment,thresholds["sig50"],
                    args.output_dir/"mass_angle_sculpting_sig50.png")
    result={"input":str(args.input),"manifest":str(args.manifest),
            "bdt_metrics":str(args.bdt_metrics),"variants":trained,
            "selected_variant":chosen["variant"],"feature_names":chosen["features"],
            "feature_group_permutation":importance,
            "selection_rule":"highest validation AUC; tie-break fewer validation Zbb at validation sig80",
            "split_counts":bdt["split_counts"],"zbb_source_split":bdt["zbb_source_split"],
            "test_auc":float(roc_auc_score(y[(test_sig|test_bg)],score[(test_sig|test_bg)])),
            "bdt_test_auc":bdt["test_auc"],
            "denominators":bdt["denominators"],"weights_per_candidate":weights,
            "baseline_peak_mc":bdt["baseline_peak_mc"],"thresholds":rows,
            "physics_check":physics_summary,
            "cautions":["No mass/angle/truth/ID inputs, but check saved sculpting and generated-angle efficiency.",
                        "Zero Zbb survivors gives a finite-MC count upper, not zero physical background.",
                        "Lambda_b share=1 is an upper production proxy; projected purity is not a confidence bound.",
                        "Local forced signal versus central Zbb sample-domain modeling may dominate closure variables."]}
    (args.output_dir/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# Dense NN after fitted-Λ preselection","",
           f"Selected `{chosen['variant']}` from validation only; {len(chosen['features'])} inputs, "
           f"test AUC {result['test_auc']:.5f} versus BDT {bdt['test_auc']:.5f}.","",
           "| Target | Score | Test signal | Test Zbb | Peak S / Zbb / Eta | Purity using B count upper* |",
           "|---|---:|---:|---:|---:|---:|"]
    for name,row in rows.items():
        c=row["counts"]
        lines.append(f"| {name} | {row['score_cut']:.4f} | {c['test_signal']} | {c['test_zbb']} | "
                     f"{c['peak_test_signal']} / {c['peak_test_zbb']} / {c['peak_eta']} | "
                     f"{100*row['peak_purity_with_conservative_zbb_count']:.3f}% |")
    lines += ["","* This is a scenario ratio using a Zbb count upper and an upper Λb production proxy; it is not a physical purity bound.",
              "The peak interval is 5.4–5.9 GeV for diagnostics; the fit range stays 4.9–6.3 GeV."]
    (args.output_dir/"metrics.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"selected_variant":chosen["variant"],"test_auc":result["test_auc"],
                      "bdt_test_auc":result["bdt_test_auc"],"sig80":rows["sig80"],
                      "physics_sig80":physics_summary["thresholds"]["sig80"]},indent=2))


if __name__=="__main__":main()
