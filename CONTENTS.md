# Research catalog

Every structural result below concerns a hypothetical strongly regular graph with parameters $(99,14,1,2)$. The ledger gives the assumptions and stopping points of the construction and solver runs. [Research ledger](STATE.md)

## Grids and triangles

- [Grid bounds, percolation, and triangle pairs](research/grids-and-triangles/grid_intersections.md) proves the bounds of 120 grids in total and 15 through any vertex, at least 1,998 percolating nonedges, and at least 1,188 disjoint triangle pairs joined by exactly two edges. The finite enumerations and the 21-grid exclusion are included in `make verify`. [Run logs](experiments/logs/grids-and-triangles/)
- [Counting witnesses by triangle degree](research/grids-and-triangles/triangle-witness-bound.md) raises the lower bound on disjoint triangle pairs with two cross-edges to 1,203.
- [Fifteen grids through a point](research/grids-and-triangles/fifteen-grid-root.md) reduces the missing-axis graph to one type and classifies its eight-point pieces.
- [Full triangles are disjoint](research/grids-and-triangles/two-full-axes.md) exhausts the matching interfaces at two intersecting full triangles. The resulting [global bounds](research/grids-and-triangles/disjoint-full-bounds.md) give at most 114 grids, at most 14 through a point, and at least 2,106 percolating nonedges.
- [Fourteen-grid root exclusion](research/grids-and-triangles/fourteen-grid-root.md) lowers the pointwise bound to thirteen grids and gives at least 32 percolating partners for every point.
- [Parallel triangle deficits](research/grids-and-triangles/parallel-triangle-deficits.md) gives a triangle inequality with factor two for each parallel class. If two parallel lines have twelve three-edge partners, the graph partitions into 33 triangles and the third line has 35 possible marked neighborhoods.
- [Branching among parallel full triangles](research/grids-and-triangles/branching-full-triangles.md) excludes a configuration of five grids. It gives the global bounds of 113 grids, 2,124 percolating nonedges, and 1,206 two-edge triangle pairs.
- [Full-triangle components](research/grids-and-triangles/full-triangle-components.md) gives at most 24 full triangles and 112 grids, at least 2,142 percolating nonedges, and seven triangles on at most two grids. Its component census uses an integer obstruction on 45 vertices.
- [The nine-triangle rook cover](research/grids-and-triangles/nine-triangle-cover.md) excludes the 27-point configuration in which full matchings join the triangles on a three-by-three rook graph.
- [Nine-vertex grid partitions](research/grids-and-triangles/affine_grids.md) studies a construction using eleven disjoint grids and an obstruction to a particular affine matching assignment.
- [A grid with its center missing](research/grids-and-triangles/incomplete_grid.md) derives an exterior-incidence reduction for an eight-vertex core.
- [Corner fibers of every induced square](research/grids-and-triangles/incomplete-corner-fibers.md) excludes transitivity on each ten-point fiber and gives a square determinant test when both opposite-tip edges are present.
- [Diagonally opposite grid corners](research/grids-and-triangles/grid-diagonal-halves.md) classifies 3,978 connected marked cubic graphs and excludes 41 of them in a complete grid by counting intersections with seven ten-point fibers.
- [Complete triangle stars](research/grids-and-triangles/triangle_star.md) derives a 48-vertex shell from an independent exterior signature.

- [The 60-vertex triangle exterior](research/grids-and-triangles/triangle-exterior.md) determines its spectrum from the cubic shell and rules out every transitive automorphism group of the exterior.

## Independent sets

- [Fourteen independent vertices through a neighborhood transversal](research/independent-sets/hemisphere.md) gives a 14-vertex independent set with seven neighbors of any chosen root. It extends to a maximal independent set of size 14 through 20. [Independent-set experiments](experiments/logs/independent-sets/)

## Eigenlattices

