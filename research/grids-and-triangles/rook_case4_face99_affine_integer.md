# Signed-integer construction for the case4 affine system

This package prepares an exact construction for the equality system on the
proved 99-zero face. No case4 rational solve has run in this preparation.
The target is a signed integer solution, with no nonnegativity or binary
requirement. Such a point would show that these equalities alone have no
integer-lattice obstruction. It would not provide an incidence design or a
graph completion.

## Complete input system

The frozen native model has 1,214 selector coordinates. Exactly 99 are already
proved zero, leaving 1,115 unrestricted coordinates for this task. We retain
every native row with equal lower and upper endpoints: 630 Gram equations
and the two empty-support exterior-row equations. After zero substitution,
236 become 0=0 and 396 distinct nonempty equations remain, with 13,706 nonzero
coefficients. No inequality is promoted to an equation because a numerical
or rational point happens to saturate it.

The saved complete-selector rational point supplies integers $N_0$ and $D$ with

\[
 A N_0=D b,\qquad D=1661041997=19\cdot601\cdot145463.
\]

Its values are only a starting feasible point. They impose no new affine
constraint. The auxiliary max-min variable is discarded.

The previous modular audit certified rank 286 and consistency at each of
19,601,145463,2,3,5,7. Those finite-field ranks do not by themselves prove
that the rational rank is 286. The construction below does not assume that
upper bound.

## A complete rational point is required before every composition

For each prime $p$ in $19,601,145463$, retain the 286 pivot columns $P$ from the
frozen modular certificate. Row reduction of the transpose of $A[:,P]$
selects 286 original equation rows $I$. Put $K=A[I,P]$. The new preparation
saves an explicit inverse modulo $p$ and checks

\[
 K V=I_{286}\pmod p
\]

using Python integers. This proves that $K$ is nonsingular over the rationals
and that $p$ does not divide its determinant. The saved transpose row
transformation gives $V$ directly; no rational inverse is calculated during
preparation.

A production step would solve $Kq=b[I]$ exactly with one right-hand side,
using Flint's Dixon solve. Set every coordinate outside $P$ to zero to form
a candidate. These zero values belong only to this candidate construction;
they are not additional forced-zero claims.

Before that candidate can be used, the program checks all 632 original
equalities in all 1,214 original coordinates, together with the 99 known
zeros. A basic solution that fails another row is recorded as UNKNOWN.
It is never an infeasibility certificate. This check also protects against
the possibility that the rational rank exceeds the observed modular rank.

Write an accepted candidate as $N_1/d$ in reduced common-denominator form.
Cramer's rule gives $d$ dividing the absolute determinant of $K$, so
$\gcd(d,p)=1$. The implementation checks that coprimality explicitly.

## Exact denominator reduction

Suppose the current accepted point is $N/D$ and the new accepted point is $N_1/d$.
Extended Euclid supplies integers $u,v$ such that

\[
 uD+vd=g=\gcd(D,d).
\]

Then

\[
 A(uN+vN_1)=g b.
\]

Thus $(uN+vN_1)/g$ is another rational point. Its full 632 original equations
are checked again. Normalizing a common factor can only reduce $g$ further.
Since $g$ divides $D$, no new denominator prime is introduced. If $p$ divided $D$,
coprimality of $d$ and $p$ removes $p$ from the denominator.

The initial denominator has just the three listed prime factors. At most
three successful basic-point solves therefore yield denominator 1. If an
earlier composition removes a later prime, that later solve is skipped.
Every accepted stage saves both rational points, both complete row checks,
the Bézout coefficients and the exact composed vector.

The final 1,214 signed integers are the authoritative certificate. Their
direct row sums establish integer affine feasibility without depending on
the construction algorithm or any rank claim. The separate standard-library
checker reconstructs all 630 Gram supports from the diagonal supports and
checks the two remaining equalities directly from the original cut data.
It imports no solver, elimination routine, or construction source.

## Bounds and failure semantics

Preparation selected three 286-square minors and checked their inverses.
The two principal int64 selection arrays occupy 1,562,704 bytes; this is an
array-size calculation, not a peak-memory claim. All modular updates have
absolute value at most 21,159,338,906. The conservative dense dot bound is
6,051,529,324,984, below $2^{63}$. Inverse replay uses arbitrary-precision Python
integers.

For a selected minor, the product of its augmented row squared norms bounds
the square of every Cramer determinant. The largest saved numerator or
denominator bound is 381 bits. Applying the extended-Euclid coefficient
bounds through all three stages gives a conservative 1,177-bit bound for
saved composed numerators. The implementation separately enforces 4,096
bits on saved integers. It makes no claim that every temporary internal
Flint integer satisfies that bound.

The proposed production invocation has one owned child with a 60-second
hard limit including imports, validation and at most three exact solves.
It also has a 3 GiB address-space limit and 20 MiB artifact limit. A timeout,
singular or failed solve, full-row mismatch, or resource refusal remains
UNKNOWN. There is no automatic retry, HNF/SNF call, or optimizer call.
A separate cold replay has a 60-second cooperative limit and performs no
linear solve.

## Preparation controls

The frozen preparation checks 1,024 extended-Euclid cases, 81 complete
rational compositions and three small modular-minor/exact-solve controls.
It rejects a candidate satisfying only its chosen minor, a singular modular
minor, a forged inverse and an oversized saved integer. An owned-child
timeout control checks termination and reaping. The equation $2x+3y=1$ yields
the signed integer control $(-1,1)$; this deliberately demonstrates the
difference from binary incidence feasibility.

The control $4x+6y=2$ has an integer solution although its modulus 2 minor
selection fails. This records that the proposed procedure is a bounded
construction attempt, not a complete integer-feasibility decision method.

The independent direct checker also replays the saved rational point and
rejects two changed vectors, including a violation of a known zero.

## Files and commands

The constructor is
`experiments/workspace/rook_case4_face99_affine_integer.py`.
Its source SHA256 is
`0ac6d9d5b5cbeeafa43626a7016db8a25172b0f5c60b09230f590fa1a78b0e30`.
The prepared minors and record are under
`experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-preparation01/`.
Preparation took 3.301 seconds; cold minor/inventory replay took 2.370 seconds.
Neither performed a case4 rational solve.

After a separate production gate, the proposed command is:

```sh
python experiments/workspace/rook_case4_face99_affine_integer.py query \
  --preparation experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-preparation01 \
  --directory experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-run01
```

The constructor's `replay` mode checks every saved stage without solving.
The independent final-vector command is:

```sh
python experiments/workspace/rook_case4_face99_affine_integer_direct_check.py \
  --point experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-run01/integer-point.json \
  --output experiments/logs/grids-and-triangles/rook-case4-face99-affine-integer-run01-direct.json
```

No production outcome is asserted by this preparation note.
