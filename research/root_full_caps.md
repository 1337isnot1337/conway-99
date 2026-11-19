# A complete rooted model for the unrestricted 99-graph problem

This model applies to every hypothetical strongly regular graph with
parameters `(99,14,1,2)`. Its initial configuration is a vertex and its
neighborhood. No grid, graph automorphism, eigenvector support, or
bound on the number of grids is assumed.

All exterior common-neighbor caps are encoded before solving. A complete
solution of any case gives a 99-vertex graph and is checked directly.
Conversely, every hypothetical graph can be labelled to satisfy one of
eleven explicit normalization cases. A timeout in any case leaves that
case open.

The [first batch](root_full_caps_runs_01.md) finished all eleven cases
as UNKNOWN at 180 seconds each. No graph or UNSAT certificate was found.

## The mandatory fifteen-point core

Fix a root `r`. Its fourteen neighbors each have exactly one neighbor
within `N(r)`, because an adjacent pair has exactly one common neighbor.
Thus the induced graph on `N(r)` is `7K2`. Label its vertices
`0,...,13`, with mate involution `a -> a xor 1`.

Every one of the remaining 84 vertices is nonadjacent to `r`, so it has
exactly two neighbors in `N(r)`. These two cannot be mates: a mate pair
already has `r` as its unique common neighbor. Therefore an exterior
vertex has a signature `{a,b}` with `a xor 1 != b`.

Conversely, every nonmate pair `a,b` is nonadjacent and already has `r`
as one common neighbor. It has no other common neighbor within `N(r)`,
whose graph is a matching. Its unique second common neighbor is therefore
outside the core. This proves that each nonmate signature occurs once.
There are

\[
\binom{14}{2}-7=84
\]

such signatures. The exterior incidence is completely fixed; it is not
an incidence witness chosen by a search.

Let `B` be the adjacency matrix of the root and its fourteen neighbors,
and `X` the fixed core-to-exterior incidence. The builder checks every
entry of

\[
XX^T=12I+2J-B^2-B.
\]

The root has no exterior neighbors. Each near vertex has two core
neighbors and twelve exterior neighbors. Each exterior vertex has two
core neighbors and needs twelve exterior neighbors.

## Mixed equations and all exterior edges

Let `C` be the unknown exterior adjacency matrix. Its 84 vertices are
the signatures. Distinct signatures share either zero or one core
neighbor, so every one of the `binom(84,2)=3486` possible exterior edges
is initially eligible.

For an exterior signature `e={x,y}` and a near label `a`, the exact
mixed equation is

\[
\sum_{f:a\in f} C_{ef}
=2-1_{a\in e}-1_{a\mathbin{\mathrm{xor}}1\in e}.
\]

The diagonal term is absent. The right side is one on the four labels
`x,x xor 1,y,y xor 1` and two on the other ten labels. The root mixed
equation has demand zero. The builder checks this explicit expression
against the general matrix demand `2J-(B+I)X`.

Summing the fourteen near-label equations gives exterior degree twelve,
because each exterior signature contributes to exactly two sums. The
degree equation is also imposed explicitly. Identical cardinality
requests are deduplicated, leaving 1,261 counts including the empty
zero-demand root request.

For each exterior pair `e,f`, let `c=|e intersection f|`. Every
completion must satisfy

\[
C_{ef}+\sum_w C_{ew}C_{fw}\le2-c.
\]

There are 924 pairs with `c=1`, and 2,562 pairs with `c=0`. The first
count is `14*binom(12,2)`: every near label belongs to twelve signatures,
and two distinct signatures cannot share two labels. All 3,486 caps
are present in the formula.

Each pair has 82 possible path centers. A fresh path variable `p_efw`
has the clause

\[
\neg C_{ew}\lor\neg C_{fw}\lor p_{efw}.
\]

A sequential counter bounds these path variables and the direct edge
by `2-c`. Forward implications suffice: actual paths force their
variables true, while a cap-valid edge assignment extends by setting
each path variable to its exact conjunction. This gives 285,852 path
variables. No lazy separation or omitted exterior pair remains.

## A necessary broken-rook implication

This strengthening is specific to the 99-vertex parameters. The
implementation accepts only degree fourteen and the explicit degree-four
positive control; it does not expose an arbitrary-degree model with
this extra theorem.

