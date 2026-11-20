# The eleven-vertex zero class of a norm-16 vector

This note continues [the norm-16 defect-cycle reduction](coupled_shells.md).
All statements assume a hypothetical strongly regular graph with parameters
`(99,14,1,2)` and an integral eigenvector of eigenvalue `-4` and squared norm
sixteen. The preceding reduction gives a partition

\[
V=P\sqcup N\sqcup H\sqcup L\sqcup Z,
\qquad (|P|,|N|,|H|,|L|,|Z|)=(8,8,8,64,11).
\]

The graph on `H` has at most one edge. Put `e=e(H)`, so `e` is zero or one.
The graph on `Z` has `5+e` edges. The result here restricts its component
types to eleven possibilities. It does not exclude norm-16 vectors, and it
does not settle the existence of the strongly regular graph.

## Pair counts and a local weighted bound

For `z` in `Z`, let `S_z=N(z)∩H` and let `d(z)` be its degree within `Z`.
The forced degree equations give

\[
|S_z|=d(z)+2,
\qquad |N(h)\cap Z|=4+d_H(h) \quad(h\in H).
\]

Two adjacent zero vertices have at most one common high neighbor. Two
zero vertices with a common zero neighbor also have at most one common
high neighbor. These bounds follow from the respective common-neighbor
limits one and two.

Write

\[
W=\sum_{z\in Z}\binom{d(z)}2,
\qquad T=\sum_{l\in L}\binom{d_H(l)}2.
\]

The twenty-eight high pairs have total common-neighbor budget `56-e`.
The sixteen core vertices contribute sixteen to this sum. No high vertex
is a common neighbor of two high vertices, since `e≤1`. The zero vertices
contribute

\[
\sum_z\binom{d(z)+2}2
=W+2\sum_zd(z)+11
=W+31+4e.
\]

It follows that

\[
\boxed{T=9-5e-W.}
\]

In particular `W≤9` when `e=0`, and `W≤4` when `e=1`.

There is also a bound for each individual high vertex:

\[
\boxed{\sum_{z\in N(h)\cap Z}d(z)\le6-2d_H(h).}
\]

To prove it, sum the common-neighbor counts for the seven pairs `{h,k}`
with `k∈H\{h}`. The total is `14-d_H(h)`. The core contributes four.
The zero class contributes

\[
\sum_{z\in N(h)\cap Z}(|S_z|-1)
=\sum_{z\in N(h)\cap Z}d(z)+4+d_H(h).
\]

The remaining contribution from `L` is nonnegative. In fact the slack
in the boxed inequality is exactly
`Σ_{l∈N(h)∩L}(d_H(l)-1)`.

## The only possible connected components

**The graph on `Z` is a forest, and each component is `K1`, `K2`, `P3`,
`K1,3`, or `P4`.**

First, a triangle is impossible. Each of its vertices has at least four
high neighbors. An adjacent pair in the triangle already has its unique
common neighbor inside `Z`, so its high-neighbor sets are disjoint. Three
disjoint subsets of an eight-set cannot each have size at least four.

Next, suppose `u,v,w` form a path and each has degree at least two in
`Z`. Their high-neighbor sets each have size at least four. Every pair of
these sets has intersection at most one: the adjacent pairs use the
adjacent-vertex bound, and the endpoints already have the common zero
neighbor `v`. Inclusion-exclusion gives

\[
|S_u\cup S_v\cup S_w|\ge 12-3=9,
\]

again impossible. Thus three nonleaves cannot form a path. A cycle would
contain such a path, so the zero-class graph is a forest. Its nonleaf
vertices have components of order at most two. Every component is
therefore a star or a double-star.

For any edge `uv`,

\[
8\ge|S_u\cup S_v|\ge(d(u)+2)+(d(v)+2)-1,
\]

so `d(u)+d(v)≤5`. This leaves stars of maximum degree four, and
double-stars with central degree pairs `(2,2)` or `(3,2)`.

