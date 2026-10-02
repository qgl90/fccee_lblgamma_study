"""
Author: Renato Quagliani (rquaglia@cern.ch), main stage-1 analysis for 

Shared Lambda_b candidate dataframe and uncut Gamma baseline builder

The baseline writes every event and uses all type-22 reconstructed photons.
Configured callers add PV, photon-container, and charged-track prerequisites,
then use only selected photons and fit displaced opposite-charge pairs.
Truth labels are never used to build candidates.
"""

processList = {}
analysisName = "lb2lambda_gamma_baseline"
outputDir = "outputs/analysis/studies"
nCPUS = 4
includePaths = ["lb_candidate_builder.h", "lb_candidate_truth.h"]

_COUNTS = [
    "n_opposite_charge_pairs", "n_pairs_nonprimary", "n_pairs_d0_pass",
    "n_pairs_raw_mass_pass", "n_vertex_fits",
    "n_tracks", "n_photons", "n_neutrals", "n_lambdas_mass_window",
    "n_lambdas_nonprimary_tracks", "n_lambdas_track_displaced",
    "n_lambdas_fit_valid", "n_lambdas_fit_good", "n_lambdas",
    "n_lb_before_mass_window", "n_lb_before_hemisphere", "n_lb",
    "pv_valid", "n_pv_tracks", "pv_x", "pv_y", "pv_z",
    "thrust_value", "thrust_x", "thrust_y", "thrust_z",
]
_LAMBDA = [
    "lambda_proton_index", "lambda_pion_index", "lambda_sign",
    "lambda_mass", "lambda_pt", "lambda_vertex_valid",
    "lambda_px", "lambda_py", "lambda_pz", "lambda_energy",
    "lambda_vertex_primary",
    "lambda_vertex_good", "lambda_vertex_x", "lambda_vertex_y",
    "lambda_vertex_z", "lambda_vertex_chi2", "lambda_flight_rxy",
    "lambda_flight_xyz", "lambda_proton_d0sig", "lambda_pion_d0sig",
    "lambda_flight_rxy_sigma", "lambda_flight_rxy_sig",
    "lambda_flight_xyz_sigma", "lambda_flight_xyz_sig",
    "lambda_d0", "lambda_d0_sigma", "lambda_d0_sig",
]
_INPUT = [
    "input_has_pv", "input_n_photons", "input_n_charged_tracks",
    "input_n_positive_tracks", "input_n_negative_tracks",
]
_LB = [
    "lb_lambda_slot", "lb_proton_index", "lb_pion_index",
    "lb_photon_index", "lb_photon2_index", "lb_sign", "lb_mass", "lb_pt",
    "lb_cos_theta_p",
    "lb_energy", "lb_lambda_mass", "lb_lambda_px", "lb_lambda_py",
    "lb_lambda_pz", "lb_px", "lb_py", "lb_pz",
    "lb_proton_px", "lb_proton_py", "lb_proton_pz", "lb_proton_energy",
    "lb_pion_px", "lb_pion_py", "lb_pion_pz", "lb_pion_energy",
    "lb_proton_d0", "lb_pion_d0",
    "lb_photon_px", "lb_photon_py", "lb_photon_pz",
    "lb_photon_energy",
    "lb_photon2_energy", "lb_neutral_mass", "lb_neutral_energy",
    "lb_same_hemisphere", "lb_lambda_thrust_cos", "lb_neutral_thrust_cos",
    "lb_thrust_cos",
]
_TRUTH = [
    "reco_mc_index", "reco_mc_pdg", "reco_mc_n_parents",
    "reco_mc_parent_index", "reco_mc_parent_pdg",
    "reco_mc_grandparent_index", "reco_mc_grandparent_pdg",
    "reco_p", "reco_energy", "reco_mc_p", "reco_mc_energy",
    "reco_mc_pt", "reco_mc_eta", "reco_mc_vertex_rxy",
    "reco_mc_cos_opening",
    "lambda_mass_hypothesis_correct", "lambda_truth_matched",
    "lambda_truth_lambda_mc_index", "lb_truth_matched",
    "lb_mass_hypothesis_correct", "lb_truth_lb_mc_index",
    "lb_truth_cos_theta_p",
    "lb_truth_neutral_mc_index",
    "n_truth_matched_lb",
]


