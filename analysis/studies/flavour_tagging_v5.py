"""Reconstructed event-jet flavour tagging for the v5 Stage-1 study."""

import os
from pathlib import Path
import re

from addons.ONNXRuntime.jetFlavourHelper import JetFlavourHelper
from addons.FastJet.jetClusteringHelper import ExclusiveJetClusteringHelper

from examples.FCCee.weaver.config import collections


TAG = "flavtag_v5"
NJETS = int(os.environ.get("LB_FLAVTAG_NJETS", "2"))
MODEL_NAME = os.environ.get(
    "LB_FLAVTAG_MODEL_NAME", "fccee_flavtagging_edm4hep_wc_v1")
MODEL_DIR = Path(os.environ.get(
    "LB_FLAVTAG_MODEL_DIR",
    "/eos/experiment/fcc/ee/jet_flavour_tagging/"
    "winter2023/wc_pt_13_01_2022"))
PREPROCESSING = Path(os.environ.get(
    "LB_FLAVTAG_PREPROCESSING", str(MODEL_DIR / f"{MODEL_NAME}.json")))
MODEL = Path(os.environ.get(
    "LB_FLAVTAG_ONNX", str(MODEL_DIR / f"{MODEL_NAME}.onnx")))

_clusterer = None
_tagger = None
_BRANCHES = ("flavtag_v5_pv_x", "flavtag_v5_pv_y", "flavtag_v5_pv_z")
_CANDIDATE_BRANCHES = []


def attach(df):
    """Add event-level reconstructed-jet scores after candidate selection."""
    global _clusterer, _tagger, _CANDIDATE_BRANCHES

    missing = [str(path) for path in (PREPROCESSING, MODEL) if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Flavour-tagging model files are unavailable: " + ", ".join(missing)
            + ". Set LB_FLAVTAG_PREPROCESSING and LB_FLAVTAG_ONNX to readable files.")

    # Candidate building and its event filter have already run. These jets are
    # diagnostic event jets; the first iteration does not remove candidate
    # daughters before reclustering.
    _clusterer = ExclusiveJetClusteringHelper(
        collections["PFParticles"], NJETS, TAG)
    df = _clusterer.define(df)

    # The upstream example uses the MC primary vertex for track-IP features.
    # v5 instead supplies the reconstructed PV already fitted by the Lb chain.
    df = (df.Define("flavtag_v5_primary_vertex_data",
                    "VertexingUtils::get_VertexData(PrimaryVertexObject)")
            .Define("flavtag_v5_primary_vertex",
                    "TLorentzVector(flavtag_v5_primary_vertex_data.position.x, "
                    "flavtag_v5_primary_vertex_data.position.y, "
                    "flavtag_v5_primary_vertex_data.position.z, 0.)")
            .Define("flavtag_v5_pv_x",
                    "flavtag_v5_primary_vertex_data.position.x")
            .Define("flavtag_v5_pv_y",
                    "flavtag_v5_primary_vertex_data.position.y")
            .Define("flavtag_v5_pv_z",
                    "flavtag_v5_primary_vertex_data.position.z"))

    _tagger = JetFlavourHelper(
        collections, _clusterer.jets, _clusterer.constituents, TAG)
    _tagger.definition[f"pv{_tagger.tag}"] = "flavtag_v5_primary_vertex"
    df = _tagger.define(df)
    df = _tagger.inference(str(PREPROCESSING), str(MODEL), df)

    # The two-jet model gives one score per jet. Add candidate-aligned
    # diagnostic scores so ordinary candidate flattening can preserve them.
    _CANDIDATE_BRANCHES = []
    for score in _tagger.scores:
        label = re.sub(r"[^A-Za-z0-9_]+", "_", score).strip("_")
        associated = f"lb_flavtag_v5_{label}_associated"
        other = f"lb_flavtag_v5_{label}_otherjet_max"
        args = (f"lb_px, lb_py, lb_pz, jet_theta_{TAG}, jet_phi_{TAG}, {score}")
        df = df.Define(
            associated,
            "FCCAnalyses::FlavourTaggingV5::associated_score(" + args + ")")
        df = df.Define(
            other,
            "FCCAnalyses::FlavourTaggingV5::other_jet_max_score(" + args + ")")
        _CANDIDATE_BRANCHES.extend((associated, other))
    return df


def output_branches():
    if _clusterer is None or _tagger is None:
        raise RuntimeError("flavour_tagging_v5.attach() must run before output_branches()")
    # Keep each jet vector and score vector event-level. Deduplicate jet_nconst,
    # which is listed by both helper output methods in this FCCAnalyses version.
    return list(dict.fromkeys(
        list(_BRANCHES)
        + _clusterer.outputBranches()
        + _tagger.outputBranches()
        + _CANDIDATE_BRANCHES))
