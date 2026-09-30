#!/usr/bin/env python3
"""Build one auditable post-preselection table from independent source files.

The only additional reco cut is the configured fitted Lambda mass window.
Truth labels are attached after reconstruction, and all wrong combinations
remain in candidate_audit.parquet for diagnostics. The model feature table
contains neither Lambda_b mass/cos(theta_p) nor truth or event identifiers as
inputs. Zbb source_id comes from each separately reconstructed central file.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from prepare_training_inputs import annotate, feature_table, FEATURES


def read_annotated(path, sample, default_source):
    table = pq.read_table(path)
    if sample == "generic_zbb":
        if "source_id" not in table.column_names:
            raise ValueError(f"Zbb file lacks source_id: {path}; flatten with --source-id")
        source = np.unique(table["source_id"].to_numpy())
        if len(source) != 1:
            raise ValueError(f"Zbb file has {len(source)} source IDs: {path}")
        default_source = int(source[0])
    return annotate(table, sample, default_source), default_source


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--signal", type=Path, required=True)
    ap.add_argument("--eta", type=Path, required=True)
    ap.add_argument("--zbb", type=Path, nargs="+", required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--signal-input-events", type=int, required=True)
    ap.add_argument("--eta-input-events", type=int, required=True)
    ap.add_argument("--zbb-events-per-file", type=int, default=100000)
    ap.add_argument("--lambda-half-window", type=float, default=.010)
    ap.add_argument("--lambda-pdg", type=float, default=1.115683)
    ap.add_argument("--lb-mass-min", type=float, default=4.9)
    ap.add_argument("--lb-mass-max", type=float, default=6.3)
    args = ap.parse_args()
    if not 0 < args.lb_mass_min < args.lb_mass_max:
        raise ValueError("Invalid Lambda-gamma mass interval")
    if min(args.signal_input_events,args.eta_input_events,
           args.zbb_events_per_file) <= 0 or not 0 < args.lambda_half_window < .3:
        raise ValueError("Invalid event denominator or Lambda mass half-window")
    paths = [args.signal,args.eta,*args.zbb]
    if len(set(paths)) != len(paths):
        raise ValueError("Duplicate input file")
    rows = []
    inputs=[]
    seen_zbb_sources=set()
    for path,sample,source in [(args.signal,"signal_gamma",100),
                                (args.eta,"specific_eta",101)] + [
                                    (p,"generic_zbb",-1) for p in args.zbb]:
        table, source = read_annotated(path,sample,source)
        if sample == "generic_zbb":
            if source in seen_zbb_sources:
                raise ValueError(f"Repeated Zbb source_id {source}")
            seen_zbb_sources.add(source)
        inputs.append({"path":str(path),"sample":sample,"source_id":source,
                       "candidate_rows":table.num_rows,
                       "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        rows.append(table)
    if len(seen_zbb_sources) < 3:
        raise ValueError("Need >=3 independent Zbb files for train/validation/test")
    audit = pa.concat_tables(rows,promote_options="default")
    mass = audit["lambda_mass"].to_numpy().astype(float)
    lbmass = audit["lb_mass"].to_numpy().astype(float)
    valid = (np.isfinite(mass) & (np.abs(mass-args.lambda_pdg)<args.lambda_half_window)
             & np.isfinite(lbmass) & (args.lb_mass_min<=lbmass)
             & (lbmass<=args.lb_mass_max))
    selected=audit.filter(pa.array(valid))
    # Keep the complete audit as the unchanged stage-1 comparison.
    args.output_dir.mkdir(parents=True,exist_ok=True)
    pq.write_table(audit,args.output_dir/"candidate_audit_stage1.parquet",compression="zstd")
    pq.write_table(selected,args.output_dir/"candidate_audit_postlambda.parquet",compression="zstd")
    pq.write_table(feature_table(selected),args.output_dir/"training_inputs_postlambda.parquet",
                   compression="zstd")
    full_class_id = audit["class_id"].to_numpy()
    class_id = selected["class_id"].to_numpy()
    source = selected["source_id"].to_numpy()
    counts = {str(k):int(np.count_nonzero(class_id==k)) for k in (-1,0,1,2)}
    source_counts={str(k):int(np.count_nonzero((class_id==0)&(source==k)))
                   for k in sorted(seen_zbb_sources)}
    manifest={
        "inputs":inputs,
        "input_events":{"signal_gamma":args.signal_input_events,
                        "specific_eta":args.eta_input_events,
                        "generic_zbb":len(args.zbb)*args.zbb_events_per_file},
        "stage1_candidates":audit.num_rows,
        "stage1_class_counts":{str(k):int(np.count_nonzero(full_class_id==k))
                               for k in (-1,0,1,2)},
        "postlambda_candidates":selected.num_rows,
        "postlambda_class_counts":counts,"zbb_source_candidate_counts":source_counts,
        "postlambda_cut":f"{args.lb_mass_min}<=lb_mass<={args.lb_mass_max} and abs(lambda_mass-{args.lambda_pdg})<{args.lambda_half_window}",
        "lb_mass_range_gev":[args.lb_mass_min,args.lb_mass_max],
        "lambda_mass_half_window_gev":args.lambda_half_window,
        "lambda_pdg_gev":args.lambda_pdg,
        "features":list(FEATURES),
        "excluded_model_inputs":["lb_mass","m_LamGam","cos_theta_p","lb_sign",
                                 "truth and ancestry","source_id","event_entry",
                                 "candidate_slot","candidate multiplicity"],
        "training_purpose":"binary true PHSP Lambda-gamma versus generic Zbb; eta and wrong combinations are diagnostic only"
    }
    (args.output_dir/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({k:manifest[k] for k in ("stage1_candidates","postlambda_candidates",
                                            "postlambda_class_counts","zbb_source_candidate_counts")},indent=2))


if __name__=="__main__":
    main()
