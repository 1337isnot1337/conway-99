# A grid has at most two rook-isomorphic partners

The later [integer completion proof](rook_partner_bound.md) strengthens the
bound to one partner. This note retains independent star and four-cycle
arguments. The separate [five-cycle proof](rook_interface_five_cycle.md)
extends the short-cycle exclusions without using the integer completion.

Let `R` be an induced three-by-three rook grid in a hypothetical
`srg(99,14,1,2)`. Call a disjoint induced rook grid a partner of `R`
when their perfect matching is a rook-graph isomorphism. Then `R`
has at most two partners.

This theorem has no red-triangle assumption. Its finite part uses the
[three-grid interface classification](two_rook_interfaces.md) and
324 direct common-neighbor contradictions. A second 324-case product
check excludes a four-cycle of isomorphic interfaces. These arguments
require no further
boundary completion, spectral computation, or SAT search.

## Distinct partners are disjoint

Every vertex outside an induced rook grid has exactly one neighbor
in it. Thus the matchings from `R` to two partners `S,T` identify
their point labels with those of `R`.

Suppose `v` belongs to both `S` and `T`. Its unique neighbor in `R`
is some point `p`. For each rook neighbor `q` of `p`, let `s(q)` and
`t(q)` be the matching partners of `q` in `S` and `T`.

The matching isomorphisms imply that both `s(q)` and `t(q)` are
adjacent to `v`. Both are adjacent to `q` by their matching edges.
The point `p` is another common neighbor of `v` and `q`. The pair
`v,q` is nonadjacent, since `p` is the only neighbor of `v` in `R`.
Its common-neighbor quota is two, so

\[
s(q)=t(q)
\]

for all four rook neighbors `q` of `p`.

