"""
Unit conventions and physical constants used throughout EMRICat.

READ THIS BEFORE WRITING ANY FUNCTION.
=====================================

To avoid unit bugs between groups, *every* number that travels between
modules (i.e. every column of a :class:`emricat.catalogue.Catalogue`, every
function argument and every return value) uses these internal units:

    ==============  ==========================  ===========================
    quantity        internal unit               note
    ==============  ==========================  ===========================
    mass            solar masses  [Msun]        LINEAR, not log10
    length          parsec        [pc]          (NSC radii etc.)
    time            year          [yr]          also for Gyr-scale times!
    rate            per year      [1/yr]        intrinsic (source frame)
    volume          comoving Mpc^3 [cMpc^3]     cosmological volumes only
    number density  [cMpc^-3]
    velocity        km/s
    redshift        dimensionless
    ==============  ==========================  ===========================

Rules of thumb
--------------
* If an input file stores ``log10(M)``, convert to linear Msun *inside the
  reader* (Group 1); downstream code always receives linear masses.
* If a file stores masses in ``1e10 Msun/h`` (common in simulations), the
  reader converts them using the model's own ``h``.
* Times are always in years, even when they are naturally Gyr. Use the
  constants ``GYR`` and ``MYR`` below for readability, e.g. ``dt = 0.1 * GYR``.
* Rates are *source-frame* rates. The (1+z) time dilation is applied
  only once, in :mod:`emricat.universe.sampling`.

We deliberately do not use ``astropy.units`` Quantities in the hot loops
(they are slow on 1e8-element arrays). Astropy is used only inside
:mod:`emricat.cosmology`, which returns plain floats/arrays in the units above.
"""

# --------------------------------------------------------------------------
# Time conversions (internal unit: yr)
# --------------------------------------------------------------------------
YR = 1.0
KYR = 1.0e3
MYR = 1.0e6
GYR = 1.0e9
YR_IN_S = 3.15576e7  # Julian year [s]

# --------------------------------------------------------------------------
# Length conversions (internal unit: pc)
# --------------------------------------------------------------------------
PC = 1.0
KPC = 1.0e3
MPC = 1.0e6
PC_IN_M = 3.0856775814913673e16  # [m]
AU_IN_M = 1.495978707e11  # [m]

# --------------------------------------------------------------------------
# Mass (internal unit: Msun)
# --------------------------------------------------------------------------
MSUN_IN_KG = 1.988409870698051e30  # [kg]

# --------------------------------------------------------------------------
# Physical constants, expressed in internal units where convenient
# --------------------------------------------------------------------------
#: Gravitational constant in [pc (km/s)^2 / Msun]. Handy for virial estimates
#: like sigma^2 ~ G M / R with M in Msun, R in pc, sigma in km/s.
G_PC_KMS2_MSUN = 4.30091727e-3

#: Gravitational constant in [pc^3 / (Msun yr^2)].
G_PC3_MSUN_YR2 = 4.498502151469554e-15

#: Speed of light in [km/s].
C_KMS = 299792.458

#: Speed of light in [pc/yr].
C_PC_YR = 0.30660139378555057

#: 1 km/s expressed in pc/yr.
KMS_IN_PC_YR = 1.0227121650537077e-6
