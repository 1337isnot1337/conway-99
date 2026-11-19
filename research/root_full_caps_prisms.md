# Triangular prisms and the near-anchor count

The maximum-anchor count has an exact combinatorial interpretation: it
counts triangular prisms through the chosen root, classified by the
prism edge that matches the root to its opposite triangle. The identities
below apply to any strongly regular graph with parameters
`(1+k^2/2,k,1,2)`. They introduce no new constraint into the completed
rooted searches.

## The local bijection

Fix a root `r`, a near anchor `a`, and a different near mate pair
`{b,b'}`. Write `x=x_{a,b}` and `y=x_{a,b'}` for the unique exterior
vertices with those signatures. A positive term in the anchor count is
the edge `xy`.

The six vertices

\[
\{r,b,b',a,x,y\}
\]

then induce a triangular prism. Its triangles are `{r,b,b'}` and
`{a,x,y}`, and its three matching edges are `ra`, `bx`, and `b'y`.
All other cross edges are absent: exterior points have exactly their two
specified near neighbors, and the near neighborhood is a matching.

Conversely, consider an induced triangular prism containing `r`. Its
triangle through `r` is `{r,b,b'}` for one near mate pair. Its unique
matching neighbor of `r` is a near vertex `a` outside that pair. The other
two vertices have signatures `{a,b}` and `{a,b'}` and are adjacent.
They therefore give exactly one term in the count `c_{r,a}`.

This is a bijection. The count `c_{r,a}` measures prisms in which `ra` is
one of the three edges between the prism's two triangles. It does not
count every prism in which `ra` is a triangle edge.

In particular,

\[
c_{r,a}=c_{a,r},\qquad
\sum_{a\sim r}c_{r,a}=\#\{\text{triangular prisms containing }r\}.
\]

The first equality reverses the orientation of the same matching edge.
The second counts every prism at `r` once.

## Global multiplicities and the two root choices

Let `P` be the number of induced triangular prisms. Every prism has six
vertices, three matching edges, and two triangles. Hence

\[
\sum_r\sum_{a\sim r}c_{r,a}=6P,
\qquad
\sum_{\{r,a\}\in E}c_{r,a}=3P.
\]

Summing, over all triangles, the number of prisms containing that triangle
gives `2P`. Since every anchor count has at most `(k-2)/2` terms,

\[
P\leq \frac{nk(k-2)}{12}.
\]

For `(99,14,1,2)`, this gives the existing upper bound `P <= 1386` from
`eigenlattices/positive_lattice.md`.

The completed maximum-anchor batch first fixed a root and then maximized
`c_{r,a}` over its fourteen near anchors. Its maximum-zero cases say that
the **chosen root** belongs to no triangular prism. They do not imply
`P=0` elsewhere in the graph.

There is a further possible normalization: choose the ordered adjacent
pair `(r,a)` to maximize `c_{r,a}` over the entire graph, then normalize
its matching. Under that additional global root choice, maximum zero is
equivalent to `P=0`. Every graph has such a maximizing pair, so the eleven
new global-choice cases would still cover the unrooted existence problem.
This is a different coverage convention from both earlier conventions.
No formula implementing that global choice was built or solved here.

A prism-free graph is grid-free because a rook grid contains triangular
prisms. The converse has not been assumed.

## Exact positive controls

`root_full_caps_prism_counts.py` constructs the nine-point rook graph
directly and uses the existing 243-point Golay construction in
`triangle_ball.py`. It first checks every SRG pair equation using integer
adjacency bitsets.

One enumeration lists pairs of disjoint triangles and accepts exactly
those with a perfect-matching interface. Each accepted six-vertex set is
checked to induce a cubic prism and to occur only once. A second,
independent enumeration uses the rooted signature formula for every
ordered adjacent root/anchor pair. It checks the individual edge counts,
their symmetry under reversal, and the sixfold and twofold totals.

| Control | Triangles | Prisms `P` | Anchor count on every oriented edge | Prisms through each vertex | Prisms through each triangle |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nine-point rook graph | 6 | 6 | 1 | 4 | 2 |
| 243-point Golay graph | 891 | 8,910 | 10 | 220 | 20 |

The rooted enumeration checks all 36 oriented edges in the rook control
and all 5,346 in the Golay control. Its positive terms total 36 and
53,460, respectively, exactly six times the independent prism counts.
Both controls attain the general upper bound above.

The certificate binds the graph-construction source and hashes the full
adjacency, prism catalogue, and list of oriented counts. Generation and
replay each take less than a second in this workspace. No solver runs.

## What the archived relaxations say

The old nonnegative extension-count systems already permit zero prisms.
The first ordinary core coordinate is the six-point triangular prism.
`root_full_caps_prism_archive.py` identifies that graph directly in the
existing order-nine cache and verifies that its ordinary and induced
coordinates coincide.

- The archived order-eight witness has all nine core coordinates zero.
  Its 1,224 cached induced count forms are nonnegative integers and have
  the required subset totals. Its prism count is zero.
- The archived order-nine witness also has prism count zero. Its 6,535
  cached induced count forms are nonnegative integers, and its ordinary
  counts satisfy automorphism divisibility and all subset totals.
  `core9.log` records the earlier check of all 23,189 original extension
  equations. The present inspection rechecks the cached reduction; it
  does not regenerate that catalogue.
- `nine-max-integrality.log` explicitly records `prism: 0` in the integral
  witness for the order-20 maximal single-coordinate theta relaxation.
  `eigenlattices/nine_cosets.md` documents the earlier replay of its
  rational inequalities and integrality lattice. This inspection reads
  that archived witness; it does not reconstruct or rerun the theta
  system.

These statements concern their separate finite relaxations. They do not
assert feasibility of every combination of their constraints.

The newer exact grid-free point that passes 1,416 cached count/moment and
projector blocks has prism count 326. A feasible positive value is not a
positive lower bound. This inspection does not settle whether that
stronger finite system permits `P=0`. No optimization was run to answer
that further question.

## Files and replay

Sources:

- `experiments/workspace/root_full_caps_prism_counts.py`
- `experiments/workspace/root_full_caps_prism_archive.py`

Artifacts under `experiments/logs/root-full-caps-anchor-max/`:

- `prism-multiplicity-controls.json`
- `prism-multiplicity-controls.log`
- `prism-multiplicity-controls-replay.log`
- `prism-archive-inspection.json`
- `prism-archive-inspection.log`
- `prism-archive-inspection-replay.log`

```sh
.venv/bin/python experiments/workspace/root_full_caps_prism_counts.py \
  --certificate experiments/logs/root-full-caps-anchor-max/prism-multiplicity-controls.json
.venv/bin/python experiments/workspace/root_full_caps_prism_archive.py \
  --certificate experiments/logs/root-full-caps-anchor-max/prism-archive-inspection.json
```

These files establish the count interpretation and its multiplicities,
and record the limits of the archived systems. They exclude no
99-vertex case.
