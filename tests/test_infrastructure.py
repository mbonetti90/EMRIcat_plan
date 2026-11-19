"""Tests of the shared infrastructure (catalogue, config, rng, cosmology)."""

import numpy as np
import pytest

from emricat import cosmology
from emricat.catalogue import Catalogue
from emricat.config import config_from_dict
from emricat.rng import RandomStreams
from emricat.units import MYR


def test_catalogue_basic(tmp_path):
    cat = Catalogue({"mbh_mass": np.array([1e6, 1e7]), "stellar_mass": np.array([1e9, 1e10])}, meta={"model": "x"})
    assert len(cat) == 2
    cat.add_column("redshift", 1.0)  # scalar is broadcast
    assert np.all(cat["redshift"] == 1.0)
    with pytest.raises(ValueError):
        cat.add_column("halo_mass", np.ones(3))
    with pytest.warns(UserWarning):
        cat.add_column("not_in_contract", np.ones(2))

    sub = cat.select(cat["mbh_mass"] > 5e6)
    assert len(sub) == 1
    rep = cat.repeat(np.array([2, 3]))
    assert len(rep) == 5

    path = tmp_path / "c.h5"
    cat.write_hdf5(path, group="g")
    back = Catalogue.read_hdf5(path, group="g")
    assert back.meta["model"] == "x"
    np.testing.assert_array_equal(back["mbh_mass"], cat["mbh_mass"])


def test_require_reports_missing():
    cat = Catalogue({"mbh_mass": np.ones(2)})
    with pytest.raises(KeyError, match="stellar_mass"):
        cat.require(["mbh_mass", "stellar_mass"], who="test")


def test_config_rejects_typos():
    with pytest.raises(KeyError):
        config_from_dict({"nsc": {"mass_relaton": "hoyer23"}})
    with pytest.raises(KeyError):
        config_from_dict({"nscc": {}})


def test_config_yaml_float_trap():
    cfg = config_from_dict({"universe": {"shell_dt": "1.0e8"}})  # what PyYAML gives for 1.0e8
    assert cfg.universe.shell_dt == 1e8


def test_rng_reproducible_and_independent():
    s = RandomStreams(1)
    a = s.get("nsc", snapshot=1, chunk=0).normal(size=5)
    b = s.get("nsc", chunk=0, snapshot=1).normal(size=5)  # keyword order irrelevant
    c = s.get("nsc", snapshot=1, chunk=1).normal(size=5)
    np.testing.assert_array_equal(a, b)
    assert not np.allclose(a, c)


def test_shell_volume_matches_slide13():
    """Slide 13: at z=1 with dt=100 Myr one TNG100 galaxy stands for ~6500 real ones."""
    v_box = 110.7**3
    copies = cosmology.shell_volume_thin(1.0, 100 * MYR) / v_box
    assert 6000 < copies < 7000
    # exact and thin-shell volumes agree for thin shells
    lo, hi = cosmology.redshift_edges_from_dt(1.0, 100 * MYR)
    assert cosmology.shell_volume_exact(lo, hi) == pytest.approx(cosmology.shell_volume_thin(1.0, 100 * MYR), rel=0.01)
