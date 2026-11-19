# Visible prisms force 162 F0 edge-orbit variables to zero

The complete fixed-core calculation finds 1,884 forbidden exterior edges
in 162 actual-core orbits. Every one creates an induced triangular
prism on the fixed 21-core plus its two endpoints. Therefore their
edge moments Y_ab vanish in the globally prism-free component-zero
branch. All 480 selector signatures remain available.

The census covers every one of the 68,394 eligible edges. The remaining
66,510 edges have neither a visible prism nor the forbidden ten-vertex
motif F on these 23 vertices. This is only a statement about visible
motifs on the specified core. It does not prove that those edges extend
to a graph.

## Why the edge-shell test is complete

Let H be any partial graph whose adjacent pairs have at most one common
neighbor and whose nonadjacent pairs have at most two. Fix an edge uv.
Remove u, v and their possible common neighbor from their neighborhoods.
Let L be the remaining neighbors of u and R the remaining neighbors of v.
These sets are disjoint.

Every point of L has at most one neighbor inside L, by the common-neighbor
cap on its edge to u. It also has at most one neighbor inside R: the
nonadjacent pair consisting of that point and v already has u as one
common neighbor. The same assertions hold with L and R reversed.
Consequently the induced graph on L union R has maximum degree two,
with at most one same-side and one opposite-side edge at each vertex.

A four-cycle component, together with u and v, is exactly a triangular
prism. Each such prism is counted at its three matching edges. An
eight-cycle component, together with u and v, is exactly F: its two
centers have degree five, its other eight points have degree three,
and its shell is one alternating eight-cycle.

Conversely, every visible prism or F supplies one of these cycle
components at the corresponding center edge. The cycle vertices already
have degree two inside the shell, so the degree bound prevents a larger
component from hiding the cycle. Examining every center edge therefore
detects every visible motif of these two kinds. No enumeration of
arbitrary ten-subsets is needed.

## Complete domain and transports

The source reconstructs eligible edges from the original 480 signatures
and the exact mixed common-neighbor targets. The recovered list agrees
with all 68,394 entries of the frozen baseline.

It tests one literal 23-vertex graph for each of the 5,805 actual-core
edge orbits. Every graph passes the visible common-neighbor caps.
The source verifies all twelve core actions on the complete 21-core
and all 480 signatures. For each orbit, the transported representative
must recover its entire stored edge list.

The results are:

| Visible motif types | Edge orbits | Literal edges |
| --- | ---: | ---: |
| Triangular prism | 162 | 1,884 |
| Neither prism nor F | 5,643 | 66,510 |
| F, with or without a prism | 0 | 0 |
| Total | 5,805 | 68,394 |

Each forbidden literal edge has a transported six-vertex witness.
The checker reconstructs its induced adjacency matrix and verifies the
two triangles and their matching directly. No graph automorphism is
assumed; the actions identify equivalent finite-core cases.

Thirty-two small controls use an explicit prism, the nine-vertex rook
graph, an explicit F, isolated-vertex extensions, and every single-edge
deletion from the two forbidden motifs. Prism counts are independently
computed by listing disjoint triangle pairs. The complete production
census finishes in 5.671 seconds, and its cold replay reproduces the
mathematical record exactly.

## Relation to the Schur pair test

The [full-core Schur calculation](root_prism_free_f0_full_core_schur.md)
also gives an exact two-by-two principal-minor test for two selected
exterior vertices. The complete test covers all 114,960 unordered
signature pairs, with adjacency one tested on all 68,394 eligible edges.
Every nonedge state passes both projectors. The plus projector rejects
twelve edge states in edge orbit three; the minus projector rejects none.
No tested determinant is zero.

The representative is the pair of signatures

    a = {0,2,6},  b = {1,2,13}.

These are component indices, shifted by three in the full core. Joining
the two new vertices 21 and 22 creates, among others, the prism with
triangles {0,3,4} and {5,21,22}. Thus the twelve spectrally forbidden
edges are included in the larger visible-prism census. The spectral
test and the prism test are separate proofs with different premises:
the prism prohibition uses global prism-freeness.

## The old exact point is rejected

The preceding Boolean fractional model contained the original structural
rows, ninety two-selector motif conflicts, and all 4,416 normalized
selector cuts. Its saved rational point has 5,847 coordinates and a
191-bit common denominator.

The new check reproduces all 686 quotient equalities, all 11,449
quotient inequalities, and every coordinate bound at that exact point.
Nine of the new 162 edge-zero rows have strictly positive values there.
This proves that the edge-motif rows strictly strengthen that old
Boolean fractional relaxation. The statement does not establish
feasibility or infeasibility of the later joint second-moment system.

The first point-check attempt read the old model's common scalar bounds
as coordinate arrays. It stopped with a type error before recording
a result. The corrected reader verifies the stored scalar bounds zero
and one explicitly; the failed attempt log is retained.

## Files and scope

The complete census source is
[root_prism_free_f0_edge_motif_census.py](../experiments/workspace/root_prism_free_f0_edge_motif_census.py).
Its compressed record is
[f0-edge-motif-census01.json.gz](../experiments/logs/root-prism-free/f0-edge-motif-census01.json.gz),
with separate preparation and cold-replay records. The literal record
contains every orbit, every forbidden-edge witness, and every original
Y variable fixed to zero.

The exact old-point check is
[root_prism_free_f0_edge_motif_point_check.py](../experiments/workspace/root_prism_free_f0_edge_motif_point_check.py),
with result
[f0-edge-motif-old-point-check.json](../experiments/logs/root-prism-free/f0-edge-motif-old-point-check.json).
The separate spectral census is
[root_prism_free_f0_full_core_pair_minors.py](../experiments/workspace/root_prism_free_f0_full_core_pair_minors.py).

No optimizer is used in these calculations. The other eighteen-vertex
component, its incidence and its alignment remain unrestricted. The
component-zero branch and the graph-existence problem remain open.
