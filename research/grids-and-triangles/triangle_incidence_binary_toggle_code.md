# Binary code constraints from triangle toggles

Let G be a hypothetical SRG(99,14,1,2), let B be its point-triangle
incidence matrix, and let C=ker_F2(B^T). Write A_w for the weight counts
of C and B_j for the weight counts of C-perp. The repeated letter B in
this standard coding notation is distinguished by its subscript.

The [kernel proof](triangle_incidence_binary_code.md) restricts nonzero
weights of C to 36,40,44,48,52,56,60. This note adds ten exact constraints
on the dual counts. The resulting real coding bound is

    |C| <= 52183040/17817.

It improves the real relaxation but leaves dim(C)<=11 and rank_F2(B)>=88.
The code may be zero. No graph exclusion follows from this bound alone.

## Equal columns and three-point replacements

Choose a generator matrix for C and label each graph vertex by its column.
A vertex has zero label exactly when its unit vector is in C-perp. Two
vertices have equal labels exactly when their pair vector is in C-perp.
Thus B_1 counts zero labels and B_2 counts equal-label pairs. Every graph
triangle has label sum zero.

An equal-label graph edge has a zero-label opposite tip in its unique
triangle. Conversely, each of the seven triangles through a zero-label
point gives such an edge. Hence exactly 7B_1 graph edges have equal labels,
and

    B_2 >= 7B_1.

Replace a vertex of a graph triangle by another vertex with the same
label. The new three-set is a dual word. If the replacement point is
outside the original triangle, the new set is not a graph triangle:
its unchanged edge has only one common-neighbor tip.

Every equal-label pair gives fourteen oriented replacements before the
two invalid replacements within a common triangle are removed. There
are 7B_1 equal-label graph edges, so the number of valid replacements is
14(B_2-B_1).

Let n_i count nontriangle dual three-sets with i graph edges. A nontriangle
three-set has at most two edges. Each of its edges specifies exactly one
replacement representation. Therefore

    n_1+2n_2 = 14(B_2-B_1),
    B_3 = 231+n_0+n_1+n_2.

In particular,

    B_3-7B_2+7B_1 >= 231.

These identities hold for every binary code orthogonal to the graph
triangles, including the zero code.

## Toggle identities

For a dual word S, let e(S) be its induced edge count and t(S) its induced
triangle count. Let E_j and T_j be their sums over all dual words of
weight j, and put S_j=E_j-3T_j.

Every triangle vector belongs to C-perp, so symmetric difference with a
triangle permutes the dual code. A j-set S meets exactly
7j-2e(S)+3t(S) triangles in one point. Toggling such a triangle gives a
(j+1)-set that meets it in two points. Reversing the toggle gives

    S_(j+1) = 7j B_j-2S_j-3T_j.

Toggling a triangle disjoint from a (j-3)-word instead gives

    T_j = (231-7(j-3)) B_(j-3)+E_(j-3)-T_(j-3).

The first replacement count and these two identities yield

    E_3 = 693+14(B_2-B_1),
    T_4 = 224B_1,
    T_5 = 217B_2+7B_1,
    T_6 = 210B_3+462+14B_2-14B_1,

    S_4 = 21B_3-28B_2+28B_1-693,
    S_5 = 28B_4-42B_3+56B_2-728B_1+1386,
    S_6 = 35B_5-56B_4+84B_3-763B_2+1435B_1-2772.

## Four-point words

The 2,079 distinct words obtained by adding two intersecting triangle
vectors induce two disjoint edges. Their contribution to S_4 is two per
word. A dual four-set containing a graph triangle consists of that
triangle and a zero-label point outside it. There are exactly 224B_1
such sets. They are disjoint from the two-edge words.

For a fixed zero-label point, fourteen neighbors each lie on six triangles
avoiding that point. Since a point outside a triangle has at most one
neighbor on it, these give 84 distinct one-edge attachments. The remaining
140 attachments are isolated. Thus the triangle-containing four-sets
contribute 84B_1 to S_4.

Every admissible four-set has e-3t<=4. Accounting for the preceding
disjoint families gives

    B_4-224B_1 >= 2079,
    S_4 <= 4B_4-4158-812B_1.

The second inequality is equivalent to

    4B_4-21B_3+28B_2-840B_1 >= 3465.

## Weighted three-triangle chains

The [chain collision theorem](triangle_incidence_binary_chain_code.md)
gives exactly 24948-9g distinct triangle-free dual five-words, where g
is the number of induced nine-vertex rook grids. Its only double words
have four induced edges.

Let p_e count unordered disjoint triangle pairs with e cross edges.
Those edges form a matching. Each cross edge and its unique triangle tip
gives one chain, so

    p_1+2p_2+3p_3 = 24948.

There are 2,079 induced four-cycles: each nonadjacent pair has two common
neighbors, and each four-cycle has two opposite pairs. Each four-cycle
gives two opposite-edge triangle pairs. Their tips lie outside the cycle
and are distinct; a common tip would give a third common neighbor of
opposite cycle points. Conversely, an e-cross-edge triangle pair gives
binom(e,2) such cycles. Hence

    p_2+3p_3 = 4158.

