# EMRICat

**EMRI rates and catalogues from MBH population models.**

EMRI rate predictions span ~3 orders of magnitude, largely because the
low-mass end of the MBH mass function (the LISA sweet spot) is unknown.
EMRICat is a spin-off of MBHcat: take the same galaxy + MBH models, add a
nuclear star cluster (NSC) to each galaxy, assign an EMRI rate from two-body
relaxation only (Broggi+22), and draw single events by Monte Carlo.
**Running the same chain on every model isolates the effect of the MBH mass
function on what LISA sees.** Deliverable: one EMRI catalogue per model.

> **Status: skeleton.** The infrastructure (data container, config, cosmology,
> replicas, Poisson draw, pipeline, plotting) works. The science functions are
> stubs with signatures and docstrings, which raise `NotImplementedError` until
> the groups fill them in. A fully *toy* version of every step (`emricat/mock.py`)
> lets the whole chain run today.

---

## The chain and who owns what

```
 MBHcat HDF5 snapshots
        │
        ▼
 ┌──────────────────────┐  Step 1   GROUP 1   emricat/mbh/
 │ MBH + host galaxies  │  M_bh, M_*, M_halo, number density, z
 └──────────┬───────────┘
            │  each snapshot = one shell of the Universe around LISA
            ▼
 ┌──────────────────────┐  Step 4   coordinators   emricat/universe/replication.py
 │ replicate galaxies   │  N_i = n_i ΔV_c copies of every galaxy (slides 12-13)
 └──────────┬───────────┘
            │  for every replica, independently (slide 14):
            ▼
 ┌──────────────────────┐  Step 2   GROUP 2   emricat/nsc/
 │ nuclear star cluster │  nucleus or not, M_NSC, R_eff, t_relax
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐  Step 3   GROUP 3   emricat/emri/
 │ merger clock + rate  │  Δt between mergers, time since merger, Γ(t) Broggi+22
 └──────────┬───────────┘
            ▼
 ┌──────────────────────┐  Step 5   coordinators   emricat/universe/sampling.py
 │ Poisson draw         │  λ = Γ T_obs/(1+z),  n ~ Poisson(λ)  → events
 └──────────┬───────────┘
            ▼
     EMRI catalogue (HDF5)  →  emricat/plotting/
```

| Package | Group | Slides | What to implement |
|---|---|---|---|
| `emricat/mbh/` | **Group 1** | 4 | `MBHcatReader` (file layout, units, central-MBH choice); denser snapshots |
| `emricat/nsc/` | **Group 2** | 5-6 | occupation fraction (Hoyer+21, double logistic), M_NSC (Hoyer+23), R_eff (Pechetti+20), scatter values, relaxation time |
| `emricat/emri/` | **Group 3** | 7-10 | Broggi+22 curve table + normalisation (Γ̂_E, t_E), merger clock from merger trees |
| `emricat/universe/` | coordinators | 12-14 | already working; detection criterion (SNR) to be defined |
| `emricat/plotting/` | everyone | — | add your diagnostic plots in your group's module |

To find every stub, search for `NotImplementedError` or `TODO (Group`:

```bash
grep -rn --include="*.py" "TODO (Group" emricat/
```

## Repository layout

```
emricat/
├── columns.py      ← DATA CONTRACT: every column, its unit and which group fills it
├── units.py        ← unit conventions (Msun, pc, yr, 1/yr, cMpc) + constants
├── catalogue.py    ← the single data container (dict of numpy columns + meta, HDF5 I/O)
├── config.py       ← all run options with defaults (loaded from YAML)
├── cosmology.py    ← distances, cosmic time, shell volumes (astropy wrapper)
├── rng.py          ← reproducible random streams for the Monte Carlo
├── registry.py     ← pick an implementation by name from the config
├── mock.py         ← TOY version of every step (testing only, NOT physics)
├── pipeline.py     ← runs the chain:  python -m emricat.pipeline config.yaml
├── mbh/            ← GROUP 1  readers.py, snapshots.py, hdf5_utils.py
├── nsc/            ← GROUP 2  occupation.py, scaling_relations.py, relaxation.py, populate.py
├── emri/           ← GROUP 3  rate_curve.py, merger_clock.py, assign.py
├── universe/       ← STEPS 4-5 replication.py, sampling.py, detection.py
├── plotting/       ← style.py (+ emricat.mplstyle), population.py, nsc.py, emri.py, catalogue.py
└── data/           ← small reference tables shipped with the code (Broggi+22 curve, ...)
configs/
├── mock.yaml               ← runs end-to-end now (toy prescriptions)
└── baseline_template.yaml  ← template for science runs (baseline choices of the slides)
scripts/
├── inspect_hdf5.py         ← print the structure of an unknown HDF5 file (Group 1 start here)
├── estimate_cost.py        ← replicas and CPU time of the brute-force Monte Carlo
└── make_diagnostic_plots.py← standard plots from one or more output catalogues
tests/                      ← pytest; tests/test_science_todo.py = per-group TODO tests
```

