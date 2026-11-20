# Two-edge exterior paths that force a prism

This is a point-independent scope and cost inventory for the fixed F0
component-zero branch. The branch is globally prism-free. Its other
18-vertex component and its alignment remain free. All 480 exterior
signatures and the complete frozen set of 68,394 eligible exterior edges
are retained as inputs.

The [existing three-vertex construction](root_prism_free_f0_three_vertex_prism_cuts.md)
handles prisms with one exterior edge. This family handles exactly two
exterior edges, forming a path. No point or optimizer has been used here.

## A complete literal pattern

Let x-y-z be an induced path in the fixed 18-vertex component.
Let a,b,c be three exterior signatures whose intersections with these
three core sites are

| Exterior vertex | Neighbors among x,y,z |
|---|---|
| a | x,z |
| b | x |
| c | y,z |

If exterior edges a-b and b-c are both present, the two triangles are
{a,b,x} and {c,y,z}, with matching edges a-z, b-c and x-y.
The remaining exterior edge a-c cannot be present: an adjacent pair a,c
would already have the two distinct common neighbors b and z.
Thus these six sites induce a triangular prism.

Every prism having three exterior vertices and two exterior edges has
this form. The two exterior edges form a path, and the complementary
three core vertices also form a path. The center b has exactly one
neighbor x in the core path; this determines the orientation x-y-z and
the two endpoint roles. The central three core vertices cannot occur
in this prism, since exterior signatures have no neighbors there and
every core vertex of this pattern needs an exterior neighbor.

As a finite control, the source examines all 20 choices of three exterior
sites in a literal prism. They split into two triangle cases, six
one-edge cases and twelve path cases. Every path case reconstructs the
same six-by-six adjacency matrix in triangle order (a,b,x,c,y,z).

## The linear inequality

Write x_b for a binary selector and y_ab,y_bc for binary edges at one
graph embedding. Edge activation gives y_ab,y_bc at most x_b.
Prism-freeness prohibits both edges together. Therefore

\[
y_{ab}+y_{bc}\le x_b.
\]

Averaging actual graph embeddings gives the necessary linear row

\[
Y_{ab}+Y_{bc}-x_b\le0.
\]

No product of two edge variables is introduced. The Boolean control
checks all twelve assignments satisfying activation and this prism
absence, and the single activation-compatible assignment that would
create the forbidden path.

The actual-core quotient may send the two edges to the same edge orbit.
Such a row must retain coefficient two on that edge variable. The
production construction must combine repeated variables; it must not
assume three distinct quotient columns.

## Exact pruning rules

A known zero for either edge reduces the row to the activation inequality
for the other edge. The frozen visible-edge census supplies 162 zero
edge orbits, covering 1,884 literal edges.

For a center signature b and a component site j, the exact mixed equation is

\[
\sum_{a:\,j\in h_a}Y_{ab}=t_{bj}x_b,
\qquad
t_{bj}=2-\mathbf1[j\in h_b]-\sum_{u\in h_b}A_D(j,u).
\]

If a and c both contain j and t_bj=1, nonnegativity of all other edges
already implies Y_ab+Y_bc<=x_b. The inventory removes precisely these
single-quota-one redundancies after the edge-zero pruning.

For the displayed prism pattern, a and c always share z. Each signature
has exactly three component sites, so any additional common site is
the shared third site of their two signatures. This makes the second
pruning count exact without iterating over all endpoint pairs.

## Bounded inventory

For each oriented component path and eligible center b, let A be the
eligible neighbors of b with pattern {x,z}, and let C be those with
pattern {y,z}. The product |A| |C| counts the literal pattern
configurations in that bucket. The endpoint buckets are disjoint and
exclude b. Known-zero edges first remove neighbors from both buckets.

If t_bz=1, the remaining whole bucket is redundant. Otherwise t_bz=2.
Within this bucket, each possible third site determines at most one
signature in A and at most one in C. Intersecting their third-site
bitsets with the quota-one sites of b gives the exact further pruning
count. No production exterior path pair is materialized by this inventory.

The completed inventory took 0.952331 seconds under
its ten-second limit.

| Quantity | Count |
|---|---:|
| Oriented core paths | 108 |
| Eligible center/core patterns | 7,128 |
| Nonempty raw buckets | 1,584 |
| All eligible exterior path pairs, before using a prism pattern | 19,673,442 |
| Literal prism-pattern configurations | 107,520 |
| Removed by a known edge zero | 8,724 |
| Removed by the common-site quota one | 34,296 |
| Removed by a third-site quota one | 2,988 |
| Remaining literal pattern configurations | 61,512 |
| Nonempty remaining buckets | 996 |

These are configuration counts before identifying different core
witnesses for the same exterior path or mapping rows to the quotient.
They do not yet give the number of distinct inequalities.
The 61,512 count is an upper bound on that number.

The proposed production stage is a single 30-second preparation that
reconstructs each literal six-site witness, records every disposition,
deduplicates exterior paths and quotient rows, and checks the actual-core
transports. It would be followed by an exact cold replay. It requires a
separate review before launch.

The source is
`experiments/workspace/root_prism_free_f0_path_prism_inventory.py`,
SHA256 `0d722525b142d6c4c23476540e368950e265c7efe99a654d24bb7fbb1b441960`.
The compact bucket ledger is
`experiments/logs/root-prism-free/f0-path-prism-inventory01.json.gz`,
SHA256 `52a618d43128001625b337578bcd3ae4beb4fc0e2552031ab9013a77a32711db`.
The separate preparation record contains the controls and source/input
bindings. No production cut census, fractional point evaluation or graph
exclusion is claimed by this inventory.
