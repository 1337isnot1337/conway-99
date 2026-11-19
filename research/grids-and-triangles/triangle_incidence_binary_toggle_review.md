# Independent check of the triangle-toggle counts

Let G have the strongly regular parameters (99,14,1,2), and let C be any
binary linear code orthogonal to every graph triangle. Let B_j count the
weight-j words of C-perp. This note checks the counting arguments for the
new rows. It does not run an optimizer or assert code existence from a
formal enumerator.

For a vertex set U, write e(U) for its induced edge count and t(U) for its
induced triangle count. Define

\[
E_j=\sum_{U\in C^\perp,\ |U|=j}e(U),\qquad
T_j=\sum_{U\in C^\perp,\ |U|=j}t(U),\qquad
S_j=E_j-3T_j.
\]

Every graph edge is in a unique triangle; every vertex is in seven
triangles; there are 231 triangles. For a fixed j-set U the number of
triangles meeting it once is 7j-2e(U)+3t(U). Toggling such a triangle gives
a dual (j+1)-set. Conversely, the triangles that toggle a (j+1)-set back
to size j meet it twice, and their number is e(U)-3t(U). Thus

\[
S_{j+1}=7jB_j-2S_j-3T_j.
\]

This is a bijection of incidences, so it has no unlabelled multiplicity
factor. The earlier replacement proof gives S_3=14(B_2-B_1), while
T_3=231. Consequently

\[
S_4=21B_3-28B_2+28B_1-693.
\]

## Four-point words

A four-set contains at most one triangle. If it contains a triangle, its
fourth vertex has at most one neighbor on that triangle. Such a dual word
is a triangle plus a zero generator column. Each zero-column vertex lies
outside 224 triangles. Exactly 84 of them contain one of its neighbors:
each of its 14 neighbors is on six triangles avoiding the vertex, and no
such triangle can contain two of its neighbors. The other 140 triangles
have no edge to that vertex. Therefore T_4=224B_1.

The 2,079 words obtained by toggling two triangles through a common center
induce 2K2. They are distinct: either edge of the support has that center
as its unique triangle tip. They are disjoint from the four-point words
containing a triangle. Every cap-valid four-set has 0<=e-3t<=4. Subtracting
the known deficits from the upper bound 4 gives

\[
S_4\le4B_4-2(2079)-4(140B_1)-3(84B_1)
       =4B_4-4158-812B_1.
\]

Hence

\[
4B_4-21B_3+28B_2-840B_1\ge3465,\qquad
B_4-224B_1\ge2079.
\]

## Weighted chain counts

Let p_e count unordered pairs of disjoint graph triangles joined by exactly
e crossedges. The crossedges form a matching, so 0<=e<=3. Choosing one
crossedge gives a three-triangle chain. There are

\[
p_1+2p_2+3p_3=231\cdot3\cdot6^2=24948
\]

chains. The five-point word of a chain has an isolated point and four
points spanning two edges plus the other crossedges. A chain from an
e-crossedge pair therefore has e+1 support edges.

There are 2,079 induced four-cycles: the 4,158 nonadjacent vertex pairs
each give one cycle, and a cycle has two diagonal pairs. Each cycle gives
two pairs of opposite edges. Extend those edges to their unique graph
triangles. Their tips lie outside the cycle and are distinct; a shared
tip would be a third common neighbor of opposite cycle vertices. Conversely
a disjoint triangle pair with e crossedges gives binomial(e,2) such
cycle incidences. Therefore

\[
p_2+3p_3=4158.
\]

The sum of support edge counts over chain representations is

\[
2p_1+6p_2+12p_3=2(24948)+2(4158)=58212.
\]

Here the published chain-collision theorem is used: the only repeated
five-point chain words have two representations, there are exactly 9g
of them, and each spans a four-cycle plus an isolated point. The theorem's
frozen source was read for this review. Each repeated word removes four
edges from the representation sum. Thus the distinct chain words have
total edge count 58212-36g, and total deficit from five edges
66528-9g. The factor 36g is 4 times 9g, not 2 times 9g.

