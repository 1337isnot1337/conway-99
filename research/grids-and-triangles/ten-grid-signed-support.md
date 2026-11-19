# A 28-point signed support at ten grids

Suppose a vertex realizes the [ten-grid pattern](ten-grid-bound.md#four-patterns-at-the-upper-bound) with present pairs $01,02,12,15,16,23,24,34,45,46$. It forces an integral $-4$ eigenvector with fourteen positive and fourteen negative entries, all of absolute value one. Six of the positive sites lie in the three cells on axes $2,5,6$. **Together those six sites span at most one edge.**

## A bound for any signed eigenvector of this size

Let $P,N$ be the positive and negative supports of a $-4$ eigenvector taking values in $\{0,1,-1\}$, with $|P|=|N|=14$. For a site $v$, let $p_v,n_v$ count its neighbors in $P,N$. Write $e$ for the edge count in $P$. At a positive site $n_v=p_v+4$, and at a negative site $p_v=n_v+4$. Counting the edges between $P$ and $N$ in the two directions gives $e(N)=e$. The 71 remaining sites have $p_v=n_v$ and total $\sum p_v=140-4e$.

Sum the number of common neighbors over the 91 pairs in $P$. The result is $182-e$. A negative site contributes $\binom{4+n_v}{2}=6+4n_v+\binom{n_v}{2}$. A remaining zero site contributes $\binom{p_v}{2}=p_v-1+(p_v-1)(p_v-2)/2$. Thus the exact slack identity is
\[
29-5e=
\sum_{v\in P}\binom{p_v}{2}
+\sum_{v\in N}\binom{n_v}{2}
+\sum_{v\notin P\cup N}\frac{(p_v-1)(p_v-2)}2 .
\]
All terms are nonnegative, including the term at $p_v=0$. Consequently **each sign class spans at most five edges**. The count uses only the graph parameters and the stated eigenvector.

## The three four-point cells

Let $B_e$ denote the four points on pair $e$, and put $E=B_{04}$, $F=B_{13}$ and $H=B_{14}$. At axes 1 and 4 just two incident pairs are missing. The [axis-sum equations](fourteen-grid-root.md) give $z=z_{04}=z_{13}=-z_{14}$. At a vertex of $E$ the first equality reads $2-d_E=1-d_F$, where $d$ counts neighbors in the indicated cell. Hence every site of $E$ has an internal neighbor. A missing cell has at most two edges, so $E$ is a perfect matching, $z=1$ there and $d_F=0$. The same statements hold with $E,F$ exchanged. Each of these eight points has exactly one neighbor in $H$.

At a site of $H$ write $b=d_E=d_F=2-d_H$. Then $z=-b$. Every other cell incident with axis 1 has $z=0$ except $F$, since the baselines for the two missing pairs $13,14$ there are both zero and their defects are opposite. The analogous assertion holds at axis 4 with $E$ in place of $F$. The eigenvector equation at each signed near point on these two axes says that the corresponding signed half of $H$ has $b$-sum two. In the two-by-two array of sites of $H$ all row and column sums of $b$ are therefore two. The entries are either all one or two zeros and two twos. The latter would give the internal degrees $2,2,0,0$, impossible in a simple graph. Thus $H$ is a third perfect matching, its four sites have $z=-1$, and both $E$ and $F$ match perfectly to it.

In any cell disjoint from $14$, $-z=1-d_H$ gives $z\ge-1$. The equations on $E,F$ give $z\le1$ everywhere outside the three special cells, with $z\le0$ wherever the label meets $04$ or $13$. The root and its near points have value zero. The norm identity $\langle z,z\rangle=7\sum_{w\in E}z(w)=28$ and orthogonality to constants give fourteen sites of each sign. The six additional positive sites lie in $B_{25},B_{26},B_{56}$. They have no edges to $E$ or $F$, because $z=1-d_E=1-d_F=1$ there. Four of the five possible positive edges have already been used by the two special matchings. This proves the claim.

Each of the six additional sites sees two points of $H$. Conversely, a point of $H$ has one negative neighbor in its own cell, and no other negative neighbor. All other negative cells are disjoint from $14$ and have $d_H=0$. The equation $Az=-4z$ now gives precisely three of the six positive neighbors at each point of $H$, in addition to its one neighbor in each of $E,F$.

More precisely, a pair $u,v\in H$ has $2-\mathbf1_{u\sim v}-\mathbf1_{\text{same near sign}}$ of those six sites in common. The two sites share one near point on a side of the signed square and none on a diagonal. Every site outside the six sees at most one vertex of $H$, apart from those near points. Hence if the internal matching of $H$ is the two diagonals, the six extra sites use its six unordered pairs once each. If the matching is two sides, the two diagonal pairs occur twice, the other two sides occur once, and the matched sides do not occur.
