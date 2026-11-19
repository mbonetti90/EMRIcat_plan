"""
GROUP 2 -- Nuclear star clusters (pipeline Step 2).

Responsibility
--------------
Given each galaxy *replica* (stellar mass, MBH mass, redshift), decide
whether it hosts a nuclear star cluster (NSC) and draw its properties:

    has_nsc, nsc_mass [Msun], nsc_reff [pc], (nsc_sigma [km/s]), t_relax [yr]

(see ``emricat.columns.REQUIRED_GROUP2``).

Choices made so far (slides 5-6)
--------------------------------
* Mass:      Hoyer+23, single power law in M_* at all masses.
* Radius:    Pechetti+20, R_eff ~ M_NSC^0.33 (about 2 pc at 1e8 Msun... check!).
* Scatter:   to be added around both relations (log-normal, in dex).
* Occupation: two cases, (a) every galaxy has an NSC, (b) Bernoulli draw from
             the Local Volume nucleation fraction (Hoyer+21, or the
             double-logistic refit with high-mass cutoff).

Note: parts of this have already been implemented by R. Caleno and T. Zana
in a separate code; the plan is to port those functions here, keeping the
signatures below.

Modules
-------
occupation.py         nucleation fraction f_nuc(M_*) and the Bernoulli draw
scaling_relations.py  M_NSC(M_*), R_eff(M_NSC) and log-normal scatter
relaxation.py         relaxation time of the nucleus (sets the Broggi+22 clock)
populate.py           the step driver: populate_nuclei(cat, cfg, rng)
"""

from emricat.nsc.populate import populate_nuclei  # noqa: F401
