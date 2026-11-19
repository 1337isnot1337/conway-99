# Complements from complete visible pair incompatibility

The complete visible pair-incompatibility graphs have 5,379 maximal
cliques across the 208 seven-vertex root types. The shared-quota-one
identity removes 1,553 cliques, and five roots have only the constant
flag. The remaining 3,821 cliques reduce to 811 root-automorphism
orbits. Their quotients have 1,184,175 lower entries, with largest
order 84.

This is an exact domain preparation. It constructs no count matrix
and does not test a count point. The earlier 711-representative
intersection-clique scan is preserved as a completed no-separator
result, without an exact PSD-feasibility claim.

## Complete pair criterion

Fix a labelled seven-vertex root H. Its allowed high masks are the
outside neighborhood masks of size at least three whose one-vertex
extension satisfies every visible cap

\[
(A^2)_{ij}+A_{ij}\leq2.
\]

Each corresponding class size X_a is binary. For distinct allowed
high masks a,b, set S=a∩b. Their two classes are visibly incompatible
exactly when either

1. S has at least three vertices; or
2. S contains a root pair i,j with residual quota
   \(q_{ij}=2-H_{ij}-(H^2)_{ij}=1\).

The first obstruction gives three common neighbors to the two outside
vertices. The second uses the single remaining common-neighbor slot
of a root pair twice.

If neither obstruction occurs, put no edge between the two outside
vertices. Every root pair has enough residual quota: a pair used by
both masks has quota two, and a pair used by one mask already passed
the one-vertex test. A root/outside pair gains no common neighbor from
the other outside vertex, because their mutual edge is absent. The
two outside vertices share at most two root neighbors. These exhaust
all pairs, so the resulting two-vertex extension satisfies every cap.

The criterion is complete for these visible pair caps. It does not
assert that a cap-compatible pair extends to an SRG(99,14,1,2), or
that it passes every spectral or higher-order constraint.

The program checks both mutual-edge choices directly for every
distinct pair of high masks, using literal adjacency matrices. All
104,854 pairs agree with the criterion. There are 10,998 pairs for
which both edge values are allowed, 60,980 allowing only mutual
nonadjacency, and 32,876 allowing neither. No pair permits only the
mutual edge, as expected from monotonicity of the caps.

The earlier intersection-only graphs have 24,167 edges. The complete
visible criterion adds 8,709 edges arising from residual-quota-one
pairs in intersections of size two.

## Localizers and coefficientwise zero rows

Let X contain the constant and every allowed high flag. For a clique C
in the complete visible graph, its class sum is binary:

\[
Z_C=\sum_{a\in C}X_a\in\{0,1\}.
\]

Hence the necessary localizer is

\[
L_C=M_7-\sum_{a\in C}B_aM_8(H+a)B_a^T\succeq0.
\]

The sparse child lift B_a and its labelled normalization are unchanged
from the [previous clique construction](grid_free_order10_complement_cliques.md).
No automorphism divisor occurs. The unique selected vertex is a
specified eighth root vertex.

When a and b are newly incompatible, the selected vertex of class a
already occupies a root pair's only remaining common-neighbor slot.
No outside vertex of class b can occur in the child root. Thus row b
of B_a is empty, just as for an intersection of size at least three.

The preparation reconstructs all 5,215 high-mask lifts. It compares
all 1,965 previously stored lifts exactly and checks 65,752 directed
incompatibility rows are empty. This includes all 17,418 directed rows
created by the 8,709 new edges.

The individual selected-row identities reuse the frozen coefficientwise
check of all 5,215 high masks against the parent and child tensors:
220,138 entries were checked there before any count substitution.
Together with the newly checked empty rows, those identities prove
that every clique-selected row vanishes coefficientwise. The current
maximal-clique ledger has 62,929 such row instances.

