# Both parity sums equal one

On the proved 111-zero face of case 4, both parity supports have sum one
in every nonnegative integral incidence:

\[
\sum_{a\in H_1}x_a=\sum_{a\in H_2}x_a=1.
\]

The second equality follows from the previously checked 42-Gram-row
identity and its twelve forced zeros. The first equality uses one
original signature capacity and the existing 33-Gram-row parity proof.
It requires no new optimizer or parity search.

## The first equality

After removing the proved zeros, \(H_1\) has 36 coordinates and \(H_2\)
has 42. Their intersection \(C\) has 32 coordinates. Their differences
are

\[
A=H_1\setminus H_2=\{259,260,261,262\},
\]

\[
B=H_2\setminus H_1=
\{590,591,592,593,594,595,730,731,732,733\}.
\]

Original-signature capacity row 51 belongs to original signature 96.
Its support is \(\{258,259,260,261,262\}\), with upper bound 1.
Coordinate 258 is already proved zero, so \(\sum_Ax_a\leq1\).

Since \(\sum_{H_2}x_a=1\),

\[
\sum_{H_1}x_a=1+\sum_Ax_a-\sum_Bx_a\leq2.
\]

The sum is nonnegative. The checked 33-row integer Gram combination has
right-hand side 45 and gives

\[
2\sum_a q_a x_a+\sum_{H_1}x_a=45,
\qquad q_a\in\mathbb Z_{\geq0},
\]

after all 111 zero substitutions. Thus the first support sum is odd.
The only nonnegative odd integer at most 2 is 1. Subtracting the two
equalities also gives \(\sum_Ax_a=\sum_Bx_a\leq1\).

The standalone checker reconstructs all 33 original row coefficients on
all 1,214 original coordinates, the capacity row, the support differences,
and the earlier proof of the 111 zeros and the second equality. The new
statement strengthens the real relaxation by a necessary integer
condition; it does not assert preservation of the old real feasible set.

## A complete 72-pattern partition

The two equalities give a finite disjoint partition of possible integral
assignments on \(H_1\cup H_2\):

| Type | Required selected coordinates | Number |
|---|---|---:|
| Common singleton | One coordinate from \(C\) | 32 |
| Difference pair | One coordinate from \(A\) and one from \(B\) | 40 |

Every other coordinate in the 46-coordinate union is zero in the
specified case. The 1,057 surviving coordinates outside the union remain
free subject to the full original incidence constraints.

For completeness, adding the two support equalities bounds the selected
population in their union by 2. The partition checker enumerates every
subset of that union of size 0, 1 or 2, for 1,082 exact checks. Exactly the
32 singletons and 40 pairs satisfy both equations. It saves all 72 complete
assignments on the union and verifies their disjointness. No branch is
claimed feasible, and no branch query ran.

## Artifacts and scope

The proof source is
`experiments/workspace/rook_case4_face111_two_parity_equalities.py`.
Its certificate and separate replay are under
`experiments/logs/grids-and-triangles/rook-case4-face111-two-parity-equalities-*`.

The partition source is
`experiments/workspace/rook_case4_face111_parity_partition.py`.
Its complete case ledger is
`experiments/logs/grids-and-triangles/rook-case4-face111-parity-partition-certificate.json`.

The independent review checks the 33- and 42-row identities, every
coefficient and support link, and the capacity deduction. It does not
rerun an optimizer. The new equalities and partition leave case 4 open.
