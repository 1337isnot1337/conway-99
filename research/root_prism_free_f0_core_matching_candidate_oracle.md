# Exact core matching checks on a supplied literal incidence

The oracle takes an explicit sorted list of 60 selected F0 signature IDs.
It does not interpret a native solver vector or replace the original count
and literal acceptance checks. No production selection was supplied during
preparation.

For each fixed core site i, the set U_i consists of possible exterior
neighbors that have no triangle partner already present in the fixed core.
The original Gram equations force exactly eight selected vertices in U_i.
The unique-common-neighbor condition forces those eight vertices to pair
off. This is the premise proved in the
[core matching blossom note](root_prism_free_f0_core_matching_blossom.md).

The oracle checks all 172 original selector equations first. It then
examines all 105 perfect matchings on the eight selected vertices at each
of the 18 core sites. The eligible edges come from the frozen original
model, with the 162 already proved zero edge orbits removed.

If a matching exists, the record stores its four literal edges. These
18 matchings are separate witnesses. Their existence does not establish a
single compatible exterior graph.

If no matching exists, the record supplies one missing edge for each of
the 105 possible matchings. Let T be the eight selected signature IDs.
Every actual graph satisfies the new literal inequality

\[
\sum_{a\in T}x_a\le7.
\]

If all eight were selected, the original equation for U_i would exclude
every other vertex of U_i. One of the 105 matchings on T would have to use
only eligible live edges, contradicting its recorded missing edge. This
excludes the positive eight-selector pattern without negative assumptions.

## Preparation and controls

The [source](../experiments/workspace/root_prism_free_f0_core_matching_candidate_oracle.py)
has SHA-256 `01adf67152884f59cf65c3b490de5b4f69c9d9bdec7a53ba8863991bfc9d0c60`.
Its complete source received a separate mathematical review. Preparation
and replay pass with zero production candidates and optimizer calls.

The recursion pairs the least remaining vertex and yields each perfect
matching once: 1, 1, 3, 15 and 105 templates on 0, 2, 4, 6 and 8 vertices.
Controls compare it with an independent subset recurrence on all 32,768
labelled graphs with six vertices. Six eight-vertex controls include a
complete graph, a fixed matching, a star, and two disjoint triangles with
a separate matching edge.

Preparation rechecks all 18 original Gram coefficient identities and
binds the complete eligible edge set. Its SHA-256 is
`31e9e541ac0b90975a518387bbd4656e013a40422fd7247dc2d1445eeb0eecde`.
The separate replay has SHA-256
`a2f3d6fd9e79fa8dadb9bd0c1102fc6be1f815583ee62ee42956137a4a70a439`.
The stages took 1.786 and 2.008 seconds.

These are preparation results. They contain no production exclusion,
native-model mutation, accepted count point, or graph construction.
