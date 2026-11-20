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

## Four distinguished exterior vertices of an incomplete grid

The 27-vertex reduction gives an additional exact partition of its 72 exterior vertices. Use the notation of `grids-and-triangles/incomplete_grid.md`: U is the original eight vertices, T is its four tips, P is the six vertices seeing pairs of tips, and X is the thirteen independent vertices seeing no point of U. The graph on P has one edge. The graph on T union X has just the two edges on T.

Write d(p) for the degree of p inside P, so it is one at the two endpoints of the sole edge and zero elsewhere. A vertex p has two neighbors in T and 4+d(p) in X. Each tip sees three P vertices, and each X vertex sees two P vertices.

For fixed p, sum the remaining common-neighbor quotas between p and the other five members of P. Their full quota sum is 10-d(p). Their already prescribed common neighbors in T contribute four, while those in X contribute 4+d(p). The remaining sum is therefore 2-2d(p).

Make a multigraph D on P whose pair multiplicities are those remaining common-neighbor quotas. The two endpoints of the P edge are isolated in D, and each of the other four vertices has degree two. Each multiplicity is at most two. Thus D is either a four-cycle or two doubled disjoint edges. In particular it has no triangle.

An exterior vertex cannot see three P vertices, because those three pairs would form a triangle in D. If y_j is the number of exterior vertices seeing j members of P, summing the four edges of D gives y_2=4. The six P vertices have 44 exterior neighbors counted with multiplicity, so y_1+2y_2=44. Since there are 72 exterior vertices, this proves

    y_0 = 32,    y_1 = 36,    y_2 = 4.

These cardinalities are included explicitly in both packing solvers, although they follow from the exact incidence equations.

There is also a conditional independence bound: the thirteen vertices X are anticomplete to U, and the rook graph with one vertex deleted has an independent set of size three. Therefore an incomplete grid forces an independent set of size sixteen. This does not say that those sixteen vertices contain seven neighbors of a specified root.

A local configuration sufficient to trigger this bound is a rooted two-axis cell whose two sign-changing edges form a three-vertex path. Deleting the fourth, isolated far vertex leaves exactly the eight-vertex rook graph with one vertex missing. The deleted vertex is the only possible center of that grid: its two anchors already have the root and that vertex as their two common neighbors. It lacks the two needed adjacencies to the path endpoints, so this eight-grid is incomplete. The replay control checks the eight-vertex graph identity by an explicit permutation. Consequently, if the graph has independence number at most fifteen, no rooted nongrid cell has this path configuration.

## Exact spectral pair exclusions

Two scalar Gram matrices of a hypothetical graph are positive semidefinite:

    G_- = 27I - 9A + J,    G_+ = 44I + 11A - 2J.

For a positive definite principal submatrix H of the core Gram matrix, write H^{-1}=M/d with integral M and positive d. If candidate signatures i and j have projected columns q_i and q_j and diagonal g, the 2-by-2 Schur complement must satisfy

    ((g_ij)d - q_i^T M q_j)^2
        <= (g d - q_i^T M q_i)(g d - q_j^T M q_j).

Here g_ij is either the edge entry or the nonedge entry of the chosen Gram matrix. If both adjacency choices fail, the two signatures cannot both occur. A choice also fails if it violates an integer common-neighbor quota with a core vertex.

`experiments/workspace/completion_constraints_spectral.py` uses floating point calculations only to locate possible pair exclusions. It verifies every returned exclusion using the integer inequality above. It also verifies positive definiteness of H by exact LDL decomposition. The existing cores have singular full Gram matrices, so the program selects an independent principal submatrix; it does not invert the singular full matrix. The random 27-vertex Golay control retains all 180 actual signature types, including every pair of those signatures.

## Initial results

The complete first bootstrap layers at an eight-vertex square-and-tips seed reproduce the existing catalogue: 35 labeled possibilities in 11 orbits with no opposite-tip edges, and seven labeled possibilities in five orbits with one opposite-tip edge. The simple exterior edge-incidence LP is feasible in all sixteen cases. The one-tip case whose first layer contains a vertex adjacent to all four tips is the previously excluded rook graph with one edge deleted; its exclusion is not a new result.

For the remaining one-tip case with seven activated vertices, taking no edges among those activated vertices leaves 296 admissible exterior signatures and a feasible real incidence-count relaxation. This is not a graph or an integral incidence assignment.

Replay the controls with:

The recorded environment uses NumPy 2.3.5, SciPy 1.17.0, SymPy 1.14.0, python-sat 1.9.dev23, pynauty 2.8.8.1, HiGHS/highspy 1.16.0, and OR-Tools 9.15.6755. OR-Tools is needed only for the optional CP-SAT backend.

