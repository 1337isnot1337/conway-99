# Exact native-row bounds on the 111-zero face

The bounded scan proves one further Boolean selector zero, column 663,
and one additional integer pair inequality, `x259+x590<=1`. Three other
saved pair inequalities already follow from original Gram row 580.
The proved zero total is now 112. This does not exclude case four.

The zero certificate has the exact identity

\[
3x_{663}+\sum_{a\in S}x_a=2,\qquad |S|=86.
\]

It uses 110 original Gram rows and the previously proved equality
`sum_H1 x=1`. The 38 coefficients on previously proved zero columns
are retained explicitly in the independent original-coordinate check.
Nonnegative integrality gives `x663=0`, and then `sum_S x=2`. Unit upper
bounds and numerical dual feasibility are unnecessary for this identity.

## Fixed necessary relaxation

The model starts from the original 2,271 native rows. It substitutes
the 111 proved zeros, omits 310 exact unit-box tautologies, and retains
all 1,961 other rows. It adds the two proved equalities `H1=H2=1`.
There are 1,103 variables, 1,963 rows and 25,767 nonzero coefficients.
The 178,533 coordinate covers are outside this small relaxation; the
separate complete model retains them. Every valid case-four incidence
satisfies the small model.

The two parity supports have 32 common columns, a four-column left
difference A, and a ten-column right difference B. A Boolean solution
either selects one common column, or selects one column of A and one
of B. These 32 plus 40 alternatives are a complete disjoint cover.
No graph symmetry is assumed in this split.

The fixed objective list tests these 72 patterns first, then the other
1,071 singleton selectors. For a singleton the objective must reach
one to realize that pattern. For a selected A/B pair it must reach two.
All 1,143 objective definitions are saved and independently reconstructed.

## Exact upper-bound rule

For rows `l<=A*x<=h`, unit bounds `0<=x<=1`, objective c, and any
rational multiplier vector u,

\[
c^Tx\le \sum_i u_i\begin{cases}h_i,&u_i\ge0,\\l_i,&u_i<0,\end{cases}
 +\sum_j\max\{c_j-(A^Tu)_j,0\}.
\]

The proof bounds each signed row multiplier using its appropriate
endpoint, then bounds every residual coordinate on the unit interval.
It permits arbitrary rational multipliers. A numerical solver supplies
proposals only; the complete integer calculation is the acceptance test.
A bound strictly below one proves a Boolean singleton zero. A pair bound
strictly below two proves that the two Boolean columns cannot coexist.

The helper checks 3,200 small signed-interval cases, an exact half-bound
case, and an inconsistent equality. Native transport preserves every
matrix coefficient and every bound exactly.

## Bounded numerical scan

One warm-basis simplex batch used a 60-second child budget, two seconds
per native call, and a 65-second parent deadline. It stopped at the
first interrupted or nonoptimal native return. There was no automatic
retry. The complete original row set stayed fixed during the batch;
newly certified inequalities were not fed back into this run.

The batch made 48 objective attempts: 47 numerical optimal returns and
one time-limit return. The owned child exited normally. Total parent
time was 43.994 seconds. There are five accepted exact certificates:

| Original columns | Exact saved upper bound | Boolean consequence |
|---|---:|---|
| 663 | 239/256 | Column 663 is zero |
| 259, 590 | 31387/16384 | At most one is selected |
| 259, 591 | 1 | Already implied by Gram row 580 |
| 259, 593 | 1 | Already implied by Gram row 580 |
| 259, 732 | 1 | Already implied by Gram row 580 |

These certificates exclude partition IDs 16, 32, 33, 35 and 40.
The final time-limited attempt and the unqueried suffix supply no
exclusion. This run did not exhaust the 72-pattern cover or the full
singleton family.

Requantizing the saved column-663 multiplier vector with denominator
six requires no new solver call. It gives the exact upper bound 2/3
with zero positive box correction. All residuals are zero or minus two.
Dividing the resulting equality by two gives the displayed identity
with the 86-column support. The full support and every original-row
multiplier are saved in the independent replay report.

## Verification and preserved preparations

The direct cold replay checks all five accepted certificates in 0.064
seconds without a solver. A separate checker imports none of the bound
or query code. It rebuilds all 2,271 native rows, checks every omitted
box tautology, and reconstructs both parity equalities. It checks all
1,103 coefficients in each bound and all 1,214 original coefficients
in the refined identity. It also identifies Gram row 580 as a direct
proof of the three redundant pair bounds.

Before the production batch, source review found three timing details
in the installed HiGHS wrapper. Its time limit uses an accumulated run
clock; cancellation requires registered interrupt callbacks; and its
cancellation flag persists across plain repeated calls. The final
driver offsets the clock, registers callbacks, and stops after its
first interrupt. Every earlier prepared but unrun source is preserved.
No production query was made with those earlier versions.

The initial Gram-only draft was never prepared or queried. The executed
model includes all original native row families as described above.

## Records

- Model: `experiments/logs/grids-and-triangles/rook-case4-face111-native-bounds-model01.json`,
  SHA256 `a174fde38a359f61498a0d9508beb2364ec9209f2771e9a7529a3675774008ad`.
- Exact helper: `experiments/workspace/rook_case4_face111_native_bounds.py`,
  SHA256 `df6a043f5a1f9f958536ff6c5b847b3b659c7701e609a30049b24582939ecc60`.
- Executed driver: `experiments/workspace/rook_case4_face111_native_bound_query.py`,
  SHA256 `553b6486b2ba39292b7d3fbe1dfcd37b18d63fbed30ce4bf56dcd9bd58854cfd`.
- Five certificates: `experiments/logs/grids-and-triangles/rook-case4-face111-native-bounds-run01/certificates.jsonl`,
  SHA256 `92bd55e4987b18a17359a3d9344a58f599314cb524d5c44f881fecb5c4f4ce93`.
- Refined identity certificate: `experiments/logs/grids-and-triangles/rook-case4-face111-native-bounds-663-denominator6.json`,
  SHA256 `4a808f495cc1e24a55e8979873fda659a6d82af48f521ffabb2c0873c067d30b`.
- Independent replay: `experiments/logs/grids-and-triangles/rook-case4-face111-native-bounds-independent-replay.json`,
  SHA256 `5e1e01b8c5f3c5747292d65e6938263afe7a72bfff68b00ee29cf2f41b23b2a3`.

The next Boolean formula retains the entire earlier CNF and explicitly
includes the new zero, both unit sums, the new pair inequality and the
derived sum of two. Unbranched propagation, the complete cover LP, and
the Boolean query have separate records and outcomes.
