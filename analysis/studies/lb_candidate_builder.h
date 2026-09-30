#ifndef LBLGAMMA_STUDIES_LB_CANDIDATE_BUILDER_H
#define LBLGAMMA_STUDIES_LB_CANDIDATE_BUILDER_H

#include <algorithm>
#include <cmath>
#include <vector>

#include "ROOT/RVec.hxx"
#include "TLorentzVector.h"
#include "edm4hep/ReconstructedParticleData.h"
#include "edm4hep/TrackState.h"
#include "FCCAnalyses/VertexFitterSimple.h"
#include "FCCAnalyses/VertexingUtils.h"

namespace FCCAnalyses::LbCandidateBuilder {

// Observable reconstruction only. This file must not inspect MC particles or
// MCRecoAssociations; lb_candidate_truth.h attaches labels after build().
// The same one-photon mode is used on forced Gamma and Eta samples so that
// the latter measures partial reconstruction under the signal hypothesis.

using ROOT::VecOps::RVec;

// Mass hypotheses in GeV. No particle identification is used at this stage.
constexpr double kProtonMass = 0.9382720813;
constexpr double kPionMass = 0.13957039;

struct FourMomentum {
  double px = 0., py = 0., pz = 0., energy = 0.;
};

inline FourMomentum operator+(const FourMomentum& a, const FourMomentum& b) {
  return {a.px + b.px, a.py + b.py, a.pz + b.pz, a.energy + b.energy};
}

inline FourMomentum with_mass(const edm4hep::ReconstructedParticleData& particle,
                              double mass) {
  const auto& p = particle.momentum;
  return {p.x, p.y, p.z,
          std::sqrt(double(p.x) * p.x + double(p.y) * p.y +
                    double(p.z) * p.z + mass * mass)};
}

inline FourMomentum with_mass(const TVector3& momentum, double mass) {
  const double px = momentum.Px(), py = momentum.Py(), pz = momentum.Pz();
  return {px, py, pz, std::sqrt(px * px + py * py + pz * pz + mass * mass)};
}

inline FourMomentum measured_photon(const edm4hep::ReconstructedParticleData& photon) {
  const auto& p = photon.momentum;
  return {p.x, p.y, p.z, photon.energy};
}

inline float mass(const FourMomentum& p) {
  const double m2 = p.energy * p.energy - p.px * p.px -
                    p.py * p.py - p.pz * p.pz;
  // A measured photon can make a combination space-like. Keep its signed
  // square-root instead of silently turning that response into zero mass.
  return static_cast<float>(std::copysign(std::sqrt(std::abs(m2)), m2));
}

inline float pt(const FourMomentum& p) {
  return static_cast<float>(std::hypot(p.px, p.py));
}

inline float thrust_cosine(const FourMomentum& p, const RVec<float>& thrust) {
  if (thrust.size() < 4) return -999.f;
  const double norm_p = std::sqrt(p.px * p.px + p.py * p.py + p.pz * p.pz);
  const double norm_axis = std::sqrt(double(thrust[1]) * thrust[1] +
      double(thrust[2]) * thrust[2] + double(thrust[3]) * thrust[3]);
  if (!(norm_p > 0.) || !(norm_axis > 0.) || !std::isfinite(norm_axis))
    return -999.f;
  const double dot = p.px * thrust[1] + p.py * thrust[2] + p.pz * thrust[3];
  return std::isfinite(dot) ? static_cast<float>(dot / (norm_p * norm_axis))
                            : -999.f;
}

// LHCb Lambda_b -> Lambda gamma helicity convention: cos(theta_p) is the
// angle between the (anti)proton and minus the parent Lambda_b momentum,
// evaluated in the Lambda rest frame. Both four-vectors are boosted by the
// SAME Lambda boost. Return -999 for a nonphysical or undefined boost.
inline float cos_theta_p(const FourMomentum& parent,
                         const FourMomentum& lambda,
                         const FourMomentum& proton) {
  const TLorentzVector l(lambda.px, lambda.py, lambda.pz, lambda.energy);
  if (!(l.E() > 0.) || !(l.M2() > 0.) || l.Beta() >= 1.) return -999.f;
  TLorentzVector b(parent.px, parent.py, parent.pz, parent.energy);
  TLorentzVector p(proton.px, proton.py, proton.pz, proton.energy);
  if (!(b.E() > 0.) || !(p.E() > 0.)) return -999.f;
  const auto boost = -l.BoostVector();
  b.Boost(boost);
  p.Boost(boost);
  const double denominator = b.P() * p.P();
  if (!(denominator > 0.) || !std::isfinite(denominator)) return -999.f;
  const double value = -b.Vect().Dot(p.Vect()) / denominator;
  return std::isfinite(value) ?
      static_cast<float>(std::max(-1., std::min(1., value))) : -999.f;
}

struct Result {
  int n_opposite_charge_pairs = 0;
  int n_pairs_nonprimary = 0;
  int n_pairs_d0_pass = 0;
  int n_pairs_raw_mass_pass = 0;
  int n_vertex_fits = 0;
  int n_tracks = 0;
  int n_photons = 0;
  int n_neutrals = 0;
  int n_lambdas_mass_window = 0;
  int n_lambdas_nonprimary_tracks = 0;
  int n_lambdas_track_displaced = 0;
  int n_lambdas_fit_valid = 0;
  int n_lambdas_fit_good = 0;
  int n_lambdas = 0;
  int n_lb_before_mass_window = 0;
  int n_lb_before_hemisphere = 0;
  int n_lb = 0;
  int pv_valid = 0, n_pv_tracks = 0;
  float pv_x = -999.f, pv_y = -999.f, pv_z = -999.f;
  float thrust_value = -999.f, thrust_x = -999.f;
  float thrust_y = -999.f, thrust_z = -999.f;

