"""Group 1: MBHcat v2.1 reader, tested on a small synthetic file with the v2.1 layout
(the layout written by ``src/hdf5_MBHcat_catalog_v2.1.py::write_hdf5``)."""

import h5py
import numpy as np
import pytest

from emricat.config import config_from_dict
from emricat.mbh.readers import MBHcatReader, get_reader

BOX = 100.0  # cMpc


@pytest.fixture
def v21_file(tmp_path):
    path = tmp_path / "fake_model.hdf5"
    rng = np.random.default_rng(0)
    with h5py.File(path, "w") as f:
        h = f.create_group("Header")
        h.attrs.update({"SimulationName": "Fake", "HubbleConstant": 70.0, "OmegaMatter": 0.3,
                        "OmegaLambda": 0.7, "BoxSize": BOX, "RedshiftsAllBHs": [0.0001, 1.00312]})
        for z in (0.0001, 1.00312):
            g = f.create_group(f"AllBHs/Z{z:011.8f}")
            n = 50
            mass = 10 ** rng.uniform(5, 9, n)
            mass[0] = 0.0  # an unusable row, must be dropped
            g["BlackHoles/Mass"] = mass
            g["BlackHoles/Mdot"] = np.ones(n)
            g["BlackHoles/RadEff"] = 0.1 * np.ones(n)
            g["BlackHoles/NumberDensity"] = np.full(n, 1 / BOX**3)
            g["Galaxies/StellarMass"] = 1e3 * mass + 1e8
            # DarkMatterMass is optional in v2.1: omitted on purpose
    return path


def test_mbhcat_reader_v21(v21_file):
    r = MBHcatReader(path=str(v21_file), model_name="Fake")
    np.testing.assert_allclose(r.available_redshifts(), [0.0001, 1.00312])
    with pytest.warns(UserWarning, match="dropped 1 rows"):
        cat = r.read_snapshot(1.00312)
    assert len(cat) == 49
    assert np.all(cat["redshift"] == 1.00312)
    assert np.all(np.isnan(cat["halo_mass"]))
    assert cat.meta["SimulationName"] == "Fake"
    # number density = 1/V_box for a simulation
    np.testing.assert_allclose(cat["number_density"], 1 / BOX**3)
    with pytest.raises(KeyError):
        r.read_snapshot(2.0)


def test_mbhcat_reader_from_config(v21_file):
    cfg = config_from_dict({"population": {"reader": "mbhcat", "path": str(v21_file)}})
    assert isinstance(get_reader(cfg), MBHcatReader)
