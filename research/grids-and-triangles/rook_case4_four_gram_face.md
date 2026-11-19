# A four-row Gram face in indexed case4

The bounded row-generation run stopped after one native call, in 1.716 seconds.
It added no cover rows. An exact certificate forced 23 previously free selectors
to zero. The complete matrix reconstruction and exact certificate replay passed.
This reduces indexed case4; it does not exclude that case or resolve the graph
existence problem.

The numerical max-min device is unnecessary for the resulting proof. The
following relation uses only the complete 35-core Gram equations and
nonnegative column weights.

## Direct identity

Let `h_a` be the 35-coordinate attachment column with original index `a`, and
let `x_a >= 0` be its weight. The complete domain has 1,214 columns. Its equations
are

\[
\sum_a x_a h_a(i)h_a(j)=G_{ij}.
\]

The existing three-row relation

\[
G_{3,27}+G_{4,27}-G_{17,27}=1+1-2=0
\]

has coefficient one on the previously certified 46 columns and coefficient
zero elsewhere. It proves that all those 46 weights vanish over the
nonnegative real Gram system.

Now take

\[
G_{6,27}+G_{7,27}-G_{11,27}-G_{14,27}=1+2-2-1=0.
\]

Its column coefficient is

\[
h_a(27)\bigl(h_a(6)+h_a(7)-h_a(11)-h_a(14)\bigr).
\]

The complete exact domain check gives only coefficients `-1`, `0` and `1`.
There are 25 negative positions, all among the old 46 zero columns. The 24
positive positions are:

```text
772 779 783 809 816 822 828 841 848 923 926 928
931 934 937 941 955 957 959 963 966 970 973 977
```

After the negative terms vanish, the new equation is a sum of 24 nonnegative
weights equal to zero. Every listed weight therefore vanishes.

This gives 70 Gram-only zeros in total. Column957 was also already known to be
zero from a coordinate-cover unit. Relative to the full selector model's 58
fixed zeros, the identity gives 23 new zeros and brings the total to81.

Adding the old three-row relation directly to the new four-row relation gives
a single seven-row certificate with right-hand side zero and nonnegative
coefficients on all1,214 columns. Exactly45 coefficients are one. This is an
alternative proof that does not require a numerical dual or any max-min
extension row.

## Exact verification and scope

`rook_case4_four_gram_face.py` reads only the hash-bound native inventory. It
reconstructs all630 Gram supports from the35 diagonal supports, checks all1,214
coefficients of both relations, and replays the zero implication. The checker
uses the Python standard library. It imports no optimizer and uses no coordinate
covers, exterior-row cuts, integrality or symmetry assumptions.

The earlier max-min certificate is preserved independently. Its15 nonzero
multipliers refer to the four native rows and11 max-min extension rows. The
separate cold replay regenerated the complete174,208-row selector model and
checked the lifted exact bound against the full extended domain. It did not
accept the numerical proposal as an exact feasible point.

The saved numerical proposal and basis remain available for later
artifact-only reconstruction. The numerical full-row residual was small, but
that observation is not a rational feasibility certificate.

The next operation is deterministic exact propagation from the81 proved zeros
through the original native rows and complete cover registry. No second
optimization is part of this checkpoint.
