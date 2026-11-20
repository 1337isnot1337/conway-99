# At most twelve grids through a vertex

Every vertex of a Conway graph lies in **at most twelve induced nine-point rook grids**. Thus at least 36 of its 84 nonneighbors generate the full graph with it under common-neighbor closure, by [the grid-or-percolation count](grid_intersections.md).

A stronger local statement gives the bound. Fix a grid on an axis pair $e$. **At least three of the ten axis pairs disjoint from $e$ fail to form a grid.** The [eleven-cell obstruction](central-grid-neighborhood.md) handles zero missing pairs. The argument below handles one and two. In the last possible thirteen-grid support, the missing pairs form $K_{3,3}$ minus an edge, with the seventh axis isolated. Choose $e$ within one part, using the two vertices other than the endpoint of the removed edge. Among the ten disjoint pairs exactly two are missing. This contradiction finishes the thirteen-grid exclusion.

## Coordinates on the ten cells

Call the two axes of $e$ central and the remaining five passive. Every vertex in a cell on a pair of passive axes has a unique neighbor in the central cell, by grid domination. If that passive cell is a grid, the interface is a perfect matching. It is also a perfect matching for each of the missing passive cells when there are at most two.

To see this, fix a vertex $x$ of the central cell and a passive axis $a$. Its two signed near vertices each have two common neighbors with $x$. All four common neighbors are in the four passive cells whose labels contain $a$. In fact a central vertex sees no far point in a different cell meeting its own label, and none of its near neighbors lies on $a$. Thus the four counts sum to four. Any passive cell already known to be a grid contributes one. Every missing pair has an endpoint belonging to no other missing pair, so its contribution is one as well. Transport the four central coordinates to each of the ten cells by these matchings.

Fix a passive point of coordinate $x$. Its neighbors among the ten passive cells have the following multiset of central coordinates:
\[
 \{0,1,2,3,p_0(x)\},
\]
where $p_0$ interchanges opposite corners of the central square. Indeed the common-neighbor quota with central vertex $y$ is $2-[x=y]$. Its neighbor of coordinate $x$ in the central cell contributes one when $y$ is adjacent to $x$ there. Subtracting this term gives the stated multiplicities. These five neighbors all lie in passive cells because a central vertex has already accounted for all fourteen neighbors.

With just one missing cell, each of its points sees one vertex in each of its three disjoint passive grid cells and none in the grid cells sharing an axis. The other two of its five neighbors must be internal. This would give four internal edges in a nongrid cell, violating the [two-edge bound](grid_intersections.md#the-bound-at-each-root).

## The eight vertices of two missing cells

There are two possible label intersections.

* If the missing pairs meet, each of their vertices sees three points in passive grid cells. The induced graph on the eight missing points is therefore 2-regular. On their shared axis each point sees one far point of the same sign and one of opposite sign. This follows from the common-neighbor quotas with its two signed near vertices; at the opposite near vertex the near mate provides the other common neighbor. The two known neighbors in the missing union exhaust these quotas. Around each cycle edges alternate between preserving and changing sign. The number of changes is even, so each cycle has length divisible by four. Only an eight-cycle and two four-cycles are possible.
* If the missing pairs are disjoint, each of their vertices sees two points in passive grid cells. The induced graph on the eight is cubic. The two four-point cells have equal numbers of internal edges, since their degree sums and numbers of crossing edges agree. That common number is zero, one or two.

All the eight-point graphs just described are enumerated with their vertices labeled. Graphs are indexed by the multiset of central coordinates of the neighbors of each vertex. After specifying its neighbors in passive grid cells, the five-coordinate rule gives exactly the required lookup key.

## Grid matchings and near labels

For each of the eight passive grid cells, its three disjoint passive labels still obey the coordinate-multiset rule of the [eleven-cell proof](central-grid-neighborhood.md#the-eleven-cells). Between grids the corresponding maps are permutations. To list possibilities just for those grid-to-grid maps, project the full three-permutation list onto the slots corresponding to grids. This projection is exhaustive even if some actual interfaces from missing cells fail to be permutations: the residual four-by-four table after subtracting the known permutations is nonnegative with equal row and column sums, so it splits into that many permutation matrices by the bipartite matching theorem.

After enforcing inverse permutations at the two ends of each known interface, fill the actual missing-to-grid functions. For each central coordinate, subtract the known images from the required multiset and distribute the remaining entries among the missing sources in every possible order. The eight-point lookup then gives the full 44-vertex far adjacency matrix $C$. Retain only entrywise nonnegative, positive semidefinite common-neighbor Grams $12I+2J-C-C^2$.

The signed central axes give four known outside columns. On each passive axis the sign functions from the four incident cells must sum to zero pointwise, since each signed near vertex has two common neighbors with each central vertex. In a grid cell, either of the two noncheckerboard partitions can be its axis character. In a missing cell all three balanced partitions are allowed. The two axes of every cell have different partitions because all four sign combinations occur. Interchanging the two names of a near axis fixes its first sign without loss. Subtract the outer products of the known columns, retain every simultaneous choice passing entrywise nonnegativity and positive semidefiniteness, and include the root and all fourteen near vertices. For their induced graph $H$ on 59 vertices the matrix $12I+2J-H-H^2$ is again a Gram of outside incidences.

| Missing labels | Partial grid assignments | Symmetry classes | Nonnegative far Grams | Positive semidefinite far Grams | Remaining near labelings | Valid 59-point Grams |
|---|---:|---:|---:|---:|---:|---:|
| Intersecting | 101,164 | 7,738 | 1,272 | 843 | 96 | 0 |
| Disjoint | 33,033 | 1,490 | 371 | 287 | 0 | 0 |

The symmetry group permutes the five passive axes preserving the unordered missing pair and simultaneously relabels the central coordinates preserving $p_0$. It has order 32 for intersecting labels and 64 for disjoint labels. Counts after the symmetry reduction include all admissible labeled fillings of each chosen representative.

The [integer checker](../../experiments/workspace/two_missing_grid_neighbors.py) constructs every case and tests positive semidefiniteness through the coefficients of the characteristic polynomial. Run `make verify-twelve-grid-bound`. No graph symmetry is assumed.
