"""
GROUP 3 -- Time-dependent EMRI rate (pipeline Step 3).

Responsibility
--------------
For each replica with a nucleus, assign the *current* EMRI rate:

1. Merger clock (slide 10): draw the time between two major mergers,
   Delta_t, from the distribution measured on merger trees, as a function of
   stellar mass and redshift (A. Trinca).
2. Time since last merger (slide 9): the snapshot catches the system at a
   random time t inside that interval.
3. Rate curve (slides 7-8): after each merger the NSC is "reset" (t = 0);
   the EMRI rate rises, peaks at t_E ~ t_relax/20 and slowly declines,
   following the universal dimensionless curve of Broggi+22 (Fig. 6):

        Gamma(t) = Gamma_hat_E * f(t / t_E),       f(1) = 1

   where Gamma_hat_E (peak rate) and t_E (peak time) depend on the MBH and
   the nucleus.

Only two-body relaxation is considered (slide 2).

Output columns (``emricat.columns.REQUIRED_GROUP3``):
    t_between_mergers [yr], t_since_merger [yr], emri_rate [1/yr]
    (+ emri_rate_peak [1/yr], t_emri_peak [yr])

Modules
-------
rate_curve.py    dimensionless curve f(x) and normalisation (Gamma_hat_E, t_E)
merger_clock.py  time between major mergers and time since the last one
assign.py        the step driver: assign_emri_rates(cat, cfg, rng)
"""

from emricat.emri.assign import assign_emri_rates  # noqa: F401
