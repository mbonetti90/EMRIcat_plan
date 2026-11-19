"""
GROUP 1 diagnostic plots: what the MBH population models give us.

All functions work on Catalogues with the Group 1 columns (one row per
simulated galaxy, weighted by ``number_density``).
"""

from __future__ import annotations

import numpy as np

from emricat.plotting.style import binned_median, log10_safe, model_color, new_axes


def mass_function(cat, column: str = "mbh_mass", bins=None):
    """Weighted mass function Phi = dn/dlog10M [cMpc^-3 dex^-1].

    Returns (bin centres in log10 M, Phi).
    """
    bins = np.arange(4.0, 12.6, 0.25) if bins is None else bins
    logm = log10_safe(cat[column])
    ok = np.isfinite(logm)
    hist, _ = np.histogram(logm[ok], bins=bins, weights=cat["number_density"][ok])
    return 0.5 * (bins[1:] + bins[:-1]), hist / np.diff(bins)


def plot_mass_function(cats: dict, column: str = "mbh_mass", ax=None, bins=None, **kw):
    """Compare mass functions of several models: ``cats = {model: Catalogue}``."""
    ax = new_axes(ax)
    for name, cat in cats.items():
        x, phi = mass_function(cat, column, bins)
        ok = phi > 0
        ax.plot(x[ok], phi[ok], color=model_color(name), label=name, **kw)
    ax.set_yscale("log")
    label = {"mbh_mass": r"M_\bullet", "stellar_mass": r"M_\star"}.get(column, column)
    ax.set_xlabel(rf"$\log_{{10}}({label}/{{\rm M_\odot}})$")
    ax.set_ylabel(r"$\Phi\ [{\rm cMpc^{-3}\,dex^{-1}}]$")
    ax.legend()
    return ax


def plot_mbh_vs_stellar_mass(cats: dict, ax=None, bins=None):
    """Median and 16-84% band of log M_bh in bins of log M_* for each model."""
    ax = new_axes(ax)
    bins = np.arange(7.0, 12.6, 0.25) if bins is None else bins
    for name, cat in cats.items():
        xc, q = binned_median(log10_safe(cat["stellar_mass"]), log10_safe(cat["mbh_mass"]), bins)
        c = model_color(name)
        ax.plot(xc, q[1], color=c, label=name)
        ax.fill_between(xc, q[0], q[2], color=c, alpha=0.2, lw=0)
    ax.set_xlabel(r"$\log_{10}(M_\star/{\rm M_\odot})$")
    ax.set_ylabel(r"$\log_{10}(M_\bullet/{\rm M_\odot})$")
    ax.legend()
    return ax
