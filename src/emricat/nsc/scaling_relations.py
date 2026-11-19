"""
GROUP 2 -- NSC scaling relations (slide 5).

* Mass:   M_NSC(M_*)   -- adopted: Hoyer+23 (single power law at all masses).
          Alternatives kept for comparison plots: Scott & Graham 13,
          Neumayer+20, Pechetti+20.
* Radius: R_eff(M_NSC) -- adopted: Pechetti+20, R_eff ~ M_NSC^0.33.
* Scatter: log-normal around both relations (to be added, slide 5).

Interface
---------
Mass relations:    f(stellar_mass [Msun], **params) -> median M_NSC [Msun]
Radius relations:  f(nsc_mass [Msun], **params)     -> median R_eff [pc]

All relations return the *median* (no scatter). The scatter is applied in
one place, :func:`lognormal_scatter`, so that every relation is treated in
the same way.

TIP: write relations as  log10 Y = a + b * (log10 X - x0)  and put a, b, x0
as keyword defaults with the paper's values, citing the equation/table.
"""

from __future__ import annotations

import numpy as np

from emricat import mock


# ----------------------------------------------------------------------
# Mass relations  M_NSC(M_*)
# ----------------------------------------------------------------------
def nsc_mass_hoyer23(stellar_mass, **params):
    """Hoyer et al. 2023: single power law M_NSC(M_*).  ADOPTED BASELINE.

    TODO (Group 2): give equation number, slope, intercept, pivot and the
    intrinsic scatter (to be used as the default ``nsc.mass_scatter_dex``).
    Port from Caleno & Zana's implementation.
    """
    raise NotImplementedError("Group 2: nsc_mass_hoyer23")


def nsc_mass_neumayer20(stellar_mass, **params):
    """Neumayer, Seth & Boeker 2020 relation (for comparison)."""
    raise NotImplementedError("Group 2: nsc_mass_neumayer20")


def nsc_mass_scott13(stellar_mass, **params):
    """Scott & Graham 2013 relation (for comparison)."""
    raise NotImplementedError("Group 2: nsc_mass_scott13")


def nsc_mass_pechetti20(stellar_mass, **params):
    """Pechetti et al. 2020 M_NSC(M_*) relation (for comparison)."""
    raise NotImplementedError("Group 2: nsc_mass_pechetti20")


#: Registry: config key ``nsc.mass_relation`` -> function.
MASS_RELATIONS = {
    "hoyer23": nsc_mass_hoyer23,
    "neumayer20": nsc_mass_neumayer20,
    "scott13": nsc_mass_scott13,
    "pechetti20": nsc_mass_pechetti20,
    "toy": mock.toy_nsc_mass,  # TESTING ONLY
}


# ----------------------------------------------------------------------
# Radius relations  R_eff(M_NSC)
# ----------------------------------------------------------------------
def nsc_radius_pechetti20(nsc_mass, **params):
    """Pechetti et al. 2020: R_eff proportional to M_NSC^0.33.  ADOPTED BASELINE.

    Slide 5 quotes "about 2 pc at 1e8 Msun" -- please double check the
    normalisation against the paper (it looks small for such a massive NSC).
    """
    raise NotImplementedError("Group 2: nsc_radius_pechetti20")


#: Registry: config key ``nsc.radius_relation`` -> function.
RADIUS_RELATIONS = {
    "pechetti20": nsc_radius_pechetti20,
    "toy": mock.toy_nsc_radius,  # TESTING ONLY
}


# ----------------------------------------------------------------------
# Scatter
# ----------------------------------------------------------------------
def lognormal_scatter(median, scatter_dex: float, rng: np.random.Generator):
    """Draw values log-normally distributed around ``median``.

        log10 Y = log10 median + N(0, scatter_dex)

    With ``scatter_dex = 0`` the median is returned unchanged (no random
    numbers consumed). Note this keeps the *median* fixed, so the *mean* of Y
    increases with the scatter; that is the usual convention for observed
    relations fitted in log space.
    """
    median = np.asarray(median, dtype=float)
    if scatter_dex <= 0:
        return median.copy()
    return median * 10 ** rng.normal(0.0, scatter_dex, size=median.shape)