## Quick start

```bash
pip install -e ".[dev]"
```

```bash
python -m pytest
```

```bash
python -m emricat.pipeline configs/mock.yaml
```

```bash
python scripts/make_diagnostic_plots.py output/mock_emricat.h5 --outdir figures
```

```bash
python -m emricat.columns
```

The last command prints the data contract. The mock run takes about 1 s and
writes `output/mock_emricat.h5` with:

* `/events`: one row per replica that produced ≥1 EMRI (all galaxy, NSC and rate columns);
* `/snapshots`: per-snapshot summary (shell edges and volume, number of replicas, expected and drawn EMRIs, CPU time);
* root attribute `config`: the full YAML config used (for reproducibility).

## Design principles

1. **One data container, one contract.** Every step receives a `Catalogue`,
   *adds* the columns declared in `emricat/columns.py` and returns it.
   Groups only need to agree on that file.
2. **One unit system.** Msun, pc, yr, 1/yr, cMpc (see `emricat/units.py`).
   Readers convert on input; nothing else converts.
3. **Alternatives by name.** Each physical ingredient has a small dict of
   implementations (e.g. `MASS_RELATIONS = {"hoyer23": ..., "neumayer20": ...}`)
   and the YAML picks one. Comparing prescriptions = changing one line of config.
4. **Explicit randomness.** Every function that draws numbers takes an `rng`
   argument; streams are derived from the master seed and labels
   (`emricat/rng.py`). Same seed + same config = same catalogue.
5. **Vectorised and chunked.** Functions act on numpy arrays (one element per
   replica), and replicas are processed in chunks of `run.chunk_size`, so
   memory stays bounded.

## Monte Carlo cost (to be assessed)

Brute force means one row per copy of every galaxy. `scripts/estimate_cost.py`
gives, for TNG100 (110.7 cMpc box, ~3×10⁵ galaxies, 100 Myr shells to z = 4):
about 6.5×10³ copies per galaxy at z = 1 (matches slide 13), 122 shells, and
~3.5×10¹¹ replicas in total. That is ~25 core-hours at the toy-prescription
throughput (~4×10⁶ replicas/s). Real prescriptions will be slower, and TNG50-like
boxes need ~10× more copies.

A cheap mode is already available: `universe.max_replicas_per_galaxy: K`
simulates at most K replicas per galaxy, each standing for N_i/K real ones.
Expected counts are exact, and the only approximation is that those galaxies
share one NSC/merger draw, which matters only at second order since λ ≪ 1. Use
the brute force (`null`) on a test snapshot to validate K. Details are in
`emricat/universe/replication.py`.

## Open questions flagged in the code

* Relaxation-time definition: it must match the one used to scale the Broggi+22 curves (`nsc/relaxation.py`).
* Extrapolating the rate curve beyond t/t_E ≈ 10: power law, constant, or zero? (`emri/rate_curve.py`).
* Time since the last merger: uniform in the interval (slide 9), or length-biased (inspection paradox)? (`emri/merger_clock.py`).
* Intervals longer than the age of the Universe are currently capped at the age (`emri/merger_clock.py`).
* Each model's own cosmology vs Planck18 for shell volumes (`cosmology.py`).
* Galaxies with several MBHs, or without one (`mbh/readers.py`).
* Correlated scatter between M_NSC and R_eff; NSCs much lighter than their MBH (`nsc/populate.py`).
* Event redshifts within a shell; detection criterion (`universe/`).

See `CONTRIBUTING.md` for how to fill a stub.
