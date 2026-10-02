#!/usr/bin/env python3
"""FCCAnalyses native HTCondor entry point for the Z->bb preselection.

Run with ``fccanalysis run``. Custom options follow the analysis path, e.g.:
``--input-glob '/eos/.../p8_ee_Zbb_ecm91/events_*.root'``.
"""

from argparse import ArgumentParser
from pathlib import Path
import glob
import os
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GLOB = (
    "/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/"
    "p8_ee_Zbb_ecm91/events_*.root")
DEFAULT_OUTPUT_EOS = (
    "/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/"
    "zbb_full_condor/native_batch")
DEFAULT_COMP_GROUP = "group_u_LHCBT3.e_lhcb_lbd"
SAMPLE_NAME = "p8_ee_Zbb_ecm91"
include_paths = [
    "lb_event_selection.h", "lb_candidate_builder.h",
    "lb_candidate_truth.h", "lb_candidate_observables.h",
]

sys.path.insert(0, str(Path(__file__).resolve().parent))
# lb2lambda_gamma_reco reads this at import time, so set it before importing.
os.environ["LB_RECO_CONFIG"] = str(
    REPO_ROOT / "config/lb_reco_preselection_15mev_45_65.json")
from lb2lambda_gamma_reco import RDFanalysis as _RDFanalysis  # noqa: E402


def parse_zbb_args(cmdline_args):
    parser = ArgumentParser(
        description="Zbb native FCCAnalyses batching options",
        add_help=False)
    parser.add_argument("--zbb-help", action="store_true",
                        help="show these Zbb-specific options and exit")
    parser.add_argument("--input-glob", default=DEFAULT_GLOB,
                        help="local EOS glob used to validate the complete input directory")
    parser.add_argument("--chunks", type=int, default=1200,
                        help="number of native FCCAnalyses Condor chunks (default: 1200)")
    parser.add_argument("--comp-group", default=DEFAULT_COMP_GROUP,
                        help="CERN Condor accounting group")
    parser.add_argument("--queue", default="workday",
                        help="CERN Condor JobFlavour")
    parser.add_argument("--output-eos", default=DEFAULT_OUTPUT_EOS,
                        help="EOS mount path for completed chunk ROOT files")
    parser.add_argument("--eos-type", default="eoslhcb",
                        help="XRootD endpoint prefix used by FCCAnalyses xrdcp")
    parser.add_argument("--check-only", action="store_true",
                        help="check glob, chunk count, config, and output path; submit nothing")
    opts, unknown = parser.parse_known_args(cmdline_args.get("unknown", []))
    if opts.zbb_help:
        parser.print_help()
        raise SystemExit(0)
    return opts, unknown


def check_setup(opts):
    paths = sorted(Path(p) for p in glob.glob(opts.input_glob))
    if not paths:
        raise ValueError(f"Input glob matched no files: {opts.input_glob}")
    if any(not p.is_file() for p in paths):
        raise ValueError("Input glob includes a path that is not a regular file")
    if any(p.suffix != ".root" for p in paths):
        raise ValueError("Input glob must match only .root files")
    parent_dirs = {p.parent.parent for p in paths}
    sample_dirs = {p.parent.name for p in paths}
    if len(parent_dirs) != 1 or sample_dirs != {SAMPLE_NAME}:
        raise ValueError("All inputs must be under one p8_ee_Zbb_ecm91 directory")
    if opts.chunks < 1 or opts.chunks > len(paths):
        raise ValueError(f"chunks must be in [1, {len(paths)}]; got {opts.chunks}")
    config = REPO_ROOT / "config/lb_reco_preselection_15mev_45_65.json"
    if not config.is_file():
        raise ValueError(f"Missing reconstruction config: {config}")
    return paths, next(iter(parent_dirs)), config


class Analysis:
    """Stage-1 candidate builder and selections, dispatched by FCCAnalyses."""

    def __init__(self, cmdline_args):
        self.options, self.unknown_args = parse_zbb_args(cmdline_args)
        self.ncpus = int(cmdline_args.get("ncpus", 4))
        if self.ncpus < 1:
            raise ValueError("ncpus must be at least 1")
        # The dispatcher invokes this class again on each worker with
        # --batch --files-list. Those jobs receive explicit XRootD-ready input
        # paths and must not try to expand the submit host's mounted EOS glob.
        is_worker = bool(cmdline_args.get("batch", False))
        if is_worker:
            paths = []
            input_parent = Path(DEFAULT_GLOB.split("/p8_ee_Zbb_ecm91/")[0])
            config = REPO_ROOT / "config/lb_reco_preselection_15mev_45_65.json"
        else:
            paths, input_parent, config = check_setup(self.options)
        self.input_files = paths
        self.input_parent = input_parent
        self.config_path = config

        # Reconstruction reads this same config on the submit host and workers.
        os.environ["LB_RECO_CONFIG"] = str(config)

        self.process_list = {
            SAMPLE_NAME: {
                "chunks": self.options.chunks,
                "input_dir": str(input_parent),
            }
        }
        self.prod_tag = None
        self.input_dir = None
        # Keep temporary outputs in the FCCAnalyses checkout; completed chunks
        # are copied by the managed worker script to the requested EOS folder.
        self.output_dir = "outputs/zbb_native_batch_work"
        self.run_batch = True
        self.batch_queue = self.options.queue
        self.comp_group = self.options.comp_group
        self.n_threads = self.ncpus
        self.nCPUS = self.ncpus
        self.output_dir_eos = self.options.output_eos
        self.eos_type = self.options.eos_type
        self.include_paths = include_paths
        self.test_file = (
            "root://eospublic.cern.ch//eos/experiment/fcc/ee/generation/"
            "DelphesEvents/winter2023/IDEA/p8_ee_Zbb_ecm91/"
            "events_000083138.root")

        if not is_worker:
            print(f"Validated {len(paths)} ROOT inputs from {self.options.input_glob}")
            print(f"Chunks: {self.options.chunks}; ~{len(paths) / self.options.chunks:.2f} files/job")
            print("Input mode: mounted /eos paths are rewritten by FCCAnalyses to root://eospublic.cern.ch")
            print(f"Config: {self.config_path}")
            print(f"Accounting group: {self.comp_group}; queue: {self.batch_queue}; CPUs/job: {self.n_threads}")
            print(f"EOS output: {self.output_dir_eos} (root://{self.eos_type}.cern.ch)")
        if self.options.check_only:
            print("Check-only complete; no jobs submitted.")
            raise SystemExit(0)

    def analyzers(self, dframe):
        # Reuse the exact reconstruction chain and branches from the tested
        # single-file workflow. This wrapper changes dispatch only.
        return _RDFanalysis.analysers(dframe)

    def output(self):
        return _RDFanalysis.output()
