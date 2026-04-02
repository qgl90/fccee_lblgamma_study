# FCCAnalyses quick test (signal + background)

This is a minimal “does the analysis run?” checklist to validate the FCCAnalyses step on:

- your **signal** EDM4hep ROOT produced by `delphes_edm4hep`
- a few **background** files from EOS (winter2023 IDEA `Z→bb`)

## 0) Prerequisites

In the same shell you run these commands, make sure you have:

- `fccanalysis` on `PATH`
- `root` available

## 1) Sanity-check the EDM4hep collections exist

Run on one file first:

```bash
root -l -b -q 'outputs/delphes/Lb2LambdaGamma_IDEA_edm4hep.root' -e \
'auto f=TFile::Open(gROOT->GetListOfFiles()->At(0)->GetName()); auto t=(TTree*)f->Get("events"); t->Print();'
```

You want to see branches like:

- `ReconstructedParticles` (needed for reco mode)
- `Particle`, `MCRecoAssociations` (needed for truth-matching mode)

## 2) Prepare small input file lists (signal + background)

```bash
mkdir -p work/filelists

# signal (your produced file)
printf "%s\n" "$PWD/outputs/delphes/Lb2LambdaGamma_IDEA_edm4hep.root" > work/filelists/signal.txt

# background: start with 1–5 files only
ls /eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/p8_ee_Zbb_ecm91/events_*.root \
  | head -n 5 > work/filelists/Zbb_5files.txt
```

## 3) Run FCCAnalyses (recommended: reco mode for background shape)

Truth-matching (`analysis/analysis_lb2lgamma.py`) is a good sanity check for **signal**,
but it is **not** a realistic estimate of combinatorial background.

For a first-pass background shape, use the simple combinatorial reco script:

```bash
# signal reco
fccanalysis run analysis/analysis_lb2lgamma_reco.py \
  --input-file-list work/filelists/signal.txt \
  --output outputs/analysis/signal_reco_test.root

# background reco
fccanalysis run analysis/analysis_lb2lgamma_reco.py \
  --input-file-list work/filelists/Zbb_5files.txt \
  --output outputs/analysis/Zbb_reco_test.root
```

Quick check that trees are non-empty:

```bash
root -l -b -q outputs/analysis/signal_reco_test.root -e 'events->GetEntries()'
root -l -b -q outputs/analysis/Zbb_reco_test.root    -e 'events->GetEntries()'
```

## 4) Quick plots

In ROOT:

```bash
root -l outputs/analysis/signal_reco_test.root -e 'events->Draw("lb_reco_m")'
root -l outputs/analysis/Zbb_reco_test.root    -e 'events->Draw("lb_reco_m")'
```

Or with the overlay helper:

```bash
python3 plots/plot_mass_overlay.py \
  --out outputs/plots/lb_reco_m_test.png \
  --branch lb_reco_m --nbins 120 --xmin 4.8 --xmax 6.4 \
  --normalize none \
  --signal outputs/analysis/signal_reco_test.root|1.0 \
  --backgrounds "Zbb|outputs/analysis/Zbb_reco_test.root|1.0"
```

Output: `outputs/plots/lb_reco_m_test.png`

