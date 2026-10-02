#!/usr/bin/env python3
"""FCCAnalyses native HTCondor entry point for inclusive Z-flavour samples.

Run with ``fccanalysis run``. Custom options follow the analysis path, e.g.:
``--input-glob '/eos/.../p8_ee_Zbb_ecm91/events_*.root'``.
"""

from argparse import ArgumentParser
from pathlib import Path
import glob
import os
import re
import sys


"""
fccanalysis run --batch --ncpus 4 analysis/studies/analysis_preselection_zbb.py
"""

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GLOB = (
    "/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/"
    "p8_ee_Zbb_ecm91/events_*.root")
DEFAULT_OUTPUT_EOS = (
    "/eos/lhcb/lbdt3/user/rquaglia/fcc_ee/lblgamma/outputs/"
    "zbb_full_condor/native_batch_3d_activity_v2")
DEFAULT_COMP_GROUP = "group_u_LHCBT3.e_lhcb_lbd"
DEFAULT_SAMPLE_NAME = "p8_ee_Zbb_ecm91"
SAMPLE_RE = re.compile(r"p8_ee_Z[a-z]+_ecm91")
CONFIG_PATH = Path(os.environ.get(
    "LB_RECO_CONFIG",
    REPO_ROOT / "config/lb_reco_preselection_15mev_45_65_3d.json")).resolve()
include_paths = [
    "lb_event_selection.h", "lb_candidate_builder.h",
    "lb_candidate_truth.h", "lb_candidate_observables.h",
]

sys.path.insert(0, str(Path(__file__).resolve().parent))
# lb2lambda_gamma_reco reads this at import time, so set it before importing.
os.environ["LB_RECO_CONFIG"] = str(CONFIG_PATH)
from lb2lambda_gamma_reco import RDFanalysis as _RDFanalysis  # noqa: E402


def parse_sample_args(cmdline_args):
    parser = ArgumentParser(
        description="Z-flavour native FCCAnalyses batching options",
        add_help=False)
    parser.add_argument("--sample-help", "--zbb-help", action="store_true",
                        help="show sample batching options and exit")
    parser.add_argument("--input-glob", default=DEFAULT_GLOB,
                        help="local EOS glob used to validate the complete input directory")
    parser.add_argument("--sample-name", default=None,
                        help="process name; defaults to the input-glob parent directory")
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
    if opts.sample_help:
        parser.print_help()
        raise SystemExit(0)
    return opts, unknown


def check_setup(opts):
    sample_name = opts.sample_name or Path(opts.input_glob).parent.name
    if not SAMPLE_RE.fullmatch(sample_name):
        raise ValueError(f"Unsupported sample name: {sample_name}")
    paths = sorted(Path(p) for p in glob.glob(opts.input_glob))
    if not paths:
        raise ValueError(f"Input glob matched no files: {opts.input_glob}")
    if any(not p.is_file() for p in paths):
        raise ValueError("Input glob includes a path that is not a regular file")
    if any(p.suffix != ".root" for p in paths):
        raise ValueError("Input glob must match only .root files")
    parent_dirs = {p.parent.parent for p in paths}
    sample_dirs = {p.parent.name for p in paths}
    if len(parent_dirs) != 1 or sample_dirs != {sample_name}:
        raise ValueError(f"All inputs must be under one {sample_name} directory")
    if sample_name != DEFAULT_SAMPLE_NAME and opts.output_eos == DEFAULT_OUTPUT_EOS:
        raise ValueError("Pass a distinct --output-eos for non-Zbb samples")
    if opts.chunks < 1 or opts.chunks > len(paths):
        raise ValueError(f"chunks must be in [1, {len(paths)}]; got {opts.chunks}")
    config = CONFIG_PATH
    if not config.is_file():
        raise ValueError(f"Missing reconstruction config: {config}")
    return paths, next(iter(parent_dirs)), config, sample_name


class Analysis:
    """Stage-1 candidate builder and selections, dispatched by FCCAnalyses."""

    def __init__(self, cmdline_args):
        self.options, self.unknown_args = parse_sample_args(cmdline_args)
        self.ncpus = int(cmdline_args.get("ncpus", 4))
        if self.ncpus < 1:
            raise ValueError("ncpus must be at least 1")
        # The dispatcher invokes this class again on each worker with
        # --batch --files-list. Those jobs receive explicit XRootD-ready input
        # paths and must not try to expand the submit host's mounted EOS glob.
        is_worker = bool(cmdline_args.get("batch", False))
        sample_name = self.options.sample_name or Path(self.options.input_glob).parent.name
        if is_worker:
            paths = []
            input_parent = Path(self.options.input_glob).parent.parent
            config = CONFIG_PATH
        else:
            paths, input_parent, config, sample_name = check_setup(self.options)
        self.input_files = paths
        self.input_parent = input_parent
        self.config_path = config
        self.sample_name = sample_name

        # Reconstruction reads this same config on the submit host and workers.
        os.environ["LB_RECO_CONFIG"] = str(config)

        self.process_list = {
            sample_name: {
                "chunks": self.options.chunks,
                "input_dir": str(input_parent),
            }
        }
        self.prod_tag = "FCCee/winter2023/IDEA/"
        self.input_dir = None
        # Keep temporary outputs in the FCCAnalyses checkout; completed chunks
        # are copied by the managed worker script to the requested EOS folder.
        self.output_dir = f"outputs/{sample_name}_native_batch_3d_activity_v2_work"
        self.run_batch = True
        self.batch_queue = self.options.queue
        self.comp_group = self.options.comp_group
        self.n_threads = self.ncpus
        self.nCPUS = self.ncpus
        self.output_dir_eos = self.options.output_eos
        self.eos_type = self.options.eos_type
        self.include_paths = include_paths
        self.test_file = ("root://eospublic.cern.ch/" + str(paths[0])
                          if paths else "")

        if not is_worker:
            print(f"Validated {len(paths)} ROOT inputs for {sample_name} from {self.options.input_glob}")
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
