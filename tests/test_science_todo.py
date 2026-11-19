"""
Science tests to be written by each group. They are SKIPPED until the
corresponding function is implemented: remove the ``skip`` marker and fill
the test when you implement the function. Each one is a TODO list.
"""

import numpy as np
import pytest

todo = pytest.mark.skip(reason="TODO: implement the function, then this test")


# ---------------------------------------------------------------- Group 1
@todo
def test_group1_mbhcat_reader_mass_function():
    """Read one MBHcat snapshot; compare the MBH mass function with arXiv:2605.00092."""


@todo
def test_group1_number_density_is_one_over_box():
    """For a simulation, number_density == 1/V_box for every galaxy."""


# ---------------------------------------------------------------- Group 2
@todo
def test_group2_hoyer21_logistic_half_at_m50():
    from emricat.nsc.occupation import occupation_hoyer21

    assert occupation_hoyer21(np.array([10**8.63]))[0] == pytest.approx(0.5)


@todo
def test_group2_double_logistic_peaks_near_1e10():
    """Slide 6: maximum ~70% at log M* ~ 10, dropping at higher mass."""


@todo
def test_group2_hoyer23_reproduces_slide5_plot():
    """Spot-check a few values of M_NSC(M_*) against the paper."""


@todo
def test_group2_pechetti20_radius_normalisation():
    """R_eff at a reference NSC mass, from the paper."""


@todo
def test_group2_relaxation_time_milky_way():
    """MW-like NSC (~2.5e7 Msun, ~4 pc, 4e6 Msun MBH): t_relax of a few Gyr (check value)."""


# ---------------------------------------------------------------- Group 3
@todo
def test_group3_broggi22_curve_peak_at_one():
    from emricat.emri.rate_curve import broggi22_curve

    f = broggi22_curve()
    x = np.linspace(0.05, 10, 2000)
    assert x[np.argmax(f(x))] == pytest.approx(1.0, abs=0.1)


@todo
def test_group3_milky_way_peak_rate():
    """Slide 8: MW-like MBH peak rate ~1e-7 /yr within the Broggi+22 range."""


@todo
def test_group3_merger_clock_mean_interval():
    """Slide 10: <Delta t> ~ 2 Gyr at z=0 and ~0.5 Gyr at z~2 (within x2)."""
