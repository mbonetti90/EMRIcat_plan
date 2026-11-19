"""
The one data container used everywhere in EMRICat: :class:`Catalogue`.

A Catalogue is simply

* ``columns``: a dict ``name -> 1D numpy array``, all of the same length;
* ``meta``:    a dict of scalar metadata (model name, snapshot redshift,
               box volume, cosmology, random seed, ...).

Why not pandas / astropy Tables?  Plain numpy arrays are fast, have no
surprises, and map one-to-one onto HDF5 datasets. If you prefer pandas for
interactive work use :meth:`Catalogue.to_pandas`.

Column names, units and producers are declared in :mod:`emricat.columns`.

Typical use
-----------
>>> cat = Catalogue({"mbh_mass": m, "stellar_mass": ms}, meta={"model": "TNG100"})
>>> cat["mbh_mass"]                     # numpy array
>>> cat.add_column("nsc_mass", m_nsc)   # Group 2 adds its columns
>>> big = cat.select(cat["stellar_mass"] > 1e9)
>>> cat.write_hdf5("out.h5")
"""

from __future__ import annotations

import warnings
from typing import Iterable, Iterator, Mapping

import h5py
import numpy as np

from emricat.columns import COLUMNS


class Catalogue:
    """Column-oriented table of numpy arrays plus a metadata dictionary."""

    def __init__(self, columns: Mapping[str, np.ndarray] | None = None, meta: Mapping | None = None):
        self.columns: dict[str, np.ndarray] = {}
        self.meta: dict = dict(meta or {})
        for name, values in (columns or {}).items():
            self.add_column(name, values)

    # ------------------------------------------------------------------
    # Basic container behaviour
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        if not self.columns:
            return 0
        return len(next(iter(self.columns.values())))

    def __getitem__(self, name: str) -> np.ndarray:
        return self.columns[name]

    def __setitem__(self, name: str, values) -> None:
        self.add_column(name, values, overwrite=True)

    def __contains__(self, name: str) -> bool:
        return name in self.columns

    def __repr__(self) -> str:
        meta = ", ".join(f"{k}={v!r}" for k, v in list(self.meta.items())[:4])
        return f"Catalogue(n={len(self)}, columns={list(self.columns)}, meta={{{meta}}})"

    @property
    def colnames(self) -> list[str]:
        return list(self.columns)

    # ------------------------------------------------------------------
    # Adding / selecting
    # ------------------------------------------------------------------
    def add_column(self, name: str, values, overwrite: bool = False) -> None:
        """Add a column. Scalars are broadcast to the catalogue length.

        A warning is emitted if ``name`` is not declared in
        :mod:`emricat.columns` (to keep the data contract honest).
        """
        if name in self.columns and not overwrite:
            raise KeyError(f"Column '{name}' already exists (use overwrite=True).")
        if name not in COLUMNS:
            warnings.warn(
                f"Column '{name}' is not declared in src/emricat/columns.py. "
                "Please add it there with its unit and description.",
                stacklevel=2,
            )
        arr = np.asarray(values)
        if arr.ndim == 0:
            arr = np.full(len(self), arr)
        if self.columns and len(arr) != len(self):
            raise ValueError(f"Column '{name}' has length {len(arr)}, catalogue has {len(self)}.")
        self.columns[name] = arr

    def require(self, names: Iterable[str], who: str = "") -> None:
        """Raise a clear error if any of ``names`` is missing.

        Every pipeline step should call this on its input, e.g.
        ``cat.require(REQUIRED_GROUP1, who="nsc.populate_nuclei")``.
        """
        missing = [n for n in names if n not in self.columns]
        if missing:
            raise KeyError(f"{who or 'Catalogue'}: missing required columns {missing}. Present: {self.colnames}")

    @classmethod
    def _from_trusted(cls, columns: dict, meta) -> "Catalogue":
        """Build without re-checking columns (they come from an existing Catalogue)."""
        cat = cls(meta=meta)
        cat.columns = columns
        return cat

    def select(self, mask_or_index) -> "Catalogue":
        """Return a new Catalogue with the selected rows (boolean mask or index array)."""
        return Catalogue._from_trusted({k: v[mask_or_index] for k, v in self.columns.items()}, self.meta)

    def repeat(self, counts: np.ndarray) -> "Catalogue":
        """Repeat row ``i`` ``counts[i]`` times (used to build galaxy replicas)."""
        return Catalogue._from_trusted({k: np.repeat(v, counts) for k, v in self.columns.items()}, self.meta)

    def iter_chunks(self, chunk_size: int) -> Iterator["Catalogue"]:
        """Yield consecutive row-chunks of at most ``chunk_size`` rows."""
        for start in range(0, len(self), chunk_size):
            yield self.select(slice(start, start + chunk_size))

    @staticmethod
    def concatenate(cats: Iterable["Catalogue"]) -> "Catalogue":
        """Stack catalogues with identical columns. Meta is taken from the first one."""
        cats = [c for c in cats if len(c) > 0]
        if not cats:
            return Catalogue()
        names = cats[0].colnames
        for c in cats[1:]:
            if c.colnames != names:
                raise ValueError("Cannot concatenate catalogues with different columns.")
        return Catalogue._from_trusted({n: np.concatenate([c[n] for c in cats]) for n in names}, cats[0].meta)

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------
    def write_hdf5(self, path, group: str = "/", mode: str = "a") -> None:
        """Write columns as datasets and meta as attributes into ``path[group]``.

        Units and descriptions from :mod:`emricat.columns` are stored as
        dataset attributes, so the files are self-documenting.
        """
        with h5py.File(path, mode) as f:
            g = f.require_group(group)
            for k, v in self.meta.items():
                g.attrs[k] = v if v is not None else "None"
            for name, arr in self.columns.items():
                if name in g:
                    del g[name]
                ds = g.create_dataset(name, data=arr, compression="gzip", compression_opts=4)
                if name in COLUMNS:
                    ds.attrs["unit"] = COLUMNS[name].unit
                    ds.attrs["description"] = COLUMNS[name].description

    @classmethod
    def read_hdf5(cls, path, group: str = "/") -> "Catalogue":
        """Inverse of :meth:`write_hdf5`."""
        with h5py.File(path, "r") as f:
            g = f[group]
            meta = {k: (v.item() if hasattr(v, "item") else v) for k, v in g.attrs.items()}
            cols = {k: g[k][()] for k in g.keys() if isinstance(g[k], h5py.Dataset)}
        return cls._from_trusted(cols, meta)  # no contract warnings when reading back

    def to_pandas(self):
        """Convenience conversion for interactive exploration (needs pandas)."""
        import pandas as pd

        return pd.DataFrame(self.columns)
