"""
Random number management for the Monte Carlo.

Goal: **reproducibility.** The same master seed (and the same
``run.chunk_size``) must give the same catalogue, whether chunks are processed
serially or in parallel and in any order. Changing ``chunk_size`` gives a
statistically equivalent but not identical realisation.

How: we never use ``np.random.seed`` / global state. Instead a single
:class:`numpy.random.SeedSequence` is built from the master seed, and an
independent child stream is derived *deterministically from labels*
(snapshot index, galaxy chunk, stage name). Two different labels give
statistically independent streams; the same labels always give the same one.

Usage
-----
>>> streams = RandomStreams(seed=12345)
>>> rng = streams.get("nsc", snapshot=3, chunk=0)   # a numpy Generator
>>> rng.normal(size=10)

Rule for contributors: every function that draws random numbers takes an
explicit ``rng: numpy.random.Generator`` argument. Never create a Generator
inside a physics function.
"""

from __future__ import annotations

import hashlib

import numpy as np


def _label_to_ints(*labels) -> list[int]:
    """Hash arbitrary labels (strings, ints) to a list of 32-bit integers."""
    out = []
    for lab in labels:
        h = hashlib.sha256(str(lab).encode()).digest()
        out.append(int.from_bytes(h[:4], "little"))
    return out


class RandomStreams:
    """Factory of independent, reproducible random Generators."""

    def __init__(self, seed: int):
        self.seed = int(seed)

    def get(self, stage: str, **labels) -> np.random.Generator:
        """Return the Generator for a given stage and set of labels.

        Parameters
        ----------
        stage : str
            Pipeline stage, e.g. "replicas", "nsc", "emri", "poisson".
        **labels
            Anything identifying the unit of work, e.g. ``snapshot=3, chunk=12``.
            Labels are sorted by key, so the order of keywords does not matter.
        """
        key = [stage] + [f"{k}={labels[k]}" for k in sorted(labels)]
        ss = np.random.SeedSequence(entropy=self.seed, spawn_key=_label_to_ints(*key))
        return np.random.default_rng(ss)
