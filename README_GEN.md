# Running local production

Run these commands from the repository root in a shell where Key4hep has **not** already been sourced. There is one `Snakefile`; its default target produces both samples as ten independently seeded 50,000-event chunks per sample, then merges each set into a 500,000-event EDM4hep file. Seeds and decay files are in `config/config.yaml`.

For a concise map of the full analysis stages, including Condor reconstruction
and the separate detector-response studies, see
[`docs/REPOSITORY_GUIDE.md`](docs/REPOSITORY_GUIDE.md).

## Option A: Snakemake

First check the setup and build the pinned local FCCAnalyses source:

```bash
bash scripts/fetch_local_inputs.sh
bash scripts/check_environment.sh
bash scripts/build_fccanalyses.sh 4
```

Then preview and run both production jobs:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 20 --dry-run --printshellcmds
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 20
```

To request only one sample, replace the default target with its full output path:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 10 \
  outputs/delphes/Lb2LambdaGamma_nev500000_IDEA_edm4hep.root
```

The earlier 50,000-event outputs remain available under their existing names. To confirm that the completed files are current by input modification time, use `--rerun-triggers mtime`:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake --snakefile Snakefile --cores 20 \
  --dry-run --rerun-triggers mtime
```

Snakemake's default provenance triggers can schedule a rerun if its stored code
or parameter record differs, even when the completed ROOT inputs have not
changed. Inspect the dry run before starting another million events. To see
the command for one chunk without executing it, force that chunk in a dry run:

```bash
env -u PYTHONPATH -u PYTHONHOME XDG_CACHE_HOME="$PWD/.snakemake/cache" \
  myenv/bin/python -m snakemake \
  outputs/delphes/chunks/Lb2LambdaGamma_nev500000_chunk0_IDEA_edm4hep.root \
  --snakefile Snakefile --cores 1 --dry-run --printshellcmds \
  --forcerun delphes_chunk --rerun-triggers mtime
```

If `myenv/bin/python` is unavailable, substitute a Python interpreter with Snakemake installed. Do not source the generation Key4hep stack in the Snakemake parent shell; each job does so itself.

## Option B: direct Bash scripts

The scripts contain the Pythia card preparation, exact Delphes command, EvtGen decay file, stack setup, ROOT entry count check, and merge in plain Bash. Run the same chunked production from a clean shell:

```bash
bash scripts/produce_500k_chunked.sh 20
```

The argument is the maximum number of parallel chunk jobs. `produce_chunk.sh` takes sample, chunk index, seed, chunk event count, and total event count explicitly; `merge_chunks.sh` validates and merges the ten outputs. The earlier single-file scripts remain available for a quick independent check with a different event count:

```bash
bash scripts/produce_chunk.sh Lb2LambdaGamma 0 22345 50000 500000
bash scripts/merge_chunks.sh Lb2LambdaGamma 500000 10  # after all ten chunks exist
```

For the earlier single-file scripts, a small check is:

```bash
bash scripts/produce_Lb2LambdaGamma.sh 5
bash scripts/produce_Lb2LambdaEta.sh 5
```

The Bash scripts check the entry count and leave existing final outputs unchanged. For new outputs, they write first to a `.partial.root` file, check the `events` count, then rename it to the final `.root` path. If a job fails, the partial file and log remain for inspection. Each log is under `outputs/logs/`; for example:

```bash
tail -f outputs/logs/Lb2LambdaGamma_nev500000_chunk0.production.log
```

Both methods use the same local cards, seed ranges (22345–22354 for Λγ and 22355–22364 for Λη), decays, stack, and output naming. These seeds differ from the earlier 50,000-event seeds so the new samples are statistically distinct. Snakemake tracks dependencies and schedules missing targets; the Bash scripts expose each step for inspection and verify existing outputs before reusing them.

## The three 100,000-event preselection samples

The development/preselection samples are a separate named configuration and
do not change the default 500,000-event target. They are PHSP Λγ, the
HELAMP/polarization Λγ model, and Λη→γγ; each is divided into ten 10,000-event
chunks. Run locally using the targets in the repository guide, or prepare and
submit the same 30 chunks to Condor:

```bash
scripts/submit_forced_samples_100k_condor.sh --help
scripts/submit_forced_samples_100k_condor.sh --dry-run
scripts/submit_forced_samples_100k_condor.sh
```

Edit `REPO_DIR` in `scripts/condor_forced_samples_100k.sub` for the shared
worker-visible checkout before submitting. The queue is generated from
`config/config.yaml`. After jobs finish, merge with
`bash scripts/merge_chunks.sh SAMPLE 100000 10` for each sample. The same
chunk helper is used by Condor and Snakemake; a rerun promotes a partial ROOT
file only after its logged provenance and exact event count validate.
