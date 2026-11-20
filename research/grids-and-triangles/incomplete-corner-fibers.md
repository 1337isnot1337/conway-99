# Every induced square has intransitive corner fibers

Fix an induced square in a hypothetical Conway graph. Let $v_0,\dots,v_3$ be its cyclic corners, let $t_i$ complete the triangle on side $v_iv_{i+1}$, and let $C_i$ consist of the other ten neighbors of $v_i$. Every group of automorphisms of the induced graph on $C=\bigcup_i C_i$ preserving all four fibers is intransitive on each fiber. The theorem requires no symmetry of the full graph.

## Squares with a missing opposite-tip edge

The four tips are distinct. Consecutive tips cannot be adjacent, since that would give their shared corner two triangles through the same edge. The $C_i$ are disjoint because the corner pairs already have all their common neighbors inside the square and its tips. A point $x\in C_i$ sees neither incident tip, since its edge to $v_i$ would give that tip and $v_i$ a second common neighbor. It can see either nonincident tip. For each nonincident tip $t$, its two common neighbors with $v_i$ include one corner. The other is the tip opposite $t$ if that edge exists, and otherwise is a unique point in $C_i$.

Write $e(x)$ for the number of tips adjacent to $x$. The neighborhood of $v_i$ induces a matching, giving $x$ one neighbor inside $C_i$. For each $j\ne i$, count the two common neighbors of $x$ and $v_j$. Subtract the contribution of $v_i$ if $v_i$ and $v_j$ are adjacent and one for each tip seen by $x$ incident to $v_j$. What remains is the number of neighbors in $C_j$. Summing gives
\[
\deg_C(x)=1+6-2-2e(x)=5-2e(x).
\]
If at least one opposite-tip edge is missing, every $C_i$ has at least one and at most two points adjacent to tips. Each $C_i$ therefore contains two different degrees in $C$.

## The 48-point graph

Now suppose both opposite-tip edges are present. The corners and tips form the eight-point grid $U$. Each point of $C_i$ sees corner $i$ alone among these eight points. The neighbors of corner $i$ consist of two triangle edges among the eight points and a matching on $C_i$. Each point of $C_i$ has two common neighbors with each other corner. For a neighboring corner one of these is $i$, leaving one neighbor in its fiber. For the opposite corner both neighbors lie in its fiber. Thus consecutive fibers are joined by perfect matchings and opposite fibers by bipartite 2-factors. In particular $C$ is 5-regular.

Write $H$ for the graph on two opposite fibers. It is cubic, and every component has the same number of vertices in the two fibers by the cross 2-factor. Each of these numbers is even by the internal matching. In fact **$H$ must be connected**, without any group assumption. For a component of size $m$, subtract $(m/20)\mathbf1_H$ from its indicator, extending both by zero to the full graph. This vector is perpendicular to the full constant vector and attains Rayleigh quotient three. Since the second full eigenvalue is three, it is a full eigenvector. Each point of either other corner fiber has two neighbors in $H$, hence exactly $m/10$ in the component. A proper component would have size ten, which is not divisible by four. Also $H$ contains no triangle: every cross-layer triangle would include an internal matching edge whose common neighbor is already its corner. No cross 2-factor cycle can have length four because two of its points in the same fiber would have three common neighbors including the corner.

## A square determinant test without symmetry

Every such 40-point graph satisfies $-\det(3I-C)=h^2$ for some integer $h$, using $C$ also for its adjacency matrix. Take the eight coordinate vectors on $U$, and in each fiber take the nine differences of its first nine coordinate vectors with its tenth. The 44 columns have zero cross terms between the two blocks in the negative Gram form $G=27I-9A+J$. Its block on $U$ has determinant $47{,}829{,}690{,}000=2^4 3^{14}5^4$. On the contrasts its form is nine times $3I-C$. Their Euclidean Gram determinant is $10^4$. The four fiber constants form an invariant subspace with eigenvalues $5,1,-1,-1$, contributing $-64$ to $\det(3I-C)$.

The determinant of $G$ on any 44 rational columns is a rational square. If they are independent in the Gram space, change coordinates from any nonsingular 44-point principal basis, whose determinant is a [square](../eigenlattices/square_certificate.md). Otherwise the determinant vanishes. Dividing out the square factors above proves the claim, since an integer that is a rational square is an integer square.

## Normalizing the symmetry

Transport the labels of $C_0$ around three consecutive matchings. Any group preserving all four fibers now acts by the same permutations on four copies of ten points. Transitivity on one is equivalent to transitivity on all four. The resulting faithful permutation group is one of the 45 transitive groups of degree ten. The final side matching commutes with it, as do the four fixed-point-free internal involutions. Each opposite relation is an invariant directed relation on two copies of the ten labels, of valency two. It is a union of ordered-pair orbits.

