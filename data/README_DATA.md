# Data directory

This folder is not tracked by git. It should contain (or symlink to)
the shared project data hosted on Google Drive.

Symlink Setup:
  ln -s /your/path/to/GoogleDrive/project_data ./data

## What goes here

* The MBHcat catalogues (HDF5, MBHcat format v2.1, one file per model).
  Point the `population.path` option of the run configuration
  (`configs/*.yaml`) to the file of the model you want to process.
  Run `python scripts/inspect_hdf5.py data/<file>` to see a file's structure.

Small reference tables that the code itself needs (e.g. the Broggi+22 Fig. 6
curve) are *committed* inside the package instead, in `src/emricat/data/`.
