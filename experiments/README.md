# Computations and replay

## Main checks

From the repository root, use Python, GNU Make, and a C++20 compiler. The archived checks were replayed with Python 3.14 and GCC 16.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r experiments/requirements-verify.txt
make verify
```

`make verify` uses the repository's `.venv` when present. Set `PYTHON` to the absolute path of a different interpreter or set `CXX` to select the compiler.

| Check | Scope |
| --- | --- |
| [`grid_intersections.py`](workspace/grid_intersections.py) | Enumerates all 2,097,152 labeled seven-vertex graphs for the grid-count inequalities and equality case. |
| [`grid_support.cpp`](workspace/grid_support.cpp) | Computes disjoint-pair minima for the grid proof's incidence-support condition. [Log](logs/grids-and-triangles/grid-support.log) |
| [`root_cover_audit.py`](workspace/root_cover_audit.py) | Replays the parity and transport cases used to exclude a root contained in 21 grids. [Log](logs/grids-and-triangles/root-cover-audit.log) |
| [`level_seven_check.py`](workspace/level_seven_check.py) | Replays the rational rank certificates and checks the theta transform on five explicit lattice controls. [Log](logs/eigenlattices/level-seven-check.log) |

## Global-constraint certificates

The additional [global-constraints investigation](../research/session-ab2f.md)
uses the versions pinned in `requirements-global-constraints.txt`:

```sh
.venv/bin/python -m pip install -r experiments/requirements-global-constraints.txt
make verify-global-constraints
```

This target replays four integer Farkas certificates for size-twenty
transversal cocliques, seventeen elementary norm-16 counting certificates,
61 further integer Farkas branch certificates, eleven zero-class forest
witnesses, five exact scalar-theta witnesses, the incomplete-grid signature
and edge-completion certificates, and an integral grid-count witness. It
also checks the small covering enumeration for the all-red grid bound and
the exact minimum-Ramsey hemisphere witness. It does
not start a new SAT or mixed-integer search. These certificates prove the
stated local exclusions or feasibility of finite relaxations; none is a
solution of the existence problem.

The fourteen additional norm-16 exclusions have saved CNF cores and DRAT
proofs. Build [drat-trim](https://github.com/marijnheule/drat-trim) at revision
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`, then run:

```sh
make verify-coupled-shells DRAT_TRIM=/absolute/path/to/drat-trim
```

This target regenerates the five template censuses in two ways, compares the
478 canonical representatives with the archive, and replays every outcome:
seventeen counting exclusions, fourteen DRAT exclusions, and 447 explicit
partial adjacency witnesses. Each DRAT replay rebuilds the full formula,
checks its SHA-256 digest, verifies that the saved core contains only input
clauses of that formula, and runs the separate checker. The 447 witnesses
still have unchosen edges and do not certify strongly regular graphs.

The [norm-16 note](../research/eigenlattices/coupled_shells.md),
[transversal note](../research/independent-sets/transversal_constraints.md),
and [completion note](../research/unrestricted-completion.md) state the
reductions and their limits. Independent replay output is in
[`logs/session-ab2f/`](logs/session-ab2f/).

The [linear-certificate note](../research/eigenlattices/coupled_shells_linear.md)
also gives a command to project all 447 saved partial witnesses into the
independent aggregate model. That exact control passed. The 61 branch
certificates include complete proofs for ten already excluded templates;
they do not add ten more exclusions to the census.

## Explore the archive

Run the individual research scripts from [`experiments/workspace/`](workspace/). The Python and C++ sources, certificate JSON, candidate arrays, and cached moment data share this directory because the scripts use sibling paths.

The archived logs cover [grids and triangles](logs/grids-and-triangles/), [independent sets](logs/independent-sets/), [eigenlattices](logs/eigenlattices/), [moments and counts](logs/moments-and-counts/), and [construction searches](logs/construction-searches/). The [research ledger](../STATE.md) explains which runs concern relaxations or particular construction families.

Some exploratory scripts refer to solver builds and generated inputs in the original `/tmp/conway99-tools` directory, which was unavailable when the archive was published. The four checks above use the archived files and the dependencies listed here. The [initial publication](https://github.com/1337isnot1337/conway-99/tree/270ae4f8c4cfb751f9c4b5b74949c41263b645ba) preserves the original paths.
