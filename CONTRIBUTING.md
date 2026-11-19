# Contributing to EMRICat

## Filling a stub: the recipe

1. **Find your stubs:** `grep -rn --include="*.py" "TODO (Group 2" emricat/` (replace the number with your group's).
2. **Read the docstring.** It gives the expected signature, units, references
   and the open questions. Keep the signature, because the pipeline relies on it.
   If it really has to change, update the step driver (`populate.py`, `assign.py`,
   `readers.py`) in the same commit and tell the other groups.
3. **Implement it vectorised:** inputs and outputs are numpy arrays with one
   element per galaxy/replica. Avoid Python loops over galaxies.
4. **Units:** inputs and outputs in Msun, pc, yr, 1/yr (see `emricat/units.py`).
   Write the units in the docstring of every argument.
5. **Randomness:** if you draw random numbers, take `rng` as an argument
   and use only `rng.*` methods. Never call `np.random.seed` or `np.random.normal`.
6. **Literature values:** put them as keyword defaults, with the paper,
   equation or table number in the docstring, so they can be overridden from the
   YAML (`*_params` dictionaries).
7. **Test:** in `tests/test_science_todo.py`, remove the `@todo` marker from
   your test and fill it, or add new tests (e.g. reproduce a figure value from the paper).
8. **Plot:** add a diagnostic plot for your ingredient to your group's module in
   `emricat/plotting/`.
9. **Switch it on:** if your function is the new baseline, set it in
   `configs/baseline_template.yaml`.

## Adding an alternative prescription

Write a new function with the same signature and add it to the registry dict
at the bottom of the module (e.g. `MASS_RELATIONS["myrelation"] = nsc_mass_myrelation`).
You can then select it from the YAML with `nsc.mass_relation: myrelation`.

## Adding a new column

Declare it in `emricat/columns.py` (name, unit, producer, description) first.
The `Catalogue` warns about undeclared columns.

## Code style

* Comments and docstrings are welcome, even verbose ones: many people will read this code.
* Docstrings use NumPy style (`Parameters`, `Returns`).
* Keep the toy implementations in `emricat/mock.py`; they are for tests only.
* Run `python -m pytest` before pushing.

## Git workflow

* Work on a branch named after the group and topic, e.g. `g2-hoyer23`, and open a pull request to `main`.
* Do not commit large data files (MBHcat HDF5). They are ignored by `.gitignore`.
  Small reference tables go in `emricat/data/` (see its README).
