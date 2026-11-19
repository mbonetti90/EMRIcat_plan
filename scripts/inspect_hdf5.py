#!/usr/bin/env python
"""Print the structure (groups, datasets, shapes, attributes) of an HDF5 file.

First thing to run on a new MBHcat file (Group 1):

    python scripts/inspect_hdf5.py path/to/file.h5
"""

import argparse

from emricat.mbh.hdf5_utils import hdf5_tree

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+")
    p.add_argument("--max-attrs", type=int, default=10)
    args = p.parse_args()
    for f in args.files:
        print(hdf5_tree(f, max_attrs=args.max_attrs))
        print()
