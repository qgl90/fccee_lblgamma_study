# Stage 1 v4 job preparation — 2026-10-05

The native Condor entry passed `--check-only` for all three inclusive flavours.
The requested `group_u_FCC.local_gen` is configured as `--comp-group` (the
accounting group). `--queue` remains the job flavour, set to `workday`.

| Flavour | Files found | Chunks | CPUs/job | Output destination |
|---|---:|---:|---:|---|
| Zbb | 4,398 | 1,200 | 4 | `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zbb_full_condor/stage1_v4_pointing_20261005` |
| Zcc | 5,018 | 1,200 | 4 | `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zcc_full_condor/stage1_v4_pointing_20261005` |
| Zss | 5,015 | 1,200 | 4 | `/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/zss_full_condor/stage1_v4_pointing_20261005` |

FCCAnalyses reported each full input glob and destination. The complete log is
[frozen here](data/stage1_v4_pointing_jobs_20261005/condor_check_only.log).
The prepared script checks only by default. Submission requires explicit
`scripts/submit_stage1_v4_zflavours.sh --submit`; that command was not run.

The 100k merged input inventory has five existing files: Lambda gamma PHSP
(685,136,941 bytes), Lambda gamma HELAMP (686,453,206 bytes), Lambda eta PHSP
(693,381,547 bytes), Lambda eta HELAMP (693,440,232 bytes), and Lambda pi0
HELAMP (694,190,756 bytes). The configured Lambda pi0 PHSP merged file is
missing at the checked repository and EOS paths. Its config has ten 10k chunks
with seed base 72001. The precise inventory is
[frozen here](data/stage1_v4_pointing_jobs_20261005/forced_100k_inventory.log).
The rerunner defaults to `--check-only`; `--run` processes up to four samples
concurrently with eight CPUs each (32 total by default), logs each sample,
and writes a candidate-vector validation JSON beside each v4 ROOT output.

## PI presentation

The [four-slide Beamer PDF](../presentations/stage1_v4_pointing_20261005/stage1_v4_pointing_20261005.pdf)
shows the v4 stored fields and offline smear calculation, paired 200-event
signal comparison, prepared Condor jobs, and 100k mode inventory. Its source,
build script, figure, and source hashes are in the presentation directory.
