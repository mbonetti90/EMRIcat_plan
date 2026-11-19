"""
GROUP 2 diagnostic plots: NSC relations and occupation fraction (slides 5-6).
"""

from __future__ import annotations

import warnings

import numpy as np

from emricat.nsc.occupation import OCCUPATION_MODELS
from emricat.nsc.scaling_relations import MASS_RELATIONS
from emricat.plotting.style import LINESTYLES, binned_median, log10_safe, new_axes


def plot_nsc_mass_relations(names=None, ax=None, log_mstar=np.linspace(4, 12, 200)):
    """Reproduce the slide-5 comparison of M_NSC(M_*) relations.

    Relations not implemented yet are skipped with a warning.
    """
    ax = new_axes(ax)
    names = names or [n for n in MASS_RELATIONS if n != "toy"]
    for i, name in enumerate(names):
        try:
            m_nsc = MASS_RELATIONS[name](10**log_mstar)
        except NotImplementedError:
            warnings.warn(f"NSC mass relation '{name}' not implemented yet: skipped.")
            continue
        ax.plot(log_mstar, np.log10(m_nsc), ls=LINESTYLES[i % len(LINESTYLES)], label=name)
    ax.set_xlabel(r"$\log_{10}(M_\star/{\rm M_\odot})$")
    ax.set_ylabel(r"$\log_{10}(M_{\rm NSC}/{\rm M_\odot})$")
    ax.legend()
    return ax


def plot_occupation_fraction(names=None, ax=None, log_mstar=np.linspace(2.5, 12.5, 300), params=None):
    """Nucleation fraction f_nuc(M_*) for the available occupation models (slide 6)."""
    ax = new_axes(ax)
    names = names or list(OCCUPATION_MODELS)
    params = params or {}
    for i, name in enumerate(names):
        try:
            f = OCCUPATION_MODELS[name](10**log_mstar, **params.get(name, {}))
        except NotImplementedError:
            warnings.warn(f"Occupation model '{name}' not implemented yet: skipped.")
            continue
        ax.plot(log_mstar, 100 * f, ls=LINESTYLES[i % len(LINESTYLES)], label=name)
    ax.set_xlabel(r"$\log_{10}(M_\star/{\rm M_\odot})$")
    ax.set_ylabel(r"$f_{\rm nuc}\ [\%]$")
    ax.set_ylim(-3, 103)
    ax.legend()
    return ax


def plot_nsc_population(cat, ax=None, x="stellar_mass", y="nsc_mass", bins=None, n_points=20_000, rng=None):
    """Scatter (random subsample) + running median of an NSC column vs a galaxy column.

    Useful to check the drawn scatter, e.g. ``y="nsc_reff", x="nsc_mass"`` or ``y="t_relax"``.
    """
    ax = new_axes(ax)
    rng = rng or np.random.default_rng(0)
    sel = np.flatnonzero(cat["has_nsc"] == 1)
    if sel.size > n_points:
        sel = rng.choice(sel, n_points, replace=False)
    lx, ly = log10_safe(cat[x][sel]), log10_safe(cat[y][sel])
    ax.scatter(lx, ly, s=2, alpha=0.3, color="0.5", rasterized=True)
    bins = np.linspace(np.nanmin(lx), np.nanmax(lx), 20) if bins is None else bins
    xc, q = binned_median(lx, ly, bins)
    ax.plot(xc, q[1], color="k")
    ax.plot(xc, q[0], color="k", ls="--", lw=1)
    ax.plot(xc, q[2], color="k", ls="--", lw=1)
    ax.set_xlabel(rf"$\log_{{10}}$ {x}")
    ax.set_ylabel(rf"$\log_{{10}}$ {y}")
    return ax
