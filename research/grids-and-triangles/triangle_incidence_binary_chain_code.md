# Binary triangle-incidence rank at least 88

Let B be the point-triangle incidence matrix of an SRG(99,14,1,2),
and let C=ker_F2(B^T). The [kernel-weight proof](triangle_incidence_binary_code.md)
restricts its nonzero weights to 36,40,44,48,52,56,60. The following
argument proves dim(C)<=11, hence rank_F2(B)>=88.

## Three-triangle chains

Choose a middle triangle {a,b,c}, two distinct points a,b of that
triangle, another triangle {a,u,v} at a, and another triangle {b,w,z}
at b. There are

    231 * binom(3,2) * 6^2 = 24948

unordered chains. The endpoint triangles are disjoint: a shared point
would be an additional common neighbor of the adjacent pair a,b.

The binary sum of these three triangle words has support {c,u,v,w,z}.
The point c is isolated in the induced support. The other four points
contain the two edges uv,wz; their additional edges form a matching.
The induced support is therefore an isolated point together with two
disjoint edges, a four-vertex path, or a four-cycle.

The isolated point c is determined by the support. Each perfect
matching on the other four points determines the two endpoint
triangles, since each of its edges has a unique common-neighbor tip.
It then determines the middle triangle. The two-edge graph and path
have one perfect matching, and the four-cycle has two. Thus every
word has multiplicity at most two.

If two chains give the same word, the nonisolated support is a
four-cycle. Its four edge tips are distinct and outside the support.
The isolated point, the four-cycle, and its four tips form an induced
nine-vertex rook grid. The two middle triangles pass through the
isolated point. These six triangles provide all 18 grid edges. An
extra edge is impossible because each nonedge of this grid already
has two common neighbors.

Conversely, each choice of a point in a rook grid gives one double
word: take that point and its four nonneighbors within the grid.
The two perfect matchings of the resulting four-cycle give the two
chains. The grid and chosen point are determined by the word, so
this correspondence has no further multiplicity.

If g is the induced grid count, these chains therefore supply exactly
24948-9g distinct weight-five words in C-perp. The proved global bound
[g<=120](grid_intersections.md) gives at least 23868 such words. This
uses no prism-free assumption and no symmetry assumption.

## Complete local collision check

The source `triangle_chain_binary_words.py` checks every cap-valid
catalogue graph of orders seven, eight and nine: 6,435 hosts in total.
Two chains with the same five-point word use at most nine vertices,
so this covers every possible collision union.

The census contains 537 chains and 528 distinct words. Its only nine
double words occur in the unique nine-vertex rook grid. For every
collision, the checker reconstructs the four tips and compares all
18 induced edges with the union of the six chain triangles. A direct
independently labelled rook graph gives 18 chains and nine words.
The proof above also explains the classification without relying on
the census alone.

## Exact coding certificate

Retain the forced dual-weight counts from the
[star-word model](triangle_incidence_binary_star_code.md), and add
L_5=23868. For j=1,...,99, MacWilliams gives

    sum_w (L_j-K_j(w)) A_w <= binom(99,j)-L_j.

An exact dual has only three nonzero multipliers:

| Degree | Multiplier |
| --- | --- |
| 1 | 2144/105189 |
| 4 | 13/315567 |
| 5 | 17/315567 |

Each of the seven dual column sums is at least one. The resulting
bound is

    |C| <= 140594432/35063 < 4096.

Since |C| is a power of two, dim(C)<=11 and rank_F2(B)>=88.

An equivalent integer form makes the certificate short. For each
allowed nonzero weight w,

    -6432*K_1(w) + 13*(2079-K_4(w))
      + 17*(23868-K_5(w)) >= 315567.

The excesses at weights 36,40,44,48,52,56,60 are respectively
0,232704,0,28416,225280,235776,0. Summing the corresponding three
MacWilliams inequalities gives

    315567*|C| + 232704*A_40 + 28416*A_48
      + 225280*A_52 + 235776*A_56 <= 1265349888.

The left side already exceeds the right side when |C|>=4096.

The saved exact primal has nonzero entries
A_36=206251023/140252, A_44=118315809/280504, and
A_60=593657097/280504. All 99 inequalities pass and its objective
equals the dual bound. This proves the optimum of the specified real
weight-enumerator relaxation; those fractional numbers are not a code.

The query source is `triangle_incidence_binary_chain_code.py`. The
query record, cold replay and separate recurrence-based arithmetic
check are under `experiments/logs/grids-and-triangles/`. The earlier
rank-82 and rank-85 certificates remain intact.

The result does not force a nonzero binary kernel. It therefore does
not prove nonexistence of the graph.
