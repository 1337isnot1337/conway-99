# Three rook-isomorphic bases are impossible

In a hypothetical strongly regular graph with parameters `(99,14,1,2)`,
there cannot be three disjoint induced 3-by-3 rook grids whose three
matching interfaces are rook-graph isomorphisms. This statement does
not assume that the grids are all-red.

The proof has three cases. The identity case permits too few outside
neighborhoods. A fixed point excludes the reflection case. The
translation case has inconsistent linear incidence equations. All
three cases have independent exact enumerations using only Python's
standard library.

Together with the established red-triangle closure properties, this
also proves that the graph has at most one all-red grid.

## The three interface classes

Every exterior vertex has exactly one neighbor in an induced rook
grid. Any pair of grid vertices has its full common-neighbor quota
inside that grid, so an exterior vertex has at most one neighbor there.
The grid sends `9(14-4)=90` edges to its 90 exterior vertices, forcing
equality. Thus two disjoint grids are joined by a perfect matching.

Suppose three such grids have pairwise rook-isomorphic matchings.
Label the grids `0,1,2`. Transport the point labels of grid zero
through its two matchings. Both root matchings become identities, and
the remaining interface is a rook automorphism `p` from grid one to
grid two. Points within each grid are `(x,y)` in `F_3^2`, numbered
`3x+y`.

The map `p` cannot send a point `x` to a rook neighbor. Otherwise the
root point `x` and point `p(x)` in grid two have three common neighbors:
root point `p(x)`, point `x` in grid two, and point `x` in grid one.

A rook automorphism either permutes the two coordinate classes
separately or exchanges them. There are `2(3!)^2=72` possibilities.
The condition above leaves exactly these eleven:

- The identity.
- Four maps `(x,y) -> (x+a,y+b)`, where `a,b` are both nonzero in `F_3`.
- Six maps `(x,y) -> (sigma(y),sigma^{-1}(x))`, with `sigma` in `S_3`.

For the first coordinate-preserving form, a fixed coordinate together
with a moving coordinate is forbidden. Thus either both coordinate
permutations are identities or both are 3-cycles. For a coordinate
exchange `(x,y) -> (sigma(y),tau(x))`, setting `x=sigma(y)` forces
`tau=sigma^{-1}`.

Common relabeling of all three bases preserves the identity root
matchings. Coordinate reversals conjugate the four translations to

\[
p(x,y)=(x+1,y+1).
\]

Relabeling the first coordinate by `sigma^{-1}` conjugates every
exchange map to the reflection

\[
p(x,y)=(y,x).
\]

The checker enumerates all 72 automorphisms, retains the eleven, and
saves an explicit conjugating permutation for each. Its class sizes
are `1,6,4`.

## Outside neighborhoods and the exact census

Let `B` be the adjacency matrix on the 27 core vertices. Each core
vertex has degree six in the core and requires eight neighbors among
the 72 exterior vertices. Every exterior vertex has a three-point
signature: one neighbor in each base.

The full adjacency identity is

\[
A^2+A=12I+2J.
\]

If `X` is the incidence matrix from the core to the exterior, then

\[
XX^{\mathsf T}=G:=12I+2J-B^2-B.
\]

For a signature indicator `h`, two necessary conditions are

\[
G_{ij}>0\quad(i\ne j,\ h_i=h_j=1),
\qquad (B+I)h\le2\mathbf1.
\]

The first preserves the common-neighbor quota of a core pair. The
second bounds the common neighbors of a core vertex and the exterior
vertex that already lie in the core. It ignores all remaining
contributions, so it is a necessary condition.

No signature can occur twice: its two exterior vertices would then
share three common neighbors, exceeding the maximum of two.

Enumeration of all `9^3=729` signatures gives:

| Interface | Positive pair quotas | Also satisfies mixed caps | Occurrences at a core vertex |
| --- | ---: | ---: | --- |
| Identity | 36 | 36 | 4 at every vertex |
| Reflection | 102 | 84 | 6 at nine vertices, 11 at eighteen |
| Translation | 135 | 108 | 12 at every vertex |

The saved artifact contains the complete adjacency matrices, Gram
matrices, signature lists, occurrence counts, and map conjugators.

## Identity: 36 possible signatures for 72 vertices

For the identity map, two selected points in different bases have
positive residual quota precisely when both their row and column
coordinates differ. Hence, for a signature with one point in each
base, its three row coordinates and its three column coordinates must
each be permutations of `0,1,2`. There are `(3!)^2=36` signatures.

None can repeat, but 72 exterior vertices are required. Equivalently,
each core vertex occurs in four candidate signatures and needs eight
exterior neighbors. Either count is a contradiction.

## Reflection: a fixed point has only six possible neighbors

Take the representative `p(x,y)=(y,x)` and the root vertex `0=(0,0)`.
Consider any exterior signature containing this vertex. Its labels
`a,b` in the other two grids must both belong to

\[
D=\{(1,1),(1,2),(2,1),(2,2)\}.
\]

A selected point equal to zero has exhausted its quota through the
matching triangle. A point in the same rook row or column as zero
already has two common neighbors in the endpoint grids.

For the pair consisting of `a` in grid one and `b` in grid two, the
residual quota is

\[
2-2\,[p(a)\sim b]-[a=b]-[b=p(a)].
\]

Here `~` denotes rook adjacency within the nine-point coordinate set.
Within the two-by-two rectangle `D`, a positive quota permits exactly
the following six ordered pairs, in numerical point labels:

\[
(4,8),\ (8,4),\ (5,7),\ (7,5),\ (5,5),\ (7,7).
\]