  // Lambda slots are ordered by unordered track pair, then hypothesis:
  // +1 denotes p+ pi-; -1 denotes pbar- pi+.
  std::vector<int> lambda_proton_index, lambda_pion_index, lambda_sign;
  std::vector<float> lambda_mass, lambda_pt;
  std::vector<float> lambda_px, lambda_py, lambda_pz, lambda_energy;
  // Fitted two-track vertex and its displacement from reconstructed PV, mm.
  // Sentinels are -999 when vertex or PV fit fails. No MC vertex is used.
  std::vector<int> lambda_vertex_valid, lambda_vertex_good;
  std::vector<int> lambda_vertex_primary;
  std::vector<float> lambda_vertex_x, lambda_vertex_y, lambda_vertex_z;
  std::vector<float> lambda_vertex_chi2, lambda_flight_rxy, lambda_flight_xyz;
  std::vector<float> lambda_proton_d0sig, lambda_pion_d0sig;
  std::vector<float> lambda_flight_rxy_sigma, lambda_flight_rxy_sig;
  std::vector<float> lambda_d0, lambda_d0_sigma, lambda_d0_sig;

  // All Lambda slots crossed with type-22 reconstructed photons. Configured
  // reconstruction uses only the selected Photon collection; baseline uses all.
  // Indices refer to the original ReconstructedParticles collection. The
  // Lambda slot links each Lambda_b candidate to its two-track hypothesis.
  std::vector<int> lb_lambda_slot, lb_proton_index, lb_pion_index;
  std::vector<int> lb_photon_index, lb_photon2_index, lb_sign;
  std::vector<float> lb_mass, lb_pt, lb_energy, lb_lambda_mass;
  std::vector<float> lb_px, lb_py, lb_pz;
  std::vector<float> lb_proton_px, lb_proton_py, lb_proton_pz, lb_proton_energy;
  std::vector<float> lb_pion_px, lb_pion_py, lb_pion_pz, lb_pion_energy;
  std::vector<float> lb_proton_d0, lb_pion_d0;
  // Fitted Lambda momentum, needed by candidate-level recoil and pointing.
  std::vector<float> lb_lambda_px, lb_lambda_py, lb_lambda_pz;
  // Measured photon four-vector from ReconstructedParticles, before any
  // candidate-level fit or derived isolation calculation.
  std::vector<float> lb_photon_px, lb_photon_py, lb_photon_pz;
  std::vector<float> lb_photon_energy, lb_photon2_energy;
  std::vector<float> lb_neutral_mass, lb_neutral_energy;
  // Fits use the chosen (anti)proton mass assignment and fitted-vertex
  // momentum. This angle is an observable, not a truth-based selection.
  std::vector<float> lb_cos_theta_p;
  std::vector<int> lb_same_hemisphere;
  std::vector<float> lb_lambda_thrust_cos, lb_neutral_thrust_cos;
};

struct Config {
  // Analysis choices, loaded from config/lb_reco*.json. Detector-response
  // assumptions live upstream in the Delphes card/EDM4hep production.
  double lambda_mass_gev = 1.115683;
  // Negative lower bound disables the window for the uncut baseline.
  double lambda_mass_min_gev = -1.;
  double lambda_mass_max_gev = -1.;
  // Optional preselection after the broad p/pi hypothesis choice and before
  // crossing accepted Lambda candidates with photons.
  double candidate_lambda_mass_min_gev = -1.;
  double candidate_lambda_mass_max_gev = -1.;
  bool choose_closest_hypothesis = false;
  double vertex_max_chi2 = 9.;
  double min_flight_rxy_mm = 0.;
  double min_track_d0sig = 0.;
  double min_vertex_flight_sig = 0.;
  bool require_good_vertex = false;
  // 22: direct photon; 221: eta made from an unordered photon pair.
  int neutral_pdg = 22;
  double neutral_mass_min_gev = -1.;
  double neutral_mass_max_gev = -1.;
  // Final Lambda_b fit interval; negative lower bound disables this cut.
  double lb_mass_min_gev = -1.;
  double lb_mass_max_gev = -1.;
  bool require_same_hemisphere = false;
  // Optional pre-fit guard using the original reconstructed track momenta.
  // Negative disables it; positive values are half-widths around Lambda mass.
  double raw_mass_prefilter_half_window_gev = -1.;
};

struct Neutral {
  int photon1 = -1, photon2 = -1;
  FourMomentum momentum;
  float mass_gev = 0.f;
  float photon1_energy = 0.f, photon2_energy = 0.f;
};

inline float d0_significance_at_pv(
    const edm4hep::TrackState& track,
    const VertexingUtils::FCCAnalysesVertex& pv) {
  // Linearized transverse impact parameter of the helix at the fitted PV.
  // Track D0 and its covariance use mm; the PV contribution is propagated
  // along the normal (-sin(phi), cos(phi)) to the track direction.
  const auto& pos = pv.vertex.position;
  const auto& cov = pv.vertex.covMatrix;
  const double s = std::sin(track.phi), c = std::cos(track.phi);
  const double d0 = track.D0 + pos.x * s - pos.y * c;
  // VertexFitterSimple writes [xx, yx, yy, zx, zy, zz] in this checkout.
  const double variance = track.covMatrix[0] + s * s * cov[0] -
                          2. * s * c * cov[1] + c * c * cov[2];
  return std::isfinite(variance) && variance > 0. && std::isfinite(d0) ?
      std::abs(d0) / std::sqrt(variance) : -999.f;
}

// One geometric fit per opposite-charge pair: its two fitted momenta are
// independent of which proton/pion masses are assigned afterwards. The
// ordering of updated_track_momentum_at_vertex follows the input track pair.
struct PairFit {
  bool linked = false, nonprimary = false, tracks_displaced = false;
  bool raw_mass_pass = true, fit_attempted = false;
  bool valid = false, good = false;
  int primary = -1;
  TVector3 plus_momentum, minus_momentum;
  float x = -999.f, y = -999.f, z = -999.f, chi2 = -999.f;
  float plus_d0 = -999.f, minus_d0 = -999.f;
  float plus_d0sig = -999.f, minus_d0sig = -999.f;
  float flight_rxy = -999.f, flight_xyz = -999.f;
  float flight_sigma = -999.f, flight_sig = -999.f;
  float lambda_d0 = -999.f, lambda_d0_sigma = -999.f;
  float lambda_d0_sig = -999.f;
};

inline PairFit fit_pair(
    const RVec<edm4hep::ReconstructedParticleData>& particles,
    const RVec<edm4hep::TrackState>& tracks,
    const VertexingUtils::FCCAnalysesVertex& pv,
    const RVec<bool>& primary_track_mask,
    int plus, int minus, const Config& config) {
  PairFit out;
  const auto plus_track = particles[plus].tracks_begin;
  const auto minus_track = particles[minus].tracks_begin;
  out.linked = plus_track < tracks.size() && minus_track < tracks.size() &&
               plus_track != minus_track;
  if (!out.linked) return out;
  out.nonprimary = plus_track < primary_track_mask.size() &&
                   minus_track < primary_track_mask.size() &&
                   !primary_track_mask[plus_track] &&
                   !primary_track_mask[minus_track];
  if (!out.nonprimary) return out;

  const auto signed_d0_at_pv = [&](const edm4hep::TrackState& track) {
    const auto& pos = pv.vertex.position;
    return static_cast<float>(track.D0 + pos.x * std::sin(track.phi) -
                              pos.y * std::cos(track.phi));
  };
  out.plus_d0 = signed_d0_at_pv(tracks[plus_track]);
  out.minus_d0 = signed_d0_at_pv(tracks[minus_track]);
  out.plus_d0sig = d0_significance_at_pv(tracks[plus_track], pv);
  out.minus_d0sig = d0_significance_at_pv(tracks[minus_track], pv);
  out.tracks_displaced = out.plus_d0sig >= config.min_track_d0sig &&
                         out.minus_d0sig >= config.min_track_d0sig;
  if (config.require_good_vertex && !out.tracks_displaced) return out;

  if (config.raw_mass_prefilter_half_window_gev >= 0.) {
    const auto plus_as_proton =
        with_mass(particles[plus], kProtonMass) +
        with_mass(particles[minus], kPionMass);
    const auto minus_as_proton =
        with_mass(particles[minus], kProtonMass) +
        with_mass(particles[plus], kPionMass);
    const double width = config.raw_mass_prefilter_half_window_gev;
    const double plus_mass = mass(plus_as_proton);
    const double minus_mass = mass(minus_as_proton);
    out.raw_mass_pass =
        (std::isfinite(plus_mass) &&
         std::abs(plus_mass - config.lambda_mass_gev) <= width) ||
        (std::isfinite(minus_mass) &&
         std::abs(minus_mass - config.lambda_mass_gev) <= width);
    if (!out.raw_mass_pass) return out;
  }

  RVec<edm4hep::TrackState> pair = {tracks[plus_track], tracks[minus_track]};
  out.fit_attempted = true;
  const auto fit = VertexFitterSimple::VertexFitter_Tk(2, pair);
  const auto& pos = fit.vertex.position;
  out.primary = fit.vertex.primary;
  out.chi2 = fit.vertex.chi2;
  const auto& updated = fit.updated_track_momentum_at_vertex;
  const auto finite_momentum = [](const TVector3& p) {
    return std::isfinite(p.Px()) && std::isfinite(p.Py()) &&
           std::isfinite(p.Pz());
  };
  out.valid = fit.ntracks == 2 && updated.size() == 2 &&
              std::isfinite(pos.x) && std::isfinite(pos.y) &&
              std::isfinite(pos.z) && std::isfinite(out.chi2) &&
              out.chi2 >= 0.f;
  if (!out.valid) return out;
  out.valid = finite_momentum(updated[0]) && finite_momentum(updated[1]);
  if (!out.valid) return out;
  out.plus_momentum = updated[0];
  out.minus_momentum = updated[1];
  out.x = pos.x; out.y = pos.y; out.z = pos.z;
  const auto& pv_pos = pv.vertex.position;
  const double dx = out.x - pv_pos.x, dy = out.y - pv_pos.y;
  const double dz = out.z - pv_pos.z;
  out.flight_rxy = std::hypot(dx, dy);
  out.flight_xyz = std::hypot(out.flight_rxy, dz);
  if (out.flight_rxy > 0.) {
    const auto& sc = fit.vertex.covMatrix;
    const auto& pc = pv.vertex.covMatrix;
    const double ux = dx / out.flight_rxy, uy = dy / out.flight_rxy;
    const double variance = ux * ux * (sc[0] + pc[0]) +
                            2. * ux * uy * (sc[1] + pc[1]) +
                            uy * uy * (sc[2] + pc[2]);
    if (std::isfinite(variance) && variance > 0.) {
      out.flight_sigma = std::sqrt(variance);
      out.flight_sig = out.flight_rxy / out.flight_sigma;
    }
  }
  // Linearized transverse impact parameter of the fitted Lambda flight line
  // relative to the PV. Use the fitted SV and the sum of independent PV/SV
  // xy vertex covariances; track-direction uncertainty is not propagated.
  const double lambda_px = out.plus_momentum.Px() + out.minus_momentum.Px();
  const double lambda_py = out.plus_momentum.Py() + out.minus_momentum.Py();
  const double lambda_pt = std::hypot(lambda_px, lambda_py);
  if (lambda_pt > 0.) {
    const double nx = lambda_py / lambda_pt;
    const double ny = -lambda_px / lambda_pt;
    out.lambda_d0 = static_cast<float>(dx * nx + dy * ny);
    const auto& sc = fit.vertex.covMatrix;
    const auto& pc = pv.vertex.covMatrix;
    const double variance = nx * nx * (sc[0] + pc[0]) +
        2. * nx * ny * (sc[1] + pc[1]) + ny * ny * (sc[2] + pc[2]);
    if (std::isfinite(variance) && variance > 0. && std::isfinite(out.lambda_d0)) {
      out.lambda_d0_sigma = static_cast<float>(std::sqrt(variance));
      out.lambda_d0_sig = out.lambda_d0 / out.lambda_d0_sigma;
    }
  }
  out.good = out.primary != 1 && out.chi2 <= config.vertex_max_chi2 &&
             out.flight_rxy >= config.min_flight_rxy_mm &&
             out.flight_sig >= config.min_vertex_flight_sig;
  return out;
}

inline Result build_impl(
    const RVec<edm4hep::ReconstructedParticleData>& particles,
    const RVec<edm4hep::TrackState>* tracks,
    const VertexingUtils::FCCAnalysesVertex* pv,
    const RVec<bool>* primary_track_mask,
    const RVec<int>* selected_photons,
    const RVec<float>* thrust,
    const Config& config) {
  Result out;
  if (thrust != nullptr && thrust->size() >= 4) {
    out.thrust_value = (*thrust)[0];
    out.thrust_x = (*thrust)[1];
    out.thrust_y = (*thrust)[2];
    out.thrust_z = (*thrust)[3];
  }
  if (pv != nullptr) {
    out.n_pv_tracks = pv->ntracks;
    const auto& pos = pv->vertex.position;
    out.pv_valid = pv->ntracks >= 2 && std::isfinite(pos.x) &&
                   std::isfinite(pos.y) && std::isfinite(pos.z);
    if (out.pv_valid) {
      out.pv_x = pos.x; out.pv_y = pos.y; out.pv_z = pos.z;
    }
  }
  std::vector<int> positive, negative, photons;
  // The sign split supports both Lambda_b and anti-Lambda_b. No PID or truth
  // identity is required: the two mass hypotheses are tested below.
  std::vector<bool> selected(particles.size(), selected_photons == nullptr);
  if (selected_photons != nullptr) {
    for (int index : *selected_photons)
      if (index >= 0 && static_cast<size_t>(index) < selected.size())
        selected[index] = true;
  }
  for (size_t i = 0; i < particles.size(); ++i) {
    const auto& p = particles[i];
    if (p.charge > 0.5f && p.tracks_end > p.tracks_begin)
      positive.push_back(static_cast<int>(i));
    else if (p.charge < -0.5f && p.tracks_end > p.tracks_begin)
      negative.push_back(static_cast<int>(i));
    else if (p.type == 22 && p.charge == 0.f && selected[i])
      photons.push_back(static_cast<int>(i));
  }
  out.n_tracks = static_cast<int>(positive.size() + negative.size());
  out.n_photons = static_cast<int>(photons.size());
  std::vector<Neutral> neutrals;
  // photons here have been filled only by == 22 inputs PDGID.
  for (size_t i = 0; i < photons.size(); ++i) {
    const int first = photons[i];
    const auto first_p4 = measured_photon(particles[first]);
    if (config.neutral_pdg == 22) {
      // what is the -1 here for neutrals ? 
      neutrals.push_back({first, -1, first_p4, mass(first_p4),
                          particles[first].energy, 0.f});
    } else if (config.neutral_pdg == 221) {
      // Full eta -> gamma gamma diagnostic. This is distinct from running the
      // one-photon signal builder on eta-generated events, where one photon
      // can be missing and the Lambda_b mass is partially reconstructed.
      // TODO : not 100% sure what this would do, the pi0 and eta veto is in principle something we do offline only? 
      // Why we woul dhave in the 
      for (size_t j = i + 1; j < photons.size(); ++j) {
        const int second = photons[j];
        const auto pair_p4 = first_p4 + measured_photon(particles[second]);
        const float pair_mass = mass(pair_p4);
        if (config.neutral_mass_min_gev >= 0. &&
            (pair_mass < config.neutral_mass_min_gev ||
             pair_mass > config.neutral_mass_max_gev)) continue;
        neutrals.push_back({first, second, pair_p4, pair_mass,
                            particles[first].energy, particles[second].energy});
      }
    }
  }
  out.n_neutrals = static_cast<int>(neutrals.size());

  // Fit once before evaluating the proton/pion masses. In configured runs,
  // all mass decisions use momenta at the fitted Lambda0 vertex. The uncut
  // baseline has no track collection and retains its raw-momentum definition.
  for (int plus : positive) {
    for (int minus : negative) {
      ++out.n_opposite_charge_pairs;
      // this part in principle can be made much faster as we are in principle already able to tell "which vertex is not primary" and have 2 daughters      
      PairFit pair_fit;
      const bool fitted = tracks != nullptr && pv != nullptr &&
                          primary_track_mask != nullptr;
      if (fitted) {
        pair_fit = fit_pair(particles, *tracks, *pv, *primary_track_mask,
                            plus, minus, config);
        if (pair_fit.nonprimary) ++out.n_pairs_nonprimary;
        if (pair_fit.nonprimary && pair_fit.tracks_displaced)
          ++out.n_pairs_d0_pass;
        if (pair_fit.nonprimary && pair_fit.tracks_displaced &&
            pair_fit.raw_mass_pass)
          ++out.n_pairs_raw_mass_pass;
        if (pair_fit.fit_attempted) ++out.n_vertex_fits;
        if (!pair_fit.nonprimary || !pair_fit.valid ||
            (config.require_good_vertex && !pair_fit.good)) continue;
      }
      const FourMomentum plus_as_proton = fitted ?
          with_mass(pair_fit.plus_momentum, kProtonMass) +
          with_mass(pair_fit.minus_momentum, kPionMass) :
          with_mass(particles[plus], kProtonMass) +
          with_mass(particles[minus], kPionMass);
      const FourMomentum minus_as_proton = fitted ?
          with_mass(pair_fit.minus_momentum, kProtonMass) +
          with_mass(pair_fit.plus_momentum, kPionMass) :
          with_mass(particles[minus], kProtonMass) +
          with_mass(particles[plus], kPionMass);
      const float plus_mass = mass(plus_as_proton);
      const float minus_mass = mass(minus_as_proton);
      const auto in_window = [&](float m) {
        return config.lambda_mass_min_gev < 0. ||
               (m >= config.lambda_mass_min_gev && m <= config.lambda_mass_max_gev);
      };
      const bool plus_ok = in_window(plus_mass), minus_ok = in_window(minus_mass);
      if (!plus_ok && !minus_ok) continue;
      // Choose only among hypotheses that pass the broad window. Equal
      // absolute differences resolve deterministically to p+ pi-. This is an
      // analysis mass assignment, not a proton/pion identification decision.
      const int closest_sign = !minus_ok || (plus_ok &&
          std::abs(plus_mass - config.lambda_mass_gev) <=
          std::abs(minus_mass - config.lambda_mass_gev)) ? +1 : -1;
      for (int sign : {+1, -1}) {
        if (sign > 0 ? !plus_ok : !minus_ok) continue;
        if (config.choose_closest_hypothesis && sign != closest_sign) continue;
        const int proton = sign > 0 ? plus : minus;
        const int pion = sign > 0 ? minus : plus;
        const FourMomentum lambda = sign > 0 ? plus_as_proton : minus_as_proton;
        const float lm = mass(lambda);
        if (config.candidate_lambda_mass_min_gev >= 0. &&
            (lm < config.candidate_lambda_mass_min_gev ||
             lm > config.candidate_lambda_mass_max_gev)) continue;
        ++out.n_lambdas_mass_window;
        if (fitted) {
          ++out.n_lambdas_nonprimary_tracks;
          if (pair_fit.tracks_displaced) ++out.n_lambdas_track_displaced;
          ++out.n_lambdas_fit_valid;
          if (pair_fit.good) ++out.n_lambdas_fit_good;
        }
        const float p_d0sig = sign > 0 ? pair_fit.plus_d0sig : pair_fit.minus_d0sig;
        const float pi_d0sig = sign > 0 ? pair_fit.minus_d0sig : pair_fit.plus_d0sig;
        const float p_d0 = sign > 0 ? pair_fit.plus_d0 : pair_fit.minus_d0;
        const float pi_d0 = sign > 0 ? pair_fit.minus_d0 : pair_fit.plus_d0;
        const int lambda_slot = out.n_lambdas++;
        out.lambda_proton_index.push_back(proton);
        out.lambda_pion_index.push_back(pion);
        out.lambda_sign.push_back(sign);
        out.lambda_mass.push_back(lm);
        out.lambda_pt.push_back(pt(lambda));
        out.lambda_px.push_back(lambda.px);
        out.lambda_py.push_back(lambda.py);
        out.lambda_pz.push_back(lambda.pz);
        out.lambda_energy.push_back(lambda.energy);
        out.lambda_vertex_valid.push_back(pair_fit.valid);
        out.lambda_vertex_good.push_back(pair_fit.good);
        out.lambda_vertex_primary.push_back(pair_fit.primary);
        out.lambda_vertex_x.push_back(pair_fit.x);
        out.lambda_vertex_y.push_back(pair_fit.y);
        out.lambda_vertex_z.push_back(pair_fit.z);
        out.lambda_vertex_chi2.push_back(pair_fit.chi2);
        out.lambda_flight_rxy.push_back(pair_fit.flight_rxy);
        out.lambda_flight_xyz.push_back(pair_fit.flight_xyz);
        out.lambda_proton_d0sig.push_back(p_d0sig);
        out.lambda_pion_d0sig.push_back(pi_d0sig);
        out.lambda_flight_rxy_sigma.push_back(pair_fit.flight_sigma);
        out.lambda_flight_rxy_sig.push_back(pair_fit.flight_sig);
        out.lambda_d0.push_back(pair_fit.lambda_d0);
        out.lambda_d0_sigma.push_back(pair_fit.lambda_d0_sigma);
        out.lambda_d0_sig.push_back(pair_fit.lambda_d0_sig);

        for (const auto& neutral : neutrals) {
          // Keep every surviving combination, including wrong photons. A
          // future pi0/eta veto or event-level feature must be measured as a
          // separate step using these original reconstructed-particle indices.
          const FourMomentum lb = lambda + neutral.momentum;
          const float lbm = mass(lb);
          ++out.n_lb_before_mass_window;
          if (config.lb_mass_min_gev >= 0. &&
              (lbm < config.lb_mass_min_gev ||
               lbm > config.lb_mass_max_gev)) continue;
          ++out.n_lb_before_hemisphere;
          const float lambda_cos = thrust == nullptr ? -999.f :
              thrust_cosine(lambda, *thrust);
          const float neutral_cos = thrust == nullptr ? -999.f :
              thrust_cosine(neutral.momentum, *thrust);
          const bool same_hemisphere = lambda_cos != -999.f &&
              neutral_cos != -999.f && lambda_cos * neutral_cos > 0.f;
          if (config.require_same_hemisphere && !same_hemisphere) continue;
          out.lb_lambda_slot.push_back(lambda_slot);
          out.lb_proton_index.push_back(proton);
          out.lb_pion_index.push_back(pion);
          out.lb_photon_index.push_back(neutral.photon1);
          out.lb_photon2_index.push_back(neutral.photon2);
          out.lb_sign.push_back(sign);
          out.lb_mass.push_back(lbm);
          out.lb_pt.push_back(pt(lb));
          out.lb_energy.push_back(static_cast<float>(lb.energy));
          out.lb_px.push_back(static_cast<float>(lb.px));
          out.lb_py.push_back(static_cast<float>(lb.py));
          out.lb_pz.push_back(static_cast<float>(lb.pz));
          out.lb_lambda_mass.push_back(lm);
          out.lb_lambda_px.push_back(lambda.px);
          out.lb_lambda_py.push_back(lambda.py);
          out.lb_lambda_pz.push_back(lambda.pz);
          const auto photon_p4 = measured_photon(particles[neutral.photon1]);
          out.lb_photon_px.push_back(photon_p4.px);
          out.lb_photon_py.push_back(photon_p4.py);
          out.lb_photon_pz.push_back(photon_p4.pz);
          out.lb_photon_energy.push_back(neutral.photon1_energy);
          out.lb_photon2_energy.push_back(neutral.photon2_energy);
          out.lb_neutral_mass.push_back(neutral.mass_gev);
          out.lb_neutral_energy.push_back(static_cast<float>(neutral.momentum.energy));
          const FourMomentum proton_p4 = fitted ?
              with_mass(sign > 0 ? pair_fit.plus_momentum :
                                   pair_fit.minus_momentum, kProtonMass) :
              with_mass(particles[proton], kProtonMass);
          const FourMomentum pion_p4 = fitted ?
              with_mass(sign > 0 ? pair_fit.minus_momentum :
                                   pair_fit.plus_momentum, kPionMass) :
              with_mass(particles[pion], kPionMass);
          out.lb_proton_px.push_back(static_cast<float>(proton_p4.px));
          out.lb_proton_py.push_back(static_cast<float>(proton_p4.py));
          out.lb_proton_pz.push_back(static_cast<float>(proton_p4.pz));
          out.lb_proton_energy.push_back(static_cast<float>(proton_p4.energy));
          out.lb_pion_px.push_back(static_cast<float>(pion_p4.px));
          out.lb_pion_py.push_back(static_cast<float>(pion_p4.py));
          out.lb_pion_pz.push_back(static_cast<float>(pion_p4.pz));
          out.lb_pion_energy.push_back(static_cast<float>(pion_p4.energy));
          out.lb_proton_d0.push_back(p_d0);
          out.lb_pion_d0.push_back(pi_d0);
          out.lb_cos_theta_p.push_back(cos_theta_p(lb, lambda, proton_p4));
          out.lb_same_hemisphere.push_back(same_hemisphere);
          out.lb_lambda_thrust_cos.push_back(lambda_cos);
          out.lb_neutral_thrust_cos.push_back(neutral_cos);
          ++out.n_lb;
        }
      }
    }
  }
  return out;
}

inline Result build(const RVec<edm4hep::ReconstructedParticleData>& particles,
                    const Config& config = {}) {
  return build_impl(particles, nullptr, nullptr, nullptr, nullptr, nullptr,
                    config);
}

inline Result build(const RVec<edm4hep::ReconstructedParticleData>& particles,
                    const RVec<int>& selected_photons,
                    const Config& config) {
  return build_impl(particles, nullptr, nullptr, nullptr,
                    &selected_photons, nullptr, config);
}

// most complete call for building the Result struct!
inline Result build(const RVec<edm4hep::ReconstructedParticleData>& particles,
                    const RVec<edm4hep::TrackState>& tracks,
                    const VertexingUtils::FCCAnalysesVertex& pv,
                    const RVec<bool>& primary_track_mask,
                    const RVec<int>& selected_photons,
                    const RVec<float>& thrust,
                    const Config& config) {
  return build_impl(particles, &tracks, &pv, &primary_track_mask,
                    &selected_photons, &thrust, config);
}

}  // namespace FCCAnalyses::LbCandidateBuilder

#endif
