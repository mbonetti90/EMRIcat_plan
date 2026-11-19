"""
Final-catalogue plots: the project deliverable is one EMRI catalogue per
model, showing how model choices change what LISA sees (slide 2).
"""

from __future__ import annotations

import numpy as np

from emricat.plotting.style import log10_safe, model_color, new_axes


def plot_event_redshift_distribution(events: dict, ax=None, bins=np.linspace(0, 4, 21), detected_only=False):
    """dN/dz of drawn EMRIs per model (histogram of counts per bin)."""
    ax = new_axes(ax)
    for name, ev in events.items():
        sel = ev["detected"] == 1 if detected_only else slice(None)
        ax.hist(ev["event_redshift"][sel], bins=bins, weights=ev["n_emri"][sel], histtype="step",
                lw=2, color=model_color(name), label=f"{name} ({int(ev['n_emri'][sel].sum())})")
    ax.set_xlabel("z")
    ax.set_ylabel("EMRIs per bin (mission)")
    ax.legend()
    return ax


def plot_event_mbh_mass_distribution(events: dict, ax=None, bins=np.arange(4, 9.1, 0.25)):
    """Distribution of MBH masses hosting the drawn EMRIs, per model."""
    ax = new_axes(ax)
    for name, ev in events.items():
        ax.hist(log10_safe(ev["mbh_mass"]), bins=bins, weights=ev["n_emri"], histtype="step", lw=2,
                color=model_color(name), label=name)
    ax.set_xlabel(r"$\log_{10}(M_\bullet/{\rm M_\odot})$")
    ax.set_ylabel("EMRIs per bin (mission)")
    ax.legend()
    return ax


def plot_expected_vs_drawn(summaries: dict, ax=None):
    """Per-snapshot expected number of EMRIs (line) vs Poisson-drawn (points).

    ``summaries = {model: summary table}`` as written in the /snapshots group.
    """
    ax = new_axes(ax)
    for name, s in summaries.items():
        c = model_color(name)
        ax.plot(s["z"], s["n_emri_expected"], color=c, label=f"{name} expected")
        ax.plot(s["z"], s["n_emri_drawn"], "o", color=c, mfc="none", label=f"{name} drawn")
    ax.set_yscale("log")
    ax.set_xlabel("snapshot z")
    ax.set_ylabel("EMRIs per shell (mission)")
    ax.legend()
    return ax


def plot_total_counts(totals: dict, ax=None):
    """Total expected EMRIs per model, one dot each (log scale): the headline comparison."""
    ax = new_axes(ax)
    names = list(totals)
    ax.scatter(range(len(names)), [totals[n] for n in names], c=[model_color(n) for n in names], s=60, zorder=3)
    ax.set_xticks(range(len(names)), names, rotation=30, ha="right")
    ax.set_yscale("log")
    ax.set_ylabel("expected EMRIs in the mission")
    return ax
