# Homogeneous four-cycle rows from the accepted common-neighbor caps

Status: mathematical consequence only. No candidate-pair census, model
construction, optimizer call, or change to the frozen strengthened model is
made by this note.

## Bound input and scope

The complete independent spectral-gap replay is
experiments/logs/root-prism-free/f0-spectral-gap-pair-independent-cold01.json:

- SHA256 e8d27725afb707867f6683604ff1f3123f8960305c721058f495883f23476349
- Git blob 38ec9167df27b86de0341f8387cc894c6d2ff8cc

Its source is
experiments/workspace/root_prism_free_f0_spectral_gap_pair_independent_replay_v8.js,
SHA256 cbfee51b6fbaab2a61cffcf629d03f8552d6b5c4eeb37c7b757f8b3a3c7dc7be.
The underlying proof is
research/root_prism_free_f0_spectral_gap_pair_minor.md,
SHA256 169a4b0c8ba1381302d0eeacb449599a5e4913cd6a55a24bb711e5d4126829ce.

The replay's mathematical.overlap_zero_selected_pair_common_exterior_neighbor_cap_one
array contains 48 pairs. For every such pair a,b, an actual completion with
both selectors present has at most one common neighbor in the 60-vertex
exterior. This conclusion applies for either value of the adjacency between
a and b. It does not require them to be nonadjacent.

The inherited scope is the globally prism-free F0 split18+18 branch, with
the other component and its alignment free. The argument below uses only
the stated common-neighbor cap and ordinary edge activation. It makes no
additional graph-symmetry or alignment assumption.

## Variables

Let x_u be a Boolean exterior selector. Let y_uv=y_vu be the Boolean
exterior edge variable, with

    0 <= y_uv <= x_u,   0 <= y_uv <= x_v.

For an unavailable original edge, define y_uv=0. No new variable is needed
for such an edge.

Fix one accepted pair a,b and two further distinct indices c,d. All four
indices a,b,c,d must be distinct. Put

    E = y_ac + y_ad + y_bc + y_bd,
    X = x_a + x_b + x_c + x_d.

Only these four cross edges are included in E. The ambient edges ab and cd
are unrestricted by this argument and are not included in the support graph.

## Four necessary homogeneous inequalities

For each v in {a,b,c,d}, the following row is necessary:

    E <= X - x_v.                                      (1)

In explicit form the right sides are respectively

    x_b+x_c+x_d,  x_a+x_c+x_d,
    x_a+x_b+x_d,  x_a+x_b+x_c.

These are valid with inactive selectors, without a constant activation
guard and without additional auxiliary variables.

### Proof

Consider the graph F on the four fixed labels whose edges are precisely
the positive members of {ac,ad,bc,bd}. Delete every inactive label. Endpoint
activation ensures that no deleted label was incident with a positive edge.

The only possible cycle in a subgraph of this K2,2 is the complete
four-cycle. That cycle would make c and d two distinct common exterior
neighbors of a and b. All four corresponding selectors would be present,
contradicting the accepted cap n_ab<=1. Thus F is a forest.

Write k=X for the number of present labels. If k=0, then E=0 by activation,
so every row (1) holds. If k>0, a forest on the k present labels has at most
k-1 edges. For a chosen v with x_v=1, this gives E<=X-1=X-x_v.
If x_v=0, the same bound is even stronger than E<=X-x_v=X.
This proves all four rows.

The assertion is about the four listed cross edges, not about the full
induced graph on a,b,c,d. Extra ambient edges ab or cd do not enter the
proof and need not be forced nonedges.

## Boolean equivalence and continuous strength

Under Boolean selectors, Boolean edges, and endpoint activation, each
individual row (1) is equivalent to forbidding all four cross edges at once.
The proof above establishes validity whenever that four-cycle is absent.
Conversely, when all four edges are one, activation sets all four selectors
to one and every row (1) reads 4<=3.

Consequently, after considering all distinct common-neighbor candidates
c,d for a fixed a,b, these rows encode the cap n_ab<=1 exactly on Boolean
points. This is only a statement about a complete future family; no such
family has been enumerated or accepted here.

The four rows can differ on fractional points. Each implies the unguarded
inequality E<=3 when 0<=x_u<=1. The converse fails even with all endpoint
activation bounds. For example, set x_a=1 and x_b=x_c=x_d=1/2, and set all
four listed edges to 1/2. Then E=2 satisfies E<=3 and every activation bound,
but the row omitting x_a requires E<=3/2.

Permuting the role of a shows why retaining only one of the four
homogeneous forms can lose continuous strength. This example concerns
the local activation system only; it is not claimed feasible in the full
accepted model.

## An immediate sufficient redundancy test

If at least one of the four cross edges is unavailable or already proved
zero, the remaining allowed support is itself a forest. In that case all
four rows follow from endpoint activation alone, even for real variables
satisfying the activation bounds.

To see this, root the component containing v at v. Root every other
component at any one of its vertices. Orient every allowed edge away from
its component root. Associate each edge with its child endpoint. No
nonroot vertex receives more than one such edge, so summing y_uv<=x_child
gives E at most the sum of the selectors of the nonroots. That sum is at
most X-x_v because all selectors are nonnegative. The proof also covers
an isolated v.

A future enumeration can therefore discard any four-cycle candidate
containing a proved-zero or unavailable edge, while recording the exact
zero or availability premise. No test against other existing cuts has
been performed in this note.

## Literal native form

For each choice of omitted selector v, use

    sum four original edge variables
      - sum the three other selector variables <= 0.

If all four edges exist, the row has seven distinct nonzero terms:
four coefficients +1 and three coefficients -1. The safe native domain
is [-3,0], since nonnegative edges and Boolean selectors give the lower
bound -3. Every edge retains its original native index 540+edge_id;
selector indices are unchanged. Sort all native terms by variable index.
An unavailable edge is omitted rather than assigned a new variable.

The current model configuration
experiments/logs/root-prism-free/f0-strengthened-native-configuration01.json,
SHA256 796e79978b113e49603b9cb60ddcda6bd829725eb4384d10640d74feb959ca0c,
remains unchanged. This note proves no new whole-component exclusion and
does not assert that any of the proposed rows is absent from, or
independent of, the currently accepted constraints.
