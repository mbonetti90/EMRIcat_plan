"""
GROUP 1 -- Readers for MBH population models.

Every model family gets a Reader class that hides the details of its file
format and returns a standard :class:`~emricat.catalogue.Catalogue`.
Downstream code only ever talks to the :class:`BaseReader` interface.

How to add a new model
----------------------
Models delivered in the MBHcat v2.1 format are read by :class:`MBHcatReader`
(``population.reader: mbhcat``). A new class is needed only for other formats.

1. Inspect the file:  ``python scripts/inspect_hdf5.py path/to/file.h5``
2. Subclass :class:`BaseReader` (use :class:`MBHcatReader` as a template).
3. Implement ``available_redshifts`` and ``_read_raw``.
4. Register it in ``READERS`` at the bottom of this file.
5. Add a test in ``tests/test_group1_mbh.py`` (e.g. compare the MBH mass
   function with the one in the MBHcat paper, arXiv:2605.00092).

Things each reader MUST take care of (and document in its docstring)
--------------------------------------------------------------------
* Units: convert to linear Msun (beware of ``log10`` and ``1e10 Msun/h``).
* Little-h: convert comoving volumes/masses with the model's own h.
* Number density: 1/V_box for simulations, the weight w_i for SAMs.
* Multiple MBHs per galaxy: decide which one is "the" central MBH
  (most massive? closest to the potential minimum?) and say so.
* Stellar mass definition (total, within 2 R_half, within 30 kpc, ...).
* Galaxies without an MBH: drop them, or keep them with mbh_mass = 0?
  (Agree on this with the coordinators; the current proposal is to drop them.)
"""

from __future__ import annotations

import abc
import warnings
from pathlib import Path

import h5py
import numpy as np

from emricat import mock
from emricat.catalogue import Catalogue
from emricat.columns import REQUIRED_GROUP1


class BaseReader(abc.ABC):
    """Interface that every model reader implements.

    Parameters
    ----------
    path : str
        File or directory containing the model outputs.
    model_name : str
        Label of the model (stored in the catalogue metadata).
    **params
        Reader-specific options from ``cfg.population.params``.
    """

    #: Name of the astropy cosmology the model was run with (see emricat.cosmology).
    cosmology_name: str = "Planck18"

    def __init__(self, path: str = "", model_name: str = "", **params):
        self.path = Path(path) if path else None
        self.model_name = model_name
        self.params = params

    # ---- to be implemented by each model --------------------------------
    @abc.abstractmethod
    def available_redshifts(self) -> np.ndarray:
        """Sorted array of the snapshot redshifts available in the files."""

    @abc.abstractmethod
    def _read_raw(self, redshift: float, rng: np.random.Generator | None = None) -> Catalogue:
        """Read one snapshot and return a Catalogue in EMRICat units.

        Must contain at least ``REQUIRED_GROUP1`` columns. ``rng`` is only
        used by mock/synthetic readers.
        """

    # ---- shared logic: do not override ----------------------------------
    def read_snapshot(self, redshift: float, rng: np.random.Generator | None = None) -> Catalogue:
        """Read a snapshot and check it respects the data contract."""
        cat = self._read_raw(redshift, rng=rng)
        cat.require(REQUIRED_GROUP1, who=f"{type(self).__name__}.read_snapshot")
        cat.meta.setdefault("model", self.model_name)
        cat.meta.setdefault("snapshot_redshift", float(redshift))
        cat.meta.setdefault("cosmology", self.cosmology_name)
        _sanity_checks(cat)
        return cat


def _sanity_checks(cat: Catalogue) -> None:
    """Cheap checks that catch the most common unit mistakes."""
    for col in ("mbh_mass", "stellar_mass"):
        m = cat[col]
        if np.any(m < 0):
            raise ValueError(f"{col}: negative masses found.")
        med = np.median(m[m > 0]) if np.any(m > 0) else 0
        if 0 < med < 100:
            raise ValueError(f"{col}: median {med:.3g} looks like log10(M) or 1e10 Msun units, expected linear Msun.")
    if np.any(cat["number_density"] <= 0):
        raise ValueError("number_density must be > 0.")


