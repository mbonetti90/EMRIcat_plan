#!/usr/bin/env python
"""Back-of-the-envelope cost of the brute-force Monte Carlo (Steps 4-5).

For a model with a given box size and number of galaxies per snapshot, prints
the number of copies of each galaxy per shell (slide 12), the total number of
replicas out to z_max, and the CPU time for a given throughput.

    python scripts/estimate_cost.py --box 110.7 --ngal 3e5 --dt 1e8 --zmax 4 --rate 4e6

``--rate`` (replicas per second per core) can be measured from the
``cpu_seconds`` / ``n_replicas_simulated`` columns written by the pipeline in
the /snapshots group (the mock run gives ~4e6/s with toy prescriptions; the
real ones will be slower).
"""

import argparse

import numpy as np

from emricat import cosmology

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--box", type=float, required=True, help="box side [cMpc]")
    p.add_argument("--ngal", type=float, required=True, help="galaxies with an MBH per snapshot")
    p.add_argument("--dt", type=float, default=1e8, help="shell width [yr]")
    p.add_argument("--zmax", type=float, default=4.0)
    p.add_argument("--rate", type=float, default=4e6, help="replicas per second per core")
    a = p.parse_args()

    cosmo = cosmology.get_cosmology()
    t_now = float(cosmology.cosmic_time(0.0, cosmo))
    t_min = float(cosmology.cosmic_time(a.zmax, cosmo))
    t_mid = np.arange(t_now - 0.5 * a.dt, t_min, -a.dt)
    z_mid = np.atleast_1d(cosmology.redshift_at_cosmic_time(t_mid, cosmo))
    vbox = a.box**3

    print(f"{'z':>6} {'copies/galaxy':>14}")
    total = 0.0
    for z in z_mid:
        copies = cosmology.shell_volume_thin(z, a.dt, cosmo) / vbox
        total += copies * a.ngal
    for z in [0.1, 0.5, 1, 2, 3, 4]:
        print(f"{z:6.1f} {cosmology.shell_volume_thin(z, a.dt, cosmo) / vbox:14.3g}")
    print(f"\nshells: {len(z_mid)}   total replicas: {total:.3g}")
    print(f"CPU time at {a.rate:.2g} replicas/s: {total / a.rate / 3600:.3g} core-hours")
