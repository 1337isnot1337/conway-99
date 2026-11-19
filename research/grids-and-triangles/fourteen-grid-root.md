# No point lies in fourteen grids

A hypothetical Conway 99-graph has at most thirteen induced rook grids through each point. Consequently, for every vertex there are at least $84-4\cdot13=32$ nonneighbors with which it generates the whole graph by common-neighbor closure.

Fix a root and let $F$ consist of the seven missing pairs of axes if fourteen grids pass through it. The [root identities](grid_intersections.md) assign a nonzero vector $z_e$ to each edge of $F$. These vectors sum to zero at each axis. Every other pair carries the zero vector. [Disjointness of full triangles](two-full-axes.md) gives at most one isolated vertex in $F$.

## The missing graph

Every nonisolated vertex has degree at least two. If all seven are nonisolated, every component is a cycle and at least one is odd. Alternation forces zero on that cycle. Otherwise there are six nonisolated vertices. They form a connected graph, since disconnected components would have to be two triangles with only six edges. The degree sequence is either $4,2,2,2,2,2$ or $3,3,2,2,2,2$.

In the first case there are two cycles with a common vertex, of lengths three and four. In the second case there are either two disjoint cycles joined by a path, or three internally disjoint paths between the degree-three vertices. The former has two triangles joined by one edge. Both cycle cases contain a triangle with two degree-two vertices. Its two edges at the third vertex carry equal vectors by alternation. Distinct incident edges cannot have equal vectors. At some point in the first edge's cell its own defect is positive, since its four points span at most two edges. At the same point the other edge's defect is minus a neighbor count.

For the three paths, alternation determines all edge vectors from their values at one endpoint. If the three lengths have mixed parity, the two endpoint equations force the vector on the unique path of one parity to vanish. The lengths therefore are odd and sum to seven. Simplicity permits only one path of length one, leaving lengths $1,3,3$.

## The 41 populations

Label the edges of this theta graph, in order, by $12,14,23,25,36,45,56$ with axis 0 isolated. Let $B_f$ be the four far points on axis pair $f$. For each point $w$ in $B_f$, write $b_e(w)$ for its number of neighbors in $B_e$. The defect is $z_e(w)=a_{fe}-b_e(w)$, where $a_{fe}$ is two for equal pairs, zero for different intersecting pairs, and one for disjoint pairs. The defect vanishes at all near points and at the root.

The [integer verifier](../../experiments/workspace/root_cell_profiles.py) enumerates each point's possible tuple of seven defects. It assigns the degrees into missing cells from zero through four, or through two for the point's own missing cell, retaining precisely the tuples that sum to zero on each axis. Degrees into all present cells are fixed by the baseline. There are 50 types across the 21 cells.

For each cell take an unordered multiset of four point types. In a missing cell the internal degree sequence must belong to a simple graph on four vertices with at most two edges. In a present cell every defect sums to zero over its four points, by perfect domination or by symmetry of $W$. For two different cells, the totals counting edges in both directions must agree. Finally, impose the identities
$$
\sum_w z_e(w)z_h(w)=7\sum_{w\in B_e}z_h(w)
$$
for each ordered choice with $e\le h$ in the list above. These follow from $W^2=7W$ and $z_e=Wh_e$. There are exactly **41** assignments of these multisets. In the search, if the attainable intervals in a Gram identity miss its target, the corresponding choice can already be removed. At a leaf all interval tests are equalities.

Fix any one of the 21 cells, order its four points, and also order the four in each other cell. For a second cell enumerate every simple bipartite graph on the two fours with the prescribed row and column degrees. For the fixed cell itself enumerate every simple graph with its prescribed degrees. For each choice, record the contribution of its edges to $Az_{12}$ and $Az_{23}$ at all four fixed points. The sum over the 21 cells must equal $-4z_{12}$ and $-4z_{23}$ at those points. The near shell contributes zero. Every one of the 41 populations fails this integer sum test at some cell. The ordering of equally typed points loses no possibilities because every labeled bipartite graph with the given margins is considered.

Together with the earlier fifteen-through-twenty-one exclusions this proves the pointwise bound. Run `python experiments/workspace/root_cell_profiles.py` to reproduce the theta count and exclusion.

## Thirteen grids

If a root attains thirteen, its eight missing pairs must form either $K_{2,4}$ or $K_{3,3}$ with one edge removed. Each graph has one additional isolated axis. In particular **a point outside all full triangles lies on at most twelve grids**, and has at least 36 percolating partners. The two exceptional graphs have degree sequences for the seven *present* axes of $(6,4,4,4,4,2,2)$ and $(6,4,4,3,3,3,3)$, respectively.

The [eight-edge checker](../../experiments/workspace/thirteen_grid_supports.py) generates the 1,044 unlabelled graphs on seven vertices by one-vertex extensions and canonical labelling. It retains the eight-edge graphs with at most one isolated vertex and for which deletion of each edge preserves signless-incidence rank. The latter is checked by counting bipartite components, including isolates. There are twelve supports. Leaving the two stated exceptions open, eight of the other ten admit no cell population, and the last two admit one each. The exact four-point eigenvector test rejects both. The [central-grid obstruction](central-grid-neighborhood.md) subsequently excludes $K_{2,4}$, and the [two-missing-pair proof](twelve-grid-bound.md) excludes $K_{3,3}$ with one edge removed.