If every member of C contains one common residual-quota-one pair,
the localizer is a positive sum of child congruences over the other
allowed classes containing that pair. The sum includes the size-two
class. This redundancy uses the SRG common-neighbor identities and
the complete child PSD family. It is not a consequence of child PSD
with unrelated matrix entries. The full witnesses are saved for all
1,553 removed cliques.

## Two complete clique enumerations

The first enumeration is bitset Bron–Kerbosch. The second adds vertices
one at a time. Suppose all maximal cliques of the old graph are known
and a new vertex v is added. Form the candidates

\[
C\quad\text{and}\quad\{v\}\cup(C\cap N(v))
\]

for every old maximal clique C, then retain the inclusion-maximal
candidates. This procedure is complete. A maximal new clique omitting
v is an old maximal clique. If it contains v, extend its remaining
vertices to an old maximal clique C. The new clique is contained in
{v}∪(C∩N(v)), so maximality makes them equal. Starting with the empty
clique also handles empty and isolated-vertex domains.

The two independently implemented enumerations agree for every root.
Every returned clique is then checked for pairwise adjacency and
maximality against the direct literal-extension graph. The largest
intermediate family in the incremental enumeration has 477 cliques.

All five constant-only roots are retained. Each of the old 7,189
intersection cliques has an explicit containing maximal clique in
the new ledger. This proves coverage of the previous family using
positive conditional matrices. All 530 residual-two triple groups
remain maximal cliques: their triple mask itself can only be
incompatible with a mask containing that triple, because its three
root-pair residuals are all two.

## Root orbits and workload

The preparation again enumerates every degree-preserving root
permutation, checks adjacency, and compares the full resulting group
with the closure of the frozen generators. Every generator preserves
the new visible graph and the clique classification. Explicit root
transports cover all 3,821 retained cliques in 811 orbits.

This quotient only relabels the complete set of labelled root
embeddings. It assumes no automorphism of the unknown 99-vertex graph.
The same relabeling gives a congruence of the localizer matrices and
preserves their labelled induced-count forms.

| Quantity | Exact count |
| --- | ---: |
| Seven-vertex root types | 208 |
| High-mask pairs checked | 104,854 |
| Literal two-vertex edge choices checked | 209,708 |
| Complete visible incompatibility edges | 32,876 |
| Added quota-one edges | 8,709 |
| Maximal cliques | 5,379 |
| Constant-only cases | 5 |
| Shared-quota-one redundant cliques | 1,553 |
| Remaining cliques | 3,821 |
| Roots containing remaining cliques | 111 |
| Retained triple groups | 530 |
| Root-automorphism orbit representatives | 811 |
| Largest representative quotient order | 84 |
| Representative quotient lower entries | 1,184,175 |
| Conditional lifts needed by representatives | 1,575 |
| Sparse conditional lower-entry products, upper bound | 1,142,836 |
| Full-matrix conditional subtractions | 48,025,175 |
| Retained lower-entry conditional subtractions | 15,927,083 |

Per-root conditional caching requires at most 636,801 matrix object
cells, including two working matrices. At an illustrative 64 bytes
per cell, this is 40,755,264 bytes in addition to sparse cache and
process overhead. This is a sizing estimate, not a runtime memory
guarantee. The preparation itself took 14.51 seconds and reached
198,340 KiB resident memory under a 30-second bound.

## Frozen source and ledger

Source:
`experiments/workspace/grid_free_order10_complement_visible_domains.py`

Source SHA256:
`d89248dce73849059afa12cf1c731f31dcafa8a0769ccde3b25574c67ec4c54a`

Ledger:
`experiments/logs/moments-and-counts/order10-complement-visible-domains.json.gz`

Ledger SHA256:
`b273c84d939cefbe61cfbb2ed77721fd81c9f9c61a203d9fdbe17e674e453d10`

The ledger binds the earlier full coefficientwise proof, root group
ledger, literal cap checker and small catalogue. Its replay repeats
both literal edge choices, both clique enumerations, all new empty-row
checks and the complete orbit partition. No point, product tensor,
dense reduction or optimizer is used.
