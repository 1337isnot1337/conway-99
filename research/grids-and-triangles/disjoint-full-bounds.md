# At most 114 grids and at least 2,106 percolating nonedges

Let $g$ be the number of induced rook grids in a hypothetical 99-graph and $t$ the number of triangles lying in six grids. The [two-full-axis exclusion](two-full-axes.md) makes those $t$ triangles pairwise disjoint, so $t\le33$. At each point the axis graph $D_p$ has at most one vertex of degree six.

The [fifteen-grid root reduction](fifteen-grid-root.md) leaves only the missing pattern $K_{2,3}$, with two isolated axes. Both would be full. Together with the earlier exclusion of 16 through 21 grids, this gives **at most fourteen grids at each root**. At least $84-4\cdot14=28$ nonneighbors of each point percolate with it.

For a global bound use the notation of the [triangle witness count](triangle-witness-bound.md). A triangle of grid degree $d$ already has $2d$ distinct three-edge partners from its grids. Consequently $s_T\le12-2d$. Write $e_p$ for the edge count in $D_p$ and $m_p$ for the number of disjoint edge pairs. The witness inequality $4\sum m_p\le\sum_p\sum_{T\ni p}\min(2,d_T)s_T$ gives $\sum_p C_p\le0$, where

$$
 C_p=2m_p-\sum_{T\ni p}\min(2,d_T)(6-d_T).
$$

The seven-axis [integer enumeration](../../experiments/workspace/grid_support.cpp) gives $C_p-14e_p\ge-138$ at a point outside all full triangles, and at least $-146$ at a point on one. Exactly $3t$ points are on a full triangle, and $\sum e_p=9g$. Summation yields
$$
 126g\le138\cdot99+24t,\qquad 21g\le2277+4t.
$$
In particular $g\le\lfloor2409/21\rfloor=114$. The number of percolating nonedges is therefore at least $4158-18\cdot114=2106$. If there are 114 grids there must be at least 30 full triangles.

The 231 triangles have total grid degree $6g\le684$. If each belonged to at least three grids the total would be at least 693. In fact at least three triangles belong to at most two grids, since a single triangle can fall short of three by at most three. This provides an unrestricted choice of a triangle with at most two grids for construction searches.
