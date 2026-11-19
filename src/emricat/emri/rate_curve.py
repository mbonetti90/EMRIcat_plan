"""
GROUP 3 -- The Broggi+22 EMRI rate curve.

    Gamma(t) = Gamma_hat_E * f(t / t_E)

* f(x) : universal dimensionless shape (Broggi+22, MNRAS 514, 3270, Fig. 6),
         f(0) = 0, f(1) = 1 (peak), f(10) ~ 0.25.
* Gamma_hat_E : peak rate of a given nucleus [1/yr].
* t_E         : time of the peak [yr], ~ t_relax / 20 (slide 7).

Two registries:

``CURVES``          name -> callable f(x)
``NORMALIZATIONS``  name -> function(mbh_mass, nsc_mass, nsc_reff, t_relax, **params)
                            returning (Gamma_hat_E [1/yr], t_E [yr])

The table of Fig. 6 (reproduced by B. Sersante and D. Mancieri) should be
committed as ``src/emricat/data/broggi22_fig6_emri.txt`` with two columns
``x = t/t_E`` and ``f = Gamma/Gamma_hat``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from emricat import mock

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
BROGGI22_TABLE = DATA_DIR / "broggi22_fig6_emri.txt"


class TabulatedCurve:
    """Dimensionless rate curve f(x) interpolated from a table.

    Parameters
    ----------
    x, f : arrays
        Tabulated points (x = t/t_E, f = Gamma/Gamma_hat), x increasing.
    extrapolation : {"powerlaw", "constant", "zero"}
        What to do for x beyond the last tabulated point (Fig. 6 stops at
        x ~ 10, but replicas can be caught much later after a merger):
        * "powerlaw": continue with the log-log slope of the last few points,
        * "constant": keep the last value,
        * "zero": no EMRIs beyond the table (conservative).
        THIS IS A PHYSICAL CHOICE: discuss it in Group 3.
    n_tail : int
        Number of last points used to fit the power-law tail.
    """

    def __init__(self, x, f, extrapolation: str = "powerlaw", n_tail: int = 10):
        self.x = np.asarray(x, dtype=float)
        self.f = np.asarray(f, dtype=float)
        if np.any(np.diff(self.x) <= 0):
            raise ValueError("x must be strictly increasing.")
        self.extrapolation = extrapolation
        xt, ft = self.x[-n_tail:], self.f[-n_tail:]
        self.tail_slope = np.polyfit(np.log(xt), np.log(ft), 1)[0]

    @classmethod
    def from_file(cls, path=BROGGI22_TABLE, **kwargs) -> "TabulatedCurve":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Group 3: commit the Broggi+22 Fig. 6 table there "
                "(two columns: x=t/t_E, f=Gamma/Gamma_hat)."
            )
        x, f = np.loadtxt(path, unpack=True)
        return cls(x, f, **kwargs)

    def __call__(self, x):
        x = np.asarray(x, dtype=float)
        # Inside the table: linear interpolation; before x[0]: linear ramp from f(0)=0.
        xs = np.concatenate([[0.0], self.x]) if self.x[0] > 0 else self.x
        fs = np.concatenate([[0.0], self.f]) if self.x[0] > 0 else self.f
        out = np.interp(x, xs, fs)
        beyond = x > self.x[-1]
        if self.extrapolation == "powerlaw":
            out = np.where(beyond, self.f[-1] * (np.maximum(x, self.x[-1]) / self.x[-1]) ** self.tail_slope, out)
        elif self.extrapolation == "zero":
            out = np.where(beyond, 0.0, out)
        elif self.extrapolation != "constant":
            raise ValueError(f"Unknown extrapolation '{self.extrapolation}'.")
        return np.where(x < 0, 0.0, out)


def broggi22_curve(**kwargs) -> TabulatedCurve:
    """Load the Broggi+22 Fig. 6 EMRI curve (needs the data table, see module docstring)."""
    return TabulatedCurve.from_file(BROGGI22_TABLE, **kwargs)


def toy_curve(**_):
    """Analytic toy curve. TESTING ONLY."""
    return mock.toy_rate_curve


#: Registry: config key ``emri.rate_curve`` -> factory returning a callable f(x).
CURVES = {
    "broggi22": broggi22_curve,
    "toy": toy_curve,
}


# ----------------------------------------------------------------------
# Normalisation: peak rate and peak time of each nucleus
# ----------------------------------------------------------------------
def normalization_broggi22(mbh_mass, nsc_mass, nsc_reff, t_relax, **params):
    """Peak EMRI rate Gamma_hat_E and peak time t_E for each nucleus (Broggi+22).

    Parameters
    ----------
    mbh_mass : array [Msun]
    nsc_mass : array [Msun]
    nsc_reff : array [pc]
    t_relax  : array [yr]      from Group 2 (same definition as in Broggi+22!)

    Returns
    -------
    gamma_hat : array [1/yr]   peak rate
    t_peak    : array [yr]     time of the peak after the NSC reset

    TODO (Group 3):
      * extract the scaling of the peak rate with M_bh and nucleus properties
        from Broggi+22 (and the dependence on the stellar BH mass/number fraction),
      * check against the Milky Way value (~1e-7 /yr for 4e6 Msun, slide 8),
      * t_peak ~ t_relax / 20 (slide 7): confirm the exact factor.
    """
    raise NotImplementedError("Group 3: normalization_broggi22")


#: Registry: config key ``emri.rate_normalization`` -> function.
NORMALIZATIONS = {
    "broggi22": normalization_broggi22,
    "toy": mock.toy_rate_normalization,  # TESTING ONLY
}


def emri_rate(t_since_merger, gamma_hat, t_peak, curve) -> np.ndarray:
    """Source-frame EMRI rate at time ``t_since_merger`` after the NSC reset [1/yr].

        Gamma = Gamma_hat * f(t / t_peak)

    NaN inputs (replicas without NSC) give NaN, which the caller turns into 0.
    """
    return np.asarray(gamma_hat) * curve(np.asarray(t_since_merger) / np.asarray(t_peak))
