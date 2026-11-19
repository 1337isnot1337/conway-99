# Independent audit of the complete unrestricted root model

## Audit conclusion and exact binding

The mathematical reduction and source encoding in
`experiments/workspace/root_full_caps.py` passed an independent
read-only audit. This conclusion is bound to source SHA-256

```text
1e064dc0bcffa6c77fbbfbfd9513fb6d0cedfc0f291ac347cdecff7729951419
```

The eleven normalized cases cover every hypothetical
SRG(99,14,1,2). Every satisfying edge assignment would give a complete
graph with the required degrees and pair counts. Every such graph
has a labeling that satisfies one of the eleven cases, including the
84 additional broken-rook implications.

This is a reduction and encoding audit. It does not assert SAT or
UNSAT for any case and does not decide graph existence. No timed
solve, large CNF rebuild, or proof rebuild was performed in this
audit. The clause file and any future solver certificate still need
their separate hash binding and proof replay.

The matching-coverage certificate was constructed independently in
[root_full_caps_matching_audit.md](root_full_caps_matching_audit.md).
Its source and compressed certificate have SHA-256 hashes

```text
source:      aee33c08589ab04a3a97c865bebb644c1fcfe852e1af8aa7113642d5666ce587
certificate: ed492bc4c2a50e49f855ee822adf922e0dcbe609893972a0bae96fb0e2deba5f
```

The audit also read `root_full_caps_coverage.py` and checked that all
eleven canonical matchings used by the builder agree with the
independent coverage implementation. The transport conventions are
inverse descriptions of the same signed-pair relabeling: the builder
coverage maps canonical matchings to input matchings, while the
independent certificate maps input matchings to canonical matchings.

## Mandatory core and complete outside domain

For an arbitrary root, the 14 near vertices induce seven disjoint
edges. This follows from the unique-common-neighbor condition on
each root edge. Label the near vertices `0,...,13`, with mates
`i^1`; the full core uses index 0 for the root and `1+i` for near
label `i`.

Each of the other 84 vertices has exactly two near neighbors. Their
labels are a non-mate pair. Every non-mate pair has exactly one such
outside vertex: it already has the root as one common neighbor and
requires one more. The builder therefore uses exactly the forced
domain, indexed by

\[
\{a,b\}\subset\{0,\ldots,13\},\qquad b\ne a\mathbin{\oplus}1.
\]

The independent calculation reconstructed all 84 signatures and
checked all 225 entries of the core incidence identity

\[
XX^{\mathsf T}=12I+2J-B^2-B.
\]

For an outside vertex labeled `{a,b}`, the mixed demand at the root
is zero. The demand is one at the four near labels
`a,a^1,b,b^1`, and two at the other ten near labels. The demands sum
to 24, consistent with its twelve outside neighbors, each having
two near incidences. The explicit exterior-degree equation also
requires degree twelve.

All pairs of distinct outside signatures are initially eligible
edges. Their core overlap is zero or one, and every mixed demand at
a near label is positive. The builder retains all 3,486 independent
edge variables; none is removed by a grid or symmetry assumption.

| Independently checked quantity | Value |
| --- | ---: |
| Core vertices | 15 |
| Near mate edges | 7 |
| Outside signatures | 84 |
| Core neighbors per outside signature | 2 |
| Exterior degree | 12 |
| Possible exterior edges | 3,486 |
| Outside pairs sharing one core neighbor | 924 |
| Outside pairs sharing no core neighbor | 2,562 |
| Outside pairs sharing two core neighbors | 0 |

The shared-pair count is `14*binom(12,2)=924`. Since signatures are
distinct two-subsets, no pair is counted at two near labels.

## Mixed equations, complete pair caps, and variable allocation

For each outside vertex, the builder imposes every mixed core
equation and its exterior degree by exact cardinality constraints.
Deduplicating identical literal lists with identical right sides
does not remove any distinct restriction. The empty root equation
has right side zero.

For every unordered exterior pair `a,b`, the cap is

\[
e_{ab}+\sum_{w\ne a,b}(e_{aw}\land e_{bw})
\le2-|h_a\cap h_b|.
\]

All 82 possible outside centers are included for every pair. Hence
there are exactly

\[
3486\cdot82=285,852
\]

forward path variables. The direct edge is included in every cap.
The right side is one for the 924 pairs with one common core
neighbor and two for the other 2,562 pairs.

Each path variable is constrained by

\[
\neg e_{aw}\lor\neg e_{bw}\lor p_{abw}.
\]

This implication direction is sufficient and exact for an upper
bound. If both edges are present, the path variable must be true.
Conversely, a valid edge assignment extends by setting each path
variable equal to the conjunction of its two edges. Thus the
existential auxiliary variables do not exclude a valid edge
assignment and cannot conceal a cap violation.

