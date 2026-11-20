# Native equalities on the case4 zero face

The complete seven-prime audit found no inconsistency and no
single-coordinate congruence in any of the tested fields. In each field,
the native equality matrix has rank 286 and nullity 829. This gives no new
binary zero or one, and case4 remains open.

## The exact affine domain

The domain consists of all native rows whose lower and upper bounds are
equal, after substituting the previously proved 99 zero coordinates.
There are 632 such rows: all 630 Gram positions and two empty-support
exterior-row cuts. Their complete original-row provenance is retained.
Exactly 236 rows become the identity zero equals zero. The other 396 rows
are distinct and have 13,706 nonzero coefficients on the 1,115 surviving
variables.

No inequality or binary constraint is converted into an additional
equality. No newly proposed zero is assumed. The auxiliary max-min
coordinate, the active numerical basis, and the values of the saved real
point are absent from the affine system.

The inventory replays the complete 99-zero proof and checks the saved
rational point against all 2,271 original native rows. Its denominator is

\[
1661041997=19\cdot601\cdot145463.
\]

Complete trial division verifies that the three factors are prime. For
every prime not dividing this denominator, reducing the rational point
using the inverse denominator proves affine consistency over that field.
In particular, the inventory stores and checks such points for 2, 3, 5,
and 7. Those primes can still reveal a coordinate congruence relevant to
binary solutions. A prime-field inconsistency can occur only at a prime
dividing the verified denominator.

## Certificates and arithmetic

The single bounded batch processed primes 19, 601, 145463, 2, 3, 5, and 7
in that order. It completed in 5.604890 seconds. No result from an earlier
prime was substituted as a new premise for a later prime.

Exact modular row operations use signed 64-bit NumPy arrays. Each array
entry is reduced into the interval from zero to the prime minus one.
The largest planned update bound is 21,159,338,906, and the conservative
dense dot-product bound is 8,379,040,603,824. Both are below the signed
64-bit limit. No floating-point matrix operation is used.

Each prime certificate contains the pivot columns, the 286 reduced
augmented rows, and an explicit combination of the 396 input equations
for each reduced row. A separate verifier uses Python integers and no
row-reduction routine. It checks both inclusions:

1. Every saved reduced row is the claimed combination of input rows.
2. Every input row is exactly the combination of reduced rows given by
   its coefficients at the pivot columns.

The second check is essential. It verifies the entire row space and
therefore the rank and completeness of the coordinate-congruence test.
A coordinate is fixed throughout the affine solution set precisely when
its pivot row has no other nonzero variable coefficient. No such row
exists in these seven certificates. Each certificate also supplies a
directly checked modular point, obtained by setting free coordinates to
zero.

Any discovered contradiction or fixed coordinate would be expanded back
over all 1,214 original coordinates, with every nonzero coefficient at a
removed coordinate justified by the known-zero proof. No such conclusion
was produced in this run.

The separate cold replay passed in 3.076707 seconds. It checked every
stored row-space certificate and every original-coordinate conclusion
without repeating elimination. The preparation controls covered 512
small matrix systems with 8,960 complete field assignments, 42 additional
signed-coefficient, large-prime and empty-system controls, and rejection
of a deliberately altered certificate.

## Results and limits

| Prime | Rank | Nullity | Fixed coordinates | Consistent |
|---:|---:|---:|---:|:---|
| 19 | 286 | 829 | 0 | Yes |
| 601 | 286 | 829 | 0 | Yes |
| 145463 | 286 | 829 | 0 | Yes |
| 2 | 286 | 829 | 0 | Yes |
| 3 | 286 | 829 | 0 | Yes |
| 5 | 286 | 829 | 0 | Yes |
| 7 | 286 | 829 | 0 | Yes |

This closes the stated finite prime-field test. It does not prove that
the affine system has an integer solution, that its rational rank is 286,
or that binary incidences exist. Agreement of ranks over finitely many
fields is not a rational-rank certificate. Higher prime powers and the
integer column lattice were not tested. The binary bounds and remaining
inequalities can still conflict with an affine solution.

The result is
`experiments/logs/grids-and-triangles/rook-case4-face99-affine-modular-run01/result.json`,
SHA-256
`e45439adddd20ddf8ec564ffe7eae3a733475ca1e281998fe42f7133b9779f7a`.
The separate replay is
`experiments/logs/grids-and-triangles/rook-case4-face99-affine-modular-run01-replay.json`,
SHA-256
`0bf5fb3687db3fd81a5cf270cc6b30666f1c22c7318878f201d7720f8abf29b0`.
All seven compressed certificates are retained beside the result. The
terminal manifest binds the inventory, source, controls, result, and
replay. No optimizer, SAT solver, rational elimination, HNF, or SNF was
called by this package.
