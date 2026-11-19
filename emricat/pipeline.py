"""
The EMRICat chain, model by model (slide 3):

    1 MBHs and hosts    (Group 1, emricat.mbh)
    2 A nucleus each    (Group 2, emricat.nsc)
    3 EMRI rate         (Group 3, emricat.emri)
    4 Fill the Universe (emricat.universe.replication)
    5 Draw the events   (emricat.universe.sampling / detection)

Running the *same chain* on every MBH population model isolates the effect
of the uncertain MBH mass function on the EMRI rates LISA will measure.

Pseudo-code of :func:`run`
--------------------------
::

    for each snapshot z (one shell of the Universe each):
        galaxies = read snapshot                                  # Step 1
        N_i      = number_density_i * shell_volume                # Step 4
        for each chunk of replicas:
            nucleus or not, M_NSC, R_eff, t_relax                 # Step 2 / 5.1-5.2
            merger interval, time since merger, EMRI rate         # Step 3 / 5.3-5.4
            lambda = rate * T_obs/(1+z);  n ~ Poisson(lambda)     # Step 5.5-5.6
            keep replicas with n > 0
    event redshifts, detection, write catalogue

Command line
------------
    python -m emricat.pipeline configs/mock.yaml
    # or, after `pip install -e .`:
    emricat-run configs/mock.yaml
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import h5py
import numpy as np
import yaml

from emricat import cosmology
from emricat.catalogue import Catalogue
from emricat.config import Config, load_config
from emricat.emri import assign_emri_rates
from emricat.mbh import apply_cuts, get_reader
from emricat.nsc import populate_nuclei
from emricat.registry import choose
from emricat.rng import RandomStreams
from emricat.universe import replication, sampling
from emricat.universe.detection import DETECTION_MODELS

log = logging.getLogger("emricat")


def select_redshifts(available, cfg: Config) -> np.ndarray:
    """Snapshots to process: those requested in the config (or all), up to z_max."""
    z = np.sort(np.asarray(available, dtype=float))
    if cfg.population.redshifts is not None:
        wanted = np.asarray(cfg.population.redshifts, dtype=float)
        missing = [w for w in wanted if not np.any(np.isclose(z, w))]
        if missing:
            raise ValueError(f"Requested redshifts {missing} not available. Available: {z}")
        z = z[np.any(np.isclose(z[:, None], wanted[None, :]), axis=1)]
    return z[z <= cfg.run.z_max]


def process_snapshot(shell, reader, cfg: Config, streams: RandomStreams):
    """Run Steps 1-5 on one snapshot. Returns (events Catalogue, summary dict)."""
    t0 = time.perf_counter()

    # ---- Step 1: galaxies of this snapshot --------------------------------
    gal = reader.read_snapshot(shell.z, rng=streams.get("population", snapshot=shell.index))
    gal = apply_cuts(gal, cfg.population.min_stellar_mass, cfg.population.min_mbh_mass)

    # ---- Step 4: how many copies of each galaxy in the shell --------------
    n_expected = replication.expected_copies(gal, shell)
    n_sim, weight = replication.draw_replica_counts(
        n_expected,
        streams.get("replicas", snapshot=shell.index),
        rounding=cfg.universe.replica_rounding,
        max_per_galaxy=cfg.universe.max_replicas_per_galaxy,
    )

    # ---- Steps 2, 3, 5 on chunks of replicas -------------------------------
    kept, n_rep, sum_lambda, n_events = [], 0, 0.0, 0
    for j, chunk in enumerate(replication.iter_replica_chunks(gal, n_sim, weight, cfg.run.chunk_size)):
        populate_nuclei(chunk, cfg.nsc, streams.get("nsc", snapshot=shell.index, chunk=j))
        assign_emri_rates(chunk, cfg.emri, streams.get("emri", snapshot=shell.index, chunk=j))
        sampling.draw_events(chunk, cfg.run.t_obs, streams.get("poisson", snapshot=shell.index, chunk=j))

        n_rep += len(chunk)
        sum_lambda += float(chunk["n_emri_expected"].sum())
        n_events += int(chunk["n_emri"].sum())
        kept.append(chunk.select(chunk["n_emri"] > 0) if cfg.run.keep_only_events else chunk)

    summary = {
        "z": shell.z,
        "z_lo": shell.z_lo,
        "z_hi": shell.z_hi,
        "shell_volume_cmpc3": shell.volume,
        "n_galaxies": len(gal),
        "n_real_galaxies": float(n_expected.sum()),
        "n_replicas_simulated": n_rep,
        "n_emri_expected": sum_lambda,
        "n_emri_drawn": n_events,
        "cpu_seconds": time.perf_counter() - t0,
    }
    log.info(
        "z=%.3f  galaxies=%d  replicas=%.3g  <N_EMRI>=%.3g  drawn=%d  (%.1fs)",
        shell.z, len(gal), n_rep, sum_lambda, n_events, summary["cpu_seconds"],
    )
    return Catalogue.concatenate(kept), summary


def run(cfg: Config) -> tuple[Catalogue, dict]:
    """Run the full chain for one MBH population model. Returns (events, summary table)."""
    streams = RandomStreams(cfg.run.seed)
    reader = get_reader(cfg)
    cosmo = cosmology.get_cosmology(reader.cosmology_name)

    redshifts = select_redshifts(reader.available_redshifts(), cfg)
    shells = replication.build_shells(redshifts, cfg.universe, cosmo)
    log.info("Model %s: %d snapshots, z = %s", cfg.run.model_name, len(shells), np.round(redshifts, 3))

    all_events, summaries = [], []
    for shell in shells:
        ev, summ = process_snapshot(shell, reader, cfg, streams)
        all_events.append(ev)
        summaries.append(summ)
    events = Catalogue.concatenate(all_events)
    events.meta.update({"model": cfg.run.model_name, "seed": cfg.run.seed, "t_obs_yr": cfg.run.t_obs})

    if len(events) > 0:
        sampling.assign_event_redshifts(events, shells, cfg.universe.event_redshift, streams.get("event_z"))
        detect = choose(DETECTION_MODELS, cfg.universe.detection, "detection model")
        snr, detected = detect(events, streams.get("detection"), **cfg.universe.detection_params)
        events["snr"] = snr
        events["detected"] = detected

    summary_table = {k: np.array([s[k] for s in summaries]) for k in summaries[0]} if summaries else {}
    return events, summary_table


def write_output(events: Catalogue, summary: dict, cfg: Config) -> Path:
    """Write ``<output_dir>/<model>_emricat.h5`` with groups /events and /snapshots.

    The full config is stored as a YAML string in the root attribute ``config``.
    """
    out = Path(cfg.run.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{cfg.run.model_name}_emricat.h5"
    if path.exists():
        path.unlink()
    events.write_hdf5(path, group="events")
    with h5py.File(path, "a") as f:
        f.attrs["config"] = yaml.safe_dump(cfg.to_dict(), sort_keys=False)
        g = f.create_group("snapshots")
        for k, v in summary.items():
            g.create_dataset(k, data=v)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the EMRICat chain for one MBH population model.")
    parser.add_argument("config", help="YAML configuration file (see configs/)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(message)s")

    cfg = load_config(args.config)
    events, summary = run(cfg)
    path = write_output(events, summary, cfg)
    log.info("Total events: %d (expected %.3g). Written to %s",
             int(events["n_emri"].sum()) if len(events) else 0, float(np.sum(summary.get("n_emri_expected", 0))), path)


if __name__ == "__main__":
    main()
