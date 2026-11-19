"""Shared pytest fixtures."""

import numpy as np
import pytest

from emricat.config import config_from_dict


@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def mock_config(tmp_path):
    """Small, fast, all-toy configuration."""
    return config_from_dict(
        {
            "run": {"model_name": "mock", "output_dir": str(tmp_path), "chunk_size": 50_000},
            "population": {"reader": "mock", "params": {"redshifts": [0.5, 1.0, 2.0], "n_gal": 300}},
            "nsc": {"mass_relation": "toy", "radius_relation": "toy", "relaxation": "toy", "mass_scatter_dex": 0.3},
            "emri": {"rate_curve": "toy", "rate_normalization": "toy", "merger_clock": "toy"},
            "universe": {"max_replicas_per_galaxy": 50, "event_redshift": "uniform_in_volume"},
        }
    )
