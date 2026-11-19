"""
GROUP 1 -- Helpers to explore HDF5 files whose layout we do not know yet.

Run from the command line:

    python scripts/inspect_hdf5.py path/to/file.h5
"""

from __future__ import annotations

import h5py


def hdf5_tree(path, max_attrs: int = 10) -> str:
    """Return a text tree of groups, datasets (shape, dtype) and attributes."""
    lines: list[str] = []

    def _attrs(obj, indent):
        for i, (k, v) in enumerate(obj.attrs.items()):
            if i >= max_attrs:
                lines.append(f"{indent}  @... ({len(obj.attrs) - max_attrs} more attrs)")
                break
            lines.append(f"{indent}  @{k} = {v!r}")

    def _visit(name, obj):
        depth = name.count("/")
        indent = "  " * depth
        short = name.split("/")[-1]
        if isinstance(obj, h5py.Dataset):
            lines.append(f"{indent}{short}  [dataset shape={obj.shape} dtype={obj.dtype}]")
        else:
            lines.append(f"{indent}{short}/")
        _attrs(obj, indent)

    with h5py.File(path, "r") as f:
        lines.append(f"{path}")
        _attrs(f, "")
        f.visititems(_visit)
    return "\n".join(lines)
