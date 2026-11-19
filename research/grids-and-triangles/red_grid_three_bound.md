# At most three all-red grids

A hypothetical strongly regular graph with parameters `(99,14,1,2)`
contains at most three all-red grids. A triangle is red if it belongs
to six induced rook grids; a grid is all-red if its six triangles
are red.

The proof actually excludes four disjoint induced rook grids whenever
their pairwise matching interfaces are rook isomorphisms. It consists
of an exhaustive eleven-label calculation, integer negative quadratic
forms, and an outside-neighborhood count. It uses no SAT result or
floating-point sign decision.

## Reduction to 136 local assignments

The [preliminary grid facts](red_grid_limit.md) show that all-red grids
are disjoint, every vertex outside any rook grid has exactly one
neighbor in it, and every matching between two all-red grids is a rook
isomorphism.

Choose one of four putative bases as the root. Transport its labels
through the three root matchings. Those matchings become identities,
and the three other matchings remain rook automorphisms. A matching
cannot move a point to a rook neighbor: the corresponding cross-base
pair already has two common neighbors in the endpoint grids, and the
root would give a third.

Of the 72 rook automorphisms, exactly eleven satisfy this condition.
Thus the three unknown interfaces have only 11^3 = 1,331 possible
assignments. Reconstruct the full 36-vertex matrix B for each assignment
and retain it precisely when

    (B^2)_{ij}+B_{ij} <= 2    for every distinct i,j.

Exactly 136 assignments remain. The exhaustive Python matrix calculation
and the independent C++ adjacency backtracker give the same count.
There is no isomorphism pruning in this enumeration. The
[interface audit](red_interface_backtrack_audit.md) proves completeness
of the gauge and the eleven-map list.

## The exact Gram obstruction

If B were an induced core of the full graph, and X described its edges
to the other vertices, the full adjacency identity would give

    X X^T = G = 12I+2J-B^2-B.

Consequently G must be positive semidefinite. For 124 of the 136
assignments, the saved certificate contains an integer vector v with

    v^T G v < 0.

The replay rebuilds B and G and evaluates each quadratic form with
Python integers. Floating-point eigenvectors were used only to propose
these vectors during discovery; their signs are verified exactly.

The other twelve assignments are explicitly isomorphic to the same
core, whose three matching labels are `[1,6,7]` in the saved order.
Each saved isomorphism is checked on every pair of vertices. The
representative has spectrum

    7^1, 3^9, 1^6, 0^3, (-1)^6, (-2)^2, (-3)^6, (-4)^3.

An exact characteristic polynomial verifies this spectrum. Its Gram
matrix is positive semidefinite, so the final case needs a further
argument.

## Only 27 possible outside neighborhoods

The [boundary calculation](four_red_boundary.md) specifies the surviving
core's three permutations explicitly. Every outside vertex must have
one neighbor in each of the four bases. There are 9^4 = 6,561 possible
four-point signatures.

For a signature to contain two core vertices i and j, their residual
common-neighbor quota must be positive:

    2-B_{ij}-(B^2)_{ij} > 0.

Only 27 signatures meet all these pair conditions. A Cartesian-product
enumeration and a separate recursive enumeration agree on the entire
list. Each core vertex occurs in exactly three of the signatures.

No signature can be used by two different outside vertices: those
vertices would have four common neighbors, exceeding the maximum of
two. The core therefore permits at most 27 outside vertices, but the
full graph requires 99-36 = 63. Equivalently, each core vertex can have
at most three outside neighbors and requires seven. This contradiction
excludes the last core and proves the bound of three.

## Independent five- and six-base checks

The same exact spectral certificate archive also checks the complete
five-base census. Of its 564 assignments, 552 have integer negative
Gram vectors. The remaining twelve have explicit isomorphisms to one
45-vertex core built from the Petersen graph. A saved isomorphism binds
the interface representative to that explicit construction.

The [Petersen boundary proof](petersen_red_core_boundary.md) excludes
that core independently: only eighteen five-point signatures survive,
and each has a short integer kernel-vector contradiction. This gives
a separate, weaker bound of four all-red grids.

The six-base local model has no assignments even before Gram tests.
Both a [checked DRAT proof](seven_red_interfaces.md) and an independent
direct backtracker verify that weaker bound of five. Neither is needed
for the four-base argument above.

## Reproduction and limits

```sh
make verify-rook-interfaces
```

The exact vectors and isomorphisms are in
[`rook-interface-small-spectral-certificates.json`](../../experiments/workspace/rook-interface-small-spectral-certificates.json).
The replay source is
[`rook_interface_small_spectra.py`](../../experiments/workspace/rook_interface_small_spectra.py).
The boundary checker uses only Python's standard library.

This is a restriction on a specific kind of grid. It does not assert
that a hypothetical graph contains four such grids, and it does not
resolve the existence of the graph.