def build_dataframe(df, config_expression="", with_vertices=False,
                    filter_min_photons=0, filter_empty_candidates=False):
    """Attach candidates and post-build truth labels.

    The configured path applies event prerequisites before snapshotting, so
    its output cannot by itself measure losses at those filters. Use the
    dedicated signal cutflow and generated-chain audit for denominators.
    `event_entry` is retained to join event and candidate tables later.
    """
    
    print("Building Lambda_b candidate dataframe with config expression built from lb_reco.json:")
    print("build_dataframe, with_vertices:", with_vertices, "filter_min_photons:", filter_min_photons)
    
    print(config_expression)
    arguments = "ReconstructedParticles"
    if with_vertices:
        # Match the pinned FCCAnalyses vertexing examples. The PV track mask
        # rejects tracks assigned to the PV before displaced-pair fitting.
        df = (df.Define("PrimaryTracks",
                        "VertexFitterSimple::get_PrimaryTracks("
                        "EFlowTrack_1, true, 4.5, 20e-3, 300, 0., 0., 0.)")
                .Define("PrimaryVertexObject",
                        "VertexFitterSimple::VertexFitter_Tk("
                        "1, PrimaryTracks, true, 4.5, 20e-3, 300, "
                        "0., 0., 0., false)"))
        if filter_min_photons:
            """
            See the lb_event_selection.h header for the FCCAnalyses::LbEventSelection::inspect() signature and task.
            Inspect fills a InputCounts struct with the number of 
            - reconstructed photons
            - charged tracks (positive and negative ones) found in event.
            The struct also contains a boolean flag to indicate if a reconstructed PV was found in the event having at least >=2 tracks            
            """          
            
            
            """
            Execute the inspection, and then define fields for "Event info"
            in the dataframe
            """              
            df = df.Alias("SelectedPhotonIndices", "Photon#0.index").Define(
                "InputSelection",
                "FCCAnalyses::LbEventSelection::inspect("
                "ReconstructedParticles, PrimaryVertexObject, "
                "SelectedPhotonIndices)")
            for name, field in (
                ("input_has_pv", "has_pv"),
                ("input_n_photons", "n_photons"),
                ("input_n_charged_tracks", "n_charged_tracks"),
                ("input_n_positive_tracks", "n_positive_tracks"),
                ("input_n_negative_tracks", "n_negative_tracks"),
            ):
                df = df.Define(name, "InputSelection." + field)
            
            ################################################
            # Now filter on the inspected counts ! 
            ################################################
            print( "Filtering on event counts:")
            print( "Filter for has PV")
            print( f"Filter for min-nphotons found >= {filter_min_photons}" )
            print( "Filter for min-ncharged-tracks found >= 2" )
            print( "Filter for min-npositive-tracks found >= 1 and min-nnegative-tracks found >= 1" )
            df = (df.Filter("input_has_pv == 1", "has reconstructed PV")
                    .Filter(f"input_n_photons >= {filter_min_photons}",
                            "enough reconstructed photons")
                    .Filter("input_n_charged_tracks >= 2",
                            "at least two charged tracks")
                    .Filter("input_n_positive_tracks >= 1 && "
                            "input_n_negative_tracks >= 1",
                            "opposite-charge tracks available"))
        ##################################################
        # Define a primary track mask to apply
        ##################################################
        df = df.Define(
            "PrimaryTrackMask",
            "VertexFitterSimple::IsPrimary_forTracks(EFlowTrack_1, PrimaryTracks)")
        ###################################################
        # Define the Event Thrust observable, which is used to select the hemisphere of the Lambda_b candidate
        ###################################################
        df = df.Define(
            "EventThrust",
            # Full reconstructed event, including the candidate daughters;
            # future global-event scenarios must document any exclusions.
            "Algorithms::calculate_thrust()("
            "ReconstructedParticle::get_px(ReconstructedParticles), "
            "ReconstructedParticle::get_py(ReconstructedParticles), "
            "ReconstructedParticle::get_pz(ReconstructedParticles))")
        arguments += ", EFlowTrack_1, PrimaryVertexObject, PrimaryTrackMask"
        if filter_min_photons:
            arguments += ", SelectedPhotonIndices, EventThrust"
    if config_expression:
        arguments += ", " + config_expression
    df = (df.Alias("AssocReco", "MCRecoAssociations#0.index")
            .Alias("AssocMC", "MCRecoAssociations#1.index")
            .Alias("MCParents", "Particle#0.index")
            .Define("event_entry", "static_cast<unsigned long long>(rdfentry_)")
            .Define("candidates",
                    "FCCAnalyses::LbCandidateBuilder::build(" + arguments + ")")
            .Define("candidate_truth",
                    "FCCAnalyses::LbCandidateTruth::label("
                    "candidates, ReconstructedParticles, Particle, "
                    "AssocReco, AssocMC, MCParents)"))
    for name in _COUNTS + _LAMBDA + _LB:
        df = df.Define(name, "candidates." + name)
    for name in _TRUTH:
        df = df.Define(name, "candidate_truth." + name)
    if filter_empty_candidates:
        # This is deliberately after candidate construction: an event can
        # only be rejected once the fitted, fully selected Lambda_b list is
        # known. It reduces downstream output/flattening, not fit CPU time.
        df = df.Filter("n_lb > 0", "at least one selected Lambda_b candidate")
    return df


class RDFanalysis:
    @staticmethod
    def analysers(df):
        return build_dataframe(df)

    @staticmethod
    def output():
        return ["event_entry"] + _COUNTS + _LAMBDA + _LB + _TRUTH