```sh
.venv/bin/python experiments/workspace/completion_constraints.py --control
.venv/bin/python experiments/workspace/completion_constraints_packing.py --control
.venv/bin/python experiments/workspace/completion_constraints_packing.py --control --solver cp-sat
```

Run a bounded test of all eight incomplete-grid cores with:

```sh
.venv/bin/python experiments/workspace/completion_constraints_packing.py --seconds 30 --out /tmp/incomplete-grid-packing.json
```

Add `--pair-cuts --solver cp-sat` to include the independently checked spectral pair exclusions and use CP-SAT instead of MiniCard.

The `unknown` status is a time limit. The `integer incidence feasible` status describes only the checked incidence assignment. Neither status decides whether the full graph exists.

## Neighborhood rows and checked partial exclusions

If an exterior signature S occurs, its exterior neighbors must supply the remaining common-neighbor quotas between that vertex and the core. They also form a pair packing on the core: two such neighbors already share the proposed source vertex, so they cannot share two additional core neighbors. `completion_constraints_rows.py` encodes these conditions and uses integral Farkas rays for exclusions. Its positive control checks all 216 exterior neighborhood rows of the random 27-vertex Golay core.

For incomplete-grid core 5, there are 516 possible signatures seeing two P sites. Exactly four fail this row relaxation, and the other 512 pass it. All four failures have one-entry exact certificates: a core coordinate needs a further common neighbor, but no admissible neighbor signature contains that coordinate. The file `completion-rows-case5-certificate.json` records the source signatures and rays.

The remaining constraints still admit a verified 72-column integer incidence assignment for core 5. MiniCard found one after the 7,552 exactly checked pair exclusions were imposed. The assignment satisfies the complete core identity and the triple-packing condition. Its symmetric exterior-edge system has 1,677 possible edge variables and is infeasible. Again a single deficient row gives an exact certificate. `completion-core5-edge-certificate.json` records the ordered columns and the certificate, and `completion_constraints_edges.py` independently rebuilds and checks both the incidence matrix and the edge obstruction. The Golay control retains every one of its actual exterior edges.

This excludes that incidence assignment, not core 5. The bounded packing runs on all eight cores did not exhaust any core.

Checking required neighbor supports across every candidate, rather than only the mandatory two-P candidates, gives 172 exact signature exclusions. `completion-propagation-certificate.json` records each deficient coordinate and its available and required counts. The replay program checks these integer inequalities without calling an optimizer.

| Incomplete-grid core | Initial signatures | Excluded by deficient support | Remaining signatures |
| --- | ---: | ---: | ---: |
| 0 | 5,260 | 50 | 5,210 |
| 1 | 5,071 | 0 | 5,071 |
| 2 | 4,810 | 30 | 4,780 |
| 3 | 5,382 | 24 | 5,358 |
| 4 | 5,118 | 0 | 5,118 |
| 5 | 4,536 | 36 | 4,500 |
| 6 | 5,076 | 32 | 5,044 |
| 7 | 4,928 | 0 | 4,928 |

Every signature here contains at least two core sites. Therefore two exterior neighbors of a proposed source cannot have the same signature: they would share the source and at least two core sites. This justifies counting candidate signature types, rather than allowing repeated copies, in the support bound. The Golay triangle-core control retains all 180 exterior vertices and their true exterior neighbors.

`completion_constraints_refine.py` applies the same necessary condition to each proposed 72-column incidence assignment. If a selected source needs another neighbor of a core coordinate, it adds a conditional cardinality clause requiring sufficient compatible signature types to be selected. This clause applies to every completion using that source signature. The program reports incidence feasibility separately from graph completion.

The stored incidence assignment produces four such conditional neighbor-support cuts. Starting from that verified assignment avoids spending the whole time limit rediscovering it:

```sh
.venv/bin/python experiments/workspace/completion_constraints_refine.py --case 5 --seconds 60 --propagation-certificate experiments/workspace/completion-propagation-certificate.json --pair-cuts --seed-witness experiments/workspace/completion-core5-edge-certificate.json --out /tmp/completion-refinement-5.json
```

```sh
.venv/bin/python experiments/workspace/completion_constraints_rows.py --replay experiments/workspace/completion-rows-case5-certificate.json
.venv/bin/python experiments/workspace/completion_constraints_edges.py --replay experiments/workspace/completion-core5-edge-certificate.json
.venv/bin/python experiments/workspace/completion_constraints_propagation.py --control --replay experiments/workspace/completion-propagation-certificate.json
```
