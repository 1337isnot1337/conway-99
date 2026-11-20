# Exact box-hull membership

The accepted six-cut selector point belongs to the convex hull of all 191
surviving branch boxes. The certificate has 34 positive mixture weights.
Its common denominator is 2,594,289,631, equal to the point denominator.
The remaining 157 weights are zero.

The independent replay checks the complete 191-weight vector, nonnegativity,
sum one, all 2,204 coordinate endpoint inequalities, and the 112 original
zero coordinates. It checks the endpoint inequalities by integer
cross-multiplication. Thirty-six weighted coordinate intervals are
degenerate, and the point equals their fixed endpoint. The coordinatewise
interpolation argument in `rook_case4_box_hull_membership.md` then gives an
explicit convex combination of points from the boxes.

Consequently, no linear inequality valid on every one of these 191 entire
boxes can reject this point. This includes further box-only weighted
cover or signed-endpoint inequalities. It does not imply that a box is
feasible for the original selector model, that the point is a convex
combination of Boolean solutions, or that a graph exists. A stronger
disjunctive test must retain additional constraints inside the branches or
refine the branches.

## Computation and independent acceptance

The single permitted native call used 65 simplex iterations and took
0.023341 seconds. It returned a numerical feasible basis. One 35-square
exact rational solve reconstructed the mixture; the solve itself took
0.001602 seconds. The complete exact child took 0.198809 seconds.

The separate independent cold checker took 0.053073 seconds. It imported no
producer, constructed no numerical model, repeated no linear solve, and
replayed no branch propagation. It read the frozen accepted branch-cover
and point records, then checked the mixture directly. The subsequent
bindings-only verification passed. All owners and children exited and
were reaped without timeout. No retry occurred.

The authoritative certificate is
`experiments/logs/grids-and-triangles/rook-case4-box-hull-membership-run01/exact/certificate.json`,
SHA256 `1c079f5616269cdc263bf150c6e3248b26d638135f2dd9dff715571e34ef8bd1`.
The independent cold result is
`experiments/logs/grids-and-triangles/rook-case4-box-hull-membership-run01/cold/result.json`,
SHA256 `5ddd8a2ae81b091813dd4de8e23576cc07fa70769d220c71cf3734fd5eac187b`.

## Preserved transport-performance issue

The native child took 75.162507 seconds in total, despite the 0.023341-second
solve. Its transport audit repeatedly accessed the native sparse-vector
properties inside the 38,333-entry loop. The installed HiGHS type stub
declares these getters as Python lists. This identifies avoidable repeated
vector reads; conversion of a full native vector on each read makes this
audit quadratic. The original run did not record individual setup-operation
times, so it cannot assign an exact duration to each setup operation.

The successful original query source, configuration, and terminal remain
unchanged. A separate unrun source,
`rook_case4_box_hull_membership_query_cached_unrun_v2.py`, caches the three
native arrays once and performs the same entrywise assertions on those
lists. Its reproduction record checks the exact text substitution, all
11 unchanged function ASTs, unchanged module statements, and one load of
each array getter. No native import, new configuration, performance rerun,
or optimizer call was used to validate this source delta.

The complete owner took 76.427165 seconds. The case remains open.