For a regular action of order ten use its cyclic or dihedral multiplication table; commuting maps are right translations. The opposite relations are the unions of two distinct right translations. In the cyclic case the only internal matching is translation by five. In the dihedral case it is a reflection; normalize the first to the standard reflection. Multiplication of rotation exponents by units gives simultaneous relabelings in both cases. For the other groups the checker directly enumerates all commuting maps, matching involutions and valency-two orbit unions from the [GAP catalog](https://gap-packages.github.io/transgrp/).

| Actions | Normalized choices | Meet local common-neighbor bounds |
| --- | ---: | ---: |
| Cyclic regular group | 5,076 | 1,208 |
| Dihedral regular group | 632,826 | 48,038 |
| Nonregular transitive groups | 230 | 64 |

Identify isomorphic graphs preserving the sets of corners, tips and fiber vertices. There are 6,593 marked cores across the three rows.

## Exact tests

On the four fiber constants the eigenvalues of $C$ are $5,1,-1,-1$. The other 36 modes must lie in $[-4,3]$ by interlacing with the full graph (the upper bound also follows directly on vectors perpendicular to the full constant). Divide the integral characteristic polynomial of $C$ by $(x-5)(x-1)(x+1)^2$, obtaining $p$. All roots are real. The remaining modes satisfy the two bounds exactly when both $p(3+x)$ and $p(-4-x)$ have nonnegative coefficients: a root outside the interval gives a positive root of one test polynomial, while inside the interval both are products of factors with nonnegative coefficients. This leaves 341 cores.

On a surviving core with adjacency $M$, use the two principal Gram matrices $G=27I-9M+J$ and $H=44I+11M-2J$. The full $G$ has rank 44 and all its principal minors of that order are [nonnegative squares](../eigenlattices/square_certificate.md). Take independent principal coordinates by exact elimination. The rank bound and the determinant of a rank-44 basis leave 148 cores.

There are [two possible completions of the tip pairs](incomplete_grid.md). In the incomplete case each of the six pairs must have its own exterior point. For a given pair of tips, its point has $2-j$ neighbors in a corner fiber when $j$ of its marked tips see that corner. These give four marks among the forty fiber vertices, in addition to the two tips. Enumerate all choices with these counts. Check common-neighbor bounds, membership of the new Gram column in the column space on the core, and the nonnegative Schur residual for both Gram matrices. A rank-44 core requires residual zero in $G$. At rank 43 the determinant of the principal basis extended by this point must be square. Only two cores admit at least one individual attachment for each of the six tip pairs, and both have rank 43.

For these two cores the six new vectors have at most one dimension left perpendicular to the basis in the negative eigenspace. If the basis determinant is $D$ and the Schur residual at the new point is $r$, its signed coordinate in this line is $\pm\sqrt{Dr}$ after scaling by $\sqrt D$. Thus for two choices their projected inner product plus the signed product divided by $D$ must equal $1$ for a nonedge or $-8$ for an edge. Select one signed vector for each tip pair, checking these exact inner products and the common-neighbor bounds. The six vertices must have exactly one internal edge by the incomplete-grid argument. Neither core admits a selection.

In the complete case, add the center to form the nine-point rook grid. At tip $t_0$, four grid neighbors already form two matched pairs, so the ten remaining neighbors of $t_0$ must pair among themselves. Such a neighbor sees only $t_0$ in the grid: every pair of grid vertices already attains its common-neighbor quota there. To attain its two common neighbors with each corner, it must mark one point in each of $C_0,C_1$ and two in each of $C_2,C_3$. There are $10^2\binom{10}{2}^2=202{,}500$ choices. For existence of one point, local transitivity allows its $C_0$ mark to be fixed. Of the 148 cores, 139 fail this test. For the nine survivors the negative Gram rank on the 49 points is 43. Restore all choices for both points and test the signed inner products and common-neighbor quotas. None permits an adjacent pair through $t_0$. This excludes the complete case and proves the assertion for all induced squares.

Run `make verify-incomplete-corners` with GAP/TransGrp, NumPy, pynauty and python-flint. The [action enumerator](../../experiments/workspace/incomplete_corner_actions.py) and [exact checker](../../experiments/workspace/incomplete_corner_check.py) recreate the counts with integer characteristic polynomials, rational projections and integer square tests. A 3-by-3 rook control checks the one-dimensional residual against actual Gram entries of both signs.
