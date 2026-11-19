"""
TOY implementations of every pipeline step.  ***NOT PHYSICS.***

Purpose
-------
These functions exist only so that the full chain

    MBH population -> NSC -> EMRI rate -> replicas -> Poisson draw -> catalogue

can be run end-to-end *today*, before the real prescriptions are coded. They let us

* test the plumbing (``pytest``, ``configs/mock.yaml``),
* test the plotting routines,
* get early timing estimates for the Monte Carlo (computational affordability).

Every number below is a rough placeholder chosen to give plausible orders of
magnitude. **Never use the "toy"/"mock" options for science runs.** The
real implementations live in emricat/mbh, emricat/nsc, emricat/emri.
"""

from __future__ import annotations

import numpy as np

from emricat.catalogue import Catalogue
from emricat.units import G_PC3_MSUN_YR2, GYR

# ----------------------------------------------------------------------
# Group 1 toy: a fake galaxy + MBH population in a periodic box
# ----------------------------------------------------------------------
def mock_snapshot(redshift: float, rng: np.random.Generator, n_gal: int = 20_000, box_size_cmpc: float = 100.0) -> Catalogue:
    """Fake snapshot: log-normal-ish stellar mass function + M_bh ~ 1e-3 M_* with scatter."""
    # Stellar masses: truncated power law dN/dlogM ~ M^-0.4 between 1e8 and 1e12, plus exponential cutoff.
    log_ms = rng.uniform(8.0, 12.0, size=4 * n_gal)
    keep = rng.uniform(size=log_ms.size) < 10 ** (-0.4 * (log_ms - 8.0)) * np.exp(-(10 ** (log_ms - 11.0)))
    log_ms = log_ms[keep][:n_gal]
    n = log_ms.size
    log_mbh = np.log10(1e-3) + log_ms + rng.normal(0.0, 0.4, size=n) - 0.1 * redshift
    return Catalogue(
        {
            "galaxy_id": np.arange(n, dtype=np.int64),
            "mbh_mass": 10**log_mbh,
            "stellar_mass": 10**log_ms,
            "halo_mass": 10 ** (log_ms + 1.5),
            "number_density": np.full(n, 1.0 / box_size_cmpc**3),
            "redshift": np.full(n, float(redshift)),
        },
        meta={"model": "mock", "snapshot_redshift": float(redshift), "box_volume_cmpc3": box_size_cmpc**3},
    )


# ----------------------------------------------------------------------
# Group 2 toys
# ----------------------------------------------------------------------
def toy_nsc_mass(stellar_mass: np.ndarray, **_) -> np.ndarray:
    """TOY: M_NSC = 1e-3 M_*."""
    return 1e-3 * np.asarray(stellar_mass)


def toy_nsc_radius(nsc_mass: np.ndarray, **_) -> np.ndarray:
    """TOY: R_eff = 3 pc (M_NSC / 1e6 Msun)^0.33 (slope as in Pechetti+20, normalisation made up)."""
    return 3.0 * (np.asarray(nsc_mass) / 1e6) ** 0.33


def toy_relaxation_time(nsc_mass, nsc_reff, mbh_mass, m_star: float = 1.0, ln_lambda: float = 10.0, **_):
    """TOY: Spitzer half-mass relaxation time of the cluster, ignoring the MBH.

        t_rh = 0.138 N^(1/2) r_h^(3/2) / (m^(1/2) G^(1/2) lnLambda),  N = M/m.
    """
    n_star = np.asarray(nsc_mass) / m_star
    return 0.138 * np.sqrt(n_star) * np.asarray(nsc_reff) ** 1.5 / (np.sqrt(m_star * G_PC3_MSUN_YR2) * ln_lambda)


# ----------------------------------------------------------------------
# Group 3 toys
# ----------------------------------------------------------------------
def toy_merger_interval(stellar_mass, redshift, rng, **_):
    """TOY: exponential distribution of intervals with mean 2 Gyr / (1+z)^1.2 (rough slide-10 trend)."""
    mean = 2.0 * GYR / (1.0 + np.asarray(redshift)) ** 1.2
    return rng.exponential(mean)


def toy_rate_curve(x):
    """TOY dimensionless curve f(x = t/t_E), f(1) = 1: rise x e^(1-x), then decline x^-0.6."""
    x = np.asarray(x, dtype=float)
    return np.where(x < 1.0, x * np.exp(1.0 - x), np.maximum(x, 1.0) ** -0.6)


def toy_rate_normalization(mbh_mass, nsc_mass, nsc_reff, t_relax, **_):
    """TOY: Gamma_hat = 3e-7 /yr (M_bh/1e6)^-0.19 (Babak+17-like), t_E = t_relax / 20 (slide 7)."""
    gamma_hat = 3e-7 * (np.asarray(mbh_mass) / 1e6) ** -0.19
    t_e = np.asarray(t_relax) / 20.0
    return gamma_hat, t_e
