#!/usr/bin/env python
"""Standard diagnostic plots from one or more EMRICat output files.

    python scripts/make_diagnostic_plots.py output/*_emricat.h5 --outdir figures

Each file is one model; models are compared in the same panels.
"""

import argparse
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from emricat.catalogue import Catalogue  # noqa: E402
from emricat.plotting import savefig, use_style  # noqa: E402
from emricat.plotting import catalogue as pcat  # noqa: E402
from emricat.plotting import emri as pemri  # noqa: E402


def load(path):
    events = Catalogue.read_hdf5(path, "events")
    with h5py.File(path, "r") as f:
        summary = {k: f["snapshots"][k][()] for k in f["snapshots"]}
    return events, summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+")
    p.add_argument("--outdir", default="figures")
    a = p.parse_args()

    use_style()
    events, summaries = {}, {}
    for f in a.files:
        ev, s = load(f)
        name = str(ev.meta.get("model", Path(f).stem))
        events[name], summaries[name] = ev, s

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    pcat.plot_event_redshift_distribution(events, ax=axes[0, 0])
    pcat.plot_event_mbh_mass_distribution(events, ax=axes[0, 1])
    pcat.plot_expected_vs_drawn(summaries, ax=axes[1, 0])
    pcat.plot_total_counts({n: s["n_emri_expected"].sum() for n, s in summaries.items()}, ax=axes[1, 1])
    fig.tight_layout()
    print(savefig(fig, "catalogue_overview", a.outdir))

    # Properties of the EMRI hosts (only replicas with events are stored by default)
    fig, ax = plt.subplots()
    pemri.plot_rate_vs_mbh_mass(events, ax=ax)
    ax.set_title("EMRI hosts only")
    print(savefig(fig, "emri_hosts_rate_vs_mbh", a.outdir))
