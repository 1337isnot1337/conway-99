# Research catalog

Every structural result below concerns a hypothetical strongly regular graph with parameters $(99,14,1,2)$. The ledger gives the assumptions and stopping points of the construction and solver runs. [Research ledger](STATE.md)

## Grids and triangles

- [Grid bounds, percolation, and triangle pairs](research/grids-and-triangles/grid_intersections.md) proves the bounds of 120 grids in total and 15 through any vertex, at least 1,998 percolating nonedges, and at least 1,188 disjoint triangle pairs joined by exactly two edges. The finite enumerations and the 21-grid exclusion are included in `make verify`. [Run logs](experiments/logs/grids-and-triangles/)
- [Counting witnesses by triangle degree](research/grids-and-triangles/triangle-witness-bound.md) raises the lower bound on disjoint triangle pairs with two cross-edges to 1,203.
- [Fifteen grids through a point](research/grids-and-triangles/fifteen-grid-root.md) reduces the missing-axis graph to one type and classifies its eight-point pieces.
- [Two full axes](research/grids-and-triangles/two-full-axes.md) proves at least four of their twenty matchings mix the distinguished sign classes.
- [Nine-vertex grid partitions](research/grids-and-triangles/affine_grids.md) studies a construction using eleven disjoint grids and an obstruction to a particular affine matching assignment.
- [A grid with its center missing](research/grids-and-triangles/incomplete_grid.md) derives an exterior-incidence reduction for an eight-vertex core.
- [Complete triangle stars](research/grids-and-triangles/triangle_star.md) derives a 48-vertex shell from an independent exterior signature.

## Independent sets

- [Fourteen independent vertices through a neighborhood transversal](research/independent-sets/hemisphere.md) gives a 14-vertex independent set with seven neighbors of any chosen root. It extends to a maximal independent set of size 14 through 20. [Independent-set experiments](experiments/logs/independent-sets/)

## Eigenlattices

- [Theta-series rank restrictions](research/eigenlattices/level_seven.md) derives contradictions at three ranks over $\mathbb F_7$. The exact coefficient certificates are part of `make verify`. [Rank 28](experiments/workspace/level-seven-certificate-28.json) · [Rank 30](experiments/workspace/level-seven-certificate-30.json) · [Rank 32](experiments/workspace/level-seven-certificate-32.json) · [Run logs](experiments/logs/eigenlattices/)
- [Square principal minors](research/eigenlattices/square_certificate.md) gives the determinant test on every 44-vertex set and explains its relation to prior work on the mod-7 rank.
- [Shortest vectors and maximum independent sets](research/eigenlattices/shortest_vectors.md) identifies norm-14 integral vectors in the $-4$ eigenspace with pairs of maximum independent sets meeting in 15 vertices.
- [Cube classes](research/eigenlattices/cube_shells.md) bounds the populations of the two shortest integral shells.
- [Nine translated lattices](research/eigenlattices/nine_cosets.md) gives shell identities and a maximal-lattice relaxation.
- [The positive eigenspace](research/eigenlattices/positive_lattice.md) gives a companion construction in the $3$ eigenspace.

## Other computations

- [Moments and subgraph counts](experiments/logs/moments-and-counts/) includes integer count witnesses, modular consistency checks, and semidefinite relaxations.
- [Construction searches](experiments/logs/construction-searches/) includes rooted searches, quotient cases, and checks of sampled partial graphs.
- [Experiment guide](experiments/README.md) gives the workspace layout, replay commands, and limits of the archived runs.
