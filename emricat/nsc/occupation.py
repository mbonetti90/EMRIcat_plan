"""
GROUP 2 -- NSC occupation (nucleation) fraction  (slide 6).

Two approaches will be compared:

1. ``"all"``: every galaxy hosts an NSC (f_nuc = 1).
2. Draw whether each replica hosts an NSC from the nucleation fraction
   measured in the Local Volume (Hoyer+21, MNRAS 507, 3246):

   * ``"hoyer21"``          single logistic (keeps rising at high mass),
   * ``"double_logistic"``  refit with a high-mass cutoff (E. Bortolas),
                            follows the drop of f_nuc in massive galaxies.

Interface
---------
Every occupation model is a function

    f(stellar_mass: ndarray [Msun], **params) -> ndarray in [0, 1]

registered in ``OCCUPATION_MODELS``. The Bernoulli draw is done once,
generically, in :func:`draw_has_nsc`.
"""

from __future__ import annotations

import numpy as np

from emricat.registry import choose


def occupation_all(stellar_mass, **_):
    """Every galaxy is nucleated: f_nuc = 1."""
    return np.ones_like(np.asarray(stellar_mass, dtype=float))


def occupation_hoyer21(stellar_mass, kappa: float = 1.40, log_m50: float = 8.63, **_):
    """Single logistic nucleation fraction of Hoyer+21 (Local Volume).

    Expected form (CHECK against the paper!):

        f_nuc(M_*) = 1 / (1 + exp[-kappa * (log10 M_* - log_m50)])

    Default parameters are those quoted on slide 6 (kappa=1.40, M50=8.63).

    Parameters
    ----------
    stellar_mass : array [Msun]
    kappa : float      steepness
    log_m50 : float    log10 of the stellar mass with f_nuc = 0.5

    Returns
    -------
    f_nuc : array in [0, 1]
    """
    # TODO (Group 2): implement and add a test against Fig. of Hoyer+21.
    raise NotImplementedError("Group 2: occupation_hoyer21")


def occupation_double_logistic(
    stellar_mass,
    kappa: float = 1.28,
    log_m50: float = 8.65,
    kappa_c: float = 1.71,
    log_mc: float = 10.96,
    **_,
):
    """Double logistic: rising logistic times a high-mass cutoff (slide 6 refit).

    Best-fit values from slide 6: kappa = 1.28, log M50 = 8.65,
    kappa_c = 1.71, log M_c = 10.96. The exact functional form must be taken
    from E. Bortolas' fit script; a natural guess is

        f = 1/(1+exp[-kappa (x - log_m50)]) * 1/(1+exp[+kappa_c (x - log_mc)]),   x = log10 M_*

    Consider also drawing (kappa, log_m50, ...) from the posterior instead of
    fixing them, to propagate the fit uncertainty (68%/95% bands on slide 6).
    """
    # TODO (Group 2): implement (ask E. Bortolas for the fit code).
    raise NotImplementedError("Group 2: occupation_double_logistic")


#: Registry: config key ``nsc.occupation`` -> function.
OCCUPATION_MODELS = {
    "all": occupation_all,
    "hoyer21": occupation_hoyer21,
    "double_logistic": occupation_double_logistic,
}


def draw_has_nsc(stellar_mass, model: str, rng: np.random.Generator, **params) -> np.ndarray:
    """Bernoulli draw: does each replica host an NSC?  (Step 5.1, slide 14)

    Returns an int8 array of 0/1.
    """
    f_nuc = choose(OCCUPATION_MODELS, model, "NSC occupation model")(stellar_mass, **params)
    if np.any((f_nuc < 0) | (f_nuc > 1)):
        raise ValueError("Occupation fraction outside [0, 1].")
    return (rng.uniform(size=np.shape(f_nuc)) < f_nuc).astype(np.int8)
