"""
GROUP 2 -- Step driver: attach a nuclear star cluster to every replica.

This function only *chains* the building blocks of occupation.py,
scaling_relations.py and relaxation.py. It is already complete: Group 2
mainly needs to fill the building blocks. Change it only if the logic changes
(e.g. if the radius should depend on M_* too).

Called by :mod:`emricat.pipeline` once per chunk of replicas, i.e. every
replica gets its own independent draw (slide 14, points 1-2).
"""

from __future__ import annotations

import numpy as np

from emricat.catalogue import Catalogue
from emricat.columns import REQUIRED_GROUP1
from emricat.nsc.occupation import draw_has_nsc
from emricat.nsc.relaxation import RELAXATION_MODELS
from emricat.nsc.scaling_relations import MASS_RELATIONS, RADIUS_RELATIONS, lognormal_scatter
from emricat.registry import choose


def populate_nuclei(cat: Catalogue, cfg_nsc, rng: np.random.Generator) -> Catalogue:
    """Add the Group 2 columns to ``cat`` (in place) and return it.

    Parameters
    ----------
    cat : Catalogue
        Replicas, with at least the Group 1 columns.
    cfg_nsc : emricat.config.NSCConfig
    rng : numpy.random.Generator

    Adds
    ----
    has_nsc, nsc_mass, nsc_reff, t_relax
    """
    cat.require(REQUIRED_GROUP1, who="populate_nuclei")
    m_star = cat["stellar_mass"]

    # 1) Nucleus or not (slide 14, point 1)
    has_nsc = draw_has_nsc(m_star, cfg_nsc.occupation, rng, **cfg_nsc.occupation_params)

    # 2) NSC mass and radius, median relation + log-normal scatter (slide 14, point 2)
    mass_fn = choose(MASS_RELATIONS, cfg_nsc.mass_relation, "NSC mass relation")
    radius_fn = choose(RADIUS_RELATIONS, cfg_nsc.radius_relation, "NSC radius relation")

    m_nsc = lognormal_scatter(mass_fn(m_star), cfg_nsc.mass_scatter_dex, rng)
    r_eff = lognormal_scatter(radius_fn(m_nsc), cfg_nsc.radius_scatter_dex, rng)
    # NOTE (to discuss): should the radius scatter be correlated with the mass scatter?
    # NOTE (to discuss): what if m_nsc << mbh_mass? (NSC likely eroded; see occupation cutoff)

    # 3) Relaxation time -> clock of the Broggi+22 curve
    relax_fn = choose(RELAXATION_MODELS, cfg_nsc.relaxation, "relaxation model")
    t_relax = relax_fn(m_nsc, r_eff, cat["mbh_mass"], **cfg_nsc.relaxation_params)

    # Replicas without NSC: zero mass, undefined radius/relaxation.
    no = has_nsc == 0
    m_nsc = np.where(no, 0.0, m_nsc)
    r_eff = np.where(no, np.nan, r_eff)
    t_relax = np.where(no, np.nan, t_relax)

    cat["has_nsc"] = has_nsc
    cat["nsc_mass"] = m_nsc
    cat["nsc_reff"] = r_eff
    cat["t_relax"] = t_relax
    return cat
