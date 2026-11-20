# Independent CP-SAT reconstruction of the remaining three-grid case

The independent model reconstructs the remaining 27-vertex three-grid
core and all of its necessary completion constraints without importing the
SAT builder or its saved signatures. It recovers the same 168 possible
outside signatures and 9,846 possible outside edges. A known nine-vertex
rook control passes.

The bounded target solve returned `UNKNOWN`, with no search branches or
conflicts. This run does not independently prove infeasibility. The
separately checked CNF/DRAT proof supplies that conclusion. The contribution
here is an independent construction, a positive control, and a necessity
audit of the mathematical constraints.

## Core and signatures

The core consists of three disjoint rook grids, with the two matchings
from grid zero gauged to the identity. The remaining matching from grid
one to grid two is the permutation

```text
(0,5,7,8,6,1,4,2,3).
```

Let `B` be the core adjacency matrix. Every core vertex has degree six.
Set

\[
G=12I+2J-B^2-B.
\]

Every one of the 72 outside vertices must have one neighbor in each rook
grid. A candidate signature `h_s` therefore has three entries equal to
one, one in each base. The program independently enumerates all `9^3`
possibilities, retaining exactly those satisfying

\[
G_{ij}>0\quad\text{for every selected pair }i,j,
\qquad d_s=2\mathbf1-(B+I)h_s\ge0.
\]

These are necessary pair-quota and mixed common-neighbor bounds. Exactly
168 signatures survive. A signature cannot occur twice: two such outside
vertices would share three core neighbors, exceeding the common-neighbor
maximum two. Its population `z_s` is therefore binary.

## Outside edges and exact equations

An outside edge between signatures `s,t` is eligible only if

\[
h_s^T h_t\le1,
\qquad d_s[i]\ge1\text{ for }i\in h_t,
\qquad d_t[i]\ge1\text{ for }i\in h_s.
\]

An adjacent pair has only one common neighbor, giving the first
condition. In the mixed equation for `s` and a core point `i`, its neighbor
`t` contributes one whenever `i` belongs to `h_t`, giving the other
conditions. This leaves exactly 9,846 unordered possible edges.

Let their binary variables be `a_st`. The model imposes:

\[
\begin{aligned}
a_{st}&\le z_s,z_t,\\
\sum_s z_s&=72,\\
\sum_s z_s h_s h_s^T&=G,\\
\sum_s a_{st}h_s&=d_t z_t,\\
\sum_s a_{st}&=11z_t.
\end{aligned}
\]

The Gram identity is the core block of `A^2+A=12I+2J`. The mixed
equation is the core-to-outside block, applied only to an actual outside
vertex. Multiplication by `z_t` also gives zero for an inactive candidate,
as endpoint activation forces all its incident edges to zero.

An actual outside vertex has three core neighbors and hence eleven
outside neighbors. The degree equation is also implied by summing its
27 mixed equations: `sum_i d_t[i]=33`, while each neighboring signature
contributes three.

Finally, for every potential central vertex `t` and every core pair
`i,j`, impose

\[
\sum_{s:\{i,j\}\subseteq h_s} a_{st}\le z_t.
\]

If two actual neighbors of `t` contained the same core pair, they would
have those two core points and `t` as three common neighbors. Thus at most
one can occur. Rows with zero or one eligible variable are already
implied by activation and are omitted.

None of these constraints assumes a symmetry, fixes an outside graph, or
uses an averaged incidence assignment. They are necessary for every
completion of this specified core. They need not be sufficient for a
completion; the remaining outside-to-outside codegree equations are not
all included.

## Independent implementation and control

`experiments/workspace/three_rook_case48_cp_audit.py` constructs the core
using integer adjacency bit masks. It derives every signature, edge, Gram
equation, and packing row directly from that core. It does not import the
SAT implementation or read its candidate lists.

The model has:

| Item | Count |
| --- | ---: |
| Binary signature variables | 168 |
| Binary edge variables | 9,846 |
| Total variables | 10,014 |
| Positive off-diagonal Gram equations | 160 |
| Mixed equations | 4,536 |
| Degree equations | 168 |
| Nontrivial core-pair packing rows | 19,156 |
| Total CP-SAT constraints | 43,740 |

For a positive control, the same generic constraint builder is given two
rows of the known nine-vertex rook graph as its six-point core. It recovers
the three remaining vertices and their triangle. The control solves to
`OPTIMAL`, with all three true signatures and all three true outside edges.

## Observed target outcome

The target was launched with a 60-second limit and four search workers.
It returned `UNKNOWN` after approximately 48.9 reported seconds. Its
response had zero branches, conflicts, and propagations; the run did not
reach search. Concurrent heavy checks caused substantial execution
contention during this audit. No infeasibility conclusion is drawn from
the CP-SAT status.

The actual result, complete independent signature and edge lists, core
matrix, and positive-control result are retained in
`experiments/logs/grids-and-triangles/three-rook-case48-cp-audit.json`.
The corresponding log is retained beside it.

```sh
.venv/bin/python experiments/workspace/three_rook_case48_cp_audit.py \
  --seconds 60 --workers 4 \
  --output experiments/logs/grids-and-triangles/three-rook-case48-cp-audit.json
```
