"""
EMRICat: EMRI rates and catalogues from MBH population models.

A spin-off of MBHcat: take the same galaxy and MBH models, add a nuclear
star cluster to each galaxy, assign an EMRI rate from two-body relaxation
only (Broggi+22), and draw single events by Monte Carlo.

Package map (see README.md for the full picture)
------------------------------------------------
emricat.mbh        GROUP 1  MBH + host galaxy populations from MBHcat (HDF5)
emricat.nsc        GROUP 2  nuclear star clusters (occupation, mass, radius, t_relax)
emricat.emri       GROUP 3  merger clock + time-dependent EMRI rate (Broggi+22)
emricat.universe   STEPS 4-5 replicas in cosmic shells, Poisson draw, detection
emricat.plotting   common plotting style and standard diagnostic plots
emricat.pipeline   glues everything together (python -m emricat.pipeline config.yaml)

Shared infrastructure: catalogue (data container), columns (data contract),
config, units, cosmology, rng, registry, mock (toy versions of every step).
"""

__version__ = "0.0.1"
