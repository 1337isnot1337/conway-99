# The 39-low-triangle case: audit and a conditional weight-18 reduction

This note concerns a hypothetical SRG with parameters $(99,14,1,2)$. It does not exclude 39 low triangles. No census, solver, or verification program was run here.

## What the committed proof establishes

The external head read was [142736721631af16126eda0ad5b97322f12685f9](https://github.com/1337isnot1337/conway-99/commit/142736721631af16126eda0ad5b97322f12685f9). The paused [handoff](https://github.com/1337isnot1337/conway-99/issues/1#issuecomment-7026139885) expressly leaves the 39-low-triangle case open and says the partial weight-18 searches establish no exclusion.

[a1c4847](https://github.com/1337isnot1337/conway-99/commit/a1c4847aee2e69e1f5e25bd2c30c203d991c793d) gives the 104-grid bound. [bbcc978](https://github.com/1337isnot1337/conway-99/commit/bbcc9785fea61a32fcf79b14ae9f647a27c746f6) proves the zero-triangle capacity inequality and excludes counts 33 through 38. Its shipped verifier uses range(33,39), not a classification at 39. Commit 1427367 corrects the four-grid reduction: only three of the four ten-grid supports have a degree-four axis; the remaining profile is $(1,1,3,3,3,3,6)$.

The complete current zero-triangle-capacity and low-triangle-cover notes/sources, 104-grid note/source, and triangle-witness and double-partner notes were read. Earlier finite counts and exhaustive exclusions were not independently rerun. The zero-capacity verifier uses the ordinary-root profile generator but does not call the separate core_possible CP-SAT routine.

Conditional on the cited local and witness premises, no algebraic gap was found in the displayed capacity derivation. Its two inequalities are
$$
6m_3-18N\le m_1+6a,\qquad
36N-6m_3-2m_2\le-2\sum_p C_p.
$$
They imply $4\sum_p C_p\le2D-54N+6a$. Substituting
$$
2D=z^TAz-6N-4\sum_pz_p(z_p-1),\qquad
z^TAz\le3\sum_pz_p^2+\frac{(\sum_pz_p)^2}{9}
$$
gives precisely the implemented root inequality. The integer minimum-cost pruning uses infinity only as an infeasibility sentinel.

Exact source locations at the reviewed head:

- [zero-triangle-capacity.md](https://github.com/1337isnot1337/conway-99/blob/142736721631af16126eda0ad5b97322f12685f9/research/grids-and-triangles/zero-triangle-capacity.md)
- [zero_triangle_capacity.py](https://github.com/1337isnot1337/conway-99/blob/142736721631af16126eda0ad5b97322f12685f9/experiments/workspace/zero_triangle_capacity.py)
- [low-triangle-cover.md](https://github.com/1337isnot1337/conway-99/blob/142736721631af16126eda0ad5b97322f12685f9/research/grids-and-triangles/low-triangle-cover.md)
- [low_triangle_cover.py](https://github.com/1337isnot1337/conway-99/blob/142736721631af16126eda0ad5b97322f12685f9/experiments/workspace/low_triangle_cover.py)

## Explicit assumptions

Let $e_p$ count grids through $p$, and $\ell_p$ count axes whose triangle has grid degree at most two. Put $h=9\mathbf1-e$. Perfect domination of every grid gives
$$
Ah=3h+k\mathbf1,\qquad \sum_ph_p=9k,\qquad k=99-g.
$$
Use the established finite-table consequence that every point has a low axis and a point with exactly one has profile $(0,3,3,3,3,3,3)$, hence $e_p=9$. This ordinary-root classification is a cited premise, not a new replay.

If there are exactly 39 low triangles,
$$
\sum_p(\ell_p-1)=18. \tag{1}
$$
Everything below additionally assumes
$$
h\ge0,\qquad \sum_ph_p=18. \tag{2}
$$
Thus $g=97$ and $Ah=3h+2\mathbf1$. Neither (2) nor $g=97$ is established for every 39-triangle population by the committed proof. A ten-grid root has $h_p=-1$.

## A coordinate above two forces a star, which contradicts (1)

Suppose $h_p>2$. A zero-weight vertex cannot be adjacent to $p$, since its weighted neighbor sum is two. All 14 neighbors of $p$ have positive integer weight, so
$$
3h_p+2\ge14,\qquad 18\ge h_p+\sum_{q\sim p}h_q=4h_p+2.
$$
Therefore $h_p=4$, all its neighbors have weight one, and every other point has weight zero:
$$
h=4\mathbf1_{\{p\}}+\mathbf1_{N(p)}. \tag{3}
$$
The eigenvector equation alone cannot exclude (3): it equals $(A+4I)\mathbf1_{\{p\}}$, and $A^2+A=12I+2J$ proves the required equation identically.

In (3), $e_p=5$. Its seven-axis grid graph has five edges. It cannot have three vertices of degree at least three: their degree sum is at least nine, their induced graph has at most three edges, and hence the full graph would need at least six edges. Thus $\ell_p\ge5$.

The 14 neighbors have $e_q=8$, hence $\ell_q\ge2$. Their contribution to (1), including $p$, is at least $4+14=18$. Equality is forced: $\ell_p=5$, every neighbor has two low axes, and every other point is ordinary.

The closed neighborhood of $p$ consists of $p$ and seven matched pairs. Its only triangles are those seven triangles through $p$. At a neighbor $q$, each of its six other triangles contains ordinary points and has grid degree zero or three. If $T$ is the triangle through $p,q$, its degree satisfies
$$
16-d_T\equiv0\pmod3,\qquad 0\le d_T\le6.
$$
Hence all seven triangles through $p$ have degree one or four. Their degrees sum to $2e_p=10$, forcing six ones and one four. This gives $\ell_p=6$, a contradiction.

Consequently $h_p\in\{0,1,2\}$ under (1)--(2).

## All excess lies on the positive support

Set $X=\{h=2\}$, $Y=\{h=1\}$, and $S=X\cup Y$. Every point of $Y$ has $e=8$ and at least two low axes. Every point of $X$ has $e=7$ and at least three: five high axes would contribute at least 15 to a degree sum of 14.

Since $2|X|+|Y|=18$, (1) forces
$$
\ell_p=h_p+1\quad(p\in S),
$$
and every point outside $S$ is ordinary. The exceptional set is exactly $S$.

Using the existing exclusion of degree-five axes, the profile equation is
$$
h_p=n_1(p)+2n_2(p)+n_4(p).
$$
A degree-six axis cannot occur in these profiles. Thus if $t_i$ counts triangles of grid degree $i$,
$$
t_1+2t_2+t_4=6. \tag{4}
$$
This is scoped to (1)--(2), not all 39-triangle populations.

## A common-neighbor identity leaves five support cardinalities

Write $x=|X|$, $y=18-2x$. Let $a,b,c$ count edges inside $X$, between $X,Y$, and inside $Y$. The weighted row equations give
$$
b=8x-4a,\qquad c=45-13x+4a. \tag{5}
$$
Each vertex outside $S$ has either one neighbor in $X$ and none in $Y$, or two neighbors in $Y$ and none in $X$. The number of the latter kind is
$$
z=81-5x-2a. \tag{6}
$$
Indeed, a point of $X$ with $r$ neighbors in $X$ has $8-2r$ neighbors in $Y$ and $6+r$ outside $S$. These outside sets are disjoint for different points of $X$.

Counting all common neighbors of unordered pairs in $Y$ gives the exact identity
$$
z+\sum_{u\in X}\binom{|N(u)\cap Y|}{2}
 +\sum_{v\in Y}\binom{|N(v)\cap Y|}{2}
 =y(y-1)-c. \tag{7}
$$
There is no realizability assumption hidden in (7).

Dropping its nonnegative internal sums and using $c\ge0$ yields
$$
\left\lceil\frac{13x-45}{4}\right\rceil\le a
 \le90-26x+2x^2.
$$
The bounds conflict at $x=6,7,8$.

At $x=5$, the graph on $X$ has at most six edges: a triangle leaves at most one contact from each remaining vertex to it, and the triangle-free bound on five vertices is also six. Each point of $Y$ has positive odd degree inside $Y$, so $c\ge4$. Equation (5) forces $(a,b,c,z)=(6,16,4,44)$. The two internal sums in (7) must total eight, but the first alone is at least $b-x=11$, using $\binom r2\ge r-1$.

At $x=4$, the corresponding four-vertex edge bound is $a\le4$, and positive odd $Y$ degrees force $a\ge3$. For $a=3$, $(b,c,z)=(20,5,55)$; (7) requires internal total 30, but its first sum is at least $(20^2/4-20)/2=40$. For $a=4$, $(b,c,z)=(16,9,53)$; the required total is 28, while the first sum is at least 24 and the second at least $2c-y=8$.

Therefore
$$
|X|\in\{0,1,2,3,9\}. \tag{8}
$$
At $x=9$, $h=2\mathbf1_X$ gives $A\mathbf1_X=3\mathbf1_X+\mathbf1$. The induced nine-point graph has parameters $(9,4,1,2)$, hence is the rook grid, and every outside vertex meets it once. This identifies a remaining possibility, not a contradiction.

## Remaining scope

A full equality-case argument first needs an accepted classification of root populations at $L=39$, including negative deviations and totals other than 18. Within (2), the five cardinalities (8), the exact exceptional profiles, equation (4), and the complete pair identity (7) provide a smaller structural target.

No claim is made that these deductions were absent from the paused lane's unpublished work. They are explicit proofs from the stated premises, not conclusions inferred from its partial search results.
