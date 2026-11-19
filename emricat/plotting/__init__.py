"""
Common plotting tools for EMRICat.

* :mod:`~emricat.plotting.style`       style sheet, fixed model colours, savefig helper
* :mod:`~emricat.plotting.population`  Group 1 diagnostics (mass functions, M_bh-M_*)
* :mod:`~emricat.plotting.nsc`         Group 2 diagnostics (relations, occupation)
* :mod:`~emricat.plotting.emri`        Group 3 diagnostics (rate curve, rates, merger clock)
* :mod:`~emricat.plotting.catalogue`   final catalogue (event counts vs z, M_bh, model comparison)

Conventions
-----------
* Every function takes an optional ``ax`` and returns it, so plots can be
  combined into multi-panel figures.
* Functions comparing models take a dict ``{model_name: Catalogue}``; colours
  follow the model, not its position in the dict (:func:`style.model_color`).
* Masses are plotted as log10(M/Msun) on linear axes, rates in 1/yr.
* Save with :func:`style.savefig` (PDF for papers + PNG for slides).
"""

from emricat.plotting.style import model_color, new_axes, savefig, use_style  # noqa: F401
