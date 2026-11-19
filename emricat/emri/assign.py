"""
GROUP 3 -- Step driver: assign the current EMRI rate to every replica.

Chains merger_clock.py and rate_curve.py. Complete as is: Group 3 mainly
needs to fill the building blocks. Called once per chunk of replicas, so each
replica gets its own merger history (slide 14, points 3-4).
"""

from __future__ import annotations

import numpy as np

from emricat.catalogue import Catalogue
from emricat.columns import REQUIRED_GROUP2
from emricat.emri.merger_clock import MERGER_CLOCKS, draw_time_since_merger
from emricat.emri.rate_curve import CURVES, NORMALIZATIONS, emri_rate
from emricat.registry import choose

# The curve is loaded once per process (reading the table every chunk is wasteful).
_CURVE_CACHE: dict = {}


def get_curve(name: str, **params):
    key = (name, tuple(sorted(params.items())))
    if key not in _CURVE_CACHE:
        _CURVE_CACHE[key] = choose(CURVES, name, "EMRI rate curve")(**params)
    return _CURVE_CACHE[key]


def assign_emri_rates(cat: Catalogue, cfg_emri, rng: np.random.Generator) -> Catalogue:
    """Add the Group 3 columns to ``cat`` (in place) and return it.

    Adds
    ----
    t_between_mergers, t_since_merger, emri_rate_peak, t_emri_peak, emri_rate
    """
    cat.require(REQUIRED_GROUP2, who="assign_emri_rates")

    # 1) Merger clock (slide 14, point 3)
    clock = choose(MERGER_CLOCKS, cfg_emri.merger_clock, "merger clock")
    delta_t = clock(cat["stellar_mass"], cat["redshift"], rng, **cfg_emri.merger_clock_params)

    # 2) Time since the last merger (slide 14, point 4)
    t_since = draw_time_since_merger(delta_t, cat["redshift"], rng, method=cfg_emri.time_since_merger)

    # 3) Peak rate and peak time of each nucleus
    norm = choose(NORMALIZATIONS, cfg_emri.rate_normalization, "EMRI rate normalisation")
    gamma_hat, t_peak = norm(cat["mbh_mass"], cat["nsc_mass"], cat["nsc_reff"], cat["t_relax"], **cfg_emri.rate_params)

    # 4) Rate at the drawn time; no nucleus -> no EMRIs (two-body relaxation only)
    curve = get_curve(cfg_emri.rate_curve)
    rate = emri_rate(t_since, gamma_hat, t_peak, curve)
    rate = np.where(cat["has_nsc"] == 1, rate, 0.0)
    rate = np.nan_to_num(rate, nan=0.0)

    cat["t_between_mergers"] = delta_t
    cat["t_since_merger"] = t_since
    cat["emri_rate_peak"] = np.where(cat["has_nsc"] == 1, gamma_hat, 0.0)
    cat["t_emri_peak"] = t_peak
    cat["emri_rate"] = rate
    return cat