Choose two of the seven near mate-pairs. Their four nonmate exterior
signatures form a four-point cell. Its four side edges change one sign;
its two diagonal edges change both signs. If exactly three sides were
present, they would form a path of length three. Each diagonal would
create a second common neighbor for the middle edge, which already
has a shared near-core neighbor. Both diagonals are therefore absent
by the local common-neighbor bounds.

The root, four near points, and four cell points would then induce a
nine-point rook graph with one edge removed. The following integral
argument excludes that induced graph without assuming that any grid
exists elsewhere.

Suppose such a nine-point set `H` existed, and put

\[
P=3I-A+J/9,\qquad v=P1_H.
\]

The SRG equation and regularity give `AP=-4P`, `P1=0`, and `P^2=7P`.
Because `|H|=9`, the vector `v` is integral and has coordinate sum zero.
Since `H` has seventeen edges,

\[
\|v\|^2
=7\left(3\cdot9-2\cdot17+\frac{9^2}{9}\right)=14.
\]

If a coordinate had magnitude at least two, its eigenvector equation
would require opposite-sign mass at least eight. The positive and
negative masses are equal, so the absolute mass would be at least
sixteen. Integrality would then give squared norm at least sixteen,
a contradiction. Hence `v` consists of seven `+1` entries, seven `-1`
entries, and zeros.

Each negative site has at least four positive neighbors. Counting pairs
of positive sites with a marked negative common neighbor gives at least
`7*binom(4,2)=42` incidences. The universal two-common-neighbor bound
gives at most `2*binom(7,2)=42`. Equality forces every common neighbor
of two positive sites to be negative.

The removed edge's two endpoints have coordinate `4-3=1`; their third
vertex on the former rook line has coordinate `4-4=0`. This zero site
is a common neighbor of the two positive endpoints, a contradiction.

Thus three cell sides imply the fourth. There are four implication
clauses for each of 21 cells, giving 84 clauses. The model does **not**
globally forbid diagonal cell edges. No root-grid bound, parallel-branch
classification, or graph symmetry is used here.

## Exhaustive anchor-matching normalization

Consider the twelve exterior signatures `{0,a}` for `a=2,...,13`.
The mixed equation at near label zero gives degree one inside this
fiber, so its induced graph is a perfect matching `M`.

The twelve endpoint labels also have the fixed mate matching `M0`,
with pairs `(2,3),...,(12,13)`. The union of `M` and `M0` is an
alternating two-regular multigraph. A shared edge is represented as
a doubled two-cycle. Every component has length `2l`; its half-lengths
form an integer partition of six.

The six axes other than `{0,1}` can be permuted arbitrarily, and either
endpoint of each axis can be exchanged. These signed-axis relabelings
fix the chosen root, near label zero, and its mate. They preserve the
whole fixed core and every exterior signature. They are coordinate
relabelings, not presumed automorphisms of a completed graph.

Within each alternating component, traverse a fixed mate edge and then
an edge of `M`. This labels its axes cyclically and gives the canonical
matching used in `root_search.py`. Components can be sorted by size.
Consequently every matching with the same component partition is
equivalent to the canonical representative. Different partitions cannot
be equivalent, since component sizes are invariant.

There are exactly eleven cases:

| Case | Half-length partition | Labelled matchings |
| ---: | --- | ---: |
| 0 | `(1,1,1,1,1,1)` | 1 |
| 1 | `(1,1,1,1,2)` | 30 |
| 2 | `(1,1,1,3)` | 160 |
| 3 | `(1,1,2,2)` | 180 |
| 4 | `(1,1,4)` | 720 |
| 5 | `(1,2,3)` | 960 |
| 6 | `(1,5)` | 2,304 |
| 7 | `(2,2,2)` | 120 |
| 8 | `(2,4)` | 1,440 |
| 9 | `(3,3)` | 640 |
| 10 | `(6)` | 3,840 |

The sum is `11!!=10395`, the total number of perfect matchings on
twelve points. The primary coverage checker enumerates every matching
and verifies an explicit signed-axis transport from its canonical
representative. A separate worker independently enumerated the group
orbits by generators and obtained the same complete sets and counts.
A third check derives the orbit-size formula

