# Excluding the common triangle system with seven all-red grids

Suppose seven all-red grids exist. Let U be their 36-vertex complement.
The case where every vertex of U lies in exactly two U triangles is
impossible. Together with the [earlier remainder reduction](seven_red_residual_reduction.md),
this leaves 18 or 27 vertices in exactly two U triangles.

The proof below reduces a common triangle system to four rook grids.
The [negative rook-space argument](seven_red_four_rook_exclusion.md)
then gives a contradiction. This excludes one case of seven all-red
grids. It does not decide the full existence problem.

## A four-sheeted cover of K3,3

Every projection from U to an all-red base selects two U triangles
through each vertex. Under the present hypothesis these are all the
triangles, so every base selects the same system of 24 triangles.

Construct a graph K whose vertices are those triangles and whose edges
are the 36 points of U. Each point joins its two triangles. The graph is
simple: two triangles cannot share an edge of U. It is cubic because
each triangle has three points. The triangle edges of U form L(K).
The other edges of U form a cubic graph F on the same 36 points.

For any base grid, the twelve points over each of its six lines split
into four triangles. A triangle over a row has one point over each of
the three columns, and conversely. Thus each base gives a four-sheeted
cover K to K3,3. Its nine edge fibers are the four-point fibers of the
projection U to that base.

Two such edge fibers from different bases intersect in at most two
points: their base vertices have at most two common neighbors in the
full graph. In particular seven bases require seven distinct possible
edge fibers through every fixed edge of K.

## Exhausting connected four-covers

Label the four sheets over each of the six vertices of K3,3. A covering
is specified by a permutation on each of the nine base edges. Changing
sheet labels sets the five permutations on a spanning tree to identity.
The other four permutations are arbitrary elements of S4. Consequently
the 24^4 = 331,776 normalized assignments exhaust every cover.

The exact C++ census in
[`seven_red_four_cover_scout.cpp`](../../experiments/workspace/seven_red_four_cover_scout.cpp)
has the following component counts. A component of size 6d is a connected
d-sheeted cover.

| Component sizes | Normalized assignments |
|---|---:|
| 24 | 326,010 |
| 6 and 18 | 5,000 |
| 12 and 12 | 675 |
| 6, 6, and 12 | 90 |
| 6, 6, 6, and 6 | 1 |

For a connected K its bipartition has twelve vertices on each side.
A possible vertex fiber is a four-set whose neighborhoods are disjoint
and cover the opposite side. A possible side partition consists of
three such four-sets. Any left and right side partitions combine into
a covering: every vertex has exactly one neighbor in each opposite
fiber.

Let a(u) count the distinct fibers containing a vertex u that occur in
at least one side partition. For an edge uv, the possible edge fibers
through it are determined by a choice of left fiber at u and right
fiber at v. Hence their number is at most a(u)a(v). The census excludes
a connected cover whenever the minimum of this product is less than
seven.

| Minimum product | Connected assignments |
|---:|---:|
| 1 | 253,902 |
| 2 | 42,048 |
| 3 | 1,008 |
| 4 | 22,860 |
| 6 | 3,456 |
| 8 | 864 |
| 9 | 1,728 |
| 16 | 144 |

The last three rows contain 2,736 assignments and exactly three
underlying graphs. Each graph has eight side partitions on each side,
so it has 64 possible projections, disregarding base coordinate labels.

Make a compatibility graph on these 64 projections. Join two projections
when every edge fiber of one meets every edge fiber of the other in at
most two points. Seven actual bases would give a clique of size seven.
Saved proper colorings of the three compatibility graphs use two, four,
and four colors. No such clique exists.

These are short certificates: the verifier reconstructs all projections
and checks that every compatibility edge has differently colored
endpoints. It does not use an optimizer or assume a computed clique
maximum. The colorings are in
[`seven-red-four-cover-colorings.json`](../../experiments/workspace/seven-red-four-cover-colorings.json).

The independent audit uses an anchored partition recursion and explicit
edge-preserving isomorphisms for all 2,736 assignments. It reproduces
the compatibility graphs, with 288, 544, and 480 edges, and checks the
colorings. Thus every connected four-cover is excluded.

## Disconnected covers

Every component maps onto K3,3. Its number of sheets is independent of
which base gives the projection.

If a three-sheeted component occurs, the connected three-cover census
from the [eight-grid proof](eight_red_exclusion.md) gives an edge with
at most four possible three-edge fibers. Seven projections repeat a
fiber. The corresponding two base vertices then share at least three
U neighbors, which is impossible. This excludes the component sizes
6 and 18.

If a two-sheeted component occurs, the
[complementary-neighborhood argument](nine_red_cover_audit.md)
gives two edges of that component paired in every possible covering.
The corresponding two U vertices would have a common neighbor in all
seven bases, which is impossible. This excludes the component sizes
12 and 12, and 6, 6, and 12. Flipping the bipartition of a component
does not change its edge fibers or either obstruction.

Only four one-sheeted components remain. Each is K3,3, so L(K) consists
of four induced rook grids. No extra edge can lie inside one of these
grids: its endpoints already have their full common-neighbor quota.
Every base projection restricted to a component is an isomorphism onto
K3,3. The resulting interface from each base to each U rook grid is
therefore a rook isomorphism.

These are precisely the hypotheses of the
[four-rook exclusion](seven_red_four_rook_exclusion.md). Its negative
rook-space compression bounds an integer p+r by twelve. An exact cubic
trace identity then gives

    trace((C_Z+4I)(C_Z+I)^2) = 112(p+r)-1352 <= -8,

while every eigenvalue of C_Z is at least minus four, making this trace
nonnegative. This final contradiction excludes the common triangle
system.

## Replay and scope

```sh
make verify-seven-red-residual
```

This target includes the earlier nine-vertex spectral census, regenerates
the four-cover archive, checks the three coloring certificates in two
implementations, and replays the four-rook polynomial calculation. The
three-sheeted run of the new C++ generator also reproduces all 1,296
earlier covers and their connected fiber-bound histogram as a control.

The archived four-cover census is
[`seven-red-four-cover-scout.json`](../../experiments/logs/grids-and-triangles/seven-red-four-cover-scout.json).
The independent replay is
[`seven-red-four-cover-independent-audit.json`](../../experiments/logs/grids-and-triangles/seven-red-four-cover-independent-audit.json).
The separate exploratory projection search also imposed residual-edge
conditions, but none of those extra conditions enters this proof.