A four-leaf star is impossible. Its center has six high neighbors.
Each leaf has three high neighbors and meets the center's high set in
at most one, so every leaf contains the same two high vertices outside
the center's set. Two leaves then have at least two common high
neighbors in addition to their common zero neighbor.

A double-star with central degrees three and two is also impossible.
The two central high sets have sizes five and four and intersect in at
most one. They therefore cover all eight high vertices. A leaf attached
to either center meets each central set in at most one: one bound is
from adjacency, the other from the two-step path. A set of three high
neighbors cannot satisfy these two bounds while their union is all of
`H`.

This proves the component claim.

## Two rigid component configurations

The following descriptions will be useful when adding low-class edges.

For a `K1,3` component, let `C` be the center's five-element high set and
let `Y=H\C`, of size three. Each leaf has exactly two neighbors in `Y`
and one in `C`. The three leaves use the three different pairs from
`Y`, and their three neighbors in `C` are distinct. Indeed, a leaf must
use at least two points of `Y`. Using all three would intersect another
leaf in at least two points. Repeating a pair from `Y`, or sharing a
point of `C`, would give two leaves too many common high neighbors.

For a `P4` component, let `U,V` be the high sets of its two middle
vertices. Both have size four. Each end vertex must meet each of `U,V`
in at most one high vertex. If `U,V` were disjoint, they would cover
`H` and leave no room for the third high neighbor of an end vertex.
Thus `|U∩V|=1`. There is one high vertex outside `U∪V`. Each end
contains this outside vertex, one point of `U\V`, and one point of
`V\U`, and contains no point of `U∩V`.

## Eliminating four forest types when the high class has one edge

Let `x,y` be the endpoints of the unique high edge. Each has five
neighbors in `Z`, whose zero-class degrees sum to at most four. Hence
each endpoint must have at least one isolated zero neighbor.

The component count and `W≤4` initially leave eight forests when
`e=1`. Four are impossible:

1. `4K2 + P3` has no isolated vertex, contrary to the preceding bound.
2. `3K2 + P4 + K1` has one isolate. Each endpoint must use that isolate
   and four degree-one vertices, so both avoid the two middle vertices
   of `P4`. Their high sets cover seven of the eight high vertices.
   At most one high vertex avoids both, a contradiction.
3. `3K2 + K1,3 + K1` also has one isolate. Both endpoints must use it
   and avoid the star center. The rigid star description puts any two
   high vertices outside the center together on one star leaf. Thus
   `x,y` have both the isolate and this leaf as common neighbors,
   contradicting their adjacency.
4. `K2 + P3 + K1,3 + 2K1` has two isolates. An endpoint cannot use the
   degree-three star center: even with both isolates, its remaining
   two neighbors would give weighted degree at least five. Both
   endpoints are outside the center's high set, so they share a star
   leaf. They cannot also share an isolate. Each must therefore use
   exactly one isolate, followed by four degree-one vertices, and
   both avoid the middle vertex of `P3`. The star-center high set of
   size five and the path-middle high set of size four both lie in
   `H\{x,y}`, which has size six. Their intersection has size at least
   three. The corresponding zero vertices are in different components
   and can have at most two common neighbors, a contradiction.

## The eleven remaining component patterns

Let `a,b,c,d` count components `K2,P3,K1,3,P4`, respectively. Isolates
fill the remaining vertices. The elementary equations are

\[
a+2b+3c+3d=5+e,\quad
2a+3b+4c+4d\le11,\quad
b+3c+2d\le9-5e.
\]

They give seven cases for `e=0` and eight for `e=1`. After the four
exclusions above, the following eleven remain. `T` is the exact total
number of repeated high pairs among low neighborhoods, not an upper
bound.

