# Triangle-shell components on the prism-free \(x_{521}=0\) face

This is a necessary local reduction for a hypothetical
\(\operatorname{SRG}(99,14,1,2)\) with no triangular prisms and with
\(x_{521}=0\). The coordinate \(x_{521}\) counts the ten-vertex,
seventeen-edge motif \(F\) identified in
[the edge-component note](root_prism_free_edge_components.md).
No incidence optimizer or exterior-edge solver is used here.

The exact census has 16,960 normalized candidates, 8,992 retained
descriptions, and 66 representatives under isomorphisms of the central
triangle together with one eighteen-vertex component. Each representative
has between 414 and 612 admissible exterior-neighbor triples. None fails
the elementary population or Gram-row availability checks.

The source is
[root_prism_free_f0_components.py](../experiments/workspace/root_prism_free_f0_components.py).
The [compressed certificate](../experiments/logs/root-prism-free/f0-components-certificate.json.gz)
contains every representative, every triple domain, and an explicit
vertex transport for every retained description. Generation uses nauty
to find the transports. Replay checks the transports directly and uses
only the Python standard library.

## The mandatory thirty-nine-vertex core

Fix a triangle \(T=\{t_1,t_2,t_3\}\). For each \(i\), let \(X_i\) be the
twelve neighbors of \(t_i\) outside \(T\). These three sets are disjoint:
an additional common neighbor of an edge of \(T\) would violate
\(\lambda=1\). Each \(X_i\) induces a perfect matching.

Every vertex of \(X_i\) has exactly one neighbor in each other \(X_j\).
Indeed, the nonadjacent pair consisting of that vertex and \(t_j\)
already has \(t_i\) as one common neighbor. Its other common neighbor
must lie in \(X_j\). These cross interfaces are perfect matchings.
Thus the graph \(S\) on the 36 shell vertices is cubic. Its three edge
types at each vertex are its internal matching edge and its two cross
matching edges.

There are sixty vertices outside this thirty-nine-vertex core. Each has
exactly two neighbors in each \(X_i\), because it is nonadjacent to every
vertex of \(T\). It therefore has six core neighbors.

Each connected component of \(S\) has the same number \(n\) of vertices
in each \(X_i\), since the cross matchings restrict to bijections.
The number \(n\) is even, since the internal matching also restricts to
the component.

On the prism-free \(F\)-free face, \(n\) cannot be two or four. Restrict
to any two fibers and pull their internal matchings onto one fiber by
the cross matching. A common matching edge gives a prism, while an
alternating component on four labels gives \(F\). A matching on two or
four labels cannot avoid both possibilities. Consequently \(n\ge6\).
Since the three full fibers have size twelve, the shell is either
connected on 36 vertices or consists of two components of size eighteen.

## The Gram matrix and the forced split

Let \(B\) be the full thirty-nine-vertex core adjacency matrix. If \(X\)
is its binary incidence matrix to the sixty remaining vertices, then

\[
XX^{T}=12I+2J-B^2-B.
\]

The central-triangle rows are zero. On the shell coordinates, write
\(D=\operatorname{diag}(J_{12},J_{12},J_{12})\). The Gram matrix is

\[
G=12I-S^2-S+2J-D.
\]

The subspace of vectors constant on each fiber is invariant. On it,
\(G\) has eigenvalues \(60,0,0\). On the orthogonal complement of the
three fiber indicators,

\[
G=(3I-S)(4I+S).
\]

Since \(S\) is cubic, all its eigenvalues lie in \([-3,3]\). Hence
this Gram matrix is automatically positive semidefinite. If the shell
has \(c\) connected components, its rank is \(35-c\). This elementary
Gram test cannot exclude one of these locally admissible shells.

Let \(V\) be a component with \(n\) vertices in each fiber. The vector

\[
w=\mathbf1_V-\frac n{12}\mathbf1_S
\]

is orthogonal to every fiber indicator and satisfies \(Sw=3w\).
Thus \(Gw=0\). From \(G=XX^T\), every exterior incidence column is
orthogonal to \(w\). Since every such column has six shell entries,
every exterior vertex has exactly \(n/2\) neighbors in \(V\).

In particular, in the split eighteen-plus-eighteen case, each exterior
vertex has three neighbors in each component. The difference of the
two component indicators, extended by zero to the other 63 vertices,
is a \(+3\) eigenvector of the full graph, with squared norm 36.

## Exact triple quotas for one eighteen-vertex component

Write its three six-vertex fibers as \(V_1,V_2,V_3\). There must be sixty
distinct triples of component neighbors, one for each exterior vertex.
Two exterior vertices cannot have the same triple: they would have at
least three common neighbors.