Choose `q_1` on the row through `p` and `q_2` on its column, with
both different from `p`. They are nonadjacent. Their two images
`s(q_1),s(q_2)` are likewise nonadjacent and belong to both `S` and
`T`. The established
[grid-intersection lemma](grid_intersections.md#grids-and-common-neighbors)
says that a nonadjacent pair belongs to at most one induced rook
grid: its repeated common-neighbor closure generates that grid.
Therefore `S=T`.

Distinct partners of a grid are consequently pairwise disjoint.
This removes a possible hidden hypothesis from the four-grid
argument below.

## Reduction of a four-grid star to 324 assignments

Suppose `R_0` has three distinct partners `R_1,R_2,R_3`. They are
four pairwise disjoint rook grids. Transport the labels of `R_0`
through its three isomorphic matchings, making all three root
interfaces identities.

Every triple `R_0,R_i,R_j` now has two rook-isomorphic interfaces.
The complete three-grid classification restricts its remaining
permutation to the orbit of

\[
p=(0,5,7,8,6,1,4,2,3)
\]

under common rook conjugation and inversion. The permutation `p`
is an involution, so inversion adds no new members. Its conjugacy
orbit under the 72 rook automorphisms has exactly eighteen members.
Each member fixes one point and interchanges four pairs.

Common rook relabeling of all four bases preserves the three identity
root matchings. Use it to make the interface `R_1 -> R_2` equal to
the displayed `p`. The other two leaf interfaces remain in the same
eighteen-member orbit. There are therefore exactly

\[
18^2=324
\]

ordered assignments to check. No additional symmetry restriction is
imposed on these assignments.

## Every assignment exceeds a common-neighbor quota

For each assignment, build the induced adjacency matrix `B` on the
36 vertices. It contains four rook graphs, three identity root
matchings, and the three leaf matchings. Every core vertex has
degree seven.

For each pair of distinct core vertices `u,v`, the necessary bound is

\[
|N_B(u)\cap N_B(v)|+B_{uv}\le2.
\]

All 324 assignments violate this bound. The saved certificate for
each assignment contains the violating vertex pair, its adjacency
status, and the explicit list of common neighbors already present
inside the core. No outside vertex can remove these common
neighbors.

Using the first violating pair in numerical order gives 161
adjacent-pair violations and 163 nonadjacent-pair violations. These
counts are a description of the selected certificates, not distinct
types of cores.

The replay constructs each core from scratch and verifies every
displayed common neighbor by direct membership checks. Thus all
three-partner configurations are impossible, proving the theorem.

## Four-cycles of isomorphic interfaces are impossible

Let `O` be the eighteen-member permutation orbit from the three-grid
classification. Its members are all involutions with a unique fixed
point. The following exact finite property also holds:

\[
p,q\in O,\quad pq\text{ a rook automorphism}
\quad\Longrightarrow\quad p=q.
\]

The checker visits all 324 ordered products. Eighteen are identities,
with equal factors. For each of the other 306, the certificate gives
a pair of point labels whose adjacency differs from the adjacency
of their images. Thus these products cannot be rook automorphisms.

Suppose four distinct grids form an isomorphic-interface cycle
`R_0,R_1,R_2,R_3,R_0`. Adjacent grids are disjoint by definition, and
opposite grids are distinct partners of a common grid. The disjoint
partners lemma above therefore makes all four grids pairwise
disjoint.

Transport labels along the path `R_0 -> R_1 -> R_2 -> R_3`, making
these three cycle matchings identities. Write `r` for the remaining
cycle matching `R_0 -> R_3`; it is a rook automorphism. Write `p`
for the diagonal matching `R_0 -> R_2`.

The triple with root `R_1` has identity interfaces to `R_0` and
`R_2`, so the three-grid classification gives `p in O`. Next root
the opposite triple at `R_3`. Transporting its labels to `R_0`
uses `r^{-1}`, while transport to `R_2` is the identity. Thus its
remaining leaf interface is `p r^{-1}`, which also belongs to `O`.

Because `p` is an involution,

\[
p\,(p r^{-1})=r^{-1}.
\]

The right side is a rook automorphism. The product property forces
`p=p r^{-1}`, and hence `r` is the identity.

Let `c` be the unique fixed point of `p`. The vertices labeled `c`
in `R_0` and `R_2` are adjacent, because their matching is `p`.
All four cycle matchings are now identities, so the vertices
labeled `c` in `R_1` and `R_3` are two distinct common neighbors of
that adjacent pair. This contradicts `lambda=1`.

The second diagonal matching was not constrained in this last
argument. Its edges cannot remove either displayed common neighbor.

## Consequence for the graph of isomorphic interfaces

Form a graph whose vertices are the induced rook grids and whose
edges join partners. This graph has maximum degree two. It is also
triangle-free by the
[three-isomorphic-interface obstruction](three_red_boundary.md).
It has no four-cycle by the product argument above. Its components
are therefore isolated vertices, paths, or cycles of length at least
five. In particular, the number of isomorphic
interfaces is at most the number of grids.

These are restrictions on the grid system, not a proof that the
strongly regular graph itself is impossible.

## Replay and certificate dependencies

First replay the complete three-grid classification, then the
four-grid certificates:

```sh
python experiments/workspace/two_rook_interfaces.py \
  --verify experiments/logs/grids-and-triangles/two-rook-interfaces.json

python experiments/workspace/rook_interface_star.py \
  --verify experiments/logs/grids-and-triangles/rook-interface-star.json
```

Both commands use only the Python standard library. The star checker
independently reconstructs the eighteen conjugate permutations and
compares their complete list with the classification artifact.
It then visits all 324 ordered star assignments and checks their
saved integer certificates. It separately checks all 324 ordered
products and every saved nonisomorphism witness. The eighteen fixed
points and their resulting adjacent-pair contradictions for an
identity cycle are recorded as well.

The surviving three-grid class has at least two distinct exact
outside-incidence matrices. The second is recorded separately in
`two-rook-interfaces-incidence-second.json`. Their sets of 72
signatures intersect in 34 signatures, so the incidence witness is
not unique. Both are controls for the weaker boundary equations;
neither artifact specifies the exterior adjacencies of a graph.
