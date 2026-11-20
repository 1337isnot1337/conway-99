# At most eleven grids through a vertex

In a hypothetical strongly regular graph with parameters $(99,14,1,2)$, every vertex lies in **at most eleven induced three-by-three rook grids**. At least 40 of its 84 nonneighbors therefore generate the entire graph with it under two-neighbor closure. Each grid through a fixed vertex accounts for four different nonneighbors by the [grid-or-percolation count](grid_intersections.md).

## Three missing pairs opposite a grid

Fix a root in a grid and call the two triangles of the grid incident with the root the central axes. The other five axes determine ten four-point cells. We prove that **at least four of these ten cells fail to form grids with the root**. The cases of zero, one and two missing pairs were [excluded previously](twelve-grid-bound.md).

Suppose that three are missing. Every vertex in a passive cell has exactly one neighbor in the central four-point cell by grid domination. Fix a central point and write $d_f$ for its number of neighbors in passive cell $f$. At each passive axis the four incident $d_f$ sum to four, and $d_f=1$ on the seven passive grids. Thus the deviations $d_f-1$ on the three missing edges sum to zero at each endpoint. A three-edge simple graph is a forest or contains a triangle. Removing leaves forces the forest coefficients to zero, and the equations around an odd cycle force its coefficients to zero as well. All ten interfaces to the central cell are therefore perfect matchings. Label each passive vertex by the coordinate of its central neighbor, using coordinates $0,1,2,3$.

As in the [two-missing-cell proof](twelve-grid-bound.md#coordinates-on-the-ten-cells), a passive point of coordinate $x$ sees five passive neighbors. Their coordinates are $0,1,2,3$ and one extra copy of $p_0(x)$, where $p_0$ swaps the opposite central corners. For a passive grid with opposite map $p_i$, its two internal neighbors account for the two coordinates outside $\{x,p_i(x)\}$. The remaining three have coordinates $x,p_0(x),p_i(x)$ with multiplicities. A point in a disjoint cell has exactly one neighbor in this grid, and a point in an intersecting cell has none. Consequently the aggregate four-by-four table of its three interfaces is the sum of the identity and the two opposite-corner permutation matrices. This table is symmetric. We can read the same quotas with the source and recipient coordinates exchanged when filling the maps *from* missing cells.

For the seven passive grids, project the [full permutation list](central-grid-neighborhood.md#the-eleven-cells) onto the interfaces between grids. This covers every possibility because the unused portion of each table has constant row and column sum and decomposes into permutations. Enforce inverse maps between the two ends of each specified interface. Permute the five axes preserving the missing set and simultaneously relabel all four coordinates preserving $p_0$. For each representative, fill the maps from the missing cells to the grids by distributing the residual coordinate multiset over the missing sources in all orders.

## Completing the twelve missing points

There are three missing vertices of each central coordinate. For each such vertex, subtract its already specified passive grid neighbors from its five-coordinate multiset. The residual gives its degree into each of the four coordinate groups in the missing union. For two distinct groups, enumerate all $2^9$ labeled bipartite graphs and keep the prescribed degree margins. For one group, enumerate the $2^3$ labeled simple graphs. Join the ten blocks, discarding a partial graph only if a missing cell has more than two internal edges or a pair exceeds its common-neighbor quota. Both violations persist when adding more edges.

Let $C$ denote the induced adjacency on the 44 points of the central cell and the ten passive cells. Its exterior incidence Gram is $12I+2J-C-C^2$. Include the four central and ten passive signed near vertices by the [balanced sign enumeration](twelve-grid-bound.md#grid-matchings-and-near-labels), then include the root. For the resulting induced adjacency $H$ on 59 points, the same formula must give an entrywise nonnegative, positive semidefinite matrix of rank at most 40, the number of exterior points. The checker rejects negative entries directly. A numerical eigenvector can suggest an integer vector $v$, but a negative-direction rejection requires exact evaluation of $v^T Rv<0$ or an exact characteristic polynomial. The final rank check uses integer arithmetic.

| Three missing edges on five axes | Grid assignments | Symmetry classes | Completed far graphs passing the edge quotas | Near labelings | Admissible 59-point Grams |
|---|---:|---:|---:|---:|---:|
| Three-edge star | 141,696 | 6,376 | 19,471 | 128 | 0 |
| Triangle | 177,300 | 4,636 | 11,560 | 96 | 0 |
| Three-edge path | 45,993 | 6,840 | 164,653 | 0 | 0 |
| Two-edge path and a separate edge | 41,060 | 3,167 | 23,068 | 0 | 0 |

These are all three-edge simple graphs on five vertices, allowing isolates. Labels in the two rightmost enumeration stages are counted separately for each selected representative. The argument assumes no automorphism of the 99-vertex graph.

## The twelve-grid supports

The previous bound permits at most twelve grids. If twelve occur, nine of the 21 axis pairs are missing. Among 131 unlabelled nine-edge graphs on seven vertices, eleven have at least four missing edges disjoint from each present edge. At most one axis may be isolated by [disjointness of full triangles](two-full-axes.md). Each missing edge must also be deletable without changing signless incidence rank, since its nonzero defect vector participates in the zero sum at each axis. The [support argument](fourteen-grid-root.md#thirteen-grids) computes that rank from the number of bipartite components.

Two supports survive. In each, the [four-point degree test](../../experiments/workspace/root_cell_profiles.py) finds a missing cell whose four internal degrees cannot realize a graph with at most two edges. This excludes twelve grids.

Run `make verify-eleven-grid-bound` for the [case and Gram checker](../../experiments/workspace/three_missing_grid_neighbors.py) and its [integer block enumerator](../../experiments/workspace/central_grid_fill.cpp). The earlier two-missing-cell cases replay with `make verify-twelve-grid-bound`.
