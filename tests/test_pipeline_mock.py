"""End-to-end run of the chain with TOY prescriptions (tests the plumbing, not the physics)."""

import h5py
import numpy as np

from emricat.catalogue import Catalogue
from emricat.pipeline import run, write_output
from emricat.universe.replication import draw_replica_counts, iter_replica_chunks


def test_mock_pipeline_runs_and_is_reproducible(mock_config):
    ev1, summ1 = run(mock_config)
    ev2, _ = run(mock_config)
    assert len(summ1["z"]) == 3
    assert summ1["n_emri_expected"].sum() > 0
    np.testing.assert_array_equal(ev1["n_emri"], ev2["n_emri"])
    np.testing.assert_array_equal(ev1["mbh_mass"], ev2["mbh_mass"])
    if len(ev1):
        assert np.all(ev1["n_emri"] > 0)
        assert np.all((ev1["event_redshift"] > 0) & (ev1["event_redshift"] < 3))

    path = write_output(ev1, summ1, mock_config)
    with h5py.File(path, "r") as f:
        assert "events" in f and "snapshots" in f and "config" in f.attrs


def test_replica_chunks_cover_all_replicas(rng):
    cat = Catalogue({"galaxy_id": np.arange(4), "mbh_mass": np.ones(4)})
    n_sim = np.array([0, 3, 7, 1])
    chunks = list(iter_replica_chunks(cat, n_sim, np.ones(4), chunk_size=4))
    allc = Catalogue.concatenate(chunks)
    assert len(allc) == n_sim.sum()
    np.testing.assert_array_equal(np.bincount(allc["galaxy_id"], minlength=4), n_sim)
    # replica ids run 0..n-1 for each galaxy, also across chunk boundaries
    np.testing.assert_array_equal(allc["replica_id"][allc["galaxy_id"] == 2], np.arange(7))


def test_replica_weights_preserve_expected_number(rng):
    expected = np.array([0.3, 5.0, 2000.0, 1e5])
    n_sim, w = draw_replica_counts(expected, rng, max_per_galaxy=100)
    assert n_sim.max() <= 100
    # number of real galaxies represented = n_sim * w, Poisson around expected
    represented = n_sim * w
    assert abs(represented[-1] - 1e5) < 5 * np.sqrt(1e5)
