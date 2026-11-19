# Parallel triangle deficits in a grid

For a triangle $T$ write $s_T=12-c_T$, where $c_T$ counts the disjoint triangles joined to it by three edges. In any parallel class of an induced grid, with deficits $s_1,s_2,s_3$, we have
$$
s_i\le 2(s_j+s_k) \qquad (\{i,j,k\}=\{1,2,3\}).
$$
In particular if two parallel triangles have twelve three-edge partners, the third also has twelve. This holds if the first two triangles each lie on six grids. In that case the 99 vertices partition into 33 disjoint triangles and the neighborhood of the third parallel triangle has only 35 possible forms, keeping track of the base grid.

## Counting exterior triangles

Each of the 90 exterior vertices sees precisely one point of the grid. Split them into three sets $V_i$ of size 30 according to the row of that point. Within a given row, split them into three ten-point fibers by their grid neighbor. The edges in one fiber form a perfect matching. Distinct fibers of that row are joined by a perfect matching. For a vertex in one fiber and a grid point in another, one of the two common neighbors is already in the grid, leaving one neighbor in that fiber. Thus exactly 30 edges in $V_i$ go between different fibers.

A triangle with three matching edges to row $i$ is either another row of the grid or a triangle of $V_i$ with one vertex in each fiber. Indeed, a vertex of another grid row sees no exterior vertex attached to row $i$. Hence there are $c_i-2=10-s_i$ exterior triangles wholly in $V_i$. Their vertices are disjoint because the inter-fiber graphs are matchings. Each of the remaining $3s_i$ inter-fiber edges is completed by an exterior point in a different row. An internal matching edge in a single fiber already has its triangle in the base.

For $i\ne j$ let $a_{ij}$ count exterior triangles with two vertices in $V_i$ and one in $V_j$, and let $u$ count those meeting all three rows. There are 150 edges between each $V_i,V_j$: each vertex sees one neighbor in the fiber of the same column and two in each of the other columns. No triangle on an inter-row exterior edge can use a base point. Consequently
$$
a_{ij}+a_{ik}=3s_i,\qquad 2(a_{ij}+a_{ji})+u=150 .
$$
The pair sums $a_{ij}+a_{ji}$ are equal. Summing shows their common value is $s_1+s_2+s_3$. Therefore $3s_i\le2(s_1+s_2+s_3)$, as claimed. When all three deficits vanish, each $V_i$ splits into ten triangles, and these with the three grid rows give the partition of all 99 points.

## The third row

Take the ten triangles in $V_3$ and label their points by the three fibers. In each fiber the internal matching gives a perfect matching on the ten triangle indices. An index pair matched in exactly two colors is impossible. The third base row and the two triangles would induce the nine-vertex rook grid minus one edge, already [excluded](../../STATE.md). A pair matched in all three colors, together with the base row, gives one more grid on that row.

Remove $k$ common matched pairs. The first two remaining matchings have union an even cycle decomposition with all lengths at least four. Up to relabeling this is specified by a partition of $5-k$ into parts of size at least two. The third matching is arbitrary subject to avoiding the first two. The [finite checker](../../experiments/workspace/parallel_triangle_cores.py) builds the ordinary 39-point graph for each choice and identifies isomorphic graphs preserving the base grid and its third row. The resulting counts are

| Additional grids $k$ | 0 | 1 | 2 | 3 | 5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Core types | 23 | 8 | 2 | 1 | 1 |

The classification covers the whole neighborhood of the third row. Its sixty exterior points still require simultaneous attachment.
