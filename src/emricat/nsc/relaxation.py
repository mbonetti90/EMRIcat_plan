"""
GROUP 2 -- Relaxation time of the nucleus.

Why it matters (slide 7): the Broggi+22 EMRI-rate curve is universal when
time is measured in units of the nucleus relaxation time; the peak occurs at
roughly t_relax / 20. So t_relax sets *when* each nucleus is near its peak
rate, and this is the hand-over quantity between Group 2 and Group 3.

!! The definition used here MUST match the one used by Broggi+22 to scale
!! their curves (half-mass relaxation of the cluster? relaxation at the MBH
!! influence radius?). Group 2 and Group 3 should agree on this together.

Interface
---------
    f(nsc_mass [Msun], nsc_reff [pc], mbh_mass [Msun], **params) -> t_relax [yr]

Useful formulae (Binney & Tremaine 2008; Spitzer 1987)
-------------------------------------------------------
Half-mass relaxation time:
    t_rh = 0.138 N^(1/2) r_h^(3/2) / (m_*^(1/2) G^(1/2) ln Lambda),  N = M / m_*
Local relaxation time:
    t_r  = 0.34 sigma^3 / (G^2 m_* rho ln Lambda)
Influence radius:
    r_h,MBH ~ G M_bh / sigma^2   (or radius enclosing 2 M_bh in stars)

Use the constants in :mod:`emricat.units` (e.g. ``G_PC3_MSUN_YR2``) so the
result is directly in years.
"""

from __future__ import annotations

from emricat import mock


def relaxation_half_mass(nsc_mass, nsc_reff, mbh_mass, m_star: float = 1.0, ln_lambda: float | None = None, **params):
    """Half-mass relaxation time of the NSC [yr].

    Parameters
    ----------
    nsc_mass : array [Msun]
    nsc_reff : array [pc]       effective radius; r_h ~ (4/3) R_eff for a Plummer/Sersic-like profile (check!)
    mbh_mass : array [Msun]     may enter through ln Lambda or be ignored
    m_star : float [Msun]       mean stellar mass
    ln_lambda : float or None   Coulomb logarithm; None -> ln(0.4 N) or ln(M_bh/m_star)?

    Returns
    -------
    t_relax : array [yr]
    """
    # TODO (Group 2): implement (see mock.toy_relaxation_time for a minimal version).
    raise NotImplementedError("Group 2: relaxation_half_mass")


def relaxation_influence_radius(nsc_mass, nsc_reff, mbh_mass, m_star: float = 1.0, **params):
    """Relaxation time evaluated at the MBH influence radius [yr].

    Needs a density profile for the NSC (e.g. Dehnen/Plummer with the given
    mass and R_eff) to compute rho and sigma at r_infl.
    """
    # TODO (Group 2 + Group 3): implement if this is the definition used by Broggi+22.
    raise NotImplementedError("Group 2: relaxation_influence_radius")


#: Registry: config key ``nsc.relaxation`` -> function.
RELAXATION_MODELS = {
    "half_mass": relaxation_half_mass,
    "influence_radius": relaxation_influence_radius,
    "toy": mock.toy_relaxation_time,  # TESTING ONLY
}