The toggle recurrence and T_4 give

\[
S_5=28B_4-42B_3+56B_2-728B_1+1386.
\]

Every cap-valid five-set has 0<=e-3t<=5. With a triangle, the remaining
two vertices each have at most one neighbor on it, so e<=6 and e-3t<=3.
Without a triangle, a vertex of degree three would force any sixth edge
to complete a forbidden K2,3; maximum degree at most two gives at most
five edges directly. The distinct chain words are triangle-free. Hence

\[
58212-36g\le S_5\le5B_5-66528+9g.
\]

Using the stated previously proved bound g<=120 gives

\[
28B_4-42B_3+56B_2-728B_1\ge52506,
\]

\[
5B_5-28B_4+42B_3-56B_2+728B_1\ge66834.
\]

## Triangle containment in five and six points

Count a dual five-set together with one of its triangles by first choosing
the complementary equal-column pair. A pair is disjoint from 217 graph
triangles, with one additional triangle if its endpoints are adjacent.
There are exactly 7B_1 equal-column graph edges. Therefore

\[
T_5=217B_2+7B_1.
\]

A five-set contains at most two triangles. If there are two, they share a
center, and the label sum of their five-point union is the center's label.
Thus exactly 21B_1 dual five-sets have two triangles. The number with at
least one triangle is 217B_2-14B_1. They are disjoint from all chain words,
which proves

\[
B_5-217B_2+14B_1\ge24948-9g\ge23868.
\]

For a dual triple U, inclusion-exclusion gives 210+e(U)-t(U) graph
triangles disjoint from it. Thus

\[
T_6=210B_3+462+14B_2-14B_1.
\]

A six-set has at most two graph triangles. Three triangles with a common
center require seven vertices. Otherwise, three triangles on at most six
vertices would have three distinct pairwise intersection points; those
points would themselves form a triangle and violate uniqueness on its
edges.

There are 24,486 unordered disjoint triangle pairs, and each union is a
dual six-set with exactly two triangles. For an intersecting pair centered
at v, adding an outside vertex z gives a dual word precisely when z has
the same generator column as v. Before excluding arm vertices this counts
21 times the sum of (column-class size minus one), namely 42B_2. Each
ordered equal-column adjacent pair (v,z) appears in six of the triangle
pairs centered at v. There are 14B_1 such ordered edges, so the number of
allowed intersecting-pair unions is 42B_2-84B_1.

Subtracting these two-triangle populations from T_6 gives the exact number
of dual six-sets that contain any triangle:

\[
210B_3-28B_2+70B_1-24024.
\]

This is a lower bound for B_6.

## Two additional six-point edge bounds

Applying the same recurrence once more yields

\[
S_6=35B_5-56B_4+84B_3-763B_2+1435B_1-2772.
\]

Every cap-valid six-set has 0<=e-3t<=7. A triangle-free nonbipartite
six-vertex graph contains a five-cycle and has at most two additional
edges. In the bipartite case eight edges would force K2,3, including the
3+3 split with at most one missing edge. If the six-set has a triangle,
each of the three remaining vertices attaches to it at most once. Their
induced graph has at most two edges unless it is a second triangle. These
cases give e-3t<=5 and e-3t<=3 respectively.

The 24,486 disjoint-triangle unions contribute exactly 24,948 to S_6:
their contributions are their crossedge counts, whose total is the raw
chain count. Their deficit from the upper bound seven is 146,454. Hence

\[
24948\le S_6\le7B_6-146454,
\]

or equivalently

\[
35B_5-56B_4+84B_3-763B_2+1435B_1\ge27720,
\]

\[
7B_6-35B_5+56B_4-84B_3+763B_2-1435B_1\ge143682.
\]

These are exact counting deductions. Any numerical use remains subject
to the separate model/source gate and exact certificate replay. This note
contains no numerical optimization result or complete code exclusion.