A chain from an e-cross-edge pair has e+1 support edges. The raw chain
edge sum is therefore 2p_1+6p_2+12p_3=58212. Removing one copy of each
of the 9g double words subtracts 36g. The distinct chain words have

    total edges = 58212-36g,
    total deficit from five edges = 66528-9g.

Every admissible five-set has 0<=e-3t<=5. With a triangle, the other
two points each have at most one neighbor on it, giving at most three
edges after triangle edges are removed. Without a triangle, six edges
would force K_(2,3), contradicting the common-neighbor cap two.

The chain words thus bound both S_5 and its deficit:

    58212-36g <= S_5 <= 5B_5-66528+9g.

Using the established g<=120 gives

    28B_4-42B_3+56B_2-728B_1 >= 52506,
    5B_5-28B_4+42B_3-56B_2+728B_1 >= 66834.

## Triangle-containing five- and six-words

A five-set has at most two triangles. If it contains two, they share
one center, and the label sum of their union is the center's label.
Exactly 21B_1 dual five-sets contain two triangles. Subtracting one copy
from T_5 shows that exactly 217B_2-14B_1 dual five-sets contain a triangle.
They are disjoint from all chain words, so

    B_5-217B_2+14B_1 >= 23868.

A six-set also has at most two triangles. Three triangles through one
point need seven vertices. If three pairwise intersections are distinct,
those intersection points form a triangle whose edges already belong
to the original triangles, contradicting uniqueness of an edge's triangle.
The other intersection patterns also use at least seven vertices.

There are 24,486 distinct unions of two disjoint triangles, all dual
six-words. For two intersecting triangles with center v, adding a point
z outside their five-point union gives a dual six-word exactly when z
has v's label. Before excluding the four leaves, the number is 42B_2.
Each ordered equal-label adjacent pair belongs to six triangle pairs at
its first point. There are 14B_1 such ordered edges, so the excluded
count is 84B_1.

Consequently the number of dual six-sets containing two triangles is
24486+42B_2-84B_1. Subtracting this from T_6 gives the exact number
containing at least one triangle. In particular,

    B_6-210B_3+28B_2-70B_1 >= -24024.

Every admissible six-set has e-3t<=7. A triangle-free bipartite graph
with eight edges contains K_(2,3). A nonbipartite triangle-free graph
contains a five-cycle, and its sixth point has at most two neighbors on
that cycle. If a triangle is present, each of the other three points
has at most one neighbor on it, giving a smaller bound after triangle
edges are removed.

The 24,486 disjoint-triangle union words contribute exactly 24,948 to
S_6, namely their cross-edge total. They contribute a deficit of 146,454
from the bound seven. Thus

    24948 <= S_6 <= 7B_6-146454,

or equivalently,

    35B_5-56B_4+84B_3-763B_2+1435B_1 >= 27720,
    7B_6-35B_5+56B_4-84B_3+763B_2-1435B_1 >= 143682.

## Exact coding calculations

For any new inequality sum_j c_j B_j>=L, MacWilliams gives the row

    sum_w [L-sum_j c_j K_j(w)] A_w
        <= sum_j c_j binom(99,j)-L.

The first two replacement rows reduce the real optimum to
560594944/189229. The complete model retains the previous 99 rows and
all ten new rows. Its one numerical query proposes an exact primal
and dual whose common objective is 52183040/17817. The positive dual
multipliers are:

| Row | Exact multiplier |
| --- | --- |
| Equal-column edges | 1108331/413710740 |
| Three-point replacements | 49/71268 |
| Chain five-word edge lower bound | 1457/153226200 |
| Chain five-word edge upper bound | 412/57459825 |
| Triangle and chain five-word populations | 109/206855370 |

All 109 primal inequalities, all dual signs and all seven dual columns
pass exact rational checks. The earlier rank-88 certificate remains
valid; the stronger real bound does not cross the next power of two.

## Verification and scope

The replacement and toggle controls check all 508 binary subcodes of
the triangle kernels on two disjoint triangles, the nine-point rook
graph and the fifteen-point Kneser graph K(6,2). They directly enumerate
773,659 dual supports for the containment checks. Bounds that need
common-neighbor cap two are applied only to hosts satisfying that cap.

Separate weighted-chain checks cover all 6,435 admissible hosts through
order nine. They check every chain's support-edge count and the four-edge
double-word correction. Twenty-nine hosts contain the tip of every edge;
their disjoint-triangle/four-cycle correspondence is checked directly.
The complete order-five and order-six catalogues verify the maxima five
and seven for e-3t.

The sources use the prefixes `triangle_incidence_binary_replacement`,
`triangle_incidence_binary_toggle`, and `triangle_incidence_binary_toggle_six`.
All preparations, numerical proposals, exact certificates and cold replays
are retained under `experiments/logs/grids-and-triangles/`. The earlier
[formal enumerators](triangle_incidence_binary_integer_enumerators.md)
are preserved with the additional conditions that reject them.

No nonzero codeword is assumed to exist. These results constrain a
hypothetical graph's incidence matrix and do not resolve graph existence.
