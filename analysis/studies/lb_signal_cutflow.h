#ifndef LBLGAMMA_STUDIES_LB_SIGNAL_CUTFLOW_H
#define LBLGAMMA_STUDIES_LB_SIGNAL_CUTFLOW_H

#include <algorithm>
#include <cmath>

#include "lb_candidate_builder.h"
#include "lb_candidate_truth.h"
#include "lb_event_selection.h"

namespace FCCAnalyses::LbSignalCutflow {

using ROOT::VecOps::RVec;

// One flag per generated event, cumulative from raw reconstruction to the
// final signal selection. MC association is used only in this diagnostic;
// the candidate builder and its selection never see truth information.
struct Stages {
  int raw_truth_candidate = 0;
  int selected_photon = 0;
  int valid_pv = 0;
  int event_tracks = 0;
  int nonprimary_tracks = 0;
  int daughter_d0 = 0;
  int vertex_fit_valid = 0;
  int vertex_chi2 = 0;
  int flight_distance = 0;
  int flight_significance = 0;
  int lambda_mass_window = 0;
  int closest_mass_hypothesis = 0;
  int lb_mass_window = 0;
  int same_hemisphere = 0;
  float fitted_lambda_mass = -999.f;
  float true_vertex_chi2 = -999.f;
};

inline bool is_true_candidate(const LbCandidateBuilder::Result& candidates,
                              int proton, int pion, int photon) {
  for (size_t i = 0; i < candidates.lb_mass.size(); ++i)
    if (candidates.lb_proton_index[i] == proton &&
        candidates.lb_pion_index[i] == pion &&
        candidates.lb_photon_index[i] == photon)
      return true;
  return false;
}

inline Stages evaluate(
    const RVec<edm4hep::ReconstructedParticleData>& particles,
    const RVec<edm4hep::TrackState>& tracks,
    const VertexingUtils::FCCAnalysesVertex& pv,
    const RVec<bool>& primary_track_mask,
    const RVec<int>& selected_photons,
    const RVec<float>& thrust,
    const RVec<edm4hep::MCParticleData>& mc,
    const RVec<int>& assoc_reco,
    const RVec<int>& assoc_mc,
    const RVec<int>& parent_indices,
    const LbCandidateBuilder::Config& selection,
    int required_sign = 0) {
  // Truth-gated diagnostic only: this follows a generated direct decay's
  // reconstructed daughters through the configured selection. Do not use
  // this function to build candidates or to select inclusive background.
  // required_sign=+1/-1 separates Lambda_b/anti-Lambda_b; 0 combines both.
  Stages stages;
  const auto links = LbCandidateTruth::label(
      LbCandidateBuilder::Result{}, particles, mc,
      assoc_reco, assoc_mc, parent_indices);
  const auto input = LbEventSelection::inspect(particles, pv, selected_photons);

  auto diagnostic_config = selection;
  diagnostic_config.require_good_vertex = false;

  for (size_t ip = 0; ip < particles.size(); ++ip) {
    const int pmc = links.reco_mc_index[ip];
    if (pmc < 0 || std::abs(mc[pmc].PDG) != 2212 ||
        particles[ip].tracks_end <= particles[ip].tracks_begin) continue;
    const int sign = mc[pmc].PDG > 0 ? +1 : -1;
    if (required_sign != 0 && sign != required_sign) continue;
    if ((sign > 0 && particles[ip].charge <= 0.5f) ||
        (sign < 0 && particles[ip].charge >= -0.5f)) continue;

    for (size_t ii = 0; ii < particles.size(); ++ii) {
      const int pimc = links.reco_mc_index[ii];
      if (pimc < 0 || mc[pimc].PDG != -sign * 211 ||
          particles[ii].tracks_end <= particles[ii].tracks_begin ||
          (sign > 0 && particles[ii].charge >= -0.5f) ||
          (sign < 0 && particles[ii].charge <= 0.5f)) continue;
      const int lambda = LbCandidateTruth::shared_lambda(
          pmc, pimc, mc, parent_indices);
      if (lambda < 0 || mc[lambda].PDG != sign * 3122) continue;

      for (size_t ig = 0; ig < particles.size(); ++ig) {
        const int gmc = links.reco_mc_index[ig];
        if (gmc < 0 || mc[gmc].PDG != 22 ||
            particles[ig].type != 22 || particles[ig].charge != 0.f)
          continue;
        const int lb = LbCandidateTruth::shared_lb(
            lambda, gmc, mc, parent_indices);
        if (lb < 0 || mc[lb].PDG != sign * 5122) continue;

        stages.raw_truth_candidate = 1;
        // Cumulative stages follow the implemented order. Photon-container
        // membership precedes the Lambda0 fit here, so each conditional loss
        // is relative to the preceding stage, not an independent efficiency.
        if (std::find(selected_photons.begin(), selected_photons.end(),
                      static_cast<int>(ig)) == selected_photons.end())
          continue;
        stages.selected_photon = 1;
        if (!input.has_pv) continue;
        stages.valid_pv = 1;
        if (input.n_photons < 1 || input.n_charged_tracks < 2 ||
            input.n_positive_tracks < 1 || input.n_negative_tracks < 1)
          continue;
        stages.event_tracks = 1;

        const int plus = sign > 0 ? static_cast<int>(ip) : static_cast<int>(ii);
        const int minus = sign > 0 ? static_cast<int>(ii) : static_cast<int>(ip);
        const auto fit = LbCandidateBuilder::fit_pair(
            particles, tracks, pv, primary_track_mask, plus, minus,
            diagnostic_config);
        if (!fit.nonprimary) continue;
        stages.nonprimary_tracks = 1;
        if (!fit.tracks_displaced) continue;
        stages.daughter_d0 = 1;
        if (!fit.valid) continue;
        stages.vertex_fit_valid = 1;
        stages.true_vertex_chi2 = fit.chi2;
        if (fit.primary == 1 || fit.chi2 > selection.vertex_max_chi2) continue;
        stages.vertex_chi2 = 1;
        if (fit.flight_rxy < selection.min_flight_rxy_mm) continue;
        stages.flight_distance = 1;
        if (fit.flight_sig < selection.min_vertex_flight_sig) continue;
        stages.flight_significance = 1;

        const auto plus_hypothesis =
            LbCandidateBuilder::with_mass(fit.plus_momentum,
                                          LbCandidateBuilder::kProtonMass) +
            LbCandidateBuilder::with_mass(fit.minus_momentum,
                                          LbCandidateBuilder::kPionMass);
        const auto minus_hypothesis =
            LbCandidateBuilder::with_mass(fit.minus_momentum,
                                          LbCandidateBuilder::kProtonMass) +
            LbCandidateBuilder::with_mass(fit.plus_momentum,
                                          LbCandidateBuilder::kPionMass);
        const float plus_mass = LbCandidateBuilder::mass(plus_hypothesis);
        const float minus_mass = LbCandidateBuilder::mass(minus_hypothesis);
        const float true_mass = sign > 0 ? plus_mass : minus_mass;
        if (stages.fitted_lambda_mass < 0.f ||
            std::abs(true_mass - selection.lambda_mass_gev) <
                std::abs(stages.fitted_lambda_mass - selection.lambda_mass_gev))
          stages.fitted_lambda_mass = true_mass;
        const auto in_window = [&](float m) {
          return m >= selection.lambda_mass_min_gev &&
                 m <= selection.lambda_mass_max_gev;
        };
        const bool plus_ok = in_window(plus_mass);
        const bool minus_ok = in_window(minus_mass);
        if (!in_window(true_mass)) continue;
        stages.lambda_mass_window = 1;
        const int closest_sign = !minus_ok || (plus_ok &&
            std::abs(plus_mass - selection.lambda_mass_gev) <=
            std::abs(minus_mass - selection.lambda_mass_gev)) ? +1 : -1;
        if (selection.choose_closest_hypothesis && sign != closest_sign) continue;
        stages.closest_mass_hypothesis = 1;

        const auto lambda = sign > 0 ? plus_hypothesis : minus_hypothesis;
        const auto lb_p4 = lambda +
            LbCandidateBuilder::measured_photon(particles[ig]);
        const float lbmass = LbCandidateBuilder::mass(lb_p4);
        if (lbmass < selection.lb_mass_min_gev ||
            lbmass > selection.lb_mass_max_gev) continue;
        stages.lb_mass_window = 1;
        const float lambda_cos = LbCandidateBuilder::thrust_cosine(lambda, thrust);
        const float photon_cos = LbCandidateBuilder::thrust_cosine(
            LbCandidateBuilder::measured_photon(particles[ig]), thrust);
        const bool same_hemisphere = lambda_cos != -999.f &&
            photon_cos != -999.f && lambda_cos * photon_cos > 0.f;
        if (selection.require_same_hemisphere && !same_hemisphere) continue;

        // Check the diagnostic against the production builder with the same
        // reconstructed objects and original collection indices.
        auto masked = particles;
        for (auto& item : masked) {
          item.charge = 0.f;
          item.type = 0;
          item.tracks_end = item.tracks_begin;
        }
        masked[ip] = particles[ip];
        masked[ii] = particles[ii];
        masked[ig] = particles[ig];
        const auto candidates = LbCandidateBuilder::build(
            masked, tracks, pv, primary_track_mask, selected_photons,
            thrust, selection);
        if (is_true_candidate(candidates, ip, ii, ig))
          stages.same_hemisphere = 1;
      }
    }
  }
  return stages;
}

}  // namespace FCCAnalyses::LbSignalCutflow

#endif
