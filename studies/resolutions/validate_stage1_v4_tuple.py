#!/usr/bin/env python3
"""Check v4 photon diagnostic vectors and counters in one Stage 1 ROOT file."""
import argparse,json
from pathlib import Path
import numpy as np
import awkward as ak
import uproot
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'analysis/studies'))
from photon_pointing_stage1 import BRANCHES

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 with uproot.open(args.input,handler=uproot.source.file.MemmapSource) as root:
  tree=root['events'];available=set(tree.keys());missing=set(BRANCHES)-available
  if missing:raise ValueError(f'missing v4 diagnostic branches: {sorted(missing)}')
  names=['n_lb','lb_mass','lb_truth_matched','lb_photon_index',*BRANCHES]
  totals={'output_events':int(tree.num_entries),'candidates':0,'direct_truth_candidates':0,'pointing_matches':0,'valid_truth_hits':0,'valid_reco_hits':0,'valid_pv':0}
  for block in tree.iterate(names,step_size=2000,library='ak'):
   n=ak.to_numpy(block.n_lb); totals['candidates']+=int(n.sum());totals['direct_truth_candidates']+=int(ak.sum(block.lb_truth_matched))
   for name in ['lb_mass','lb_truth_matched','lb_photon_index',*BRANCHES]:
    if not ak.all(ak.num(block[name])==block.n_lb):raise ValueError(f'bad candidate-vector length: {name}')
   status=ak.to_numpy(ak.flatten(block.lb_photon_pointing_match_status))
   th=ak.to_numpy(ak.flatten(block.lb_photon_pointing_truth_hit_region));rh=ak.to_numpy(ak.flatten(block.lb_photon_pointing_reco_hit_region));pv=ak.to_numpy(ak.flatten(block.lb_photon_pointing_pv_valid))
   totals['pointing_matches']+=int(np.sum(status==1));totals['valid_truth_hits']+=int(np.sum((status==1)&(th>0)));totals['valid_reco_hits']+=int(np.sum(rh>0));totals['valid_pv']+=int(np.sum(pv>0))
  totals['input_events_counter']=int(root['eventsProcessed'].value);totals['new_vector_branches']=len(BRANCHES);totals['complete_v4_validation']=True
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(totals,indent=2)+'\n');print(json.dumps(totals,indent=2))
if __name__=='__main__':main()
