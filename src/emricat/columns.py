"""
The DATA CONTRACT between groups: which columns exist, who fills them, units.

The whole pipeline passes around a single kind of object, a
:class:`emricat.catalogue.Catalogue` (a table of numpy columns). Each step
*adds* columns to it. This file is the single place where those columns are
declared, so that

* Group 2 knows exactly what Group 1 will hand over,
* Group 3 knows exactly what Group 2 will hand over,
* the coordinators know what ends up in the final EMRI catalogue.

If you need a new column: add it here first (name, unit, producer,
description), then produce it in your module. Please do not silently invent
column names inside the code.

The ``producer`` field says which pipeline stage is responsible:

    "group1"   -> emricat.mbh       (MBH + host galaxy from MBHcat models)
    "group2"   -> emricat.nsc       (nuclear star cluster)
    "group3"   -> emricat.emri      (merger clock + time-dependent EMRI rate)
    "universe" -> emricat.universe  (replicas, Poisson draw, detection)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    """Description of one catalogue column."""

    name: str
    unit: str
    producer: str
    description: str
    dtype: str = "f8"


# fmt: off
_COLUMNS = [
    # ------------------------------------------------------------------
    # Group 1: one row per simulated galaxy in a snapshot
    # ------------------------------------------------------------------
    Column("galaxy_id",       "",         "group1", "Unique ID of the galaxy within its snapshot file.", "i8"),
    Column("mbh_mass",        "Msun",     "group1", "Mass of the central MBH."),
    Column("stellar_mass",    "Msun",     "group1", "Stellar mass of the host galaxy (definition depends on model; document it in the reader)."),
    Column("halo_mass",       "Msun",     "group1", "Dark matter (sub)halo mass of the host. NaN if the model does not provide it."),
    Column("number_density",  "cMpc^-3",  "group1", "Comoving number density represented by this galaxy: 1/V_box for simulations, the weight w_i for SAMs."),
    Column("redshift",        "",         "group1", "Redshift of the snapshot the galaxy comes from."),
    # Optional Group 1 extras (fill them if available; NaN otherwise)
    Column("mbh_spin",        "",         "group1", "Dimensionless MBH spin, if available."),
    Column("is_central",      "",         "group1", "1 if central galaxy, 0 if satellite, -1 if unknown.", "i1"),

    # ------------------------------------------------------------------
    # Universe (Step 4): replication of each galaxy in the cosmic shell
    # ------------------------------------------------------------------
    Column("replica_id",      "",         "universe", "Index of the replica of a given galaxy within its shell (0..N_i-1).", "i8"),
    Column("replica_weight",  "",         "universe", "Number of real galaxies represented by this simulated replica (1 in brute-force mode)."),

    # ------------------------------------------------------------------
    # Group 2: nuclear star cluster (one value per *replica*)
    # ------------------------------------------------------------------
    Column("has_nsc",         "",         "group2", "1 if this replica hosts a nuclear star cluster, 0 otherwise.", "i1"),
    Column("nsc_mass",        "Msun",     "group2", "NSC mass (0 if has_nsc == 0)."),
    Column("nsc_reff",        "pc",       "group2", "NSC effective (half-light) radius (NaN if has_nsc == 0)."),
    Column("nsc_sigma",       "km/s",     "group2", "Characteristic velocity dispersion used for the relaxation time."),
    Column("t_relax",         "yr",       "group2", "Relaxation time of the nucleus (definition documented in emricat.nsc.relaxation)."),

    # ------------------------------------------------------------------
    # Group 3: merger clock and EMRI rate (one value per replica)
    # ------------------------------------------------------------------
    Column("t_between_mergers", "yr",     "group3", "Drawn time between two successive major mergers for this replica."),
    Column("t_since_merger",    "yr",     "group3", "Drawn time elapsed since the last major merger (NSC 'reset', t=0 of the Broggi+22 curve)."),
    Column("emri_rate_peak",    "1/yr",   "group3", "Peak EMRI rate Gamma_hat_E of the Broggi+22 curve for this nucleus."),
    Column("t_emri_peak",       "yr",     "group3", "Time t_E at which the rate peaks (sets the clock of the dimensionless curve)."),
    Column("emri_rate",         "1/yr",   "group3", "Source-frame EMRI rate at time t_since_merger."),

    # ------------------------------------------------------------------
    # Universe (Step 5): expected number and Poisson draw
    # ------------------------------------------------------------------
    Column("n_emri_expected", "",         "universe", "Expected number of EMRIs during the mission: rate * T_obs / (1+z)."),
    Column("n_emri",          "",         "universe", "Poisson-drawn number of EMRIs during the mission.", "i8"),
    Column("event_redshift",  "",         "universe", "Redshift assigned to the event (snapshot z, or drawn inside the shell)."),
    Column("snr",             "",         "universe", "LISA signal-to-noise ratio (TO BE DEFINED; NaN for now)."),
    Column("detected",        "",         "universe", "1 if the event passes the detection criterion.", "i1"),
]
# fmt: on

#: Mapping ``name -> Column``. Use ``COLUMNS["mbh_mass"].unit`` etc.
COLUMNS: dict[str, Column] = {c.name: c for c in _COLUMNS}

#: Columns every Group 1 reader MUST provide.
REQUIRED_GROUP1 = ("galaxy_id", "mbh_mass", "stellar_mass", "number_density", "redshift")

#: Columns Group 2 MUST add.
REQUIRED_GROUP2 = ("has_nsc", "nsc_mass", "nsc_reff", "t_relax")

#: Columns Group 3 MUST add.
REQUIRED_GROUP3 = ("t_between_mergers", "t_since_merger", "emri_rate")


def describe(name: str) -> str:
    """Return a one-line human readable description of a column."""
    c = COLUMNS[name]
    unit = f" [{c.unit}]" if c.unit else ""
    return f"{c.name}{unit} ({c.producer}): {c.description}"


def print_contract() -> None:
    """Print the full data contract, grouped by producer."""
    for producer in ("group1", "universe", "group2", "group3"):
        print(f"\n=== {producer} ===")
        for c in _COLUMNS:
            if c.producer == producer:
                print("  " + describe(c.name))


if __name__ == "__main__":  # python -m emricat.columns
    print_contract()
