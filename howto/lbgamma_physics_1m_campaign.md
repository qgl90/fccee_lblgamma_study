# Four 1M forced-decay samples through v5 Stage 1

The campaign in `config/lbgamma_v5_forced_modes_1m_campaign.yaml` produces
four distinct samples, each as one hundred 10k EDM4hep chunks (4M generated events
total):

| Sample | Scenario | Seed range |
|---|---|---:|
| `Lb2LambdaGamma` | PHSP Λb→Λγ | 72701–72800 |
| `Lb2LambdaGammaPhysics` | HELAMP Physics Λb→Λγ | 72601–72700 |
| `Lb2LambdaEtaPhysics` | HELAMP Physics Λb→Λη(γγ) | 72801–72900 |
| `Lb2LambdaPi0Physics` | HELAMP Physics Λb→Λπ⁰(γγ) | 72901–73000 |

The η and π⁰ HELAMP modes have separate 200-event generation audits in
`docs/STAGE0_PSEUDOSCALAR_MODELS_REVIEW_2026-10-02.md`. The gamma decay
files, Pythia card and IDEA response are unchanged from their named samples.
Forced decays are conditional MC samples, not physical Z→bb yields.

## Check and produce Stage 0 chunks

Run from the repository root on a CERN host with the generation stack and EOS
mounted. Stage 0 chunks share a directory but have sample-specific names:

`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage0_v5_forced_modes_1m_20261006/chunks/`

Select all four modes and all 100 chunks:

```bash
SAMPLES=Lb2LambdaGamma,Lb2LambdaGammaPhysics,Lb2LambdaEtaPhysics,Lb2LambdaPi0Physics
CHUNKS=$(seq -s, 0 99)

scripts/run_lbgamma_physics_1m.sh stage0 --check \
  --samples "$SAMPLES" --chunks "$CHUNKS"
```

Produce locally with four concurrent jobs:

```bash
scripts/run_lbgamma_physics_1m.sh stage0 --run --executor local --jobs 4 \
  --samples "$SAMPLES" --chunks "$CHUNKS" --events-per-chunk 10000
```

Or submit the same 400 chunks to Condor:

```bash
scripts/run_lbgamma_physics_1m.sh stage0 --run --executor condor \
  --samples "$SAMPLES" --chunks "$CHUNKS" --events-per-chunk 10000
```

This writes one row per missing chunk to
`work/condor/lbgamma_v5_forced_modes_1m.queue` and submits it with
`scripts/stage0_condor.sub`. The worker runs the same
`scripts/produce_chunk.sh` used locally and writes each validated chunk
directly to the EOS directory above. The submit description sets
`LB_DELPHES_OUTPUT_DIR` and `LB_PRODUCTION_LOG_DIR` explicitly, so the output
destination does not depend on an environment variable forwarded by the
submitting shell. Condor logs go to
`outputs/logs/condor/`; per-chunk generation provenance logs go to
`outputs/logs/`. Complete chunks are omitted from the queue. Existing partial
files are also omitted so an active or interrupted local job is not overwritten;
inspect those before deciding whether to resume or regenerate them.

The submit description assumes the repository is visible at
`/afs/cern.ch/work/r/rquaglia/fcc_ee/fccee_lblgamma_study` on execute nodes,
and that workers can access the configured Key4hep stack and the EOS mount.
The batch flavor is `longlunch` (2 hours) with accounting group
`group_u_FCC.local_gen`.
Inspect the generated queue before submission. Do not submit while the local
campaign is still generating the same chunks.

Each chunk is checked for its exact 10k `events` count and logged provenance.
The Stage 0 jobs write directly into the campaign EOS folder; no merge is
needed for the chunked Stage 1 handoff. To produce only the requested new
background modes, set `SAMPLES=Lb2LambdaEtaPhysics,Lb2LambdaPi0Physics`.

## Hand chunks to v5 Stage 1

After Stage 0 completes, check all selected files:

```bash
scripts/run_lbgamma_physics_1m.sh stage1 --check \
  --samples "$SAMPLES" --chunks "$CHUNKS"
```

Run v5 Stage 1 locally or queue all selected file-level jobs on Condor:

```bash
scripts/run_lbgamma_physics_1m.sh stage1 --run --executor condor \
  --samples "$SAMPLES" --chunks "$CHUNKS"
```

Condor mode writes one queue with one 10k input chunk per job, then submits
that queue as a single cluster using `scripts/stage1_v5_condor.sub`. The worker
runs `analysis_preselection_v5.py`, the same v5 analysis wrapper used for the
inclusive Z samples. This avoids issuing one `condor_submit` call per input
file while retaining one output tuple per input chunk. Stage 1 output uses
`/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/stage1_v5_forced_modes_1m_20261006/`.
The generalized process list runs each selected input chunk with the same v5
candidate builder, pointing diagnostics, truth labels and Weaver inference.
No pointing hypothesis or tag-score cut is applied. Set
`LB_STAGE1_OUTPUT_EOS` to choose another EOS destination.

Each sample has independent chunk IDs and a distinct event basename. Keep its
Stage 0 event counts, seed list, decay/card hashes, Stage 1 job directory and
per-chunk candidate counts in the campaign manifest. Validate direct signal,
wrong combinations and η/π⁰ feed-down separately; the forced sample counts do
not set physical background normalizations.