# ======================================================================
# Real readers -- TO BE IMPLEMENTED BY GROUP 1
# ======================================================================
class MBHcatReader(BaseReader):
    """Reader for MBHcat catalogues, format v2.1 (arXiv:2605.00092).

    The format is defined by ``src/hdf5_MBHcat_catalog_v2.1.py`` (function
    ``write_hdf5``). One file per model; the part used here is::

        /Header                    attrs: SimulationName, HubbleConstant, OmegaMatter,
                                          OmegaLambda, BoxSize, RedshiftsAllBHs, ...
        /AllBHs/Z<z:011.8f>/       one group per snapshot, e.g. "Z01.00312000"
            BlackHoles/Mass           [M_sun]
            BlackHoles/NumberDensity  [Mpc^-3]   (1/V_box for simulations, weight for SAMs)
            BlackHoles/Mdot, RadEff   (not used here)
            Galaxies/StellarMass      [M_sun]    host galaxy stellar mass
            Galaxies/DarkMatterMass   [M_sun]    OPTIONAL -> halo_mass (NaN if absent)

    Units in v2.1 are already M_sun and Mpc (no little h), so no conversion
    is applied here. The snapshot redshift is taken from the group name.

    TODO (Group 1), to check and document:
        * Each row of /AllBHs is one *MBH*, with its host galaxy properties.
          If a model stores several MBHs per galaxy, the same galaxy appears
          several times: decide whether to keep only the most massive MBH per
          host (needs a host ID, not in v2.1) or keep them all.
        * Stellar-mass definition of each model (total, within an aperture...).
        * Resolution cuts per model -> ``population.min_stellar_mass`` / ``min_mbh_mass``.
        * Rows with zero/NaN masses: currently dropped (see ``_read_raw``).

    params (from the YAML ``population.params``): none required.
    """

    ALLBHS = "AllBHs"

    def _snapshot_keys(self) -> dict[float, str]:
        """Map snapshot redshift -> group name in /AllBHs."""
        if self.path is None or not self.path.is_file():
            raise FileNotFoundError(f"MBHcat file not found: {self.path} (set population.path in the config).")
        with h5py.File(self.path, "r") as f:
            return {float(k[1:]): k for k in f[self.ALLBHS].keys()}

    def available_redshifts(self) -> np.ndarray:
        return np.sort(np.array(list(self._snapshot_keys())))

    def header(self) -> dict:
        """All /Header attributes (model metadata: cosmology, box size, resolution...)."""
        with h5py.File(self.path, "r") as f:
            return {k: v for k, v in f["Header"].attrs.items()}

    def _read_raw(self, redshift: float, rng=None) -> Catalogue:
        keys = self._snapshot_keys()
        zs = np.array(list(keys))
        i = int(np.argmin(np.abs(zs - redshift)))
        if not np.isclose(zs[i], redshift, rtol=0, atol=1e-6):
            raise KeyError(f"Snapshot z={redshift} not in {self.path}. Available: {np.sort(zs)}")
        z_snap = float(zs[i])

        with h5py.File(self.path, "r") as f:
            g = f[self.ALLBHS][keys[z_snap]]
            mbh = g["BlackHoles/Mass"][()].astype(float)
            dens = g["BlackHoles/NumberDensity"][()].astype(float)
            mstar = g["Galaxies/StellarMass"][()].astype(float)
            mhalo = g["Galaxies/DarkMatterMass"][()].astype(float) if "DarkMatterMass" in g["Galaxies"] else np.full(mbh.size, np.nan)
            hdr = f["Header"].attrs
            meta = {k: hdr[k] for k in ("SimulationName", "ModelType", "HubbleConstant", "OmegaMatter", "OmegaLambda", "BoxSize") if k in hdr}

        # Drop unusable rows (no MBH, no host mass, non-positive weight).
        ok = (mbh > 0) & (mstar > 0) & (dens > 0) & np.isfinite(mbh) & np.isfinite(mstar) & np.isfinite(dens)
        n_drop = int((~ok).sum())
        if n_drop:
            warnings.warn(f"{self.path.name} z={z_snap}: dropped {n_drop} rows with non-positive/NaN mass or density.")

        meta.update({"snapshot_redshift": z_snap, "n_dropped_rows": n_drop})
        return Catalogue(
            {
                "galaxy_id": np.flatnonzero(ok).astype(np.int64),  # row index in the original file
                "mbh_mass": mbh[ok],
                "stellar_mass": mstar[ok],
                "halo_mass": mhalo[ok],
                "number_density": dens[ok],
                "redshift": np.full(int(ok.sum()), z_snap),
            },
            meta=meta,
        )


class MockReader(BaseReader):
    """Synthetic population from :func:`emricat.mock.mock_snapshot`. TESTING ONLY.

    params: ``redshifts`` (list), ``n_gal`` (int), ``box_size_cmpc`` (float).
    """

    def available_redshifts(self) -> np.ndarray:
        return np.sort(np.asarray(self.params.get("redshifts", [0.1, 0.5, 1.0, 2.0, 3.0]), dtype=float))

    def _read_raw(self, redshift: float, rng=None) -> Catalogue:
        rng = rng if rng is not None else np.random.default_rng(0)
        return mock.mock_snapshot(
            redshift,
            rng,
            n_gal=int(self.params.get("n_gal", 20_000)),
            box_size_cmpc=float(self.params.get("box_size_cmpc", 100.0)),
        )


#: Registry of available readers. The config key ``population.reader`` picks one.
READERS: dict[str, type[BaseReader]] = {
    "mbhcat": MBHcatReader,
    "mock": MockReader,
    # "lgalaxies": LGalaxiesReader,   # TODO (Group 1) if SAM files differ from simulation files
}


def get_reader(cfg) -> BaseReader:
    """Instantiate the reader requested in ``cfg.population``."""
    from emricat.registry import choose

    cls = choose(READERS, cfg.population.reader, "population reader")
    return cls(path=cfg.population.path, model_name=cfg.run.model_name, **cfg.population.params)


def apply_cuts(cat: Catalogue, min_stellar_mass: float = 0.0, min_mbh_mass: float = 0.0) -> Catalogue:
    """Remove galaxies below the resolution limits set in the config."""
    keep = (cat["stellar_mass"] >= min_stellar_mass) & (cat["mbh_mass"] >= min_mbh_mass)
    return cat.select(keep)
