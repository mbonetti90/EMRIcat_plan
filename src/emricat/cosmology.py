"""
Thin wrapper around :mod:`astropy.cosmology` returning plain numbers in
EMRICat internal units (cMpc, yr; see :mod:`emricat.units`).

Everything cosmological goes through this module, so that switching
cosmology (e.g. to the one used by a given simulation) is a one-line change.

NOTE (to discuss): each MBHcat model was run with its own cosmology
(TNG: Planck15, Horizon-AGN: WMAP7, ...). The box volume and number densities
come from the model, while shell volumes are computed here. The mismatch is
small (few %), but for consistency we may want to use each model's own
cosmology. ``get_cosmology`` accepts any astropy built-in name.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from astropy import cosmology as _apcosmo
from astropy import units as u

from emricat.units import C_PC_YR, GYR, MPC

DEFAULT_COSMOLOGY = "Planck18"


@lru_cache(maxsize=None)
def get_cosmology(name: str = DEFAULT_COSMOLOGY):
    """Return an astropy cosmology object by name (e.g. 'Planck18', 'Planck15', 'WMAP7')."""
    return getattr(_apcosmo, name)


# ----------------------------------------------------------------------
# Basic distances and times
# ----------------------------------------------------------------------
def comoving_distance(z, cosmo=None):
    """Line-of-sight comoving distance D_c(z) [cMpc]."""
    cosmo = cosmo or get_cosmology()
    return np.asarray(cosmo.comoving_distance(z).to_value(u.Mpc))


def luminosity_distance(z, cosmo=None):
    """Luminosity distance D_L(z) [Mpc] (needed later for SNR)."""
    cosmo = cosmo or get_cosmology()
    return np.asarray(cosmo.luminosity_distance(z).to_value(u.Mpc))


def cosmic_time(z, cosmo=None):
    """Age of the Universe at redshift z [yr]."""
    cosmo = cosmo or get_cosmology()
    return np.asarray(cosmo.age(z).to_value(u.Gyr)) * GYR


def redshift_at_cosmic_time(t, cosmo=None):
    """Inverse of :func:`cosmic_time`: redshift at which the Universe has age t [yr]."""
    cosmo = cosmo or get_cosmology()
    t = np.atleast_1d(t)
    z = np.array([_apcosmo.z_at_value(cosmo.age, ti / GYR * u.Gyr).value for ti in t])
    return z if z.size > 1 else z[0]


def hubble_parameter(z, cosmo=None):
    """H(z) in [km/s/Mpc]."""
    cosmo = cosmo or get_cosmology()
    return np.asarray(cosmo.H(z).to_value(u.km / u.s / u.Mpc))


# ----------------------------------------------------------------------
# Shells around a snapshot (Step 4, slide 13)
# ----------------------------------------------------------------------
def shell_volume_exact(z_lo, z_hi, cosmo=None):
    """Full-sky comoving volume between z_lo and z_hi [cMpc^3]."""
    cosmo = cosmo or get_cosmology()
    v = cosmo.comoving_volume([z_lo, z_hi]).to_value(u.Mpc**3)
    return float(v[1] - v[0])


def shell_volume_thin(z, dt, cosmo=None):
    """Thin-shell approximation of slide 13 [cMpc^3]:

        dV_c = 4 pi D_c(z)^2 * c (1+z) dt

    Parameters
    ----------
    z : float
        Central redshift of the shell.
    dt : float
        Cosmic time width of the shell [yr].
    """
    d_c = comoving_distance(z, cosmo)  # cMpc
    c_dt_mpc = C_PC_YR * dt / MPC  # light-travel distance in Mpc
    return float(4.0 * np.pi * d_c**2 * (1.0 + z) * c_dt_mpc)


def redshift_edges_from_dt(z, dt, cosmo=None):
    """Redshift interval [z_lo, z_hi] corresponding to t(z) +/- dt/2.

    z_lo is clipped at 0 (no shell extends into the future).
    """
    t = cosmic_time(z, cosmo)
    t_now = cosmic_time(0.0, cosmo)
    t_hi = min(t + 0.5 * dt, float(t_now))  # later time -> lower z
    t_lo = t - 0.5 * dt
    z_lo = 0.0 if t_hi >= t_now else float(redshift_at_cosmic_time(t_hi, cosmo))
    z_hi = float(redshift_at_cosmic_time(t_lo, cosmo))
    return z_lo, z_hi


def redshift_edges_from_snapshots(redshifts):
    """Shell edges using midpoints between consecutive snapshot redshifts.

    Each snapshot then represents the slice of cosmic history halfway to its
    neighbours. Returns an array of shape (n_snap, 2) with [z_lo, z_hi].
    The first snapshot's lower edge is max(0, z0 - (z1-z0)/2), the last
    snapshot's upper edge is symmetric too.
    """
    z = np.sort(np.asarray(redshifts, dtype=float))
    if z.size == 1:
        raise ValueError("Need at least two snapshots to build midpoint shells; use shell_dt instead.")
    mid = 0.5 * (z[1:] + z[:-1])
    lo = np.concatenate([[max(0.0, z[0] - (mid[0] - z[0]))], mid])
    hi = np.concatenate([mid, [z[-1] + (z[-1] - mid[-1])]])
    return np.column_stack([lo, hi])


def sample_redshift_uniform_in_volume(z_lo, z_hi, size, rng, cosmo=None, n_grid=256):
    """Draw redshifts inside [z_lo, z_hi] with probability proportional to dV_c/dz.

    Used when ``universe.event_redshift == "uniform_in_volume"`` to avoid all
    events sitting exactly at the snapshot redshift.
    """
    cosmo = cosmo or get_cosmology()
    zg = np.linspace(z_lo, z_hi, n_grid)
    vg = cosmo.comoving_volume(zg).to_value(u.Mpc**3)
    cdf = (vg - vg[0]) / (vg[-1] - vg[0])
    return np.interp(rng.uniform(size=size), cdf, zg)