This is the complete list. For `b=p(a)`, only the two nonfixed points
of `D` are allowed. Otherwise `b` must be the corner opposite `p(a)`
in `D`, giving four more pairs. All six pass the mixed caps, although
that fact is unnecessary for the upper bound.

The root vertex therefore has at most six exterior neighbors. It
needs eight. This excludes the reflection class without a spectral
test or a full-core completion search.

## Translation: the incidence equations imply zero equals 54

For the representative `p(x,y)=(x+1,y+1)`, the 108 admissible
signatures have inconsistent exact incidence equations. The separate
[translation proof](three_red_translation_incidence.md) supplies both
a short integer equality certificate and a forcing count.

The four classes of positive off-diagonal core-pair equations are
indexed by `(residual quota, number of available signatures)`:

| Equation class | Number of equations | Sum of right sides |
| --- | ---: | ---: |
| `(1,1)` | 27 | 27 |
| `(1,4)` | 27 | 27 |
| `(2,2)` | 54 | 108 |
| `(2,3)` | 27 | 54 |

After summing equations within each class, every signature has one
of the three coefficient vectors

\[
(1,0,0,2),\qquad(0,1,2,0),\qquad(0,2,0,1).
\]

Their multiplicities are `27,54,27`. Each vector is orthogonal to
`(-8,-2,1,4)`, while the same weighted sum of right sides equals

\[
-8(27)-2(27)+108+4(54)=54.
\]

Thus the incidence equations imply `0=54`. This certificate does not
require integrality, nonnegativity, or the no-repeat property.

An independent counting certificate uses that property: equations
of types `(1,1)` and `(2,2)` force 81 distinct signatures. There are
only 72 exterior vertices. Each core vertex lies in nine of those
forced signatures but has room for only eight exterior neighbors.

The checker accompanying this note independently builds the core
with dense integer matrices. It reconstructs all 108 signatures, all
four equation classes, both certificates, and the complete Gram
matrix. These agree with the separate translation checker's bit-mask
construction and saved artifact.

The three cases exhaust the eleven possible interfaces. Therefore
three disjoint rook grids with pairwise rook-isomorphic matchings
cannot occur.

## An all-red grid has no disjoint rook-isomorphic partner

Call a triangle red if it lies in six rook grids, and call a grid
all-red if each of its six lines is red. The
[preliminary grid facts](red_grid_limit.md) prove that distinct all-red
grids are disjoint and their matching is a rook isomorphism. They also
prove that every induced square containing a red edge lies in a grid.
The six grids through its red triangle account for all twelve squares
through the edge, two per grid.

Suppose `R_1` is all-red and `R_2` is any disjoint induced rook grid
whose matching to `R_1` is a rook isomorphism. Write `q(p)` for the
matching partner in `R_2` of `p` in `R_1`. Let `z(p)` be the unique
common neighbor of this adjacent pair. It lies outside both grids:
`q(p)` has no other neighbor in `R_1`, and `p` has no other neighbor
in `R_2`. The nine vertices `z(p)` are distinct, because any vertex
outside `R_1` has only one neighbor in `R_1`.

Take any line `T` of `R_1` and two distinct points `p,p'` on it. Since
the matching is a rook isomorphism, `q(p),q(p')` are adjacent. The four
vertices `p,p',q(p'),q(p)` form an induced square: the only edges
between the two bases are the matching edges. Its edge `pp'` is red,
so the square lies in an induced grid `K`.

Every edge has a unique triangle. Therefore `K` contains the whole
line `T` through `pp'` and the whole line `T'=q(T)` through
`q(p)q(p')`. These two disjoint lines are parallel in `K`. This step
uses no red-triangle assumption about `R_2`.

Let `U` be the third line of `K` parallel to `T`. Each matching edge
`p q(p)` lies in a triangle whose third point belongs to `U`.
Uniqueness of the triangle on that edge identifies the third point
as `z(p)`. Therefore

\[
U=\{z(p):p\in T\}.
\]

Applying this to the six lines of `R_1` shows that the nine vertices
`Z={z(p)}` contain a rook graph, with `p -> z(p)` preserving all six
lines. This rook graph is induced. An additional edge would join two
rook-nonadjacent vertices that already have two common neighbors
inside `Z`, contradicting the requirement that an adjacent pair has
exactly one common neighbor.

The interfaces from `R_1` and `R_2` to `Z` are precisely the matchings
`p -> z(p)` and `q(p) -> z(p)`, because every vertex outside either
base has exactly one neighbor in it. Both matchings preserve the
rook lines. Thus `R_1,R_2,Z` are three disjoint rook grids with
pairwise rook-isomorphic interfaces, already excluded above.

Thus an all-red grid cannot have a disjoint grid whose matching to it
is a rook isomorphism. In particular, there is at most one all-red
grid, because two all-red grids would have exactly such a matching.
No all-red property of `R_2` or the new grid `Z` was required in the
closure argument.

## Replay and scope

```sh
python experiments/workspace/three_red_boundary.py \
  --verify experiments/logs/grids-and-triangles/three-red-boundary.json \
  --translation-certificate experiments/logs/grids-and-triangles/three-red-translation-incidence.json
```

The enumeration completes in under one second in the project
environment. It uses no SAT solver, numerical eigenvalue comparison,
or floating-point feasibility decision. The translation equality
certificate is independently reconstructed, not imported from the
separate proof source.

The result is an obstruction to specific induced subgraphs. It does
not assert that such a configuration must exist in every hypothetical
graph, and does not settle existence of the strongly regular graph.
