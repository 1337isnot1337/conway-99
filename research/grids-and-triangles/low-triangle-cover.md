# At least 36 triangles on at most two grids

Call a triangle low if its grid degree is at most two. The [ten-grid root bound](ten-grid-bound.md) ensures that every point lies on a low triangle. **There must be at least 36 low triangles. If there are exactly 36, the nine vertices on two low triangles form a rook grid.** The [zero-grid triangle capacity inequality](zero-triangle-capacity.md) subsequently excludes equality and gives at least 39.

The [support enumeration](../../experiments/workspace/low_triangle_cover.py) starts from the seven-axis graphs in the [104-grid count](104-grid-bound.md) and requires at least five missing pairs disjoint from each present edge. Exactly two supports have just one low axis. Both have degrees $(0,3,3,3,3,3,3)$, nine grid edges, and witness capacity $C_p=0$. In the following, a point with one low axis is called ordinary.

## A partition by 33 low triangles is impossible

Equality in the cover bound would partition the graph into 33 low triangles, all of grid degree zero. Every other triangle would have degree three. The [witness bound](triangle-witness-bound.md) gives
$$
 4\sum_p m_p\le\sum_T W_T\le\sum_T3\min(2,d_T)s_T
 \le\sum_T3\min(2,d_T)(12-2d_T).
$$
Here $s_T=12-c_T$ with $c_T$ the number of three-edge partners, and $W_T$ counts the witnesses to two-edge partners. Since all $C_p=0$ and there are no degree-two axes, the outside quantities are equal. Every degree-three triangle therefore has $s_T=6$ and uses both witnesses for every two-edge partner. Its six three-edge partners are the parallel lines in its three grids. Each two-edge partner lies in at least one witness grid. Consequently none of these two- or three-edge partners can be low.

For a low triangle $T$ all its $3s_T$ two-edge partners and all its $12-s_T$ three-edge partners must then belong to the partition. They use $6s_T+3(12-s_T)=36+3s_T$ edges leaving $T$. Only 36 such edges exist and the partition triangles are disjoint. Hence $s_T=0$, and $T$ is matched to twelve other partition triangles and anticomplete to the rest.

The partition is equitable. Its symmetric quotient matrix has diagonal two, twelve off-diagonal ones per row, and spectrum contained in that of the full graph. The eigenvalue 14 is simple, and the others are 3 or $-4$. If 3 has multiplicity $a$ in this quotient, its trace gives $66=14+3a-4(32-a)$. This would require $7a=180$.

## Up to nine exceptional points

For $L$ low triangles the sum of the numbers of low axes at all points is $3L$. Let $B$ be the points with more than one low axis. The excess $3L-99$ is the sum over $B$ of the number of low axes beyond the first. In particular $|B|\le3L-99$. Every axis of degree $1,2,4$ or $6$ is entirely in $B$ because all ordinary points have only degrees zero and three. Degree five is impossible by the missing-edge incidence condition. Two axes meet in at most one point.

For each grid $Q$, its contribution to $A\mathbf1_Q$ is four at a point of the grid and one elsewhere. Thus the vector $e$ counting grids at each point satisfies $Ae=3e+g\mathbf1$. Write $h=9\mathbf1-e$. It vanishes outside $B$, and
$$
 Ah=3h+k\mathbf1,\qquad k=99-g=\tfrac19\sum_{p\in B}h_p.
$$
For each size of $B$ enumerate multisets of eligible root degree sequences with the required excess. Each point has room for at most $(|B|-1)/2$ axes wholly in $B$. Each special degree occurs on a multiple of three points when counted with multiplicity, and a degree that occurs must occur at three distinct points. Require $k$ integral.

For each resulting population, put a binary adjacency variable on each pair in $B$ and a binary triangle variable on each possible special-degree triple. Require the indicated number of axes of each special degree through each point. Each selected triple uses its three edges and no two selected triples can use the same edge. Impose the displayed equation for $h$ at every point of $B$. For each pair in $B$, its number of common neighbors in $B$ plus its adjacency is at most two. These finite integer constraints give the following counts.

| Low triangles | Root populations before the adjacency test | Populations after the test |
| ---: | ---: | ---: |
| 34 | 0 | 0 |
| 35 | 3 | 0 |
| 36 | 134 | 5 |

All five remaining populations have nine exceptional points. In four of them each exceptional point has eight grids, with profile $(0,0,3,3,3,3,4)$ or $(0,1,3,3,3,3,3)$. The number having the latter profile is $0,3,6$ or $9$. In these cases $h=\mathbf1_B$, so every point in $B$ has four neighbors inside and every outside point sees exactly one. Every pair in $B$ therefore has all its common neighbors inside. Its graph has parameters $(9,4,1,2)$ and is the rook grid. One direct identification takes a vertex and its two adjacent neighbor pairs. The other four points correspond to the four choices of one from each pair, and the unique-common-neighbor condition forces the sides of their square. The three special lines of degree one or four partition the grid and hence are parallel.

In the fifth population each exceptional point has profile $(0,2,3,3,3,3,4)$. The degree-two triangles and the degree-four triangles each partition $B$ into three triples. Their intersections have size at most one, so the two partitions give the rows and columns of the grid. Row and column edges already give an adjacent pair one common neighbor and a nonadjacent pair two. An additional diagonal edge would give its ends two common neighbors, excluding it.

The 36-triangle patterns satisfy only the tested constraints. Run `make verify-low-triangle-cover` for the exact enumeration.