| `e(H)` | Graph on `Z` | `W` | `T` |
| ---: | --- | ---: | ---: |
| 0 | `5K2 + K1` | 0 | 9 |
| 0 | `3K2 + P3 + 2K1` | 1 | 8 |
| 0 | `K2 + 2P3 + 3K1` | 2 | 7 |
| 0 | `2K2 + P4 + 3K1` | 2 | 7 |
| 0 | `2K2 + K1,3 + 3K1` | 3 | 6 |
| 0 | `P3 + P4 + 4K1` | 3 | 6 |
| 0 | `P3 + K1,3 + 4K1` | 4 | 5 |
| 1 | `2K2 + 2P3 + K1` | 2 | 2 |
| 1 | `3P3 + 2K1` | 3 | 1 |
| 1 | `K2 + P3 + P4 + 2K1` | 3 | 1 |
| 1 | `2P4 + 3K1` | 4 | 0 |

The final case has a useful extra consequence: every low vertex has
at most one high neighbor. In the two rows with `T=1`, exactly one
low vertex has two high neighbors and every other low vertex has at
most one. In the row with `T=2`, exactly two low vertices have two
high neighbors and every other low vertex has at most one. These
follow because `binom(3,2)=3` already exceeds the available budget.

## The unique high edge lies in a forced triangle

If `e=1` and `xy` is the high edge, its unique common neighbor is an
isolated vertex `z0` of `Z`. Consequently

\[
N(z_0)\cap H=\{x,y\},
\qquad N(x)\cap(P\cup N)\cap N(y)=\varnothing.
\]

Both endpoints need an isolated zero neighbor. Suppose that their
choices of isolates are disjoint. The first of the four remaining
forests has only one isolate, so it is immediately excluded. In the
two forests with two isolates, each endpoint must then use exactly
one isolate. Its four other zero neighbors must all be leaves, by
the weighted degree bound. There are only six leaves, so the two
endpoints share at least two of them.

In the `2P4+3K1` case, disjoint nonempty isolate sets force at least
one endpoint to use exactly one isolate. That endpoint uses all four
leaves. The other endpoint has at most two isolates and hence at
least three nonisolated zero neighbors. Their total degree is at
most four, so at least two are leaves. The endpoints again have at
least two common neighbors, contrary to adjacency.

Thus the endpoints share an isolate. That isolate is their unique
common neighbor and has exactly two high neighbors, proving the
claim. In particular a proposed high edge between signatures of
overlap one can be rejected before any low-incidence search.

The twelve low neighbors of `z0` induce six disjoint edges, and none
is adjacent to `x` or `y`. Indeed, the fourteen neighbors of any
vertex in this strongly regular graph induce seven disjoint edges.
The edge `xy` accounts for one of these seven edges at `z0`.

## Exact witnesses and the limit of this reduction

Every one of the eleven listed types satisfies the necessary degree
and pair-capacity conditions on `H∪Z`, with a core-overlap matrix from
an actual enumerated norm-16 incidence template. Explicit integer
witnesses are saved in
`experiments/logs/eigenlattices/coupled-zero-witnesses.json`.

Nine types already occur among the 447 saved high/low partial witnesses.
A read-only audit checks all 447; it does not rerun the earlier SAT
census. The other two types have new H/Z witnesses:

- `P3 + K1,3 + 4K1`, with no high edge, uses the overlap matrix of
  support core 1, incidence class 2.
- `2P4 + 3K1`, with one high edge, uses the overlap matrix of support
  core 3, incidence class 29. The high edge has endpoints 2 and 4
  in the saved labeling.

For these last two witnesses, only the high/core overlap matrix is
fixed. They do not claim a compatible choice of high/low edges.
Consequently the table is exact at the stated H/Z degree and pair-
capacity level, while further constraints involving low signatures
may remove types or individual incidence templates.

`coupled_zero_structure.py` constructs the fifteen initial forests and
the necessary SAT models. `coupled_zero_overlap.py` supplies actual
overlap matrices from the existing incidence catalog. Neither changes
the frozen norm-16 certificate builders.

The replay below invokes no SAT solver. It verifies the eleven saved
adjacency witnesses, checks their overlap matrices against the archived
incidence catalog, and audits all 447 earlier partial witnesses:

```bash
.venv/bin/python experiments/workspace/coupled_zero_replay.py
```

The four excluded forest types have the direct proofs given above;
their exclusion does not depend on solver output.
