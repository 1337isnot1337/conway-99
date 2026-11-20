# Complete two-column Gram screen for component zero paired with itself

## Result and scope

The complete two-column Gram screen gives no additional exclusion for the
39-core formed by two copies of component zero with identity fiber
alignment. Every pair of distinct admissible columns that meets the
existing triple-packing condition has a strictly positive two-column
Schur determinant. There are no equality cases that could give additional
kernel equations.

This is a finite result for that core. The core belongs to the conditional
globally prism-free, $F$-free, split $18+18$ shell case. Neither
component incidence is fixed in this screen. The calculation imposes no
graph symmetry. It does not establish a graph completion or exclude the
core.

The frozen input has 480 possible triples in each component and 39,168
compatible six-neighbor columns. Compatibility means that the two
three-fiber occupancy vectors sum to $(2,2,2)$. All columns already pass
the exact kernel and one-column Gram tests described in
`root_prism_free_f0_pair_gram.md`.

## Exact criterion

Let $G$ be the residual Gram matrix of the 39-core. It has rank 33.
The saved positive integer principal quotient has inverse denominator

\[
D=4,577,040.
\]

For two range-compatible columns $h,k$, put

\[
n_h=D h^{\mathsf T}G^+h,\qquad
n_k=D k^{\mathsf T}G^+k,\qquad
t=D h^{\mathsf T}G^+k.
\]

The complete one-column screen gives

\[
2,240,036\le n_h,n_k\le3,242,772<D.
\]

Consequently $G-hh^{\mathsf T}-kk^{\mathsf T}$ is positive semidefinite
if and only if

\[
\Delta=(D-n_h)(D-n_k)-t^2\ge0.
\]

The calculation uses the inverse form on the range of $G$; it does not
require an extension of that form to equal $G^+$ outside the range.

Let $R_{ac}=2,288,520\,a^{\mathsf T}A^{-1}c$, where $A$ is the
18-component residual Gram matrix and $a,c$ are component triples. For
full columns $h=(a,b)$, $k=(c,d)$, let $p,q$ be the occupancy
profiles of $a,c$. The previously checked full-range identity gives

\[
\begin{aligned}
n_h&=2(R_{aa}+R_{bb})-D/60-(D/36)\lVert p-\mathbf1\rVert^2,\\
n_k&=2(R_{cc}+R_{dd})-D/60-(D/36)\lVert q-\mathbf1\rVert^2,\\
t&=2(R_{ac}+R_{bd})-D/60-(D/36)(p-\mathbf1)\cdot(q-\mathbf1).
\end{aligned}
\]

All quantities are integers. The independent replay uses the equivalent
homogeneous correction $D/15-(D/36)p\cdot q$, rather than the centered
profile expression.

## Complete arithmetic compression

There are 230,400 ordered pairs of component triples. Each pair is
classified by both profiles, both diagonal inverse products, its mutual
inverse product, its three-fiber intersection profile, whether its
intersection contains a quota-one Gram pair, and whether the pair is a
saved component motif conflict. These data give 36,134 exact types.
Every type retains its full multiplicity.

Two types can combine precisely when both profiles are complementary.
The resulting 33,578,176 ordered type combinations represent all
1,534,132,224 ordered full-column pairs, including 39,168 self pairs.
The multiplicity of a type combination is the product of its component
multiplicities. This is an arithmetic classification, not a quotient by
an assumed automorphism of a hypothetical graph.

Self pairs are counted separately. Swapping distinct full columns is a
fixed-point-free involution, so the nonself weighted counts divide by
two to give unordered counts. The source also checks the corresponding
transpose involution on component types.

Five flags are retained for each nonself pair: repeated component
selector, total intersection at least three, a shared local quota-one
pair, a shared cross quota-one pair, and a saved component motif
conflict. A cross quota-one pair occurs exactly when the two component
intersection profiles are nonzero in a common fiber. The result files
preserve all 32 flag combinations, both their type counts and their
weighted pair counts; no discarded category is omitted.

## Results

| Quantity | Exact count |
| --- | ---: |
| Unordered distinct full-column pairs | 767,046,528 |
| Negative two-column determinants | 866,448 |
| Negative pairs with repeated component selector | 515,232 |
| Other negative pairs with intersection at least three | 351,216 |
| Negative pairs with intersection at most two | 0 |
| Distinct pairs with intersection at most two | 721,041,624 |
| Zero determinants among those allowed pairs | 0 |
| New retained predicates | 0 |

The two attribution rows are disjoint, in the displayed order. All
negative pairs already violate the existing triple capacities. The
quota-one and motif flags are unnecessary for this conclusion.

Among all pairs with intersection at most two, the minimum determinant
numerator is

\[
\min\Delta=613,323,123,456>0.
\]

The separate self-column accounting records 38,808 columns for which
using the same column twice would fail the Gram test. Self columns are
not exported as conflicts between distinct selection variables.

## Overflow bounds and checks

The component inverse-product range is $[-342{,}896,858{,}218]$. Profile
deviations have squared norm zero or two and mutual product between
minus two and two. Before the complete census, these ranges give

\[
-1,702,148\le t\le3,610,868,
\qquad
|\Delta|\le18,499,955,409,440<2^{63}-1.
\]

The direct square bound is 13,038,367,713,424 and the positive slack
product bound is 5,461,587,696,016. The positive quotient additionally
gives $t^2\le n_hn_k$. All comparisons and counts use integer
arithmetic. The classification does not use floating point.

The native enumeration completed all 49 profile-pair groups in about
0.69 seconds. The full generation wrapper took about 8.56 seconds.
These elapsed times are descriptive and are not part of the proof.
The source preserves incremental group totals and a complete final
record.

The independent audit imports no subject builder or classifier. It
reconstructs the 39-core Gram matrix, enumerates all 816 component
three-subsets and recovers the 480-column domain, checks the integer
component inverse, independently rebuilds the types, and recomputes all
33,578,176 combinations with vectorized integer arrays. All 32 type and
weighted-count categories agree. It directly checks that the compressed
new-predicate archive is empty. Its complete replay took about 7.36
seconds.

An independent reviewer also checked the three implementations, the
type reversal and multiplicity coverage, the overflow bounds, and the
scalar arithmetic for the recorded minimum witness. That review did not
repeat the full census or independently recompute its global minimum;
those tasks belong to the separate complete integer replay above.

Small controls use an explicit positive incidence factorization and an
impossible duplicate-column downdate. No SAT solver is called. There
are no new full-39 negative-vector witnesses because there are no new
conflicts.

## Files and replay

The generator is
`experiments/workspace/root_prism_free_f0_pair_downdate.py`, with its
same-prefix `.cpp` enumerator. Exact bounds, compressed input, complete
classification, and ordinary replay are under
`experiments/logs/root-prism-free/f0-pair-downdate*`.

The separate full integer replay is
`experiments/workspace/root_prism_free_f0_pair_downdate_independent_audit.py`.
It takes a new output path, preserves the frozen existing report, and
does not execute the native classifier:

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_pair_downdate_independent_audit.py \
  --output /tmp/f0-pair-downdate-independent-replay.json --seconds 120
```

The ordinary replay checks the bound preparation, all saved coverage
totals, the empty predicate archive, and the controls. It does not repeat
the complete classification:

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_pair_downdate.py replay \
  --certificate experiments/logs/root-prism-free/f0-pair-downdate-run01/certificate.json \
  --output /tmp/f0-pair-downdate-replay.json
```

This completes the proposed two-column exclusion test for this full
domain. Higher-order Gram downdates and exterior adjacency are not
decided by the result.
