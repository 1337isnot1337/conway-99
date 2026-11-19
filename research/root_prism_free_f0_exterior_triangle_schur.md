# Exact spectral exclusions for exterior triangles

The complete forward census checks 1,179,048 exterior triangles in the
fixed F0 domain. It finds 10,830 negative principal determinants in the
plus projector and none in the minus projector. All proper principal
minors of these triangle blocks are positive.

Each negative block proves a necessary Boolean inequality
\[
y_{ab}+y_{ac}+y_{bc}\le2.
\]
Of the 10,830 inequalities, 3,840 contain an edge already proved zero.
The other 6,990 survive that specific test. This is not a claim of
logical independence from every existing constraint.

The complete independent replay is separate pending work at this
checkpoint. The source has independent review, and the exact forward
records are preserved. No enlarged native model, solver query, graph
construction, or entire-case exclusion is claimed.

## Why the matrix test proves the inequality

For a hypothetical graph in this branch, the adjacency matrix satisfies
\(A^2+A=12I+2J\). The graph projectors
\[
Q_+=27I-9A+J,\qquad Q_-=44I+11A-2J
\]
are positive semidefinite. On the two nonconstant adjacency eigenspaces,
their nonzero eigenvalues are 63 and 77, respectively. Both annihilate
the constant vector.

The previously accepted [full-core Schur calculation](root_prism_free_f0_full_core_schur.md)
conditions these projectors on the fixed 21-vertex core. The plus core
has rank 20; a positive definite 20-vertex principal core and the checked
remaining-row compatibility give its exact Schur kernel. The minus core
is positive definite. These are necessary conditions for every completed
graph with this fixed core.

Suppose three exterior signatures \(a,b,c\) form a triangle. Their three
edge indicators force all three selectors to one. The corresponding
Schur block therefore has diagonal entries "diagonal_x" and
off-diagonal entries "off_diagonal_Z + Y", in each accepted family.
The saved positive common denominator and numerator divisor do not change
positive semidefiniteness.

Write the scaled symmetric block as
\[
M=\begin{pmatrix}
d_a&s_{ab}&s_{ac}\\
s_{ab}&d_b&s_{bc}\\
s_{ac}&s_{bc}&d_c
\end{pmatrix}.
\]
Its determinant is
\[
d_a d_b d_c+2s_{ab}s_{ac}s_{bc}
-d_a s_{bc}^2-d_b s_{ac}^2-d_c s_{ab}^2.
\]
A negative determinant is impossible for a positive semidefinite
principal block. Thus all three edge indicators cannot equal one,
which proves the displayed inequality.

An exterior triangle must have pairwise disjoint core signatures.
If two endpoints shared a core neighbor, their edge would already have
that neighbor and the third triangle vertex as two distinct common
neighbors, contrary to the adjacent-pair parameter one. Overlapping
signature triples are excluded by this separate argument; they are not
silently counted in the finite census below.

## Complete finite scope

The source reconstructs all 68,394 original eligible edges directly from
the 480 triples and their mixed quotas. It compares every reconstructed
neighbor list with the committed domain. Among these edges, 49,320 join
disjoint signatures.

For each smallest signature \(a\), it enumerates ordered pairs \(b<c\)
among its higher disjoint neighbors and checks the remaining edge and
disjointness condition. This visits every eligible disjoint triangle
exactly once.

| Family | Eligible disjoint triangles | Negative proper minor | Negative determinant | Zero determinant | Positive determinant |
| --- | ---: | ---: | ---: | ---: | ---: |
| Plus | 1,179,048 | 0 | 10,830 | 0 | 1,168,218 |
| Minus | 1,179,048 | 0 | 0 | 0 | 1,179,048 |

The preliminary pair check reproduces twelve negative plus-family
eligible-edge minors and no negative minus-family edge minors.
None of those twelve edges lies in a triangle in this disjoint census.
There are no zero eligible-edge minors.

The forward census finishes in 4.058 seconds within its declared
60-second cooperative bound. It uses exact integers: a proved
intermediate bound below \(2^{53}\) permits exact JavaScript integer
arithmetic for the plus determinant, and the minus determinant uses
BigInt. All two-by-two minors use BigInt. The source checks the
primitive kernel hashes against the prior independent direct-inverse
audit.

The controls compare the determinant formula with a separate
six-permutation expansion on all 729 symmetric matrices whose six
independent entries are in \(\{-1,0,1\}\). They also check explicit
positive, singular, and negative examples. The complete source review
checks enumeration, scaling, the exact arithmetic bound, and the proof.

## An explicit negative block

Signatures \(0,80,288\) are
\[
\{0,2,6\},\quad\{1,3,7\},\quad\{4,12,13\}.
\]
They are pairwise disjoint. If their three exterior edges were present,
the plus Schur block, multiplied by the positive denominator 60, would be
\[
\begin{pmatrix}
782&-599&-395\\
-599&962&-439\\
-395&-439&1034
\end{pmatrix}.
\]
Its leading two-by-two determinant is \(393483>0\), but its determinant
is \(-101681640\).

The integer vector
\[
v=(642951,579903,393483)^{\mathsf T}
\]
has
\[
v^{\mathsf T}Mv=-40009996752120<0.
\]
This independently displays the violated positivity condition for the
example. Its three edges are not among the saved literal edge zeros.

## Existing literal-zero disposition

A separate exact pass checks every triangle failure against the accepted
1,884 literal prism-zero rows. It binds their edge ordering, endpoints,
variable indices and native row indices. The complete ledger retains all
zero premises for every discarded triangle.

| Disposition | Count |
| --- | ---: |
| Contains at least one accepted literal edge zero | 3,840 |
| Contains no accepted literal edge zero | 6,990 |

The disposition pass takes 0.748 seconds. It tests no other native,
selector, path, or prism implication. A retained row is therefore a
candidate addition, not a certificate that all other rows fail to imply it.

## Durable records and next step

The [complete census](../experiments/logs/root-prism-free/f0-exterior-triangle-schur-v8-census01.json)
contains all 10,830 exact determinant records and their proper minors.
The [literal-zero ledger](../experiments/logs/root-prism-free/f0-exterior-triangle-schur-literal-zero-disposition01.json)
contains all 10,830 dispositions. The
[configuration](../experiments/logs/root-prism-free/f0-exterior-triangle-schur-v8-configuration01.json)
binds exact archive and raw input identities, source, controls and limits.

The shared execution environment was unavailable. This census used the
working repository connection to retrieve committed data and a pure V8
isolate for exact arithmetic. The portable decoder checks SHA-256,
Git blob SHA-1, gzip CRC and output length. The decompressed kernel also
matches its previously recorded raw SHA-256.

The next independent replay must reproduce the complete family and the
literal-zero partition. A separate proposed calculation will inspect
all eight adjacency patterns for the 10,830 negative triangles. It may
replace some triangle covers by stronger path or edge/selector
inequalities. No such pattern census has run in this checkpoint.
