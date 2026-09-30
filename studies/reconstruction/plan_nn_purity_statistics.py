#!/usr/bin/env python3
"""Independent Zbb events needed to bound a peak-purity scenario if zero survive.

The signal projection uses the editable Lambda_b production upper proxy.
This is a data-volume plan, not a measured purity or expected survivor rate.
"""

import argparse
import json
import math
from pathlib import Path

from scipy.stats import chi2


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metrics",type=Path,required=True)
    ap.add_argument("--yield-config",type=Path,default=Path("config/yield_projection.json"))
    ap.add_argument("--campaign-manifest",type=Path)
    ap.add_argument("--threshold",default="sig80")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    metrics=json.loads(args.metrics.read_text())
    config=json.loads(args.yield_config.read_text())
    row=metrics["thresholds"][args.threshold]
    sig=row["peak_expected"]["signal"]
    eta=row["peak_expected"]["eta"]
    n_zbb=config["n_z"]*config["br_z_to_bb"]
    zero_upper=float(chi2.ppf(.95,2)/2)
    campaign=None
    if args.campaign_manifest:
        campaign=json.loads(args.campaign_manifest.read_text())["campaign_metadata"]["numberOfEvents"]
    table=[]
    for purity in (.1,.5,.9):
        allowed=sig*(1-purity)/purity-eta
        if allowed<=0:
            needed=None
        else:
            needed=math.floor(zero_upper*n_zbb/allowed)+1
        table.append({"target_purity":purity,"allowed_zbb_expected_candidates":allowed,
                      "independent_zbb_events_needed_if_zero_survivors":needed,
                      "additional_over_current_test":max(0,needed-metrics["denominators"]["test_zbb_generated_events"]) if needed else None,
                      "within_campaign_count":needed<=campaign if needed and campaign else None})
    result={"metrics":str(args.metrics),"threshold":args.threshold,
            "signal_expected_upper_proxy":sig,"eta_expected":eta,
            "n_zbb_projected":n_zbb,"zero_mc_onesided95_count_upper":zero_upper,
            "current_independent_test_events":metrics["denominators"]["test_zbb_generated_events"],
            "campaign_generated_zbb_events":campaign,"rows":table,
            "warning":"The Lambda_b share=1 production proxy is optimistic; if any Zbb survive, more MC may be needed. This is not a physical purity confidence interval."}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
