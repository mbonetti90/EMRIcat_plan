"""
GROUP 1 -- Utilities for the snapshot redshift grid.

Context (slide 4): today we only have z = 0, 1, 2, 5. The method needs
snapshots dense enough (every 50-100 Myr) that each one represents a thin
slice of cosmic time. Model owners will be asked to re-run with denser
outputs. Until then, the code must work with whatever grid exists, and
should *tell us* how coarse it is.
"""

from __future__ import annotations

import numpy as np

from emricat.cosmology import cosmic_time, get_cosmology
from emricat.units import MYR


def snapshot_spacing(redshifts, cosmo=None) -> np.ndarray:
    """Cosmic time between consecutive snapshots [yr] (array of length n-1)."""
    z = np.sort(np.asarray(redshifts, dtype=float))
    t = cosmic_time(z, cosmo or get_cosmology())
    return np.abs(np.diff(t))


def spacing_report(redshifts, target_dt: float = 100 * MYR, cosmo=None) -> str:
    """Human-readable table of the snapshot spacing vs the target spacing."""
    z = np.sort(np.asarray(redshifts, dtype=float))
    dt = snapshot_spacing(z, cosmo)
    lines = [f"{'z_i':>6} {'z_i+1':>6} {'dt [Myr]':>10}  status"]
    for a, b, d in zip(z[:-1], z[1:], dt):
        flag = "ok" if d <= target_dt else f"TOO COARSE (x{d / target_dt:.0f})"
        lines.append(f"{a:6.2f} {b:6.2f} {d / MYR:10.0f}  {flag}")
    return "\n".join(lines)


def interpolate_population(cat_lo, cat_hi, z_target, rng):
    """OPTIONAL / INTERIM: build a population at an intermediate redshift.

    Only needed if denser snapshots are not available in time. Possible
    approaches (to be discussed before implementing!):

    * abundance-matching style: interpolate the *distributions*
      (e.g. the joint M_bh-M_* PDF and the mass function) in log(1+z) and
      resample galaxies from the interpolated PDF;
    * nearest-snapshot: simply reuse the closest snapshot (crude, but honest).

    Parameters
    ----------
    cat_lo, cat_hi : Catalogue
        Snapshots bracketing ``z_target``.
    z_target : float
    rng : numpy.random.Generator

    Returns
    -------
    Catalogue with REQUIRED_GROUP1 columns at ``z_target``.
    """
    # TODO (Group 1): only if we decide we need it.
    raise NotImplementedError("Group 1: interpolate_population (interim solution, to be discussed)")
