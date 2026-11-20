# Branching among grids with parallel full triangles

In a hypothetical Conway 99-graph there are at most **113 grids** and at least **2,124 percolating nonedges**. At least **1,206** disjoint triangle pairs have exactly two cross-edges. At least **five** triangles lie on at most two grids each.

Call a triangle *saturated* if it has twelve three-edge partners, or equivalently no two-edge partner. Every full triangle (one in six grids) is saturated. In a grid with two parallel full triangles the third parallel triangle is also saturated by the [parallel deficit inequality](parallel-triangle-deficits.md). Full triangles are [pairwise disjoint](two-full-axes.md).

## A forbidden configuration of five grids

Suppose a full triangle $T$ lies on four grids $G_1,\ldots,G_4$ each containing another full triangle. Write the two other rows parallel to $T$ as $U_i,V_i$. All these triangles are saturated. Distinct pages of grids on a common triangle are anticomplete to one another outside that triangle: each exterior page vertex already has a neighbor on the common triangle, which exhausts its allowance in the other grid.

Suppose $U_1$ is full and lies in a further grid of this kind outside the grids on $T$. Write $X,Y$ for its two other parallel lines. They too are saturated, and are anticomplete to $T$ and $V_1$. The eleven triangles $T,U_i,V_i,X,Y$ are disjoint. In particular no point of $X$ or $Y$ can be in any of the four original grids, since every point of each is on $T$ or sees $T$.

Each of $X,Y$ sends three edges into each $G_i$ for $i=2,3,4$ by perfect domination. None goes to $T$. Saturation excludes a split into one and two edges, so all three go to one of the two other rows. They cannot both select the same row, since each point of that row has only one neighbor in the new grid. Name the rows so that $X$ is matched to $U_2,U_3,U_4$ and $Y$ to $V_2,V_3,V_4$.

Let $H$ have one vertex for each of the eleven triangles and an edge for each three-edge matching. Every remaining pair is anticomplete. Besides the four triangles $T U_i V_i$ of $H$, its edges form the triangle $U_1 X Y$ and the six edges $XU_i,YV_i$ for $i=2,3,4$.

There are 66 points outside these eleven triangles. Say an exterior point marks a triangle when it has a neighbor there; it has at most one. The total number marking vertex $a$ of $H$ is $36-3d_H(a)$. For two distinct vertices $a,b$ the number marking both is
$$
18-15\,\mathbf 1_{a\sim b}-3|N_H(a)\cap N_H(b)|.
$$
Indeed the sum of common-neighbor counts over the nine pairs of points between the triangles is 18 minus their cross-edge count. Within the two triangles there are four contributions per cross-edge. Each common neighboring triangle contributes three more.

Every exterior point marks exactly one row of each of the five grids. Twelve points mark $T$ since its degree in $H$ is eight. The other 54 each choose one of $U_i,V_i$ for all four $i$. Across the three pairs of indices in $\{2,3,4\}$, there are 72 same-side choices: each pair $U_i,U_j$ has twelve common exterior marks and so does each pair $V_i,V_j$, by the formula. A point choosing all three on one side contributes three; every other point contributes one. Hence exactly $(72-54)/2=9$ points choose all three on one side.

But 30 exterior points mark $V_1$, since its degree is two. Each such point marks one of $X,Y$ and one of each $U_i,V_i$ for $i=2,3,4$. There are just eighteen joint marks on the six pairs $XU_i,YV_i$, three per pair by the formula. At least $30-18=12$ of the points marking $V_1$ therefore choose none of the three sides matched to their choice of $X$ or $Y$. These twelve choose all three on one side, contradicting nine.

## Global bounds

Let $t$ be the number of full triangles, and $b_j$ the number of grids with exactly $j$ full lines. Here $0\le j\le3$, as intersecting full lines are impossible. Consider the incidence structure with full triangles as vertices and the grids counted by $b_2,b_3$ as blocks. If a vertex lies on at least four blocks, all blocks of its connected component contain it. Otherwise a first block outside this family meets one of its blocks at a different full vertex, giving the five-grid contradiction. Distinct blocks through the same vertex share no other vertex.

A component with maximum degree at most three has at most three incidences per vertex on average. In a component all of whose $d$ blocks contain one vertex, every other vertex lies on just one block and there are at least $d$ such vertices. Summation gives
$$
2b_2+3b_3\le3t,\qquad b_1=6t-2b_2-3b_3\ge3t.
$$
Thus $g\ge b_1+(6t-b_1)/3\ge4t$. The [crossing-witness inequality](disjoint-full-bounds.md) gives $21g\le2277+4t\le2277+g$. Hence $g\le113$ and $4158-18g\ge2124$. The total grid degree of all 231 triangles is at most 678, at least fifteen short of $3\cdot231$. A triangle below three can account for at most three of the shortfall.

For the two-edge pair count $n$, the [weighted root expression](triangle-witness-bound.md) is at least 97 everywhere and at least 98 at a point outside all full triangles. The [integer enumeration](../../experiments/workspace/grid_support.cpp) checks the latter minimum. Exactly $3t$ points lie on full triangles, giving $8n\ge9702-3t$. If $n\le1203$, the [disjoint-edge bound](grid_intersections.md) $n\ge36g-2376$ gives $g\le99$, hence $t\le24$. This would give $8n\ge9630>8\cdot1203$. Since $n$ is a multiple of three, $n\ge1206$.
