# A rooted grid cannot have grids on all ten disjoint pairs

Fix a vertex and a grid on two of its axes. **At least one of the ten pairs among the other five axes fails to form a grid.** The obstruction permits arbitrary matchings between the grid cells and imposes no automorphism.

Consequently, **if a vertex lies on thirteen grids, its eight missing axis pairs must form $K_{3,3}$ with one edge removed**, with the seventh axis isolated in the missing graph. The [previous classification](fourteen-grid-root.md#thirteen-grids) also allowed $K_{2,4}$. In that case the two vertices on the small side form a grid and all ten pairs disjoint from it form grids, which the result excludes.

## The eleven cells

Suppose the central grid and the ten other grids exist. Between cells on disjoint pairs of axes there is a perfect matching, and cells sharing an axis have no edge between them. This follows because the nine points of any grid perfectly dominate the rest of the graph. Identify the four vertices of every other cell with the four central coordinates by its matching to the central cell. The ten cells are indexed by the two-element subsets of five axes; two have a further matching between them exactly when they are disjoint. Their disjointness graph is the Petersen graph.

A square structure on four labeled points is determined by its opposite-corner involution, one of the three fixed-point-free involutions. Write $p_0$ for that of the central cell and $p_i$ for that of cell $i$. Fix a vertex of cell $i$ with coordinate $x$. Its three neighbors in the other Petersen cells must have, as a multiset of central coordinates,
\[
 \{x,p_0(x),p_i(x)\}.
\]
Indeed its common-neighbor quota with central vertex $y$ is $2-[x=y]$. The two cells themselves contribute $[y\notin\{x,p_0(x)\}]+[y\notin\{x,p_i(x)\}]$. Every remaining common neighbor lies in one of the three cells on a pair disjoint from both labels. Subtracting the contributions gives the displayed multiset, including its multiplicities.

With the three Petersen neighbors ordered, the three outgoing permutations have nine possibilities if $p_i=p_0$ and 24 for either other $p_i$. The permutations at the ends of an edge must be inverses. Branching over these local states gives 14,160 complete assignments. Permuting the five axes and simultaneously relabeling the four coordinates while preserving $p_0$ gives 64 classes.

## The common neighbors outside the cells

Let $C$ be the induced adjacency matrix on the 44 far vertices and $R$ their incidence to all remaining vertices. The graph equation gives
\[
 RR^\top=12I+2J-C-C^2 .
\]
This must be entrywise nonnegative and positive semidefinite. Forty-nine of the 64 classes fail already. Another nine have four cells sharing an axis whose central matchings all preserve opposite corners, excluded by the [four-spoke parity argument](aligned-grid-subfamilies.md#checkerboard-vectors-and-their-parities).

For each of the six other classes, consider one of the five axes $a$. At an incident cell $i$, the two possible coordinates of a signed near neighbor on $a$ partition its four vertices into two pairs. Its sign function is one of the three balanced characters on the four central coordinates, up to a global sign on that cell. The character partition cannot be the opposite-corner partition $p_i$. The two endpoint axes of $i$ must use its two different remaining partitions.

Each signed near vertex on $a$ has two common neighbors with every central vertex. All of these lie in the four cells indexed by edges containing $a$: the central vertex sees one point of each such cell, no near neighbor on $a$, and no far points outside these eleven cells. Thus the four sign functions for $a$ sum to zero pointwise. For each allowed signed choice let $W$ be the two columns of incidences of the signed near vertices to the 44 far vertices. Subtract $WW^\top$ from $RR^\top$. The result must again be entrywise nonnegative and positive semidefinite. Keep every assignment of the four character partitions for which some signs pass both tests.

Finally choose which of the two admissible character partitions belongs to each endpoint of each Petersen cell. There are at most $2^{10}$ choices. In every remaining class, none satisfies the retained axis conditions at all five axes. This proves the result.

The [checker](../../experiments/workspace/central_grid_neighborhood.py) uses integer arithmetic. Its semidefinite test checks the coefficients of $\det(xI+Q)$ for a symmetric integer matrix $Q$. A negative eigenvalue would give a positive root, impossible when every coefficient is nonnegative. Reproduce with `make verify-central-grid-neighborhood`.
