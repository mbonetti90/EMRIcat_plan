"""
GROUP 1 -- MBH population and host galaxies (pipeline Step 1).

Responsibility
--------------
Read the MBHcat model outputs (HDF5) and return, for each snapshot, a
:class:`emricat.catalogue.Catalogue` with at least the columns listed in
``emricat.columns.REQUIRED_GROUP1``:

    galaxy_id, mbh_mass [Msun], stellar_mass [Msun], number_density [cMpc^-3], redshift

(and ``halo_mass`` / ``mbh_spin`` / ``is_central`` when available).

Remember (slide 4): galaxies cannot be followed between snapshots, so
*each snapshot is an independent population*. Nothing downstream assumes
any link between snapshots.

Modules
-------
readers.py     one Reader class per model family + the READERS registry
snapshots.py   snapshot redshift grid utilities (spacing checks, etc.)
hdf5_utils.py  helpers to inspect unknown HDF5 files
"""

from emricat.mbh.readers import READERS, BaseReader, apply_cuts, get_reader  # noqa: F401
