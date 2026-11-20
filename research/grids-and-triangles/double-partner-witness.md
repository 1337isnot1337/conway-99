# At most 105 grids

Let $T$ be a triangle, let $a$ be one of its points, and let $p,q$ be points of two different grids on $T$, each adjacent to $a$. At most one triangle $S$ joined to $T$ by two cross-edges can have unmatched point $a$ in $T$ and use **both** $p,q$ as crossing witnesses. Here witnesses are the [intersections of two grids](triangle-witness-bound.md) whose crossing square uses the other two points of each triangle as opposite sides.

This six-grid exclusion gives **at most 105 grids**, **at least 2,268 percolating nonedges**, and **at least 21 triangles contained in at most two grids**. There are at most 20 full triangles.

## The marked configuration

Suppose there are two such partners $S_1,S_2$. The two grids on $T$ are disjoint away from $T$ and have no edges between their other points. Thus $p,q$ are nonadjacent. Their two common neighbors are $a$ and a point $b$, necessarily the unmatched point of both partners. Write $T=(a,x,y)$. In each $S_i$, label the two other points by the one joined to $x$ and the one joined to $y$. Let $P,Q$ be the triangles at $b$ through $p,q$. The four axes $S_1,S_2,P,Q$ are distinct. Indeed $p,q$ cannot belong to either $S_i$ as they are external witnesses, and they are nonadjacent to each other.

At $b$ the four axis pairs $(S_i,P),(S_i,Q)$ form grids. These are exactly the grids on $S_i$ from the two witnesses. Their union has 25 points: the root, its eight marked neighbors, and four disjoint cells of size four indexed by their two signed neighbors. Grids sharing an axis are anticomplete outside that axis. For two grids sharing only the root, their far cells are joined by a perfect matching, by perfect domination and the near labels. Thus precisely two four-point matchings are unknown. Append $a,x,y$. They already see one point in each of the four grids, so their other contacts to the union are determined. Canonical labeling reduces $24^2$ choices to 117 marked bases. The colors distinguish $b$, the two kinds of near axes, the sixteen far points, $a$, and the pair $x,y$. Each axis and each grid can be recovered from these marks and the adjacency.

Write the grid on $T$ through $p$ as three rows
$$
(a,x,y),\qquad(p,r,s),\qquad(t,u,v).
$$
The five new points lie outside the 28-point base. Indeed the grid meets each witness grid on $S_i$ at $p$ only. In each opposite witness grid, the only points seeing $T$ are $q$ and the two other points of $S_i$; the former lies on a different grid on $T$ and the latter belong to the witness grid through $p$. Each new point sees $T$.

In the $(S_i,P)$ grid the only contact of $r,s,t$ is $p$. The four far points relative to $p$ match $x,y,u,v$ in the new grid. The images of $x,y$ are fixed, leaving two possible orders for the other two. This gives two choices independently for each $i$. The $(S_i,Q)$ grid is disjoint from the new grid, so the match between their nine points is perfect. The images of $a,x,y,p$ are fixed as $q$, the two other points of $S_i$, and $b$. In both opposite grids the same one of the five new points sees the third point of $Q$. Each opposite grid then has four remaining points to biject with the other four new points. There are $4\cdot5\cdot24^2=11520$ attachments for this side. The same enumeration applies to the grid on $T$ through $q$. The new sets of five are mutually anticomplete because the two grids share $T$.

## Exact exterior test

The [normalization](../../experiments/workspace/double_partner_cores.py) and [integer checker](../../experiments/workspace/double_partner_check.cpp) use 38-point ordinary adjacency matrices $A$. On each side separately, and again in combination, require every entry of $R=12I+2J-A-A^2$ to be nonnegative. Exactly 919,143 combined choices survive over the 117 bases. Duplicate 38-point cores, if any, do not affect exhaustiveness.

For every such choice enumerate subsets of the 38 points that meet each of the six grids in precisely one point. Every outside neighborhood gives such a subset. A pair with $R_{ij}=0$ cannot be selected together. For a subset with indicator $w$, also require $Aw+w\le2\mathbf1$, since an outside point and a core point have at most two common neighbors including the adjacency correction. The checker verifies that every surviving subset has size at least three; consequently each can be used at most once. Two selected subsets cannot intersect in more than two points.

Select exactly 61 of these binary rows such that the number containing $i,j$ is $R_{ij}$, including the diagonal. The checker forces a decision when a quota is zero or equals the number of remaining choices. Otherwise it branches by the first undecided row in a chosen column taking the less frequent of the two binary values. This covers every way to meet the quota. The search has no cutoff. None of the 919,143 cores admits such an exterior incidence. As a positive control, all 18 choices of two rows and one column, or the transpose, in the ordinary nine-point rook graph retain an exterior incidence for their two omitted points. Run `make verify-double-partner` for the full check.

## Charging a triangle of grid degree two

Let $d_T$ be the number of grids on $T$, $s_T=12-c_T$ its three-partner deficit, and $W_T$ its number of charged witnesses, summed over all two-edge partners. The [earlier bound](triangle-witness-bound.md) is $W_T\le3s_T\min(2,d_T)$. If $d_T=2$, allow one witness for every partner, of which there are $3s_T$. A partner with a second witness chooses an unmatched point in $T$ and one of two neighbors of that point in each of the two grids. By the exclusion each choice works for at most one partner. Hence
$$
W_T\le 3s_T+3\cdot2\cdot2\le36,
$$
using $s_T\le12-2d_T=8$. The old capacity was 48.

At a root $p$, let $e_p$ count its grids, $m_p$ its unordered pairs of grids meeting only there, and $a_p$ its number of axes of grid degree two. With $C_p$ as in the [root capacity count](disjoint-full-bounds.md), we now have $\sum_p(C_p+2a_p)\le0$. Indeed $4\sum_p m_p\le\sum_T W_T$, and the saving of twelve for each degree-two triangle gives a correction of two per incident point after division by two.

The [seven-axis integer enumeration](../../experiments/workspace/grid_support.cpp) gives $C_p+2a_p-11e_p\ge-102$ outside full triangles and at least $-108$ at a point of a full triangle. There are $3t$ such points for $t$ full triangles. Summing, using $\sum e_p=9g$, yields
$$
99g\le102\cdot99+18t.
$$
Since $t\le21$, this gives $g\le105$. The [pencil bound](eight-triangle-cover.md) $g\ge5t+k$ for $k$ full components rules out $t=21$ as well. There are $4158-18g\ge2268$ percolating pairs. The total grid degree of the 231 triangles is at most $630$, at least 63 short of three per triangle, so at least 21 triangles have degree at most two.
