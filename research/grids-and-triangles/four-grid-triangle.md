# A triangle on four grids determines twelve columns of its exterior incidence

Let $T$ be a triangle in exactly four grids of a putative Conway graph. Each of the [three fibers of twelve neighbors](triangle-exterior.md) of $T$ has four points outside these grids. Write $D$ for the graph on these twelve residual points. Up to permuting vertices and the three fibers, **at most fourteen choices for $D$ remain**. Each choice determines all incidences between these twelve points and the sixty vertices $W$ with no neighbor in $T$, up to labeling vertices of $W$. Three of the [four remaining ten-grid root patterns](ten-grid-bound.md#four-patterns-at-the-upper-bound) have an axis in exactly four grids. The remaining pattern has degrees $(1,1,3,3,3,3,6)$.

## The residual graph

A grid on $T$ contributes a six-point triangular prism to its neighborhood. The prism is a component because each point in it has used its one neighbor in each fiber, including its own. The residual graph still consists of an internal matching in each four-point fiber and a perfect matching between every pair of fibers. All components meet the three fibers equally, and those intersection sizes are even. A disconnected residual graph would have two six-point components. With two points in each fiber the inter-fiber matchings give either two transversal triangles or a six-cycle. The first choice makes a triangular prism and supplies an additional grid. In the second the three internal edges join opposite vertices of the six-cycle and give a forbidden $K_{3,3}$.

Use the matchings between the first fiber and the other two to number all three by $0,1,2,3$. Choose the remaining cross permutation in $4!$ ways and the internal matchings in $3^3$ ways. These are 648 labeled inputs. Write $P$ for the three-by-twelve fiber indicator matrix. The exterior common-neighbor matrix on the residual points must be
\[
R=12I+2J-D-D^2-P^tP.
\]
Here $D$ also denotes its adjacency matrix. Exactly 366 labeled inputs are connected and give entrywise nonnegative $R$, representing fifteen isomorphism classes with $T$ distinguished. In one class two transversal triangles of $D$ are joined by exactly two matching edges. Along with $T$ they induce the impossible [rook grid minus one edge](incomplete_grid.md). The census after this exclusion is

| Triangles in $D$ | Pairs occurring twice in $W$ | Classes |
|---:|---:|---:|
| 0 | 4 | 1 |
| 0 | 8 | 3 |
| 0 | 12 | 4 |
| 1 | 9 | 1 |
| 2 | 6 | 1 |
| 2 | 10 | 1 |
| 2 | 14 | 2 |
| 4 | 12 | 1 |

## The sixty exterior vertices

Every vertex $w\in W$ sees two points in each of the three twelve-point fibers. Perfect domination by a grid gives exactly one neighbor in each of the four prisms. Its remaining two neighbors in the fibers form an unordered pair of residual points. For distinct $u,v$ precisely $R_{uv}$ exterior vertices choose that pair. Label the sixty vertices by these pairs with multiplicity. Their incidence with the residual points is now a known matrix $B_0$ satisfying $B_0^tB_0=R$. Each column has ten ones.

This gives an exact reconstruction problem for each of the fourteen inputs. Choose four functions from the sixty labeled vertices to the six points of a prism, one function per prism. Append their four one-hot incidence matrices to $B_0$ to obtain $B$ on all 36 neighbors of $T$. Write $D_*$ for the residual graph together with the four prisms, $P_*$ for the resulting three-by-36 fiber indicators, and $L$ for the adjacency within $W$. Impose the two neighbors per fiber and the three [triangle block equations](triangle-exterior.md)
\[
B^tB=12I+2J-D_*-D_*^2-P_*^tP_*,\qquad
LB=2J-B-BD_*,\qquad L^2+L=12I+2J-BB^t .
\]
With $L$ symmetric, zero-diagonal and binary these conditions suffice. Assembling the three parts $T$, its 36 neighbors and $W$ gives a symmetric binary adjacency whose blocks satisfy $A^2+A=12I+2J$. Its diagonal therefore gives degree fourteen, and every off-diagonal entry gives the required common-neighbor count.

The principal part of the negative-eigenspace Gram $27I-9A+J$ on $T$ and its neighbors has rank 32. On the 36 neighbors the cubic graph $D_*$ has five components. Its eigenvalue three has multiplicity five, and the added $J$ leaves only the four component contrasts in the kernel. Adding $T$ preserves the rank. Indeed for the $-4$ projector $Q$, the equation for $t\in T$ gives $-3Qe_t=Q\mathbf1_T+Q\mathbf1_{U_t}$ where $U_t$ is its fiber. Summing over $t$ gives $Q\mathbf1_T=-Q\mathbf1_{U}/6$. The three projected triangle vertices are already in the fiber span. The sixty-point Schur complement, after restricting the known block to a nonsingular principal submatrix, must therefore have rank twelve.

Run `make verify-four-grid-triangle` for the [integer enumeration](../../experiments/workspace/four_grid_triangle.py).
