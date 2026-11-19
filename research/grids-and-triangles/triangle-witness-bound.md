# At least 1,203 triangle pairs with two cross-edges

Let $n$ count unordered pairs of disjoint triangles joined by exactly two edges. In a hypothetical 99-graph, $n\ge 1203$. The improvement over 1,188 comes from retaining the number of grids on each triangle when charging the crossing squares.

Fix a triangle $T$. Its three sets of twelve neighbors, one for each point of $T$, are joined pairwise by perfect matchings. Indeed a vertex in the first set has two common neighbors with the second point of $T$. The first point supplies one and the other is in the second set. Each triangle $S$ joined to $T$ by three edges uses three of the 36 matching edges. Every remaining matching edge belongs to a unique triangle joined to $T$ by two edges. Write $c_T$ for the number of three-edge partners and $s_T=12-c_T$. The number of two-edge partners is $3s_T$. In particular $n$ is divisible by three, since $2n=3\sum_T s_T$.

Around a point $p$, use the seven axes, the grid graph $D_p$ on these axes, its complement $F_p$, and the number $m_p$ of pairs of disjoint edges in $D_p$, as in the [grid intersection argument](grid_intersections.md). The degree $d_T$ of an axis is the number of grids containing its triangle, independent of the choice of point on it. For distinct axes $T,U$, define $b_{TU}$ to be the number of the two vertices of $U$ other than $p$ that lie in no triangle joined to $T$ by three edges. A vertex adjacent to $p$ outside $T$ belongs to at most one such triangle, because its neighbors in the other two fibers are uniquely determined. Thus $\sum_{U\ne T} b_{TU}=s_T$.

Both deficits vanish on a grid edge of $D_p$. In a nongrid cell the two quantities $2-b_{TU}$ and $2-b_{UT}$ count the two directions of sign-changing edges among the four far vertices. For example, the other two points of a three-edge partner through a fixed vertex of $U$ are precisely its two far neighbors on the signed axes. Their adjacency completes the triangle. At most two internal edges occur in a nongrid cell, so $b_{TU}+b_{UT}\ge2$ there.

A pair of grids meeting only at $p$ gives at least two crossing squares with a distinguished pair of opposite internal sides. Each such square has two nonadjacent tips on those sides. The triangles on the sides are a two-edge pair $T,S$. For fixed $T,S$, a witnessing center is a common neighbor of their two tips, giving at most two choices. Each center requires a grid containing $T$, and two different centers cannot use the same grid on $T$. Indeed the opposite tip is outside that grid and has a unique neighbor in it. The opposite tip lies outside because it already has a neighbor at the witnessing center and has no neighbor in $T$, while $T$ is a line of the grid. Therefore the number of witnesses is at most $q_T=\min(2,d_T)$ and at most $q_S$. Counting both triangle ends gives

$$
 4\sum_p m_p \ \le\ \sum_T 3q_T s_T
       =\sum_p\sum_{T\ni p}q_Ts_T .
$$

Each triangle has three points, so $2n=\sum_p\sum_{T\ni p}s_T$. Subtract and add one eighth of the last weighted sum. All coefficients $1-q_T/8$ are positive. On an edge $TU$ of $F_p$ put $q_{TU}=\max(q_T,q_U)$. The contribution from that edge to the remaining sum is at least $2(1-q_{TU}/8)$. It follows that

$$
 8n\ \ge\ \sum_p\left(8|F_p|+2m_p-\sum_{TU\in F_p} q_{TU}\right),
$$

where $|F_p|$ denotes the number of edges. The minimum expression on the right at a single point is 97 among the seven-axis graphs satisfying the signless incidence support test. The [integer enumeration](../../experiments/workspace/grid_support.cpp) checks all $2^{21}$ labeled graphs. This gives $8n\ge99\cdot97=9603$. The least multiple of three satisfying it is 1,203.
