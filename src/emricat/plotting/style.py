"""
Common style for EMRICat plots.

Call :func:`use_style` once at the top of a script/notebook. Every model gets a
fixed colour (:func:`model_color`) so that "TNG100" is the same colour in
every figure of every group.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

STYLE_FILE = Path(__file__).with_name("emricat.mplstyle")

#: Categorical palette (colour-blind checked), assigned in this fixed order.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]

#: Fixed colour for known models. ADD NEW MODELS HERE, so that colours never
#: change between figures. Unknown models get the next free palette colour.
MODEL_COLORS: dict[str, str] = {
    "TNG50": PALETTE[0],
    "TNG100": PALETTE[1],
    "TNG300": PALETTE[2],
    "Horizon-AGN": PALETTE[3],
    "SIMBA": PALETTE[4],
    "L-Galaxies": PALETTE[5],
    "BACH": PALETTE[6],
    "mock": "#7f7f7f",
}

#: Line styles to distinguish *prescriptions* (e.g. occupation "all" vs "double_logistic")
#: while the colour distinguishes the MBH model.
LINESTYLES = ["-", "--", ":", "-."]


def use_style() -> None:
    """Activate the EMRICat matplotlib style."""
    plt.style.use(str(STYLE_FILE))


def model_color(name: str) -> str:
    """Stable colour for a model name."""
    if name not in MODEL_COLORS:
        used = set(MODEL_COLORS.values())
        free = [c for c in PALETTE if c not in used]
        if not free:
            raise ValueError("More than 8 models: use small multiples instead of more colours.")
        MODEL_COLORS[name] = free[0]
    return MODEL_COLORS[name]


def new_axes(ax=None, **subplot_kw):
    """Return ``ax`` if given, otherwise a new figure + axes."""
    if ax is not None:
        return ax
    _, ax = plt.subplots(**subplot_kw)
    return ax


def savefig(fig, name: str, outdir: str | Path = "figures", formats=("pdf", "png")) -> list[Path]:
    """Save ``fig`` as ``<outdir>/<name>.<fmt>`` for each format. Returns the paths."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for fmt in formats:
        p = outdir / f"{name}.{fmt}"
        fig.savefig(p)
        paths.append(p)
    return paths


def log10_safe(x):
    """log10 that maps non-positive values to NaN instead of warning/-inf."""
    x = np.asarray(x, dtype=float)
    out = np.full_like(x, np.nan)
    pos = x > 0
    out[pos] = np.log10(x[pos])
    return out


def binned_median(x, y, bins, quantiles=(0.16, 0.5, 0.84)):
    """Quantiles of y in bins of x. Returns (bin centres, array [n_q, n_bins])."""
    x, y = np.asarray(x), np.asarray(y)
    centres = 0.5 * (bins[1:] + bins[:-1])
    out = np.full((len(quantiles), len(centres)), np.nan)
    idx = np.digitize(x, bins) - 1
    for i in range(len(centres)):
        sel = (idx == i) & np.isfinite(y)
        if sel.sum() >= 5:
            out[:, i] = np.quantile(y[sel], quantiles)
    return centres, out
