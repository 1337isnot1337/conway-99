# Exterior incidence and exact packing at a fixed core

These tests concern arbitrary completions of a specified induced core. They impose no automorphism on the completed graph. The existence problem remains open.

Let B be the adjacency matrix on an m-vertex core, and let N describe edges from that core to the remaining 99-m vertices. Every completion satisfies

    NN^T = 12I + 2J - B - B^2.

An exterior signature is the subset of core vertices adjacent to one exterior vertex. A signature S must satisfy two integer conditions:

- Every pair in S has a positive remaining common-neighbor quota in the displayed matrix.
- For each core vertex i, the number of neighbors of i in S, plus the indicator that i belongs to S, is at most two.

The second condition is the common-neighbor upper bound for the exterior vertex and i. If a core already contains the entire next bootstrap layer of an earlier seed, every later exterior signature meets that earlier seed at most once.

`experiments/workspace/completion_constraints.py` enumerates these signatures and solves the resulting nonnegative incidence-count equations. For an infeasible linear relaxation, it requests a dual ray from HiGHS and converts that ray to integers. The program reports an exact incidence exclusion only after checking, with integer arithmetic, that

    y^T E >= 0,    y^T b < 0,

where Ex=b is the incidence-count system and x is nonnegative. A numerical infeasibility report alone is not an exclusion.

The program checks the actual exterior incidence counts of a nine-vertex rook core and a ten-vertex core of the 243-vertex ternary Golay graph. It also checks the certificate orientation on an independently contradictory one-variable system.

## Integer multiplicities and triple packing

The incidence equations alone omit an essential condition: two exterior vertices cannot have three common neighbors in the core. Consequently, each signature with at least three sites has multiplicity at most one, and every triple of core vertices belongs to at most one selected exterior signature. Signatures of size two have multiplicity bounded by their remaining pair quota.

`experiments/workspace/completion_constraints_packing.py` encodes the full integer incidence equations together with these triple-packing constraints as a finite Boolean cardinality problem. A returned feasible count is checked independently by building its incidence matrix N and verifying the displayed matrix identity, the exterior vertex count, and every pairwise signature intersection bound. Such a count is still only a necessary incidence assignment; no exterior-to-exterior edges have been constructed.

The incomplete-grid mode applies this model to all eight 27-vertex cores in `grids-and-triangles/incomplete_grid.md`. Its candidate generation uses the proved signature reduction in `broken_grid.py` and integer common-neighbor tests. It does not remove candidates using numerical spectral inequalities. Solver exhaustion, if obtained, is recorded separately from a proof that has been independently checked.

## Initial results

The complete first bootstrap layers at an eight-vertex square-and-tips seed reproduce the existing catalogue: 35 labeled possibilities in 11 orbits with no opposite-tip edges, and seven labeled possibilities in five orbits with one opposite-tip edge. The simple exterior edge-incidence LP is feasible in all sixteen cases. The one-tip case whose first layer contains a vertex adjacent to all four tips is the previously excluded rook graph with one edge deleted; its exclusion is not a new result.

For the remaining one-tip case with seven activated vertices, taking no edges among those activated vertices leaves 296 admissible exterior signatures and a feasible real incidence-count relaxation. This is not a graph or an integral incidence assignment.

Replay the controls with:

```sh
.venv/bin/python experiments/workspace/completion_constraints.py --control
.venv/bin/python experiments/workspace/completion_constraints_packing.py --control
```

Run a bounded test of all eight incomplete-grid cores with:

```sh
.venv/bin/python experiments/workspace/completion_constraints_packing.py --seconds 30 --out /tmp/incomplete-grid-packing.json
```

The `unknown` status is a time limit. The `integer incidence feasible` status describes only the checked incidence assignment. Neither status decides whether the full graph exists.
