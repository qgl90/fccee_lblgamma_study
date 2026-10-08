#!/usr/bin/env python3
"""Paired ROOT validation plus Stage2 retention and keyed-smearing checks."""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import awkward as ak
import numpy as np
import pyarrow.parquet as pq
import uproot
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'studies/reconstruction'))
sys.path.insert(0,str(ROOT/'analysis/studies'))
from prepare_offline_bdt import process_file
from photon_pointing_stage1 import BRANCHES
from smear_stage1_v4_pointing import augment

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--baseline',type=Path,required=True)
 ap.add_argument('--v4',type=Path,required=True)
 ap.add_argument('--output-dir',type=Path,required=True)
 ap.add_argument('--model-dir',type=Path)
 args=ap.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
 with uproot.open(args.baseline,handler=uproot.source.file.MemmapSource) as f0, uproot.open(args.v4,handler=uproot.source.file.MemmapSource) as f1:
  a=f0['events'].arrays(library='ak'); b=f1['events'].arrays(library='ak')
  assert int(f0['eventsProcessed'].value)==int(f1['eventsProcessed'].value)
  for name in a.fields:
   x=ak.to_numpy(ak.flatten(a[name],axis=None));y=ak.to_numpy(ak.flatten(b[name],axis=None))
   assert np.array_equal(x,y,equal_nan=True),name
  for name in BRANCHES:
   assert ak.all(ak.num(b[name])==b.n_lb),name
  def col(s):return ak.to_numpy(ak.flatten(b['lb_photon_pointing_'+s]))
  def vec(names):return np.column_stack([col(s) for s in names])
  valid=col('truth_hit_region')>0
  p=vec(['truth_px','truth_py','truth_pz']);v=vec(['truth_vx','truth_vy','truth_vz'])
  h=vec(['truth_hit_x','truth_hit_y','truth_hit_z'])
  n=p/np.linalg.norm(p,axis=1)[:,None]
  closure=np.linalg.norm(h-v-col('truth_hit_path')[:,None]*n,axis=1)
  assert np.all(closure[valid]<1e-8)
  region=col('truth_hit_region')
  assert np.allclose(np.linalg.norm(h[region==1,:2],axis=1),2250)
  assert np.allclose(abs(h[region==2,2]),2500)
  matched=int(ak.sum(b.lb_truth_matched))
  report={'input_events':int(f1['eventsProcessed'].value),'output_events':len(b),'candidates':int(ak.sum(b.n_lb)),'direct_candidates':matched,'wrong_candidates':int(ak.sum(b.n_lb))-matched,'unchanged_baseline_branches':len(a.fields),'new_branches':len(BRANCHES),'matched_photons':int(sum(col('match_status')==1)),'valid_truth_hits':int(sum(valid)),'max_ray_closure_mm':float(np.max(closure[valid]))}
 cfg=json.loads((ROOT/'config/lb_offline_selections.json').read_text())
 scan=defaultdict(lambda:defaultdict(lambda:defaultdict(Counter)))
 report['stage2']=process_file(args.v4,'signal',-1,cfg,cfg['default_prebdt_scenario'],args.output_dir,None,scan)
 for kind in ('audit','selected'):
  t=pq.read_table(args.output_dir/f'signal_-1_{kind}.parquet')
  assert all(k in t.column_names for k in BRANCHES)
  u=augment(t,'v4_validation')
  rev=np.arange(len(t)-1,-1,-1)
  w=augment(t.take(rev),'v4_validation').take(rev)
  for name in u.column_names[len(t.column_names):]:
   assert np.array_equal(u[name].to_numpy(),w[name].to_numpy(),equal_nan=True),name
  pq.write_table(u,args.output_dir/f'signal_{kind}_pointing_v4.parquet')
  report[kind+'_rows']=len(t)
 if args.model_dir:
  import train_offline_bdt as training
  from xgboost import XGBClassifier
  info=json.loads((args.model_dir/'training_summary.json').read_text())
  assert info['scenario']==cfg['default_prebdt_scenario']
  training.FEATURES=info['features']
  assert not any('pointing' in f or 'truth' in f for f in training.FEATURES)
  model=XGBClassifier(n_jobs=1); model.load_model(args.model_dir/'bdt_model.json')
  training.score_files(model,[args.output_dir/'signal_-1_selected.parquet'],args.output_dir/'scored')
  t=pq.read_table(args.output_dir/'scored/signal_-1_selected.parquet')
  assert all(k in t.column_names for k in BRANCHES)
  post=t.filter(t['bdt_score'].to_numpy()>=0.9855620861)
  u=augment(post,'v4_validation')
  pq.write_table(u,args.output_dir/'signal_post_bdt_pointing_v4.parquet')
  report['post_bdt_rows']=len(post)
  report['validation_bdt_cut']=0.9855620861
  report['model_sha256']=hashlib.sha256((args.model_dir/'bdt_model.json').read_bytes()).hexdigest()
 report['repository_base']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 report['fccanalyses_revision']=subprocess.check_output(['git','-C','external/FCCAnalyses','rev-parse','HEAD'],text=True).strip()
 report['files_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.baseline,args.v4,ROOT/'config/lb_reco_preselection_15mev_45_65_3d.json',ROOT/'config/lb_observables.json',ROOT/'analysis/studies/photon_pointing_v4.h']}
 report['baseline']=str(args.baseline);report['v4']=str(args.v4)
 (args.output_dir/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='stage2'},indent=2))
if __name__=='__main__':main()
