#!/usr/bin/env python3
"""Plot the bounded v4 validation; conditional pilot shapes, no yield claim."""
import argparse
from pathlib import Path
import sys
import numpy as np
import pyarrow.parquet as pq
import matplotlib
matplotlib.use('Agg')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reconstruction'))
import v3_plot_style
import matplotlib.pyplot as plt
from smear_stage1_v4_pointing import augment
from photon_pointing import photon_impact_parameters

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--input',type=Path,required=True)
 ap.add_argument('--output',type=Path,required=True)
 args=ap.parse_args();t=pq.read_table(args.input)
 t=t.filter(t['truth_matched'].to_numpy()==1)
 prefix='lb_photon_pointing_'
 def vec(names):return np.column_stack([t[prefix+n].to_numpy() for n in names])
 true_ip,_=photon_impact_parameters(vec(['truth_vx','truth_vy','truth_vz']),vec(['truth_px','truth_py','truth_pz']),vec(['pv_x','pv_y','pv_z']))
 fig,axes=plt.subplots(1,2,figsize=(11,4.5))
 for ax,anchor,limit in zip(axes,('truth','reco'),(15,100)):
  u=augment(t,'v4_validation',anchor)
  bins=np.linspace(0,limit,31)
  ax.hist(true_ip,bins=bins,histtype='step',label='True photon line / reconstructed PV',color='black')
  for sigma in ('0p5','1p5'):
   values=u[f'photon_ip3d_mm_{sigma}mrad'].to_numpy()
   ax.hist(values,bins=bins,histtype='step',label=f'{sigma.replace("p", ".")} mrad/component')
  ax.set(xlabel='Photon IP$_{3D}$ [mm]',ylabel='Candidates / bin',title=f'{anchor.capitalize()} hit anchor')
  ax.legend(fontsize=9)
 fig.suptitle(f'v4 validation: {len(t)} direct candidates after Stage 1\nFirst 200 signal events; distributions conditional on reconstruction',fontsize=12)
 fig.tight_layout();args.output.parent.mkdir(parents=True,exist_ok=True)
 fig.savefig(args.output,dpi=170)
if __name__=='__main__':main()
