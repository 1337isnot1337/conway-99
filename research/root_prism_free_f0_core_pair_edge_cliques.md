# Edge cliques from two common core neighbors

The fixed F0 branch has a central triangle, a fixed eighteen-vertex shell
component, and an unspecified second shell component. The sixty vertices
outside the triangle shell have 480 possible signatures on the fixed
component. An exterior vertex has three neighbors in each component and
eight among the sixty exterior vertices.

This note gives necessary inequalities on exterior edges. It does not
forbid two signatures from occurring together. The common-neighbor
argument does not need prism-freeness. The removal of the previously
proved 162 zero edge orbits uses the branch's prism-free hypothesis.

## The pointwise inequality

Fix an exterior center signature b and two distinct component vertices
i,j. Let S(b,i,j) contain the eligible neighbors a of b whose signature
contains both i and j. Write z_b for the binary selector and y_ab for
the binary exterior edge.

If two distinct vertices a,c in S(b,i,j) are both neighbors of b, then
a,c have the three distinct common neighbors b,i,j. This contradicts
the common-neighbor cap of two. The conclusion holds whether a,c are
adjacent or nonadjacent. Edge activation also gives y_ab<=z_b. Therefore

\[
\sum_{a\in S(b,i,j)}y_{ab}\le z_b.
\]

Taking the same average over actual fixed-core relabelings used by the
existing moment model gives

\[
\sum_{a\in S(b,i,j)}Y_{ab}\le x_b.
\]

This argument introduces no product of two edges and no third selector
moment. Several literal edges may share one quotient variable. Their
coefficients must be added, rather than replaced by one.

## Redundancies removed before construction

Known zero edges are removed from each bucket. Empty buckets need no
row, and a bucket of size one gives only an edge-activation inequality.

Let K be the fixed 21-vertex adjacency matrix, and define

\[
q_{ij}=2-K_{ij}-|N_K(i)\cap N_K(j)|.
\]

All further common neighbors of i,j lie among the sixty exterior
vertices. The original selector Gram equation is

\[
\sum_{a:\ i,j\in h_a}z_a=q_{ij}.
\]

Its existing lift at b says that the sum of the corresponding Z_ab is
q_ij*x_b, including the diagonal term when applicable. Since Y_ab<=Z_ab
and all moments are nonnegative, q_ij<=1 already implies the new row.
These buckets are removed.

For the remaining buckets, the existing mixed equations are

\[
\sum_{a:\ i\in h_a}Y_{ab}=t_{bi}x_b,
\qquad
t_{bi}=2-\mathbf1[i\in h_b]-\sum_{u\in h_b}K_{iu}.
\]

If either t_bi or t_bj is at most one, its mixed equation and edge
nonnegativity imply the bucket row. These buckets are also removed.
Every retained bucket has q_ij=t_bi=t_bj=2. This pruning does not claim
that all retained rows are independent of the complete existing model.

The mixed targets sum to 24 at every center. Each eligible neighboring
signature contributes to three targets, so the mixed equations give
sum_a Y_ab=8*x_b. The local exterior degree is eight.

## Complete finite inventory

The inventory covers all 480 centers and all 153 unordered pairs of
component sites. Each of the 68,394 eligible edges contributes to both
center roles and all three pairs in its other endpoint's signature.
Thus there are exactly 410,364 raw edge memberships.

| Disposition | Buckets |
|---|---:|
| Empty after known edge zeros | 25,128 |
| Implied by a lifted core-pair quota at most one | 29,616 |
| Implied by a mixed quota at most one | 15,600 |
| Retained | 3,096 |
| Total | 73,440 |

There are no singleton live buckets. The retained buckets contain
30,528 edge memberships and 136,740 unordered endpoint-pair conflict
instances. Their largest size is twelve. These are literal bucket
counts, before quotient-row deduplication.

The inventory took 2.898483 seconds. It did not construct quotient
inequalities, load a fractional point, or call an optimizer. Its source
is `experiments/workspace/root_prism_free_f0_core_pair_edge_cliques.py`,
SHA256 `2721f32b6bc1778fb7bd4dd7b6893880e2fe0ef014323fb7365e20f02fbb1811`.
The compact record is
`experiments/logs/root-prism-free/f0-core-pair-edge-cliques-inventory01.json.gz`,
SHA256 `cd80b99e9667fe87b2288a931570950cd319b1d9ec7927b38cb191a2cf5cb680`.

The finite controls examine every simple graph on five labelled
vertices. All 20,490 bucket tests on the 683 graphs satisfying the
common-neighbor caps pass. Separate controls check binary activation
and addition of coincident quotient coefficients.

## Completed construction and replay

An independent mathematical and source review checked the pruning
against the original lifted Gram equations and all literal Y<=Z links.
The complete construction then took 3.205994 seconds. It retains every
bucket disposition and gives 258 distinct quotient inequalities with
2,802 nonzero coefficients. The largest literal bucket has twelve edges.
None of these 258 rows happens to have a repeated edge-orbit column.
All 3,096 actual-core transports pass.

A separate cold replay took 3.147466 seconds and reproduced the full
mathematical record byte for byte. The record is
`experiments/logs/root-prism-free/f0-core-pair-edge-cliques01.json.gz`,
SHA256 `728f3de4ed0febf90f4062820b5a58c8e31335ebc7e65d354872c7bc8d38370e`.
Its uncompressed canonical hash is
`eb2c2c8829a2c75e59103609b4cb984b52eb44f64868efc7b735b6bb817fef18`.

No point has been evaluated against this family, and no model has yet
been optimized with these rows. Their independence from the complete
existing relaxation is not claimed. Graph existence and component-zero
completion remain unresolved.
