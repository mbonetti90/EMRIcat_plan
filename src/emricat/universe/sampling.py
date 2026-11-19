"""
STEP 5 -- From rates to discrete events (slide 14, points 5-6).

First-version assumptions (slide 14 footnote):
* the rate is constant over the mission;
* the time spent in band and non-plunging EMRIs are ignored;
* detection criterion (SNR) to be defined (see detection.py).
"""

from __future__ import annotations

import numpy as np

from emricat import cosmology
from emricat.catalogue import Catalogue


def expected_emris(rate, t_obs: float, redshift, weight=1.0):
    """Expected number of EMRIs observed during the mission.

        lambda = weight * Gamma * T_obs / (1 + z)

    Gamma is the source-frame rate [1/yr], T_obs the observer-frame mission
    duration [yr]; (1+z) because clocks at z tick slower for us.
    ``weight`` is the number of real galaxies the replica stands for.
    """
    return np.asarray(weight) * np.asarray(rate) * t_obs / (1.0 + np.asarray(redshift))


def draw_events(cat: Catalogue, t_obs: float, rng: np.random.Generator) -> Catalogue:
    """Add ``n_emri_expected`` and the Poisson-drawn ``n_emri`` to ``cat`` (in place)."""
    cat.require(["emri_rate", "redshift"], who="draw_events")
    weight = cat["replica_weight"] if "replica_weight" in cat else 1.0
    lam = expected_emris(cat["emri_rate"], t_obs, cat["redshift"], weight)
    cat["n_emri_expected"] = lam
    cat["n_emri"] = rng.poisson(lam).astype(np.int64)
    return cat


def assign_event_redshifts(events: Catalogue, shells, method: str, rng: np.random.Generator) -> Catalogue:
    """Give each event a redshift (column ``event_redshift``).

    * "snapshot": the snapshot redshift (simplest; creates spikes in z).
    * "uniform_in_volume": uniform in comoving volume inside the shell, so the
      redshift distribution of the catalogue is smooth.
      NOTE: the (1+z) factor and the rate were computed at the snapshot z;
      this is consistent only if shells are thin (the whole point of denser snapshots).
    """
    z = events["redshift"].copy()
    if method == "uniform_in_volume":
        for sh in shells:
            sel = np.isclose(events["redshift"], sh.z)
            if np.any(sel):
                z[sel] = cosmology.sample_redshift_uniform_in_volume(sh.z_lo, sh.z_hi, sel.sum(), rng)
    elif method != "snapshot":
        raise ValueError(f"Unknown event_redshift method '{method}'.")
    events["event_redshift"] = z
    return events


def expand_multiple_events(events: Catalogue) -> Catalogue:
    """One row per EMRI: rows with n_emri = k > 1 are repeated k times.

    Rare (lambda << 1) but possible, especially with large replica weights.
    """
    return events.repeat(events["n_emri"])