\[
\frac{2^{6-\ell(\lambda)}6!}
{\prod_j j^{m_j}m_j!},
\]

where `m_j` counts parts of size `j` and `ell(lambda)` is the number of
parts.

Each normalized formula fixes the six canonical matching edges to one.
The existing degree-one fiber equations force all its other edges to
zero. No further ordering or symmetry is imposed. In particular, the
sevenfold quotient used only to construct a phase seed in
`anchor_seed.py` is absent from this model.

## Why SAT gives a complete graph

The fixed Gram matrix makes every core pair exact, and the mixed
equations make every core/exterior pair exact. All 99 vertices have
degree fourteen. Every exterior pair has the required upper cap.
For every row,

\[
\sum_{j\ne i}(A^2+A)_{ij}=14^2=196=98\cdot2.
\]

Every term is at most two, so every term must equal two. Thus the full
matrix satisfies `A^2+A=12I+2J`.

The solve wrapper nevertheless reconstructs all 99 adjacency lists and
independently checks degree, symmetry, absence of loops, and every pair
count. A saved graph candidate requires a separate independent check
before acceptance.

## Positive control and formula size

The nine-point rook graph is constructed directly from its nine grid
coordinates. Its six exterior edge values are fixed as assumptions in
the degree-four version of the complete normalized CNF. The solver
accepts this exact known assignment, and reconstruction matches the
original adjacency lists and all 36 pair equations. A second solve
without those fixed edge assumptions also passes full verification.
All four cell implications hold in this control.

The forward-path/cardinality helper additionally passes 3,069 exhaustive
small primary assignments. The root-domain audit checks every fixed
Gram entry and verifies all 3,486 eligible edges and 285,852 path domains.
The independent read-only builder audit agrees with these counts and
with every canonical anchor matching.

| Quantity | Count |
| --- | ---: |
| Primary exterior edges | 3,486 |
| Mixed and degree cardinality requests | 1,261 |
| Variables before exterior caps | 183,750 |
| Clauses before exterior caps | 364,056 |
| Path variables | 285,852 |
| Total variables | 960,414 |
| Base clauses, including broken-rook implications | 1,908,858 |
| Anchor unit clauses per case | 6 |
| Total clauses per normalized case | 1,908,864 |

The shared base CNF SHA256 is
`0a3e0507a165d8f02ee77e3a2b66ff0fd2202939e92531a4a17020862b797b3c`.
All eleven complete case hashes, partitions, and units are stored in
`experiments/logs/root-full-caps/model.json`.

## Source, replay, and bounded batch

The source files are:

- `experiments/workspace/root_full_caps.py`: complete formula, positive
  controls, construction, and single-case solving;
- `experiments/workspace/root_full_caps_coverage.py`: matching coverage
  with explicit transports;
- `experiments/workspace/root_full_caps_batch.py`: sequential bounded
  cases and durable per-case status;
- `experiments/workspace/root_full_caps_certificate.py`: regeneration,
  retained-clause inclusion, and independent proof replay.

The independent matching audit is documented in
`research/root_full_caps_matching_audit.md`.

To rebuild, use temporary outputs rather than overwrite the archived
manifest that binds any solver records:

```sh
.venv/bin/python experiments/workspace/root_full_caps.py build \
  --coverage experiments/logs/root-full-caps/matching-coverage.json \
  --cnf-directory /tmp/conway-root-full-caps-replay \
  --manifest /tmp/conway-root-full-caps-model.json
```

The batch gives each case a requested 180-second solver budget,
including CNF parsing and initialization. Cases run sequentially. Their
actual elapsed times and terminal statuses are saved after every case.
The batch has a separate execution guard and stops if a process fails
without a terminal solver record.

For any UNSAT return, the exact case CNF and raw proof are checked with
`drat-trim`; a retained core, trimmed proof, hashes, and certificate
manifest are saved. The separate replay wrapper rebuilds the model and
checks retained-clause inclusion before checking the trimmed proof.
An unverified solver return is not an exclusion.

Only checked exclusions of **all eleven** cases would exclude the
unrestricted graph. A single `UNKNOWN` case keeps the problem open.
The build and coverage certificates by themselves make no
nonexistence claim.
