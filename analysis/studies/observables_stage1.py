"""Attach candidate isolation, pi0 pairing, and Z-recoil diagnostics.

Selections and candidate construction stay in lb2lambda_gamma_reco.py and
lb_candidate_builder.h. All branches here are diagnostic and have one element
per surviving candidate. Constants live in config/lb_observables.json.
"""

import json
import math
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "lb_observables.json"
CONFIG = json.loads(CONFIG_PATH.read_text())
KEYS = ("ecm_gev", "lb_mass_gev", "lambda_mass_gev", "pi0_mass_gev",
        "cone_r02", "cone_r03", "cone_r05", "cone_r07", "cone_r10",
        "cone_r70")
if not all(math.isfinite(float(CONFIG[key])) and float(CONFIG[key]) > 0
           for key in KEYS):
    raise ValueError(f"Invalid candidate-observable config: {CONFIG_PATH}")
if not (CONFIG["cone_r02"] < CONFIG["cone_r03"] < CONFIG["cone_r05"] <
        CONFIG["cone_r07"] < CONFIG["cone_r10"] < CONFIG["cone_r70"]):
    raise ValueError("Isolation cone sizes must increase")

BASE_BRANCHES = (
    "iso_delphes", "iso_delphes_available", "iso_R02", "iso_R03",
    "iso_R05", "iso_R02_E", "iso_R03_E", "iso_R05_E",
    "iso_R03_noLambda", "iso_R05_noLambda",
    "iso_R03_noLambda_E", "iso_R05_noLambda_E",
    "iso_charged", "iso_neutral", "iso_charged_E", "iso_neutral_E",
    "n_photons_DR03", "n_photons_DR05", "m_gg_best", "dm_gg_pi0",
    "E_gamma2", "dr_gg", "gamma2_index",
    "gamma_combo_other_gamma_mass", "gamma_combo_other_gamma_index",
    "gamma_combo_same_hemi_all_mass", "gamma_combo_same_hemi_all_index",
    "gamma_combo_same_hemi_selected_mass", "gamma_combo_same_hemi_selected_index",
    "m_LamGam", "m_rec",
    "dm_rec", "m_rec_all", "deltaE", "px_bal", "py_bal", "pz_bal",
    "deltaP", "cos_rec_sig", "Estar_gamma", "Estar_gamma_rec",
    "opp_hemi_px", "opp_hemi_py", "opp_hemi_pz", "opp_hemi_p",
    "opp_hemi_energy", "opp_hemi_n", "z_partial_deltaE", "z_partial_px",
    "z_partial_py", "z_partial_pz", "z_partial_deltaP",
    "z_full_deltaE", "z_full_px", "z_full_py", "z_full_pz", "z_full_deltaP",
    "dEstar", "dEstar_rec", "E_same", "m_same", "dca_Lam_gamma",
    "Lxyz_implied", "cos_dir_implied", "roe_thrust_x", "roe_thrust_y",
    "roe_thrust_z", "roe_n_other", "roe_n_same", "lambda_pv_cos",
    "lambda_pv_dca", "arm_alpha", "arm_qt",
)

ACTIVITY_BRANCHES = {}
for cone_index, cone_name in enumerate(("R02", "R03", "R05", "R07", "R10", "R70")):
    for class_index, class_name in enumerate(("all", "charged", "neutral")):
        for metric in ("px", "py", "pz", "p", "energy", "n"):
            ACTIVITY_BRANCHES[f"iso_{cone_name}_{class_name}_{metric}"] = (
                f"candidate_observables.iso_activity_{metric}"
                f"[{cone_index}][{class_index}]")
    for metric in ("d0_min", "d0_max", "absd0_min", "absd0_max", "n_d0"):
        ACTIVITY_BRANCHES[f"iso_{cone_name}_charged_{metric}"] = (
            f"candidate_observables.iso_charged_{metric}[{cone_index}]")

BRANCHES = BASE_BRANCHES + tuple(ACTIVITY_BRANCHES)


def attach(df):
    """Define observable vectors aligned slot-for-slot with candidates.lb_mass."""
    values = ", ".join(repr(float(CONFIG[key])) for key in KEYS)
    call = ("FCCAnalyses::LbCandidateObservables::compute("
            "candidates, ReconstructedParticles, EFlowTrack_1, SelectedPhotonIndices, "
            f"FCCAnalyses::LbCandidateObservables::Config{{{values}}})")
    df = df.Define("candidate_observables", call)
    for name in BRANCHES:
        df = df.Define(name, ACTIVITY_BRANCHES.get(name,
                       "candidate_observables." + name))
    return df
