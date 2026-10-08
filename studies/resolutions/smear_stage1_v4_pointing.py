#!/usr/bin/env python3
"""Stream a prepared/scored v4 Parquet table into offline pointing hypotheses.

No candidate is removed. Invalid synthetic measurements remain NaN with a flag.
The namespace must identify the frozen Stage1 catalog, not an individual shard.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from photon_pointing import smear_direction, photon_impact_parameters

PREFIX = "lb_photon_pointing_"
SIGMAS = (0.5, 0.7, 0.9, 1.1, 1.3, 1.5)


def augment(table, namespace, anchor="truth", seed=20261005):
    def col(name):
        return table[name].to_numpy()
    def vector(names):
        return np.column_stack([col(PREFIX+n) for n in names])
    truth = vector(["truth_px", "truth_py", "truth_pz"])
    hit = vector([f"{anchor}_hit_{x}" for x in "xyz"])
    pv = vector([f"pv_{x}" for x in "xyz"])
    # Keyed draws make chunk order, row order, and batch size irrelevant.
    cache = {}
    draws = []
    for source, event, photon in zip(col("source_id"), col("event_entry"), col("photon_reco_index")):
        key = f"{namespace}:{int(source)}:{int(event)}:{int(photon)}:{seed}"
        if key not in cache:
            entropy = int.from_bytes(hashlib.sha256(key.encode()).digest()[:16], "little")
            cache[key] = np.random.default_rng(entropy).normal(size=2)
        draws.append(cache[key])
    draws = np.asarray(draws).reshape(-1, 2)
    valid = ((col(PREFIX+"match_status")==1) &
             (col(PREFIX+anchor+"_hit_region")>0) &
             (col(PREFIX+"pv_valid")==1) &
             np.isfinite(truth).all(axis=1) & (np.linalg.norm(truth,axis=1)>0) &
             np.isfinite(hit).all(axis=1) & np.isfinite(pv).all(axis=1))
    table = table.append_column("pointing_valid", pa.array(valid))
    for sigma in SIGMAS:
        direction = smear_direction(truth, sigma*1e-3, draws)
        ip3d, ipxy = photon_impact_parameters(hit, direction, pv)
        tag = str(sigma).replace(".", "p")
        for name, value in (("ip3d_mm", ip3d), ("d0_abs_mm", ipxy)):
            table = table.append_column(f"photon_{name}_{tag}mrad", pa.array(np.where(valid,value,np.nan)))
        for i, axis in enumerate("xyz"):
            value = col("lb_photon_energy") * direction[:,i]
            table = table.append_column(f"photon_p{axis}_{tag}mrad", pa.array(np.where(valid,value,np.nan)))
    return table


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--namespace", required=True, help="Unique frozen catalog/production ID, shared by its shards")
    ap.add_argument("--anchor", choices=("truth","reco"), default="truth")
    ap.add_argument("--seed", type=int, default=20261005)
    args=ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    scenario={"namespace":args.namespace,"anchor":args.anchor,"seed":args.seed,"sigma_mrad_per_component":SIGMAS,"input":str(args.input.resolve()),"geometry":"stored v4 effective IDEA surface","position_response":"ideal truth hit" if args.anchor=="truth" else "inherited reconstructed direction"}
    reader=pq.ParquetFile(args.input)
    writer=None
    rows=valid=0
    try:
        for batch in reader.iter_batches(batch_size=50000):
            table=augment(pa.Table.from_batches([batch]),args.namespace,args.anchor,args.seed)
            if writer is None:
                metadata=dict(table.schema.metadata or {})
                metadata[b"pointing_scenario"]=json.dumps(scenario).encode()
                writer=pq.ParquetWriter(args.output,table.schema.with_metadata(metadata))
            writer.write_table(table)
            rows+=len(table); valid+=int(table["pointing_valid"].to_numpy().sum())
    finally:
        if writer: writer.close()
    if writer is None:
        empty=augment(pa.Table.from_batches([],schema=reader.schema_arrow),args.namespace,args.anchor,args.seed)
        metadata=dict(empty.schema.metadata or {})
        metadata[b"pointing_scenario"]=json.dumps(scenario).encode()
        pq.write_table(empty.replace_schema_metadata(metadata),args.output)
    print(json.dumps({"rows":rows,"valid":valid,"unresolved":rows-valid,"output":str(args.output)}))

if __name__=="__main__":
    main()
