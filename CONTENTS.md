# Research catalog

Every structural result below concerns a hypothetical strongly regular graph with parameters $(99,14,1,2)$. The ledger gives the assumptions and stopping points of the construction and solver runs. [Research ledger](STATE.md)

## Grids and triangles

- [Grid bounds, percolation, and triangle pairs](research/grids-and-triangles/grid_intersections.md) proves the baseline bounds of 120 grids in total and 15 through any vertex, at least 1,998 percolating nonedges, and at least 1,188 disjoint triangle pairs joined by exactly two edges. The finite enumerations and the 21-grid exclusion are included in `make verify`. [Run logs](experiments/logs/grids-and-triangles/)
- [Three rook-isomorphic bases are impossible](research/grids-and-triangles/three_red_boundary.md) excludes three disjoint grids with pairwise isomorphic matching interfaces. Its three cases use exact boundary counts and an integer incidence contradiction. It independently gives at most one all-red grid. [Translation certificate](research/grids-and-triangles/three_red_translation_incidence.md)
- [An exact aggregate certificate](research/grids-and-triangles/grid_count_119.md) proves `29g-4b<=3465`, hence at most 119 grids and at least 2,016 percolating nonedges using the preceding all-red bound. The parallel [root-grid branch](https://github.com/1337isnot1337/conway-99/pull/3) has the stronger total bound of 114 from a separate exclusion of intersecting red triangles.
- [Nine-vertex grid partitions](research/grids-and-triangles/affine_grids.md) studies a construction using eleven disjoint grids and an obstruction to a particular affine matching assignment.
- [A grid with its center missing](research/grids-and-triangles/incomplete_grid.md) derives an exterior-incidence reduction for an eight-vertex core.
- [Earlier bound of three all-red grids](research/grids-and-triangles/red_grid_three_bound.md) exhausts four-grid matching interfaces, rejects 124 assignments by integer Gram vectors, and excludes the remaining core by its outside-neighborhood count.
- [Earlier bound of seven all-red grids](research/grids-and-triangles/eight_red_exclusion.md) uses exact cycle spectra and covering certificates. [Nine-grid preliminary argument](research/grids-and-triangles/red_grid_limit.md)
- [Cubic trace closure](research/grids-and-triangles/red_grid_cubic_trace.md) gives a second, shorter proof of the seven-grid bound, using the cycle census and no three-cover enumeration.
- [The seven-grid remainder](research/grids-and-triangles/seven_red_residual_reduction.md) gives a spectral restriction on its triangle counts. The [four-cover exclusion](research/grids-and-triangles/seven_red_four_cover_reduction.md) and a [negative rook-space inequality](research/grids-and-triangles/seven_red_four_rook_exclusion.md) leave only 18 or 27 vertices in exactly two internal triangles.
- [No induced ternary Hamming cube](research/grids-and-triangles/eight_red_hamming.md) excludes an induced `H(3,3)` by boundary and common-neighbor counting.
- [Earlier aggregate grid-line constraints](research/grids-and-triangles/grid_flag_relaxation.md) records an exact integral count witness at 120 grids with the old bound of seven all-red grids. It does not satisfy the later all-red bound.
- [Incomplete-grid completion constraints](research/unrestricted-completion.md) proves a conditional sixteen-vertex independent set and records exact signature and partial-assignment exclusions. All eight starting cores remain unresolved.
- [Complete triangle stars](research/grids-and-triangles/triangle_star.md) derives a 48-vertex shell from an independent exterior signature.

## Independent sets

- [Fourteen independent vertices through a neighborhood transversal](research/independent-sets/hemisphere.md) gives a 14-vertex independent set with seven neighbors of any chosen root. It extends to a maximal independent set of size 14 through 20. [Independent-set experiments](experiments/logs/independent-sets/)
- [Transversal degree and incidence constraints](research/independent-sets/transversal_constraints.md) proves the size-twenty degree restrictions and excludes four of 56 core patterns with integer certificates. The other 52 pass the tested real incidence relaxations.
- [A surviving minimum Ramsey hemisphere](research/independent-sets/transversal_hemisphere_minimum.md) gives an exact 36-vertex spectral witness with a 21-vertex hemisphere of independence number seven. This identifies a limit of the local relaxation.

## Eigenlattices

- [Theta-series rank restrictions](research/eigenlattices/level_seven.md) derives contradictions at three ranks over $\mathbb F_7$. The exact coefficient certificates are part of `make verify`. [Rank 28](experiments/workspace/level-seven-certificate-28.json) · [Rank 30](experiments/workspace/level-seven-certificate-30.json) · [Rank 32](experiments/workspace/level-seven-certificate-32.json) · [Run logs](experiments/logs/eigenlattices/)
- [Square principal minors](research/eigenlattices/square_certificate.md) gives the determinant test on every 44-vertex set and explains its relation to prior work on the mod-7 rank.
- [Shortest vectors and maximum independent sets](research/eigenlattices/shortest_vectors.md) identifies norm-14 integral vectors in the $-4$ eigenspace with pairs of maximum independent sets meeting in 15 vertices.
- [Cube classes](research/eigenlattices/cube_shells.md) bounds the populations of the two shortest integral shells.
- [Coupled norm-16 shells](research/eigenlattices/coupled_shells.md) proves the even deficit-cycle restriction, exterior degree identities, and at most one edge on the eight high vertices. A complete finite census excludes 31 of 478 incidence classes and checks 447 partial witnesses. This is conditional on a norm-16 vector.
- [Eleven zero-class forests](research/eigenlattices/coupled_zero_structure.md) classifies the possible eleven-vertex zero-class graphs at the high/zero incidence level.
- [Independent linear exclusions](research/eigenlattices/coupled_shells_linear.md) gives integer Farkas proofs for ten of the fourteen SAT-excluded templates. These are overlapping proofs, not further exclusions.
- [Stronger fixed-core completion tests](research/eigenlattices/coupled_zero_completion.md) gives 265 exact Gram exclusions of partial cores, a row Farkas certificate, and a DRAT proof for a specified canonically labeled pattern. No further whole template is excluded.
- [Fixed-forest completion searches](research/eigenlattices/coupled_fixed_forest_search.md) records six full-incidence instances with the zero forest fixed. All six bounded runs are undecided.
- [Nine translated lattices](research/eigenlattices/nine_cosets.md) gives shell identities and a maximal-lattice relaxation.
- [The positive eigenspace](research/eigenlattices/positive_lattice.md) gives a companion construction in the $3$ eigenspace.

## Other computations

- [Moments and subgraph counts](experiments/logs/moments-and-counts/) includes integer count witnesses, modular consistency checks, and semidefinite relaxations.
- [Construction searches](experiments/logs/construction-searches/) includes rooted searches, quotient cases, and checks of sampled partial graphs.
- [Experiment guide](experiments/README.md) gives the workspace layout, replay commands, and limits of the archived runs.
