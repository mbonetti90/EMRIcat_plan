"""
Run configuration.

A run of EMRICat is fully specified by one YAML file (see ``configs/``).
The YAML is loaded into the nested dataclasses below, so that

* every option has a documented default right here,
* typos in the YAML raise an error instead of being silently ignored,
* code can use ``cfg.nsc.mass_relation`` with autocompletion.

Choosing *which* physical prescription to use (e.g. Hoyer+23 vs
Neumayer+20 for the NSC mass) is done by NAME: each module keeps a small
dictionary ("registry") of available implementations and the config picks one
by its key. Model-specific free parameters go in the ``params`` dictionaries
and are forwarded as keyword arguments to the chosen implementation.

To add an option: add a field here with a default and a comment, then use it.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from emricat.units import MYR, YR


@dataclass
class RunConfig:
    """Global options of a run."""

    #: Free label identifying the MBH population model (e.g. "TNG100", "L-Galaxies").
    model_name: str = "mock"
    #: Output directory. The catalogue goes in ``<output_dir>/<model_name>_emricat.h5``.
    output_dir: str = "output"
    #: Master random seed. Same seed + same config = identical catalogue.
    seed: int = 12345
    #: LISA mission duration (observer frame) [yr].
    t_obs: float = 4.0 * YR
    #: Maximum redshift considered (EMRI horizon for LISA).
    z_max: float = 4.0
    #: Number of replicas processed at once. Controls memory use. Results are
    #: bit-for-bit reproducible for a fixed chunk_size (statistically equivalent otherwise).
    chunk_size: int = 2_000_000
    #: Keep only replicas with n_emri > 0 in the output (True), or all of them (False, debug only!).
    keep_only_events: bool = True


@dataclass
class PopulationConfig:
    """Group 1 options: where/how to read the MBH + galaxy population."""

    #: Reader name, a key of ``emricat.mbh.readers.READERS`` (e.g. "mbhcat", "mock").
    reader: str = "mock"
    #: Path to the file or directory with the model snapshots (HDF5).
    path: str = ""
    #: Optional explicit list of snapshot redshifts to use (None = all available up to z_max).
    redshifts: list[float] | None = None
    #: Discard galaxies below this stellar mass [Msun] (resolution limit of the model).
    min_stellar_mass: float = 0.0
    #: Discard MBHs below this mass [Msun].
    min_mbh_mass: float = 0.0
    #: Extra keyword arguments passed to the reader.
    params: dict = field(default_factory=dict)


@dataclass
class NSCConfig:
    """Group 2 options: nuclear star cluster prescription."""

    #: Occupation fraction model, key of ``emricat.nsc.occupation.OCCUPATION_MODELS``.
    #: "all" = every galaxy has an NSC; "hoyer21" = single logistic;
    #: "double_logistic" = refit with high-mass cutoff (slide 6).
    occupation: str = "all"
    occupation_params: dict = field(default_factory=dict)

    #: M_NSC(M_*) relation, key of ``emricat.nsc.scaling_relations.MASS_RELATIONS``.
    mass_relation: str = "hoyer23"
    #: Log-normal scatter around the mass relation [dex].
    mass_scatter_dex: float = 0.0

    #: R_eff(M_NSC) relation, key of ``emricat.nsc.scaling_relations.RADIUS_RELATIONS``.
    radius_relation: str = "pechetti20"
    #: Log-normal scatter around the radius relation [dex].
    radius_scatter_dex: float = 0.0

    #: Definition of the relaxation time, key of ``emricat.nsc.relaxation.RELAXATION_MODELS``.
    relaxation: str = "half_mass"
    relaxation_params: dict = field(default_factory=dict)


@dataclass
class EMRIConfig:
    """Group 3 options: merger clock and time-dependent EMRI rate (Broggi+22)."""

    #: Shape of the dimensionless curve Gamma(t)/Gamma_hat, key of ``emricat.emri.rate_curve.CURVES``.
    rate_curve: str = "broggi22"
    #: Model for the peak rate Gamma_hat and peak time t_E, key of ``emricat.emri.rate_curve.NORMALIZATIONS``.
    rate_normalization: str = "broggi22"
    rate_params: dict = field(default_factory=dict)

    #: Distribution of the time between major mergers, key of ``emricat.emri.merger_clock.MERGER_CLOCKS``.
    merger_clock: str = "merger_trees"
    merger_clock_params: dict = field(default_factory=dict)
    #: How to draw the time since the last merger inside the interval:
    #: "uniform" (slide 9) or "length_biased" (see merger_clock.py docstring).
    time_since_merger: str = "uniform"


@dataclass
class UniverseConfig:
    """Steps 4-5 options (coordinators): replicas, Poisson draw, detection."""

    #: Time width of the shell around each snapshot [yr]. None = use the midpoints
    #: between consecutive snapshots (recommended once dense snapshots exist).
    shell_dt: float | None = 100.0 * MYR
    #: "thin_shell" uses dV = 4 pi D_c^2 c (1+z) dt (slide 13); "exact" uses V_c(z2) - V_c(z1).
    shell_volume: str = "exact"
    #: How to turn the (non-integer) expected number of copies N_i into an integer:
    #: "poisson" (unbiased, adds cosmic variance) or "stochastic_round" (floor + Bernoulli).
    replica_rounding: str = "poisson"
    #: Monte Carlo cost control, see emricat/universe/replication.py.
    #: None = brute force: every copy of every galaxy is drawn explicitly (slide 14).
    #: K (int) = draw at most K replicas per galaxy, each standing for N_i/K real
    #: galaxies (column ``replica_weight``). Expected counts are unchanged.
    max_replicas_per_galaxy: int | None = None
    #: "snapshot" (all events at the snapshot z) or "uniform_in_volume" (spread inside the shell).
    event_redshift: str = "snapshot"
    #: Detection model, key of ``emricat.universe.detection.DETECTION_MODELS`` ("none" keeps all).
    detection: str = "none"
    detection_params: dict = field(default_factory=dict)


@dataclass
class Config:
    """Top-level configuration (one section per pipeline stage)."""

    run: RunConfig = field(default_factory=RunConfig)
    population: PopulationConfig = field(default_factory=PopulationConfig)
    nsc: NSCConfig = field(default_factory=NSCConfig)
    emri: EMRIConfig = field(default_factory=EMRIConfig)
    universe: UniverseConfig = field(default_factory=UniverseConfig)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


_SECTIONS = {
    "run": RunConfig,
    "population": PopulationConfig,
    "nsc": NSCConfig,
    "emri": EMRIConfig,
    "universe": UniverseConfig,
}


def config_from_dict(d: dict) -> Config:
    """Build a :class:`Config` from a (possibly partial) nested dict."""
    unknown = set(d) - set(_SECTIONS)
    if unknown:
        raise KeyError(f"Unknown config section(s): {sorted(unknown)}. Allowed: {sorted(_SECTIONS)}")
    kwargs = {}
    for name, cls in _SECTIONS.items():
        section = d.get(name) or {}
        allowed = {f.name for f in dataclasses.fields(cls)}
        bad = set(section) - allowed
        if bad:
            raise KeyError(f"Unknown option(s) {sorted(bad)} in section '{name}'. Allowed: {sorted(allowed)}")
        kwargs[name] = cls(**{k: _coerce(cls, k, v) for k, v in section.items()})
    return Config(**kwargs)


def _coerce(cls, key, value):
    """Convert strings like "1.0e8" to numbers for numeric fields.

    PyYAML (YAML 1.1) reads ``1.0e8`` as a *string* (it wants ``1.0e+8``);
    this saves everybody from that trap.
    """
    ftype = str({f.name: f.type for f in dataclasses.fields(cls)}[key])
    if isinstance(value, str) and ("float" in ftype or "int" in ftype):
        num = float(value)
        return int(num) if ftype.startswith("int") else num
    return value


def load_config(path: str | Path) -> Config:
    """Load a YAML config file. Missing options take the defaults above."""
    with open(path) as f:
        d = yaml.safe_load(f) or {}
    return config_from_dict(d)


def save_config(cfg: Config, path: str | Path) -> None:
    """Write the full (defaults included) config to YAML, for reproducibility."""
    with open(path, "w") as f:
        yaml.safe_dump(cfg.to_dict(), f, sort_keys=False)
