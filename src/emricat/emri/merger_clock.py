"""
GROUP 3 -- Merger clock: time between major mergers and time since the last one.

Context (slides 9-10)
---------------------
A snapshot gives a galaxy at one cosmic time, but not when its last major
merger happened (which resets the NSC and restarts the Broggi+22 curve).
So for every replica we

1. draw the time between two successive major mergers, Delta_t, from the
   distribution measured on merger trees as a function of stellar mass,
   redshift (and mass ratio) -- task of A. Trinca;
2. draw the time since the last merger, t, inside that interval.

Observations and models agree on <Delta_t> ~ 2 Gyr at z = 0, ~ 0.5 Gyr at
z ~ 2, with a model spread of about x2 (D. Roberts' review, slide 10).

Interface
---------
Merger clocks:  f(stellar_mass [Msun], redshift, rng, **params) -> Delta_t [yr]

NOTE FOR DISCUSSION: the "inspection paradox"
---------------------------------------------
If intervals between mergers follow p(Delta_t), the interval that *contains
a randomly chosen observation time* is NOT distributed as p(Delta_t): longer
intervals are more likely to be "hit". It follows the length-biased
distribution  Delta_t p(Delta_t) / <Delta_t>.  For an exponential (Poisson
process) p, this doubles the mean interval. Option ``time_since_merger:
"length_biased"`` is a placeholder for this choice: whoever implements the
merger-tree clock should decide whether the tabulated distribution is
already "as seen at a random time" or "per merger".
"""

from __future__ import annotations

import numpy as np

from emricat import mock
from emricat.cosmology import cosmic_time


def merger_clock_from_trees(stellar_mass, redshift, rng, table_path: str = "", **params):
    """Draw Delta_t from the merger-tree distribution (A. Trinca).  BASELINE.

    Planned implementation:
      * a pre-computed table (HDF5) of the distribution of Delta_t in bins of
        (log M_*, z, mass-ratio threshold) produced by a merger-tree generator;
      * here: locate the bin of each replica and draw from the tabulated
        CDF by inverse-transform sampling (vectorised over bins).

    Parameters
    ----------
    stellar_mass : array [Msun]
    redshift : array
    rng : numpy.random.Generator
    table_path : str     path to the pre-computed distribution table

    Returns
    -------
    delta_t : array [yr]
    """
    # TODO (Group 3 / A. Trinca)
    raise NotImplementedError("Group 3: merger_clock_from_trees")


def merger_clock_observational(stellar_mass, redshift, rng, t0: float = 2.0e9, slope: float = 1.2, **params):
    """Simple interim clock: exponential intervals with mean t0 / (1+z)^slope.

    Defaults roughly follow slide 10 (2 Gyr at z=0 -> ~0.5 Gyr at z=2).
    Useful as a cross-check of the merger-tree clock.

    TODO (Group 3): calibrate t0, slope (and possibly a mass dependence) on
    the observational compilation of slide 10.
    """
    raise NotImplementedError("Group 3: merger_clock_observational")


#: Registry: config key ``emri.merger_clock`` -> function.
MERGER_CLOCKS = {
    "merger_trees": merger_clock_from_trees,
    "observational": merger_clock_observational,
    "toy": mock.toy_merger_interval,  # TESTING ONLY
}


def draw_time_since_merger(delta_t, redshift, rng, method: str = "uniform"):
    """Time elapsed since the last major merger [yr] (slide 9).

    Parameters
    ----------
    delta_t : array [yr]       interval between mergers (already drawn)
    redshift : array           used to cap t at the age of the Universe
    rng : numpy.random.Generator
    method : {"uniform", "length_biased"}
        "uniform": t ~ U(0, delta_t), as on slide 9.
        "length_biased": see module docstring. Here it only changes how
        delta_t should have been drawn, so it is handled by the clock; this
        function raises until that is implemented.

    Returns
    -------
    t_since : array [yr]

    The result is capped at the age of the Universe at the replica's redshift
    (an interval longer than the age means "no major merger yet": the NSC is
    then as old as the galaxy). TO BE DISCUSSED.
    """
    if method == "length_biased":
        # TODO (Group 3): decide if/how to implement the length-biased sampling.
        raise NotImplementedError("Group 3: length-biased time since merger")
    if method != "uniform":
        raise ValueError(f"Unknown method '{method}'.")
    t_since = rng.uniform(size=np.shape(delta_t)) * np.asarray(delta_t)
    # Age of the Universe, computed only for the distinct redshifts (astropy is slow on big arrays).
    z_unique, inverse = np.unique(np.asarray(redshift), return_inverse=True)
    age = np.atleast_1d(cosmic_time(z_unique))[inverse]
    return np.minimum(t_since, age)
