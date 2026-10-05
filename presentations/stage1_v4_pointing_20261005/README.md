# v4 pointing and Stage 1 reprocessing deck

Build with `bash build.sh`. The PDF contains four slides on the saved v4 photon
information, six offline angular smearing points, the paired 200-event signal
check, Zbb/Zcc/Zss Condor preparation, and the available 100k forced modes.

The slide figure is copied from
`docs/figures/stage1_v4_pointing_validation.png` (SHA-256 recorded below).
The frozen data and the paired Stage 1 commands are documented in
`docs/data/stage1_v4_pointing_validation/manifest.json` and
`docs/STAGE1_V4_POINTING_REVIEW_2026-10-05.md`. Condor check-only and forced
sample inventory logs are frozen under
`docs/data/stage1_v4_pointing_jobs_20261005/`.

SHA-256 source record:

```text
35f3b15c6678911509da067c3ba88506fe6ea797ceda3bed3f10b53b529fcec4  presentations/stage1_v4_pointing_20261005/stage1_v4_pointing_20261005.tex
ec4bbd0495a45685bac6973e1ef4c03941e08dd4b89f73b2176b8f8419b7e902  presentations/stage1_v4_pointing_20261005/build.sh
68d2f961029432ca257cd800f34ceeaa246eebdab3f9258051917c1603a67599  presentations/stage1_v4_pointing_20261005/figures/stage1_v4_pointing_validation.png
68d2f961029432ca257cd800f34ceeaa246eebdab3f9258051917c1603a67599  docs/figures/stage1_v4_pointing_validation.png
39279d35b3638b04c971b9837cf536712d4c0e9e4c605dc9d4ca89c18afacf84  docs/data/stage1_v4_pointing_validation/validation.json
150e2744f390a70b0b25d40cb1b68bc417c8af33eff93b09142093d461db4e65  docs/data/stage1_v4_pointing_jobs_20261005/condor_check_only.log
495746bb0c57366c7326f7c530b512c5eb83b976d3999ab81d0046bca2121aa1  docs/data/stage1_v4_pointing_jobs_20261005/forced_100k_inventory.log
d12de046f6ac1c32eff4fe2bd3ce7cd05606cb71c6b2106c06e3aa6ca5939e3a  analysis/studies/analysis_preselection_v4.py
ab84f63cb65d96aa6aa03b831233f731a5c0f7fb71127ecd2983167ad8426635  analysis/studies/photon_pointing_v4.h
daa55f9e67c8275375129e289b9d5a79992552a79c1a3e8348e2519618bee5c9  scripts/submit_stage1_v4_zflavours.sh
4de04101d0cb39d5e7d2b0662cbeec5101a36b51a548c8e847e2dacbc4dd88fe  scripts/run_stage1_v4_forced_100k.sh
```
