#!/usr/bin/env python3
"""Estimate inclusive Zbb events needed to bound target post-BDT purity.

Uses the observed post-Lambda preselection rate and specified signal retention.
For zero test-background survivors, 3/N is the approximate 95% Poisson upper
bound on the survivor fraction. This is a planning estimate, not a sensitivity.
"""

import argparse
import json
import math
from pathlib import Path


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest",type=Path,required=True,
                    help="prepare_bdt_dataset.py manifest with post-Lambda counts")
    ap.add_argument("--yield-config",type=Path,default=Path("config/yield_projection.json"))
    ap.add_argument("--signal-relative-efficiency",type=float,default=.8)
    ap.add_argument("--test-fraction",type=float,default=.2)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if not 0<args.signal_relative_efficiency<=1 or not 0<args.test_fraction<=1:
        raise ValueError("Fractions must lie in (0,1]")
    manifest=json.loads(args.manifest.read_text())
    config=json.loads(args.yield_config.read_text())
    n_zbb=config['n_z']*config['br_z_to_bb']
    n_lb=2*n_zbb*config['f_b_baryon_per_b_at_z']*config['lambda_b_share_of_b_baryons']
    sig_rate=(manifest['postlambda_class_counts']['1']/manifest['input_events']['signal_gamma'])
    bg_rate=(manifest['postlambda_class_counts']['0']/manifest['input_events']['generic_zbb'])
    expected_signal=(n_lb*config['br_lb_to_lambda_gamma']*config['br_lambda_to_p_pi']*
                     sig_rate*args.signal_relative_efficiency)
    expected_background=n_zbb*bg_rate
    rows=[]
    for purity in (.1,.5,.9):
        allowed_background=expected_signal*(1-purity)/purity
        allowed_eff=allowed_background/expected_background
        postlambda_test=math.ceil(3/allowed_eff)
        zbb_test=math.ceil(postlambda_test/bg_rate)
        zbb_total=math.ceil(zbb_test/args.test_fraction)
        rows.append({'target_purity':purity,
                     'maximum_zbb_bdt_efficiency':allowed_eff,
                     'minimum_rejection_factor':1/allowed_eff,
                     'postlambda_test_candidates_for_zero_survivor_95pct':postlambda_test,
                     'zbb_test_events_needed':zbb_test,
                     'total_zbb_events_at_test_fraction':zbb_total})
    result={'manifest':str(args.manifest),'yield_config':str(args.yield_config),
            'signal_relative_efficiency':args.signal_relative_efficiency,
            'test_fraction':args.test_fraction,
            'postlambda_signal_rate_per_generated_forced_event':sig_rate,
            'postlambda_zbb_candidates_per_generated_event':bg_rate,
            'expected_signal_after_bdt':expected_signal,
            'expected_postlambda_zbb':expected_background,
            'planning_rows':rows,
            'assumption':'zero BDT survivors in independent test; 95% Poisson upper is about 3 events; Lambda_b share=1 is an upper proxy'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
