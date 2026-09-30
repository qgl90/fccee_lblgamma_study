"""Read FCCAnalyses response ntuples using uproot and awkward arrays."""

from dataclasses import dataclass
from pathlib import Path

import awkward as ak
import numpy as np
import uproot


BRANCHES = [
    "track_truth_p", "track_truth_pt", "track_truth_eta", "track_truth_rxy", "track_matched",
    "track_reco_pt", "track_dp_rel", "track_dpt_rel", "track_dqoverpt",
    "gamma_truth_e", "gamma_truth_eta",
    "gamma_matched", "gamma_selected", "gamma_reco_e", "gamma_dE_rel",
]


@dataclass
class ResolutionSample:
    events_read: int
    track_truth_pt: np.ndarray
    track_truth_eta: np.ndarray
    track_truth_rxy: np.ndarray
    track_truth_matched: np.ndarray
    track_p: np.ndarray
    track_pt: np.ndarray
    track_eta: np.ndarray
    track_rxy: np.ndarray
    track_reco_pt: np.ndarray
    track_dp_rel: np.ndarray
    track_dpt_rel: np.ndarray
    track_dqoverpt: np.ndarray
    gamma_truth_e: np.ndarray
    gamma_truth_eta: np.ndarray
    gamma_truth_matched: np.ndarray
    gamma_truth_selected: np.ndarray
    gamma_e: np.ndarray
    gamma_eta: np.ndarray
    gamma_reco_e: np.ndarray
    gamma_dE_rel: np.ndarray
    gamma_selected: np.ndarray


def _flat(array):
    return ak.to_numpy(ak.flatten(array, axis=1))


def load_sample(path: str | Path, target_pairs: int = 200_000,
                chunk_events: int = 1_000) -> ResolutionSample:
    """Read events until both matched categories reach target_pairs.

    Input events are used in file order. The two matched arrays are then trimmed
    independently to exactly target_pairs; truth arrays retain every read event
    so efficiency denominators remain event-complete.
    """
    if target_pairs <= 0 or chunk_events <= 0:
        raise ValueError("target_pairs and chunk_events must be positive")

    pieces = {name: [] for name in ResolutionSample.__dataclass_fields__
              if name != "events_read"}
    events_read = 0
    n_tracks = n_photons = 0
    # Explicit MemmapSource avoids the fsspec async reader used by some CERN
    # Python environments, while all branch decoding stays in uproot.
    with uproot.open(str(path), handler=uproot.source.file.MemmapSource) as root:
        tree = root["events"]
        for chunk in tree.iterate(BRANCHES, library="ak", step_size=chunk_events):
            events_read += len(chunk)
            track_match = chunk["track_matched"] == 1
            gamma_match = chunk["gamma_matched"] == 1

            pieces["track_truth_pt"].append(_flat(chunk["track_truth_pt"]))
            pieces["track_truth_eta"].append(_flat(chunk["track_truth_eta"]))
            pieces["track_truth_rxy"].append(_flat(chunk["track_truth_rxy"]))
            pieces["track_truth_matched"].append(_flat(chunk["track_matched"]))
            pieces["gamma_truth_e"].append(_flat(chunk["gamma_truth_e"]))
            pieces["gamma_truth_eta"].append(_flat(chunk["gamma_truth_eta"]))
            pieces["gamma_truth_matched"].append(_flat(chunk["gamma_matched"]))
            pieces["gamma_truth_selected"].append(_flat(chunk["gamma_selected"]))

            if n_tracks < target_pairs:
                for target, branch in [
                    ("track_p", "track_truth_p"),
                    ("track_pt", "track_truth_pt"),
                    ("track_eta", "track_truth_eta"),
                    ("track_rxy", "track_truth_rxy"),
                    ("track_reco_pt", "track_reco_pt"),
                    ("track_dp_rel", "track_dp_rel"),
                    ("track_dpt_rel", "track_dpt_rel"),
                    ("track_dqoverpt", "track_dqoverpt"),
                ]:
                    pieces[target].append(_flat(chunk[branch][track_match]))
                n_tracks += len(pieces["track_pt"][-1])

            if n_photons < target_pairs:
                for target, branch in [
                    ("gamma_e", "gamma_truth_e"),
                    ("gamma_eta", "gamma_truth_eta"),
                    ("gamma_reco_e", "gamma_reco_e"),
                    ("gamma_dE_rel", "gamma_dE_rel"),
                    ("gamma_selected", "gamma_selected"),
                ]:
                    pieces[target].append(_flat(chunk[branch][gamma_match]))
                n_photons += len(pieces["gamma_e"][-1])

            if n_tracks >= target_pairs and n_photons >= target_pairs:
                break

    if events_read == 0:
        raise ValueError(f"No events in {path}")
    arrays = {name: np.concatenate(parts) if parts else np.array([])
              for name, parts in pieces.items()}
    for name in ["track_p", "track_pt", "track_eta", "track_rxy", "track_reco_pt",
                 "track_dp_rel", "track_dpt_rel", "track_dqoverpt",
                 "gamma_e", "gamma_eta", "gamma_reco_e", "gamma_dE_rel", "gamma_selected"]:
        arrays[name] = arrays[name][:target_pairs]
    return ResolutionSample(events_read=events_read, **arrays)
