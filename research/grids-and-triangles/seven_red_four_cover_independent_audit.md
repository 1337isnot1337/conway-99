# Independent audit of the seven-base four-cover reduction

This audit checks the reduction for seven all-red bases when all thirty-six
remaining vertices lie in exactly two internal triangles. It also checks
the surviving four-cover graphs and their projection-coloring certificates.
The full 331,776-cover C++ enumeration was reviewed, not independently
rerun in this audit.

## The common triangle graph

For each all-red base, the inverse image of each rook line has twelve
vertices. The unique-grid partition through that red line splits them
into four internal triangles, each mapped bijectively onto the line.
Every remaining vertex belongs to the selected triangle over its row
and the selected triangle over its column.

When each remaining vertex lies in exactly two internal triangles,
these are its entire triangle set. Thus the selected twenty-four
triangles are common to all seven bases. Use them as vertices of `K`,
and use each remaining vertex as the edge joining its two triangles.
Two distinct triangles cannot share two vertices, since the shared
edge would have two common neighbors. Hence `K` is simple and cubic,
with twenty-four vertices and thirty-six edges.

For each base, triangle vertices map to its six rook lines. The three
edges incident to a triangle map bijectively to the three points of
that line. The opposite triangle through each point maps to its
opposite-orientation line. This is a four-sheeted covering of `K3,3`.

## Completeness of the normalized cover census

Every covering can be described by one permutation of four sheets on
each of the nine base edges. The five edges in the first row or first
column form a spanning tree. Relabeling sheets at its six vertices
normalizes these five permutations to the identity. The other four
permutations are free, giving `24^4=331,776` assignments.

The loops in `seven_red_four_cover_scout.cpp` exhaust exactly this
Cartesian product. They build both directions of every edge and
check degree three. The masks have at most twelve bits and the loop
counts fit the integer types used. The subset cache is initialized
for one sheet count per executable invocation; this matches both the
three-sheet control run and the four-sheet run.

For a connected cover the bipartition is unique up to exchange. A
possible vertex fiber on one side is a four-set whose neighborhoods
are disjoint and cover the twelve opposite vertices. The code tests
this by a union of size twelve; four degree-three neighborhoods make
that condition equivalent to disjointness. It enumerates every
partition into three such fibers exactly once.

Any valid left partition and valid right partition combine into a
covering: the edges between a left fiber and a right fiber form a
perfect matching of size four. Distinct pairs of fibers give distinct
edge fibers, because their endpoint sets recover the pair. Therefore
the product of the two recorded fiber-occurrence counts at an edge
is exactly the number of possible four-edge fibers containing it.

Seven base projections need seven different fibers at each edge.
Repeating a four-edge fiber would give two vertices in different
bases four common neighbors. Thus the minimum occurrence product
below seven is a valid exclusion. The recorded histogram discards
323,274 of the 326,010 connected assignments and leaves 2,736.

## Independent replay of all survivors and colorings

`seven_red_four_cover_independent_audit.py` imports none of the original
projection-building helpers. It reconstructs every surviving normalized
cover and obtains an explicit graph isomorphism to one of the three
saved representatives. It checks bijectivity and exact equality of
the mapped edge sets. All 2,736 mappings passed, with class sizes
864, 1,728, and 144.

For each representative, a separate anchored recursion enumerates
partitions of a side into four-sets. It finds eight valid partitions
on each side and therefore sixty-four projections. It then rebuilds
every four-edge fiber and all pairwise fiber intersections.

Two projections can coexist only if each fiber of one meets every
fiber of the other in at most two edges. Any larger intersection
would give two base vertices at least three common neighbors. Thus
seven bases would require a seven-clique in this compatibility graph.
Identical projections cannot be repeated, since their corresponding
fibers meet in four edges.

The saved proper colorings were checked directly against every
compatibility edge:

| Assignments | Projections | Compatibility edges | Verified colors |
| ---: | ---: | ---: | ---: |
| 864 | 64 | 288 | 2 |
| 1,728 | 64 | 544 | 4 |
| 144 | 64 | 480 | 4 |

A proper coloring with at most four colors excludes a seven-clique.
This verifies the connected-cover exclusion without using any of
the optional residual-edge pruning in the earlier projection search.

## Disconnected covers

Each connected component of a covering also covers the connected
base. Its order is therefore six times its sheet count. The possible
disconnected component-size partitions are `6+18`, `12+12`,
`6+6+12`, and `6+6+6+6`.

In the `6+18` case, restrict the seven projections to the connected
three-cover component. Its earlier exact fiber bound is at most four
at some edge. Repeating one of these three-edge fibers already gives
three common neighbors between two base vertices, regardless of
their fibers in the six-vertex component. Hence seven projections
are impossible.

Either partition containing a twelve-vertex component fails the
earlier connected-double-cover common-edge-pair lemma. The same
two edges are paired by every restricted projection. Their two
corresponding vertices in the remainder would have a common
neighbor in all seven bases.

The final case is four copies of `K3,3`. Their line graphs are four
rook graphs. These rook graphs are induced: adding an edge between
one of their nonadjacent pairs would give an adjacent pair two
already-present common neighbors. Their interfaces with each red
base are rook isomorphisms, since each restricted covering is an
isomorphism of `K3,3`.

## Independent algebra check of the final four-rook contradiction

The hypotheses above are exactly those used in
[`seven_red_four_rook_exclusion.md`](seven_red_four_rook_exclusion.md).
Its negative-rook lift has

\[
12r-s_1-s_2=112,\qquad 7p=56-3r+s_1.
\]

Counting cross-base triangles gives `t_R=39`. The negative-rook
character gives

\[
\operatorname{tr}(H^3)=-224-1008+210+2(39)=-944.
\]

The invariant block equations give
`tr(H³)=-840+12s1-s2-s3`, so

\[
g:=s_3+s_2-12s_1=104.
\]

The sign here is positive. Compression into the sixteen-dimensional
sum of the four remaining rook negative spaces has trace `-32`.
The complementary compression has eigenvalues at least `-4`, giving
`s1≤32-4r`. Consequently `7(p+r)≤88` and the integer `p+r` is at most
twelve. No invariance of the complementary compression is needed.

Finally,

\[
0\le\sum_\mu(\mu+4)(\mu+1)^2
=112(p+r)-1352\le-8.
\]

The lower bound follows from `μ≥-4`. This independently checks the
algebra and completes the last disconnected case, conditional on
the covering reduction and the earlier two-/three-cover lemmas.

## Replay

```bash
.venv/bin/python experiments/workspace/seven_red_four_cover_independent_audit.py \
  --output /tmp/seven-red-four-cover-independent-audit.json
```

The archived output is
`experiments/logs/grids-and-triangles/seven-red-four-cover-independent-audit.json`.
The replay checks the survivor quotient and coloring certificates;
the complete normalized-cover enumeration remains the separate C++
census described above.