Edges, paths, and sequential-cardinality auxiliaries use the same
`IDPool`. Edge identifiers are allocated first. Path names use a
separate tuple prefix and unique pair/center indices. The pool is
passed to every cardinality encoder, so later paths cannot collide
with previously allocated cardinality auxiliaries. The extraction
routine reconstructs the same initial edge ordering.

The audit reviewed this logic directly. It did not rerun the
builder owner's 3,069 solver-based forward-gadget controls or
rebuild the full formula.

## Why upper caps suffice for the exact SRG equations

The fixed core and the Gram identity give the exact core pair
counts. The mixed equalities give the exact core/outside counts.
Core degree plus incidence gives degree 14 for every core vertex,
and the exterior degree equations give degree 14 for every outside
vertex.

For any symmetric zero-diagonal degree-14 adjacency matrix,

\[
\sum_{u\ne v}\bigl((A^2)_{vu}+A_{vu}\bigr)
=14^2=196=98\cdot2.
\]

All 98 summands are at most two. Their fixed sum therefore forces
every summand to equal two. This is exactly the required adjacent
and nonadjacent common-neighbor condition. The extraction routine
also checks all degrees, symmetry, zero diagonal, and all 4,851
unordered pair equations directly.

## The eleven anchor normalizations

Choose near label 0. Its twelve outside neighbors are the vertices
with signatures `{0,j}`, `j=2,...,13`. They induce a perfect
matching. The remaining six near mate-pairs can be permuted and
independently flipped without changing the mandatory core or its
incidence labels.

The independent coverage audit exhausts all 10,395 such matchings,
constructs a mate-preserving transport for each, and separately
recomputes their eleven group orbits. The builder's
`anchor_units` function maps each canonical local edge `{a,b}` to
the exterior edge between signatures `{0,2+a}` and `{0,2+b}`.
All eleven mappings were checked directly against the independent
canonical matchings.

Each case sets six disjoint exterior edges to one. They cover all
twelve outside neighbors of near 0. The corresponding mixed
degree-one equations force all other edges within that twelve-set
to zero, so separate negative normalization units are unnecessary.

These are choices of coordinate representatives. No completed graph
is required to possess an automorphism. All eleven case formulas
share the same unrestricted base and differ only by these six units.

## The 84 broken-rook implications

For each choice of two near mate-pairs, take the four outside
vertices indexed by one endpoint from each pair. Their four cell
sides are the pairs sharing one near label. The builder adds, for
each side, the implication that the other three sides force that
side. There are

\[
4\binom72=84
\]

clauses. Their signs were checked: the forced side is positive and
the other three sides are negative. Neither diagonal is forbidden
unconditionally.

An independent enumeration of all 64 assignments to the six cell
edges gives 19 patterns satisfying the visible common-neighbor
caps. Exactly four have three sides, and every one has both
diagonals absent. The same implication follows directly: a
diagonal together with the relevant two-side path would give an
adjacent side pair a second common neighbor in addition to its
shared near vertex.

With exactly three sides and no diagonals, the root, the four near
vertices, and the four cell vertices induce the nine-point rook
graph with one edge deleted. That induced graph is unconditionally
forbidden in an SRG(99,14,1,2), by the integral norm argument in
`STATE.md`, restated in
[two_rook_tip_edge_bound.md](grids-and-triangles/two_rook_tip_edge_bound.md).

The proof was read and checked independently for this audit. If
`h` is the indicator of the nine vertices, then

\[
z=(3I-A+J/9)h
\]

is an integral -4 eigenvector with zero sum and squared norm 14.
A coordinate of magnitude at least two would require opposite-sign
mass at least eight, hence squared norm at least sixteen. Therefore
`z` has seven coordinates +1 and seven coordinates -1. Counting
pairs of positive coordinates with a negative common neighbor
gives a lower bound `7*binom(4,2)=42` and an upper bound
`2*binom(7,2)=42`. Equality forces every common neighbor of two
positive coordinates to be negative. The endpoints of the deleted
edge have coordinate +1, while their third rook-line vertex is a
common neighbor of coordinate zero, a contradiction.

Thus all 84 implications are necessary without a grid-existence,
root-grid-count, complete-axis, or graph-symmetry hypothesis. The
builder exposes this strengthening only for degree 14 and the
explicit degree-four rook control.

## Positive-control review and verification limits

The direct nine-rook coordinates in `rook_control` were checked
against the rooted labels and the four outside signatures. Its
canonical anchor edge is an actual rook edge, all four cell sides
are present, and the diagonal cell edges are absent. The source
checks both this fixed primary assignment and a free normalized
degree-four solve. Those solver checks were run by the builder
owner; this independent audit did not launch them again.

The audit concludes that the mathematical coverage and the reviewed
source encoding are sound at the bound source hash. It does not
certify the third-party cardinality library independently, compare
every emitted CNF clause with a second builder, or verify any
solver proof. Those checks remain separate from the coverage and
domain calculations recorded here.
