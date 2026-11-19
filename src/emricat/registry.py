"""
Tiny helper to pick an implementation by name from a dictionary.

Every module that offers alternative physical prescriptions keeps a plain
dictionary, e.g. ::

    MASS_RELATIONS = {
        "hoyer23":    nsc_mass_hoyer23,
        "neumayer20": nsc_mass_neumayer20,
    }

and the pipeline calls ``choose(MASS_RELATIONS, cfg.nsc.mass_relation, "NSC mass relation")``.
This keeps the code explicit: to see what options exist, just read the dict.
"""

from __future__ import annotations

from typing import Callable, Mapping


def choose(registry: Mapping[str, Callable], name: str, what: str = "option") -> Callable:
    """Return ``registry[name]`` with a helpful error message if missing."""
    try:
        return registry[name]
    except KeyError:
        raise KeyError(f"Unknown {what} '{name}'. Available: {sorted(registry)}") from None
