"""
STEP 4 -- Shells around each snapshot and replication of galaxies.

Computational cost (to be assessed!)
------------------------------------
Brute force means one row per copy of every galaxy. Order of magnitude
(slide 12, 100 Myr shells): ~1e3-1e5 copies per galaxy, times ~1e5-1e6
galaxies per snapshot, times ~100 snapshots out to z ~ 4: 1e10-1e13 rows.
Each row costs a few random numbers and some arithmetic (~0.1-1 us in
numpy), so the brute force can be expensive.

Cheap alternative implemented here: ``universe.max_replicas_per_galaxy = K``.
At most K replicas per galaxy are drawn explicitly, each standing for
w = N_i / K real galaxies (column ``replica_weight``). The Poisson draw then
uses lambda = w * Gamma * T_obs / (1+z). Because the sum of w independent
Poisson(lambda_1) variables is Poisson(w lambda_1), expected numbers of
events are *exact*; the only approximation is that the w galaxies share the
same NSC / merger draw, which matters only at second order when lambda << 1.
Use the brute force (K = None) as reference to validate K on a test snapshot.

Processing in chunks
--------------------
Replicas are never all held in memory: :func:`iter_replica_chunks` yields
blocks of at most ``chunk_size`` rows, even when a single galaxy has more
copies than that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np

from emricat import cosmology
from emricat.catalogue import Catalogue


@dataclass
class Shell:
    """The slice of the Universe represented by one snapshot."""

    index: int  #: position in the list of snapshots
    z: float  #: snapshot redshift
    z_lo: float  #: lower redshift edge
    z_hi: float  #: upper redshift edge
    volume: float  #: full-sky comoving volume of the shell [cMpc^3]


def build_shells(redshifts, cfg_universe, cosmo=None) -> list[Shell]:
    """Build one :class:`Shell` per snapshot redshift.

    * ``cfg_universe.shell_dt`` set: shell = t(z) +/- dt/2 (slide 13).
      Shells of neighbouring snapshots may then overlap or leave gaps: this is
      only correct once snapshots are spaced by ~dt.
    * ``shell_dt = None``: shells extend to the midpoints between consecutive
      snapshots, so they tile the redshift range without gaps or overlaps.
    """
    cosmo = cosmo or cosmology.get_cosmology()
    z = np.sort(np.asarray(redshifts, dtype=float))
    if cfg_universe.shell_dt is None:
        edges = cosmology.redshift_edges_from_snapshots(z)
    else:
        edges = np.array([cosmology.redshift_edges_from_dt(zi, cfg_universe.shell_dt, cosmo) for zi in z])

    shells = []
    for i, (zi, (lo, hi)) in enumerate(zip(z, edges)):
        if cfg_universe.shell_volume == "exact":
            vol = cosmology.shell_volume_exact(lo, hi, cosmo)
        elif cfg_universe.shell_volume == "thin_shell":
            dt = float(cosmology.cosmic_time(lo, cosmo) - cosmology.cosmic_time(hi, cosmo))
            vol = cosmology.shell_volume_thin(zi, dt, cosmo)
        else:
            raise ValueError(f"Unknown shell_volume '{cfg_universe.shell_volume}'.")
        shells.append(Shell(index=i, z=float(zi), z_lo=float(lo), z_hi=float(hi), volume=vol))
    return shells


def expected_copies(cat: Catalogue, shell: Shell) -> np.ndarray:
    """N_i = n_i * Delta V_c : expected number of real galaxies like galaxy i in the shell."""
    return cat["number_density"] * shell.volume


def draw_replica_counts(expected: np.ndarray, rng: np.random.Generator, rounding: str = "poisson", max_per_galaxy: int | None = None):
    """Turn expected copies N_i (non-integer) into simulated replica counts and weights.

    Parameters
    ----------
    expected : array    N_i
    rng : Generator
    rounding : {"poisson", "stochastic_round"}
        "poisson": n_i ~ Poisson(N_i) (includes Poisson cosmic variance);
        "stochastic_round": floor(N_i) + Bernoulli(frac(N_i)) (minimal variance).
    max_per_galaxy : int or None
        Cap K on the simulated replicas (see module docstring).

    Returns
    -------
    n_sim : int array     replicas actually simulated per galaxy
    weight : float array  real galaxies represented by each simulated replica of galaxy i
    """
    expected = np.asarray(expected, dtype=float)
    if rounding == "poisson":
        n_real = rng.poisson(expected)
    elif rounding == "stochastic_round":
        base = np.floor(expected)
        n_real = (base + (rng.uniform(size=expected.shape) < expected - base)).astype(np.int64)
    else:
        raise ValueError(f"Unknown replica_rounding '{rounding}'.")

    if max_per_galaxy is None:
        return n_real.astype(np.int64), np.ones_like(expected)
    n_sim = np.minimum(n_real, int(max_per_galaxy)).astype(np.int64)
    weight = np.where(n_sim > 0, n_real / np.maximum(n_sim, 1), 0.0)
    return n_sim, weight


def iter_replica_chunks(cat: Catalogue, n_sim: np.ndarray, weight: np.ndarray, chunk_size: int) -> Iterator[Catalogue]:
    """Yield replicas of the galaxies in ``cat`` in chunks of <= chunk_size rows.

    Replica r (global index) belongs to galaxy ``g = searchsorted(cumsum(n_sim), r, 'right')``.
    Each chunk carries all galaxy columns plus ``replica_id`` and ``replica_weight``.
    """
    n_sim = np.asarray(n_sim, dtype=np.int64)
    ends = np.cumsum(n_sim)
    starts = ends - n_sim
    total = int(ends[-1]) if len(ends) else 0
    for a in range(0, total, chunk_size):
        r = np.arange(a, min(a + chunk_size, total), dtype=np.int64)
        g = np.searchsorted(ends, r, side="right")
        chunk = cat.select(g)
        chunk["replica_id"] = r - starts[g]
        chunk["replica_weight"] = np.asarray(weight)[g]
        yield chunk
