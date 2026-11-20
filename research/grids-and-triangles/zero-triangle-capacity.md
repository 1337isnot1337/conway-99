# At least 39 triangles on at most two grids

A hypothetical Conway graph has **at least 39 triangles of grid degree at most two**. The count uses a restriction on pairs of three-edge partners of a triangle on no grid. It also gives a separate constraint on triangle partitions. In any partition into 33 triangles on no grids, at least 149 pairs of its triangles have exactly one or two cross-edges.

## Count the triangles on no grid

Let $\mathcal Z$ be the family of all triangles of grid degree zero, $N=|\mathcal Z|$, and $z_p$ the number through point $p$. Write $a=\sum_p(z_p-1)_+$. For $i=1,2,3$, let $m_i$ count unordered disjoint pairs in $\mathcal Z$ with $i$ cross-edges. Set $D=m_1+2m_2+3m_3$.

Fix $T\in\mathcal Z$, and let $u_T$ be its number of three-edge partners in $\mathcal Z$. In each of the three twelve-point fibers of $T$, these partners supply $u_T$ distinct sites. Indeed the matchings between the fibers determine the rest of a partner from any one of its sites. The matching within a fiber has at least $u_T-6$ edges among the chosen sites, since the other $12-u_T$ sites can cover at most that many matching edges.

A matching edge in a fiber joins two different three-edge partners $U,V$. Their only possible edges are aligned within the three fibers because each vertex has already used both its cross-fiber neighbors inside its own triangle. Two edges between $U,V$ would force the third by the [rook-minus-one-edge exclusion](../../STATE.md). Three edges would give a grid on $T$. Thus the edge is the unique edge between $U,V$. Its endpoints determine their unique common neighbor $p\in T$. Different triangles $T$ can charge this same pair only at $p$. At each point on a zero-grid triangle choose one such triangle as primary. Each additional triangle at that point can charge at most six edges in that fiber. It follows that
$$
 6m_3-18N=3\sum_{T\in\mathcal Z}(u_T-6)\le m_1+6a.
$$
If a *selected* family of 33 zero-grid triangles partitions the graph, the same argument within that family has $a=0$, $N=33$ and $D=594$. Substituting $3m_3=594-m_1-2m_2$ gives $3m_1+4m_2\ge594$, proving the stated bound of 149. This part permits additional zero-grid triangles outside the partition.

## Crossing witnesses lost to zero-grid partners

Return to the family of all zero-grid triangles. For a positive-degree triangle $S$, let $h_i(S)$ be its number of $i$-edge partners in $\mathcal Z$. Among its $c_S=12-s_S$ three-edge partners, $2d_S$ are parallel partners in its own grids. Thus $h_3(S)\le12-s_S-2d_S$. Each of its $3s_S$ two-edge partners belonging to $\mathcal Z$ has no crossing witness, as a witness requires a grid at both ends.

For $d_S\ne2$, the issued capacity for $S$ is $3q_S(12-2d_S)$, with $q_S=\min(2,d_S)$. Its unused capacity is at least $3h_3(S)+h_2(S)$ by the preceding bounds. For $d_S=2$ the issued capacity is 36. The [double-partner argument](double-partner-witness.md) allows at most twelve partners with two witnesses, so $W_S\le3s_S-h_2(S)+12$. Again the unused capacity is at least $3h_3(S)+h_2(S)$.

The sum of the issued capacities minus four times the number of grid pairs meeting at a point is $-2\sum_p C_p$, for the [root weights](104-grid-bound.md#sum-of-root-weights). This bounds the total unused capacity from above. At each zero-grid triangle, three times the total number of three-edge partners plus the number of two-edge partners equals 36. Subtract pairs with both ends in $\mathcal Z$ to obtain
$$
 36N-6m_3-2m_2=\sum_{S\notin\mathcal Z}(3h_3(S)+h_2(S))\le -2\sum_p C_p .
$$

Writing $m=m_1+m_2$, the first inequality gives $4m\ge2D-18N-6a$, and the second gives $m\le D-18N-\sum_p C_p$. Hence $4\sum_p C_p\le2D-54N+6a$.

The quadratic form $z^tAz$ counts ordered cross-edges. Each triangle contributes six to its self-term. An ordered pair of distinct triangles meeting at a point contributes four, from the four edges incident with that point. Thus $2D=z^tAz-6N-4\sum_p z_p(z_p-1)$. The largest nonconstant adjacency eigenvalue is three, so
$$
 z^tAz\le3\sum_p z_p^2+\frac{(\sum_p z_p)^2}{9}.
$$
Using $3N=\sum_p z_p$ gives an inequality involving only the root supports:
$$
 \sum_p\left(4C_p+z_p^2+16z_p-6(z_p-1)_+\right)
 \le \frac{(\sum_p z_p)^2}{9}.
$$

## Check near-minimal covers

As in the [cover classification](low-triangle-cover.md), a point on one low triangle has six degree-three axes, one zero axis, nine grids and $C_p=0$. Such a point contributes 17 to the left side. A point with $\ell>1$ low axes consumes $\ell-1$ of the total excess $3L-99$ for $L$ low triangles.

The [integer verifier](../../experiments/workspace/zero_triangle_capacity.py) enumerates exceptional root profiles as multisets. For each suffix of the degree profile list, excess and change in the total number of zero axes, it computes the minimum possible change to the left side. A branch is discarded only when its minimum already violates the inequality. The sum of the zero axes is divisible by three. For $33\le L\le37$ no root multisets remain. At $L=38$ there are 244, reduced to 18 by the special-triangle divisibility, available-neighbor count and grid divisibility from the cover classification.

For each of the 18, $h=9\mathbf1-e$ is nonnegative with fewer than fifteen positive entries, and its largest entry exceeds $k=(\sum_p h_p)/9$. By perfect domination of each grid, $Ah=3h+k\mathbf1$. A vertex with $h=0$ therefore cannot neighbor the maximum. The maximum vertex and its fourteen neighbors must all have positive weight, which contradicts the support count. Run `make verify-zero-triangle-capacity` for the enumeration.
