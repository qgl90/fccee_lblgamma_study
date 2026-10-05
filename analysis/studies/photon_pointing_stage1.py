"""Versioned candidate diagnostics; no selection or random smearing."""
FIELDS = ('mc_index', 'match_status', 'truth_px', 'truth_py', 'truth_pz', 'truth_energy', 'truth_vx', 'truth_vy', 'truth_vz', 'truth_hit_x', 'truth_hit_y', 'truth_hit_z', 'truth_hit_path', 'truth_hit_region', 'reco_hit_x', 'reco_hit_y', 'reco_hit_z', 'reco_hit_path', 'reco_hit_region', 'geometry_version', 'barrel_radius', 'endcap_abs_z', 'endcap_inner_radius', 'endcap_outer_radius', 'pv_x', 'pv_y', 'pv_z', 'pv_valid')
BRANCHES = tuple("lb_photon_pointing_" + name for name in FIELDS)

def attach(df):
    df = df.Define("photon_pointing_v4", "FCCAnalyses::PhotonPointingV4::label(candidates, candidate_truth, ReconstructedParticles, Particle)")
    for name, branch in zip(FIELDS, BRANCHES):
        df = df.Define(branch, "photon_pointing_v4." + name)
    return df
