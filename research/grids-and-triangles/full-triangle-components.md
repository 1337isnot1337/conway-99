# Components of full triangles

Join two full triangles when three edges run between them. The edges form a matching. The triangles are then parallel lines in a common grid, since the twelve three-edge partners of a full triangle are precisely the two other parallel lines in each of its six grids. Two full triangles cannot intersect or have two cross-edges.

Within a connected component of this graph $H$, every nonadjacent pair is anticomplete in the original graph. To see this, take adjacent full triangles $T,U$ and their common grid. A third full triangle disjoint from the grid sends three edges into it. It cannot send exactly two to any row, by saturation. Its three row counts are therefore all one or a permutation of $(3,0,0)$. If the third full triangle meets the grid at one point, that point is on the remaining row. It sees one point in each of $T,U$, and its other vertices see only the intersection point in the grid. A full triangle contained in this grid and distinct from $T,U$ is its third parallel line. Thus $T,U$ have identical sets of full triangles to which they send exactly one edge. Equality propagates along paths, and a triangle has no singleton connection to itself.

Let $W=3I-A+J/9$ and attach to each triangle $T$ the real vector $v_T=W^{1/2}\mathbf{1}_T$. These vectors have squared norm four. For distinct triangles the inner product is zero if they meet and $1-k$ if they are disjoint with $k$ cross-edges. On a component of full triangles their Gram matrix is therefore $3I-3H+J$, using $H$ also for its adjacency matrix.

If $T$ is full, $S$ is saturated, and $v_T\cdot v_S=-2$, the triangles are disjoint and have three cross-edges. The full line $T$ puts them in a grid, whose third parallel line $R$ is saturated by the [parallel deficit inequality](parallel-triangle-deficits.md). The three pairwise inner products are $-2$, so $v_R=-v_T-v_S$. This rule generates further actual triangle vectors. Equal vectors refer to the same triangle, since distinct triangle vectors have inner product at most one. All vectors generated from one component are integral combinations of its full-triangle vectors, with coefficient sum congruent to one modulo three. Their pairwise products are all one modulo three. Distinct generated triangles are consequently disjoint, with either zero or three cross-edges.

More generally, three disjoint triangles pairwise joined by three-edge matchings form a grid. The sum of their three vectors has squared norm zero. If $h$ is the indicator of their nine points, $Wh=0$ gives internal degree four at each point and exactly one neighbor there for each exterior point. Every adjacent pair in the union therefore has its unique common neighbor inside it. For a matched edge between the first two triangles this common neighbor must belong to the third triangle. The matchings line up in three transverse triangles, giving the rook grid.

## The fifteen triangles indexed by the edges of a six-point set

There cannot be fifteen disjoint triangles indexed by the edges $ab$ of $K_6$, matched by three edges for disjoint indices and anticomplete for indices with a common endpoint. Every perfect matching of $K_6$ would give a grid by the preceding observation. Each point outside the 45 vertices would therefore mark exactly one index in every perfect matching, where marking means having a neighbor on its triangle.

There are fifteen perfect matchings and each edge belongs to three, so five indices are marked. They are pairwise intersecting as edges of $K_6$, since two disjoint edges belong to a perfect matching. Five pairwise intersecting edges must be a star: if three edges have no common endpoint they already form a triangle, to which no fourth edge can be added. Label an exterior point by the center $a$ of its star.

For any exterior point $x$ let $n_b$ count its exterior neighbors of star type $b$. Sum the common-neighbor numbers of $x$ with the three vertices indexed by an edge $bc$. When $a\in\{b,c\}$ the sum is five. Two contributions come from the point of the triangle seen by $x$, and its other four marked triangles are anticomplete to this one. When $a\notin\{b,c\}$ the sum is six. Precisely three of its five marked indices are disjoint from $bc$, giving three contributions from the 45-point union. In both cases
$$
n_b+n_c=3
$$
for every distinct $b,c$. This would require six equal integers all equal to $3/2$. There are 54 exterior vertices, so the configuration is impossible.
