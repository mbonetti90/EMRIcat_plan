"""
GROUP 3 diagnostic plots: rate curve, distribution of rates, merger clock (slides 7-10).
"""

from __future__ import annotations

import numpy as np

from emricat.plotting.style import binned_median, log10_safe, model_color, new_axes
from emricat.units import GYR


def plot_rate_curve(curve, ax=None, x=np.linspace(0, 15, 400), label="", **kw):
    """Dimensionless EMRI curve f(t/t_E) (compare with Broggi+22 Fig. 6, slide 7).

    The table range ends at x ~ 10: the plot goes beyond it to show the extrapolation.
    """
    ax = new_axes(ax)
    ax.plot(x, curve(x), label=label, **kw)
    ax.set_xlabel(r"$t/t_E$")
    ax.set_ylabel(r"$\Gamma_E/\hat\Gamma_E$")
    if label:
        ax.legend()
    return ax


def plot_rate_vs_mbh_mass(cats: dict, ax=None, bins=np.arange(4, 10.1, 0.25)):
    """Median (16-84%) EMRI rate vs MBH mass, nucleated replicas only.

    Compare with the Milky-Way range 1e-8 - 1e-6 /yr at 4e6 Msun (slide 8).
    """
    ax = new_axes(ax)
    for name, cat in cats.items():
        sel = cat["has_nsc"] == 1
        xc, q = binned_median(log10_safe(cat["mbh_mass"][sel]), log10_safe(cat["emri_rate"][sel]), bins)
        c = model_color(name)
        ax.plot(xc, q[1], color=c, label=name)
        ax.fill_between(xc, q[0], q[2], color=c, alpha=0.2, lw=0)
    ax.axvline(np.log10(4e6), color="0.4", ls=":", lw=1)
    ax.set_xlabel(r"$\log_{10}(M_\bullet/{\rm M_\odot})$")
    ax.set_ylabel(r"$\log_{10}(\Gamma_E\,/\,{\rm yr^{-1}})$")
    ax.legend()
    return ax


def plot_merger_intervals(cat, ax=None):
    """Mean drawn time between major mergers vs redshift (compare with slide 10)."""
    ax = new_axes(ax)
    z = cat["redshift"]
    zs = np.unique(z)
    mean = [np.mean(cat["t_between_mergers"][z == zi]) / GYR for zi in zs]
    ax.plot(zs, mean, "o-", label=r"$\langle\Delta t\rangle$ drawn")
    ax.set_xlabel("z")
    ax.set_ylabel(r"$\langle\Delta t\rangle$ [Gyr]")
    ax.legend()
    return ax


def plot_time_since_merger(cat, ax=None, bins=50):
    """Distribution of t_since_merger / t_E: where on the curve are replicas caught?"""
    ax = new_axes(ax)
    x = cat["t_since_merger"] / cat["t_emri_peak"]
    x = x[np.isfinite(x) & (x > 0)]
    ax.hist(np.log10(x), bins=bins, histtype="step")
    ax.axvline(0, color="0.4", ls=":", lw=1)
    ax.set_xlabel(r"$\log_{10}(t_{\rm since}/t_E)$")
    ax.set_ylabel("replicas")
    return ax
