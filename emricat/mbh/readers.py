"""
GROUP 1 -- Readers for MBH population models.

Every model family gets a Reader class that hides the details of its file
format and returns a standard :class:`~emricat.catalogue.Catalogue`.
Downstream code only ever talks to the :class:`BaseReader` interface.

How to add a new model
----------------------
1. Inspect the file:  ``python scripts/inspect_hdf5.py path/to/file.h5``
2. Subclass :class:`BaseReader` (copy :class:`MBHcatReader` as a template).
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
from pathlib import Path

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
    """Reader for the MBHcat catalogues (LISA Astrophysics MBHcatalogues, arXiv:2605.00092).

    TODO (Group 1):
        * describe the file layout here (one file per snapshot? groups per z?),
        * list the datasets used and their original units,
        * state the stellar-mass definition and the central-MBH choice.

    Expected ``params`` (from the YAML ``population.params``), suggestions:
        box_size_cmpc : float   side of the simulation box (simulations only)
        h             : float   little h of the model
        weights_key   : str     name of the SAM weight dataset (SAMs only)
    """

    def available_redshifts(self) -> np.ndarray:
        # TODO (Group 1): list the snapshots present in self.path and return their redshifts.
        raise NotImplementedError("Group 1: MBHcatReader.available_redshifts")

    def _read_raw(self, redshift: float, rng=None) -> Catalogue:
        # TODO (Group 1): skeleton of what this method should do
        #   1. open the HDF5 file/group for this redshift (h5py.File(...))
        #   2. read MBH mass, stellar mass, halo mass, (spin), galaxy id
        #   3. convert units -> linear Msun, little-h removed
        #   4. number_density = 1 / V_box  (or SAM weights)
        #   5. return Catalogue({...}, meta={"box_volume_cmpc3": ..., "h": ...})
        raise NotImplementedError("Group 1: MBHcatReader._read_raw")


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