Each triple has at most two entries in any \(V_i\), because it extends
to exactly two neighbors in the full twelve-vertex fiber. If \(a_i\)
is the number of its entries in \(V_i\), then

\[
a_1+a_2+a_3=3,\qquad 0\le a_i\le2.
\]

Within one fiber the required Gram block is
\(9I-M+J\), where \(M\) is its matching matrix. Its diagonal entries
are ten. Summing diagonal entries and then all entries gives

\[
\sum_{\text{60 triples}} a_i=60,\qquad
\sum_{\text{60 triples}} a_i^2=84.
\]

For each fiber, twelve triples have occupancy two, 36 have occupancy
one, and twelve have occupancy zero. Therefore 24 triples have profile
\(111\), and 36 have a permutation of \(210\).

Let \(n_{ij}\) count triples with occupancy two in \(V_i\) and occupancy
zero in \(V_j\). The row and column sums of this off-diagonal
three-by-three array are all twelve. Consequently, for an integer
\(0\le a\le12\),

\[
n_{12}=n_{23}=n_{31}=a,\qquad
n_{13}=n_{21}=n_{32}=12-a.
\]

The cross-fiber Gram sums give
\(\sum a_i a_j=48\) for \(i\ne j\). These cross moments are consistent
with the displayed profile counts; they add no further restriction to
the one-parameter description.

For a fixed component, the census considers every three-subset with
fiber occupancy at most two. It retains precisely those satisfying:

1. Every Gram entry on a selected pair is positive.
2. \((I+S)h\le2\mathbf1\), where \(h\) is the triple indicator.

The first condition is necessary because a selected column contributes
one to that Gram entry. The second is the known part of the
core-to-exterior common-neighbor cap. No unknown exterior edges enter
this test.

A binary incidence model can therefore use one selector per retained
triple and require

\[
\sum_h z_hhh^T=G_{18},\qquad z_h\in\{0,1\}.
\]

The diagonal sum already forces \(\sum_hz_h=60\). This is only a
necessary one-component model. It omits the second component, all
cross-component incidence quotas, and all exterior edges.

The source computes \(G_{18}\) from the central triangle and this
component. Only the component rows are used: the omitted second
component has no neighbors in the first component, so it contributes
zero to these Gram rows. The central vertices are not saturated in
this twenty-one-vertex description, and their incomplete Gram rows
are not imposed on the sixty triple columns.

## Complete finite normalization

Use the cross matchings from \(V_1\) to label both other fibers, making
those two matchings identity maps. Label the internal matching of
\(V_1\) as
\[
M=(01)(23)(45).
\]
Let \(P,R\) be the internal matchings of \(V_2,V_3\), and let \(Q\)
be the remaining matching from \(V_2\) to \(V_3\).

Both \(P\) and \(R\) must avoid every edge of \(M\). There are eight
choices each. For six labels, a pair of perfect matchings with no
common edge necessarily forms one alternating six-cycle. Thus both
central edge partitions are \(3\) on this component.

The permutation \(Q\) is a derangement, since a fixed point creates a
shell triangle and hence a prism with the central triangle. There
are 265 derangements. Finally, \(P\) must avoid the pullback
\(Q^{-1}RQ\), enforcing the third central edge partition \(3\).
These are necessary conditions on every split component. They leave
8,992 of the \(8\cdot8\cdot265=16,960\) normalized candidates.
Every retained candidate also passes every visible common-neighbor
cap; this is explicitly checked.

For isomorphism reduction the source uses the entire twenty-one-vertex
description. Its central vertices have degree eight and all shell
vertices have degree four. An isomorphism therefore preserves the
central triangle and transports its three fibers, possibly permuting
them. It is a relabeling of a finite core, not a symmetry imposed on
the unknown graph. The certificate provides explicit transports for
all retained candidates, and replay checks each adjacency bit.

The two eighteen-vertex components need not be isomorphic. Combining
two representatives would also require their fiber alignments. The
present reduction makes neither assumption.

## Connected local control and scope

The certificate includes a connected thirty-six-vertex shell with all
three central edge partitions equal to \(6\). On labels modulo twelve,
take \(M=(01)(23)\cdots(10\,11)\), take both other internal matchings
to be
\((12)(34)\cdots(11\,0)\), and take \(Q(i)=i+1\).

The resulting thirty-nine-vertex core has no internal prism or copy
of \(F\), and it satisfies every visible cap. Thus the local
conditions do not force the split case or a central edge of type
\(33\). This control is a partial graph, not a construction of the
required ninety-nine-vertex graph.

Replay:

    .venv/bin/python experiments/workspace/root_prism_free_f0_components.py \
      --certificate experiments/logs/root-prism-free/f0-components-certificate.json.gz \
      --replay
