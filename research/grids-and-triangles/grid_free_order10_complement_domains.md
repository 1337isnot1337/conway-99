# Seven-root Boolean-complement localizers

There are 5,215 high-mask single-vertex flags over the 208 seven-vertex
root types. A residual-pair identity makes 4,478 associated complement
matrices positive sums of existing eight-root scalar matrices. The
remaining 737 cases, over 82 root types, have 1,903,068 lower entries
after their designated zero row is removed.

The complete domain ledger records all 5,215 flags, an explicit
residual-pair witness for each of the 4,478 eliminated cases, and a
sparse child transport for each remaining case. This is a mathematical
redundancy reduction. It removes no case because of a count value at a
particular point. No point was scanned in this preparation.

## The conditional matrix

Fix a labelled seven-vertex root H. Let

\[
X=(1,X_{a_1},\ldots,X_{a_m})
\]

contain its constant flag and every allowed outside neighborhood mask
of size at least three. Each X_a is binary: two distinct vertices with
the same such mask would have at least three common neighbors.

Write M₇ for the sum of XXᵀ over labelled embeddings of H. For a
selected high mask a, define

\[
C_a=\sum_\phi X_a(\phi)X(\phi)X(\phi)^T.
\]

The necessary complement inequality is

\[
L_a=M_7-C_a
   =\sum_\phi(1-X_a(\phi))X(\phi)X(\phi)^T\succeq0.
\]

Although C_a involves three free vertices before overlaps are
identified, it uses at most ten graph vertices. It is already an
explicit congruence of an existing eight-root scalar block.

If X_a=1, let v_a be its unique vertex and extend the root to H+a.
An old flag X_i becomes

\[
X_i=\mathbf1_{i=a}
 +Y_{i,0}+Y_{i,1},
\]

where the two possible child masks prescribe nonadjacency or adjacency
to v_a. Terms that violate a visible cap are absent. Every retained
child mask still has at least three root neighbors. For i=a, both
outside terms are impossible, so this row is the constant 1.

After the explicit canonical-root transport, these expressions form
a sparse matrix B_a with at most two entries per row. Its constant
row and selected-flag row both select the child constant. Therefore

\[
C_a=B_aM_8(H+a)B_a^T.
\]

No automorphism divisor occurs. Labelled embeddings of H+a correspond
bijectively to labelled embeddings of H together with the selected
vertex v_a. The fixed isomorphism to the canonical child only changes
the labels. Both caches use labelled induced embedding counts.

The selected X_a row and column of L_a are zero. The preparation
checks this coefficientwise against the two caches for all 737
retained cases: 48,785 entry comparisons pass before any count point
is substituted. Deleting that zero row preserves the PSD question.

## The quota-one reduction

For root vertices i,j, put

\[
q_{ij}=2-H_{ij}-(H^2)_{ij}.
\]

This is their number of common neighbors outside the root. If the
selected mask a contains a pair with q_ij=1, then pointwise

\[
1-X_a=\sum_{b\ne a,\ b\supseteq\{i,j\}}N_b,
\]

where N_b is the full outside class size, including masks of size two.
Every term is nonnegative. Conditioning on a chosen vertex of class b
gives the same sparse child lift and

\[
\sum_\phi N_b(\phi)X(\phi)X(\phi)^T
  =B_bM_8(H+b)B_b^T\succeq0.
\]

This identity also applies to a class that is not one of the old high
flags. The sum over child embeddings counts each choice of its vertex
once. Hence

\[
L_a=\sum_{b\ne a,\ b\supseteq\{i,j\}}
       B_bM_8(H+b)B_b^T.
\]

The right side proves redundancy from the eight-root scalar PSD
constraints and the common-neighbor identities. The ledger stores a
specific pair i,j and the complete list of other allowed masks b for
each of these 4,478 cases. The size-two mask {i,j} is included.

Every contained pair of an allowed high mask has residual quota one
or two. Thus the 737 cases left by this reduction are exactly those
whose contained pairs all have quota two. Their root vertices are
pairwise nonadjacent and have no common neighbor inside the root.
This describes the cases left by the stated reduction; it does not
claim that no further redundancy is possible.

## Complete sizing and literal control

| Quantity | Exact count |
| --- | ---: |
| Seven-vertex root types | 208 |
| Roots with a nonconstant cached base block | 203 |
| Constant-only roots retained in the ledger | 5 |
| High-mask flags | 5,215 |
| Explicit quota-one witnesses | 4,478 |
| Remaining complement candidates | 737 |
| Root types containing those candidates | 82 |
| Distinct child root types used | 183 |
| Largest parent base order | 100 |
| Largest order after deleting X_a | 99 |
| Remaining lower entries | 1,903,068 |
| Sparse conditional-product placement bound | 1,822,897 |

The last number counts child-matrix entries used by the sparse
congruences, before duplicate positions are combined. It is not a new
tensor count. Both scalar caches already exist.

A separate literal control uses a fixed cap-compatible nine-vertex
host. Its canonical root is type 102 with adjacency rows
(64,64,0,0,0,0,3). The two outside masks are 3 and 28. The absent high
flag has mask 7, and the residual-one pair is {0,1}. Its remaining
common-neighbor class has mask 3, of size two as a root mask.

The control forms the old flag vector directly from host adjacency,
then forms the selected child vector directly after transport. The
sparse child lift recovers the entire old vector. The full outer-product
identity for the redundant sum agrees entry by entry. The old vector
has two nonzero coordinates, so the check is not a zero-matrix test.
Only the specified pair quota and visible caps are used; the small
host is not asserted to be a 99-vertex graph.

## Sources and verification

Source:
`experiments/workspace/grid_free_order10_complement_domains.py`

Source SHA256:
`4961411ec0f7671abb7e34c5dbd4ec257ac98f9bffcb745a408e979751179ed8`

Complete compressed ledger:
`experiments/logs/moments-and-counts/order10-complement-domains.json.gz`

Ledger SHA256:
`67ab98b4e727c6de1a7e79fddec560942963b6c93fdc5901ede8b38dea5f2b30`

The ledger binds the small order-ten catalogue, the full seven-root
base cache, and the complete eight-root scalar cache. Replay regenerates
the direct mask census, all transports and coefficientwise zero-row
checks, and the literal control. It compares the entire ledger apart
from runtime statistics.

Generation took 1.115 seconds. The saved replay passed in 15.082
seconds. The compressed ledger is 198,551 bytes. No new product tensor,
dense reduction, eigensystem, optimizer, or count-point scan was used.
The implication for the 4,478 omitted matrices is conditional on the
existing child PSD constraints; this domain package does not certify
those constraints at the later integer count point.
