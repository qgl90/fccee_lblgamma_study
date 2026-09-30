#!/usr/bin/env python3
"""Make an auditable candidate table and a truth-free ML feature table.

The signal and eta files are forced decays, so class counts have no physical
normalization. This script only prepares independent candidate rows and
event-grouped splits; it does not train a model or choose selection cuts.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

FEATURES = (
    "lambda_mass", "lb_pt", "lambda_vertex_chi2",
    "lambda_flight_rxy", "lambda_flight_rxy_sig", "proton_d0sig",
    "pion_d0sig", "lambda_d0", "lambda_d0_sig", "photon_reco_energy", "lambda_thrust_cos",
    "neutral_thrust_cos", "iso_R02", "iso_R03", "iso_R05",
    "iso_R03_noLambda", "iso_R05_noLambda", "iso_R03_noLambda_E",
    "iso_R05_noLambda_E", "iso_charged", "iso_neutral",
    "n_photons_DR03", "n_photons_DR05", "dm_gg_pi0",
    "E_gamma2", "dr_gg", "m_rec", "m_rec_all", "deltaE",
    "px_bal", "py_bal", "pz_bal", "deltaP", "cos_rec_sig",
    "Estar_gamma_rec", "E_same", "m_same",
    "roe_n_other", "roe_n_same", "lambda_pv_dca",
)
IDS = ("sample_id", "source_id", "event_entry", "candidate_slot",
       "candidates_in_event", "event_group", "split", "class_id",
       "class_name", "training_eligible", "candidate_weight")


def true_eta_chain(table):
    d = table.to_pydict()
    p = np.asarray(d["proton_mc_parent_index"])
    return ((p >= 0) & (p == np.asarray(d["pion_mc_parent_index"])) &
            (np.abs(np.asarray(d["proton_mc_parent_pdg"])) == 3122) &
            (np.asarray(d["mass_hypothesis_correct"]) == 1) &
            (np.abs(np.asarray(d["photon_mc_parent_pdg"])) == 221) &
            (np.asarray(d["proton_mc_grandparent_index"]) >= 0) &
            (np.asarray(d["proton_mc_grandparent_index"]) ==
             np.asarray(d["photon_mc_grandparent_index"])) &
            (np.abs(np.asarray(d["proton_mc_grandparent_pdg"])) == 5122))


def stable_split(group):
    value = int.from_bytes(hashlib.sha256(group.encode()).digest()[:8], "big") % 100
    return "train" if value < 70 else "validation" if value < 85 else "test"


def annotate(table, sample_id, default_source_id):
    n = table.num_rows
    d = table.to_pydict()
    source = np.asarray(d.get("source_id", [default_source_id] * n))
    event = np.asarray(d["event_entry"])
    slot = np.asarray(d["candidate_slot"])
    groups = [f"{sample_id}:{int(s)}:{int(e)}" for s,e in zip(source,event)]
    if len(set(zip(groups,slot))) != n:
        raise ValueError(f"Duplicate candidate keys in {sample_id}")
    if sample_id == "signal_gamma":
        matched = np.asarray(d["truth_matched"]) == 1
        class_id = np.where(matched,1,-1)
    elif sample_id == "specific_eta":
        class_id = np.where(true_eta_chain(table),2,-1)
    else:
        # A rare true signal in inclusive Zbb must not be labelled background.
        class_id = np.where(np.asarray(d["truth_matched"]) == 1,-1,0)
    class_names={-1:"diagnostic_other",0:"generic_zbb",1:"signal_gamma",2:"specific_eta"}
    extra={
        "sample_id": [sample_id]*n,
        "source_id": source.astype(np.int32),
        "event_group": groups,
        "split": [stable_split(g) for g in groups],
        "class_id": class_id.astype(np.int8),
        "class_name": [class_names[int(x)] for x in class_id],
        "training_eligible": class_id>=0,
        "candidate_weight": np.ones(n,dtype=np.float32),
    }
    if "source_id" in table.column_names:
        extra.pop("source_id")
    for key,value in extra.items():
        table=table.append_column(key,pa.array(value))
    return table


def feature_table(audit):
    columns={key:audit[key] for key in IDS}
    for name in FEATURES:
        if name not in audit.column_names:
            raise KeyError(f"Missing feature {name}")
        data=audit[name].to_numpy()
        if name in ("n_photons_DR03","n_photons_DR05","roe_n_other","roe_n_same"):
            columns[name]=audit[name]
        else:
            # Distinguish unavailable geometry/partner values from valid zero.
            invalid=~np.isfinite(data) | (data<=-998.)
            columns[name]=pa.array(data,mask=invalid)
            if np.any(invalid):
                columns[f"has_{name}"]=pa.array(~invalid)
    return pa.table(columns)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal",type=Path,required=True)
    parser.add_argument("--eta",type=Path,required=True)
    parser.add_argument("--zbb",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--signal-input-events",type=int)
    parser.add_argument("--eta-input-events",type=int)
    parser.add_argument("--zbb-input-events",type=int)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    inputs={"signal_gamma":args.signal,"specific_eta":args.eta,
            "generic_zbb":args.zbb}
    input_events={"signal_gamma":args.signal_input_events,
                  "specific_eta":args.eta_input_events,
                  "generic_zbb":args.zbb_input_events}
    for sample_id,count in input_events.items():
        if count is not None and count<=0:
            raise ValueError(f"Invalid input-event count for {sample_id}")
    annotated=[]
    for sample_id,path in inputs.items():
        table=pq.read_table(path)
        annotated.append(annotate(table,sample_id,0))
    audit=pa.concat_tables(annotated,promote_options="default")
    pq.write_table(audit,args.output_dir/"candidate_audit.parquet",compression="zstd")
    training=feature_table(audit)
    pq.write_table(training,args.output_dir/"training_inputs.parquet",compression="zstd")
    labels=audit["class_id"].to_numpy()
    splits=np.asarray(audit["split"].to_pylist())
    feature_missing={name:round(training[name].null_count/training.num_rows,6)
                     for name in FEATURES}
    groups=audit["event_group"].to_pylist()
    group_splits={}
    for group,split in zip(groups,splits):
        previous=group_splits.setdefault(group,split)
        if previous!=split:
            raise ValueError(f"Event group {group} leaks across splits")
    summary={
        "inputs":{k:str(v) for k,v in inputs.items()},
        "input_events":input_events,
        "configuration_sha256":{
            str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in
            (Path(__file__).resolve().parents[2]/"config"/"lb_reco.json",
             Path(__file__).resolve().parents[2]/"config"/"lb_observables.json")},
        "candidate_rows":audit.num_rows,
        "class_counts":{str(k):int(np.count_nonzero(labels==k)) for k in (-1,0,1,2)},
        "split_counts":{k:int(np.count_nonzero(splits==k))
                        for k in ("train","validation","test")},
        "event_groups":len(set(audit["event_group"].to_pylist())),
        "features":list(FEATURES),
        "feature_missing_fraction":feature_missing,
        "excluded_from_features":["MC truth/ancestry","lb_mass", "m_LamGam",
                                  "cos_theta_p","Estar_gamma", "source_id",
                                  "event_entry","candidate_slot","lb_sign",
                                  "dca_Lam_gamma", "Lxyz_implied",
                                  "cos_dir_implied", "lambda_pv_cos"],
        "normalization":"unit candidate weights only; forced samples and generic Zbb are not physical yield-normalized",
        "audit_output":str(args.output_dir/"candidate_audit.parquet"),
        "training_output":str(args.output_dir/"training_inputs.parquet"),
    }
    (args.output_dir/"manifest.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
