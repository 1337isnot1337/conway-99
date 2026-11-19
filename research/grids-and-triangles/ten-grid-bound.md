# At most ten grids through any vertex

In a hypothetical strongly regular graph with parameters $(99,14,1,2)$, each vertex lies on **at most ten induced nine-point rook grids**. Consequently it has at least **44 nonneighbors with which it generates all 99 vertices** by two-neighbor closure.

The [eleven-grid classification](four-missing-cones.md#exactly-eleven-grids-at-a-root) leaves a six-edge star together with five edges on four leaves. We exclude this last case by a single integral eigenvector.

## Two equal defects

Label the axes $0,1,2,3,4,5,6$. The full axis is 3; the extra five present pairs are the edges on $0,1,2,4$ other than $04$. Write $B_e$ for the four far points on a pair $e$ and $h_e$ for the indicator of the nine points consisting of the root, its four near points on $e$, and $B_e$. With $A$ the adjacency matrix, put $W=3I-A+J/9$ and $z_e=Wh_e$. The [root identities](fourteen-grid-root.md#the-41-populations) give $Az_e=-4z_e$, $W^2=7W$, and $\sum_{e\ni a}z_e=0$ at each axis. Each $z_e$ vanishes at the near points and root. At $w\in B_f$ its value is the baseline (two if $e=f$, zero if $e,f$ meet once, one if disjoint) minus the number of neighbors of $w$ in $B_e$. Present pairs have zero defect.

The axis equations at $i=1,2$ give $z_{i5}+z_{i6}=0$. Adding the equations at 0 and 4, and subtracting those at 5 and 6, now gives $z_{04}=z_{56}$. Call the common vector $z$. At each point of $B_{04}$ the internal degree equals one plus its degree into $B_{56}$. Since a missing cell has at most two internal edges, all four internal degrees are one. The same holds in $B_{56}$. The two cells are anticomplete and $z=1$ on their eight points. In particular
\[
\|z\|^2=7h_{04}^{\mathsf T}z=28.
\]

The rest of the proof gives a more general obstruction. **If two disjoint missing pairs carry the same defect, the three pairs on the remaining axes cannot all be grids.** Here the three pairs on the remaining axes are $12,13,23$, all present.

To see where $z$ can be nonzero, fix an axis $i$ among $1,2,3$. Every cell $B_{ij}$ with $j$ on a special pair ($04$ or $56$) has $z\le0$: the baseline against that special pair is zero. The two square cells on $i$ and another remaining axis each have total $z$ zero. In fact their labels are disjoint from $04$ and every site of $B_{04}$ sees exactly one site of each square. The sum of $z$ over all six cells on $i$ is zero by adding $Az=0$ at the two signed near points of $i$. Thus the nonpositive contributions all vanish, point by point. This argument uses no grid assumption on those four cells.

All remaining nonzero entries lie in two sets:

* $M=B_{05}\cup B_{06}\cup B_{45}\cup B_{46}$. At $w\in M$, let $n_w$ be its number of neighbors in $B_{04}$, equally its number in $B_{56}$. Then $z(w)=-n_w$.
* The three square cells $G_{12}=B_{12}, G_{13}=B_{13},G_{23}=B_{23}$. For a site $s$ in such a square, let $b_s$ be its number of neighbors in $B_{04}$, equally its number in $B_{56}$. Then $z(s)=1-b_s$. Each of the four points in $B_{04}$ has one neighbor in each square by grid domination, so $\sum_{s\in G} b_s=4$ separately in each $G$.

The square sums of $z$ are zero. Since $z$ is orthogonal to constants, $\sum_{w\in M} n_w=8$.

## Eight negative sites

Each $w\in M$ has one neighbor $s_G(w)$ in each of the three squares, whose labels are disjoint from its own. Evaluate $Az=-4z$ at $w$. Its positive neighbors from $B_{04},B_{56}$ contribute $2n_w$. The three squares contribute $3-\sum_G b_{s_G(w)}$. All remaining contributions come from $M$. Hence
\[
\sum_G b_{s_G(w)}+\sum_{w'\in M,\ w'\sim w} n_{w'}=3-2n_w .
\]
Both sums on the left are nonnegative. Thus $n_w\le1$, and exactly eight sites of $M$ have $n_w=1$. Each of these eight has total $b$ over its three square neighbors at most one. The eight positive sites and these eight negative sites account for 16 of the 28 units of squared norm. The three squares must account for the remaining twelve.

Let $p(s)$ denote the corner opposite $s$ in its square, and let $N_s$ be the number of negative sites of $M$ adjacent to $s$. The other two squares have no edges to this one, since their axis pairs intersect. Applying the eigenvector equation at $s$ gives
\[
N_s=6-2b_s-\sum_{t\text{ adjacent to }s\text{ in the square}}b_t
    =2-b_s+b_{p(s)} .
\]
If $b_s\ge2$, none of the eight negative sites can see $s$. Therefore $b_s-b_{p(s)}=2$ at every such site. In particular a value of four is impossible.

## The three square profiles

The table lists all multisets of the four $b_s$ and their contributions. In a $2,1,1,0$ or $2,2,0,0$ square, a two must be opposite a zero. In a $3,1,0,0$ square the three must be opposite the one. The middle column gives the squared norm of $z$ in the square. The last gives the total $b$ charged to the eight negative sites by that square.

| Values of $b_s$ | $\sum_s(1-b_s)^2$ | $\sum_s b_s N_s$ |
|---|---:|---:|
| $1,1,1,1$ | 0 | 8 |
| $2,1,1,0$ | 2 | 4 |
| $2,2,0,0$ | 4 | 0 |
| $3,1,0,0$ | 6 | 4 |

The three norms sum to twelve and the three charges sum to at most eight. The possible norm triples are $(4,4,4)$ and $(2,4,6)$; $(0,6,6)$ would charge sixteen.

On an axis of a square, the two sites adjacent to its positive near point form one signed half. For a norm-four square, $z$ is $(-1,-1,1,1)$ with the equal negative values adjacent. The half-sum has absolute value two on one axis and zero on the other. For either a norm-two or a norm-six square the half-sums have absolute value one on both axes. At each of axes 1, 2, 3 the two incident squares must cancel their half-sums, since $Az=0$ at the positive near point and every other neighbor of that point has zero $z$.

For $(4,4,4)$ there are three nonzero half-sums, which cannot cancel in pairs. For $(2,4,6)$ the norm-four square sends a half-sum of absolute value two to an axis where its partner has absolute value one. This excludes the last support. Each rooted grid accounts for four distinct nonpercolating nonneighbors by the [grid-or-percolation count](grid_intersections.md), giving $84-4\cdot10=44$.

Run `make verify-ten-grid-bound` for the [integer sign-table checker](../../experiments/workspace/last_eleven_grid.py) and the preceding four-missing support classification. The sign table tries all 13 oriented profiles directly. Of 496 norm-compatible triples, 448 pass the contact bound and none satisfies the three signed-axis equations.

## Seven patterns at the upper bound

Suppose a root lies on ten grids and put their ten edges on the seven axes. There are 148 unlabelled choices before the structural tests. The signless-incidence, full-axis and four-disjoint-missing restrictions retain 56. Excluding the five four-edge shapes leaves ten. In three more, a missing four-point cell cannot realize any of the required internal degree sequences. The [enumerator](../../experiments/workspace/ten_grid_supports.py) retains the seven labeled representatives below. The surviving cases are necessary patterns; the tests do not construct the full graph for any of them.

| Degrees of the seven axes | Ten present pairs |
|---|---|
| $1,1,2,3,3,4,6$ | $01,02,03,12,13,23,24,34,35,36$ |
| $0,2,2,4,4,4,4$ | $01,02,03,05,12,13,15,23,24,34$ |
| $0,2,3,3,4,4,4$ | $01,02,04,12,13,23,24,34,35,45$ |
| $1,1,3,3,3,3,6$ | $01,02,04,12,13,23,24,25,26,34$ |
| $0,3,3,3,3,4,4$ | $01,02,05,12,13,23,24,34,35,45$ |
| $2,2,2,3,3,4,4$ | $01,02,12,15,23,24,34,45,46,56$ |
| $2,2,2,2,4,4,4$ | $01,02,12,15,16,23,24,34,45,46$ |

In particular, if the root lies on a full triangle, exactly two of its other six axes occur in just one grid. After deleting the full axis and these two leaves, the four remaining axes induce a four-cycle or a triangle with a pendant edge.
