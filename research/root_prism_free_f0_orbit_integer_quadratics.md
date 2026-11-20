# Integer quadratic tests for one or two selector orbits

The complete stated family gives no new retained inequality. The scan
checks 1,764 forms: each of the 42 selector-orbit populations, all 861
two-orbit sums, and all 861 oriented differences. For each form it checks
the strongest integer shift at the saved earlier path proposal. A cold
replay reproduces every exact gap.

The sole positive gap is an existing equality consequence. Its exact
size is `15/72057594037927936`, approximately `2.08e-16`. The equality
certificate uses five rows of the current model. No row from this scan
is appended to a solver model.

## Validity and complete finite scope

For Boolean selectors and an integer signed population L,

\[
(L-k)(L-k-1)\geq0\qquad(k\in\mathbb Z).
\]

Expanding the product and replacing each selector square by the selector
gives a linear inequality in the existing selector and pair moments.
It remains valid after averaging over the twelve verified core
relabelings. The argument requires no automorphism of a completed graph.

For a positive orbit population N, the divided expansion is

\[
\sum_{a<b\in O}Z_{ab}-k\sum_{a\in O}x_a+
\frac{k(k+1)}2\geq0.
\]

For a difference L=N_i-N_j, it is

\[
P_{ii}+P_{jj}-P_{ij}-kN_i+(k+1)N_j+
\frac{k(k+1)}2\geq0.
\]

Here P denotes the sum of literal pair moments in the indicated block.
The preparation partitions all 114,960 literal pairs into the 903
unordered orbit blocks. It checks their exact sizes and substitutes only
the 389 previously proved zero pair orbits. All 9,353 surviving pair
orbits occur exactly once in those blocks.

At a fixed proposal, let m and q be the exact mean and second moment
of L. The shift polynomial is

\[
q-(2k+1)m+k(k+1).
\]

Its difference between consecutive shifts is `2*(k+1-m)`. Therefore
`k=floor(m)` minimizes it over every integer shift. The scan covers all
integer shifts for each of its 1,764 forms through this exact minimizer;
it does not cover arbitrary integer coefficient vectors.

The proposal is the saved optimal numerical output of the earlier
Schur/path model. Its hexadecimal coordinates are evaluated as exact
dyadic rationals. It is not asserted to satisfy the current joint model.
No optimizer or eigensolver runs in this package.

## Exact redundancy of the only candidate

The candidate uses L=N_6+N_7 and k=3. The union has 24 literal selectors.
The original Gram rows at component pairs `(0,5)`, `(1,3)` and `(2,4)`
have disjoint eight-selector supports whose union is exactly this set.
Each has quota one, so their sum gives L=3.

Multiply those three equations by each of the 24 selectors in the union
and add the resulting 72 original RLT equations. Boolean diagonal
identification gives

\[
R=L^2-3L=2P-2L=0.
\]

The candidate's signed residual is exactly

\[
3L-P-6=2(L-3)-R/2=0.
\]

After quotienting and the proved zero substitutions, this combination
uses five retained parent equations. Both the direct checker and a
separate checker compare all 15,200 coefficients and the right side.
The separate checker also reconstructs the three original supports and
all 72 lifted products without importing the subject source.

## Records

- `experiments/workspace/root_prism_free_f0_orbit_integer_quadratics.py`
  prepares and scans the complete finite family.
- `f0-orbit-integer-quadratics-preparation01.json.gz` has SHA256
  `9c12695392afa42019cc365326645863d704ad10ffce6c77443236ca3edf72be`.
- `f0-orbit-integer-quadratics-scan01.json.gz` has SHA256
  `5491abae33fb6faa79b006fe8b789df801ad289ec42167d3c53ec9041627aa51`.
- Its cold report has SHA256
  `9310202c7a4da85862615f78514e24e100119311080b8fcfa8fe6f2af65313fe`.
- The direct redundancy report has SHA256
  `495eec0bde8b61da031b10a8fe0657df72bf1822f7e04d639e74480fc9cdc88b`.
- The independent redundancy audit has SHA256
  `dca80561bc6955459aa27427da898af38e63b7ed5c223a5b7d3dab4231a9c4d0`.

The data records are in `experiments/logs/root-prism-free/`. This finite
negative result does not establish integer moment feasibility or exclude
component zero.