- [Theta-series rank restrictions](research/eigenlattices/level_seven.md) derives contradictions at three ranks over $\mathbb F_7$. The exact coefficient certificates are part of `make verify`. [Rank 28](experiments/workspace/level-seven-certificate-28.json) · [Rank 30](experiments/workspace/level-seven-certificate-30.json) · [Rank 32](experiments/workspace/level-seven-certificate-32.json) · [Run logs](experiments/logs/eigenlattices/)
- [Square principal minors](research/eigenlattices/square_certificate.md) gives the determinant test on every 44-vertex set and explains its relation to prior work on the mod-7 rank.
- [Shortest vectors and maximum independent sets](research/eigenlattices/shortest_vectors.md) identifies norm-14 integral vectors in the $-4$ eigenspace with pairs of maximum independent sets meeting in 15 vertices.
- [Cube classes](research/eigenlattices/cube_shells.md) bounds the populations of the two shortest integral shells.
- [Nine translated lattices](research/eigenlattices/nine_cosets.md) gives shell identities and a maximal-lattice relaxation.
- [The positive eigenspace](research/eigenlattices/positive_lattice.md) gives a companion construction in the $3$ eigenspace.

## Involutions

- [The one-shared-axis exclusion](research/involutions/one-shared-axis.md) proves that some paired far orbits have disjoint or identical labels. Fifteen integer norm budgets exclude the last six-axis component.
- [Six-axis eigenvector frames](research/involutions/six-axis-frame.md) exclude any connected component on six or more axes among the squares sharing one axis, for arbitrary remaining squares.
- [Eight grids cannot all preserve opposite corners](research/grids-and-triangles/aligned-grid-subfamilies.md) proves an unrestricted matching obstruction and the bound of seven grids at a one-fixed-point involution.
- [A central grid and its ten disjoint pairs](research/grids-and-triangles/central-grid-neighborhood.md) exclude the $K_{2,4}$ thirteen-grid case and leave one possible support.
- [At most twelve grids through a vertex](research/grids-and-triangles/twelve-grid-bound.md) excludes both two-missing-pair configurations opposite a grid and finishes the unrestricted thirteen-grid exclusion.
- [At most eleven grids through a vertex](research/grids-and-triangles/eleven-grid-bound.md) excludes all four three-missing-pair shapes and the remaining twelve-grid supports.
- [At least five missing pairs opposite every rooted grid](research/grids-and-triangles/four-missing-cones.md) excludes all six four-edge shapes, including all 19 alternating profiles of the four-cycle.
- [At most ten grids through a vertex](research/grids-and-triangles/ten-grid-bound.md) rules out the last eleven-grid case by two equal eigenvectors and three square profiles.
- [A triangle on exactly four grids](research/grids-and-triangles/four-grid-triangle.md) leaves fourteen residual cores, each of which fixes the incidences of all sixty exterior vertices with twelve neighbors.

- [Disconnected endpoint graph](research/involutions/connected-endpoint-squares.md) allows repeated endpoint pairs and forces component sizes six and one when all 21 squares have one shared axis.
- [Distinct endpoint pairs](research/involutions/distinct-endpoint-squares.md) rules out every assignment of centers when all 21 squares have one shared axis and their endpoint pairs are distinct. The proof uses two exact norm counts.
- [The Fano-plane square pairing](research/involutions/fano-square-pairing.md) excludes all 104 interface classes at a one-fixed-point involution, allowing the interfaces to break all Fano-plane symmetries.

## Other computations

- [A doubled Hoffman–Singleton graph](research/doubled-hoffman-singleton.md) gives a 14-regular 99-vertex graph satisfying 4,313 of the 4,950 scalar constraints. Its 49 twin pairs account for all positive residuals.

- [Moments and subgraph counts](experiments/logs/moments-and-counts/) includes integer count witnesses, modular consistency checks, and semidefinite relaxations.
- [Construction searches](experiments/logs/construction-searches/) includes rooted searches, quotient cases, and checks of sampled partial graphs.
- [Experiment guide](experiments/README.md) gives the workspace layout, replay commands, and limits of the archived runs.
