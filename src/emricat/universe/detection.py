"""
STEP 5 -- Detection criterion  (TO BE DEFINED, slide 14 footnote).

Interface
---------
    f(events: Catalogue, rng, **params) -> (snr: array, detected: int8 array)

Ideas for later
---------------
* Simple threshold on a fitting formula for the EMRI SNR as a function of
  MBH mass, redshift (luminosity distance) and spin (e.g. Babak+17 style
  horizon curves), with SNR >= 20.
* Full waveform-based SNR (FastEMRIWaveforms) on a subsample, to calibrate
  the fitting formula.
Additional event parameters (CO mass, eccentricity, inclination, sky
position, plunge time within the mission...) would be drawn here too.
"""

from __future__ import annotations

import numpy as np

from emricat.catalogue import Catalogue


def detection_none(events: Catalogue, rng=None, **_):
    """Keep every event (SNR unknown)."""
    n = len(events)
    return np.full(n, np.nan), np.ones(n, dtype=np.int8)


def detection_snr_threshold(events: Catalogue, rng=None, snr_threshold: float = 20.0, **params):
    """SNR from a fitting formula + threshold.

    TODO (coordinators / later): choose the SNR model. Needs at least
    ``mbh_mass`` and ``event_redshift`` (-> luminosity distance via
    emricat.cosmology.luminosity_distance).
    """
    raise NotImplementedError("detection_snr_threshold: detection criterion still to be defined")


#: Registry: config key ``universe.detection`` -> function.
DETECTION_MODELS = {
    "none": detection_none,
    "snr_threshold": detection_snr_threshold,
}
