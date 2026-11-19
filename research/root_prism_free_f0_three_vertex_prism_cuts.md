# Mixed edge and selector cuts from three-vertex prisms

There are 9,360 visible prism configurations with three exterior vertices
and exactly one exterior edge in the fixed F0 component-zero domain.
They give 715 distinct linear inequalities coupling the existing edge
and selector-pair moments after the known zero rows are removed.
No third selector moment or product of two edge variables is required.

The premises are the globally prism-free split-shell branch and its
fixed component-zero core. The second component and its alignment remain
free. All 480 signatures are retained.

## The local implication

Let a,b,c be distinct exterior signatures. Suppose joining a to b gives
the two triangles

    {a,b,u}, {c,v,w},

with matching cross edges a-v, b-w, u-c. Here u,v,w are component
vertices. All edges except a-b are specified by the signatures and the
fixed core. The configuration is a triangular prism whenever c is
selected and edge a-b is present.

The other two exterior edges cannot remove this obstruction. Signatures
a and c have the two common core neighbors u,v; signatures b and c have
the two common core neighbors u,w. They therefore must be nonadjacent
whenever they coexist. The six indicated vertices induce the prism.

Write z for a binary selector assignment and y_ab for the binary edge
indicator. Prism-freeness gives

    y_ab*z_c = 0.

Edge activation gives y_ab<=z_a and y_ab<=z_b. Checking the two possible
values of z_a, and then of z_b, yields

    y_ab + z_a*z_c <= z_a,
    y_ab + z_b*z_c <= z_b.

Averaging valid graph embeddings gives the necessary linear rows

    Y_ab + Z_ac <= x_a,
    Y_ab + Z_bc <= x_b.

The full Boolean check covers all nine assignments satisfying activation
and prism absence. The moments must come from the same graph embedding
before averaging. No independence assumption is used.

## Complete enumeration of the specified family

Every prism with three exterior vertices and exactly one exterior edge
has two exterior vertices in one triangle and one in the other. The
exterior edge must be the edge joining the first two vertices. Thus any
such configuration has precisely the form above.

For each of the 68,394 eligible unordered exterior edges a-b, the source
finds the common component neighbor u. An adjacent pair has at most one.
It then tests every v in h_a except u and every w in h_b except u.
It requires the core edge v-w and the available third signature

    h_c = {u,v,w}.

This is exhaustive: the two core neighbors v,w complete c's triangle,
and its matching cross edge requires u as its third component neighbor.
All recovered six-vertex graphs are reconstructed and checked directly.
The source also verifies both two-common-neighbor prohibitions above.

There are 9,360 distinct triples consisting of an exterior edge and a
third selector, hence 18,720 literal inequalities before simplification.
Their dispositions are:

| Disposition | Literal inequalities |
| --- | ---: |
| Existing Y zero reduces the row to pair activation | 456 |
| Existing Z zero reduces the row to edge activation | 9,684 |
| Retained rows | 8,580 |
| Total | 18,720 |

The retained rows reduce to 715 distinct quotient inequalities on the
existing 15,200 variables. Each has three coefficients, -1,+1,+1,
and right-hand side zero. The quotient uses the already verified
twelve actual-core actions; it imposes no symmetry on a graph.

Each discarded row has its explicit reason retained. Every retained
row identifies its first literal prism witness, and every literal
witness identifies both row dispositions. These checks do not assert
that all 715 rows are independent of other constraints.

## Verification and scope

The point-independent preparation finishes in 4.266 seconds. Its cold
replay reconstructs all 9,360 literal witnesses and all 715 rows. No
numerical point, optimizer or spectral proposal is used.

The source is
[root_prism_free_f0_three_vertex_prism_cuts.py](../experiments/workspace/root_prism_free_f0_three_vertex_prism_cuts.py).
The complete compressed record is
[f0-three-vertex-prism-cuts01.json.gz](../experiments/logs/root-prism-free/f0-three-vertex-prism-cuts01.json.gz),
with separate preparation and cold-replay records.

The [two-exterior-vertex census](root_prism_free_f0_edge_motifs.md)
supplies the 162 Y-zero premises. The 389 Z-zero premises come from
the previously verified second-moment reduction. No coordinate of a
numerical basis is imposed as a graph condition.

Prisms using two or three exterior edges, and motifs using more than
three exterior vertices, are outside this preparation. No complete
prism-free exterior graph model or graph-existence result is claimed.
