# Integer refinements of retained selector PSD directions

The exact construction produces 25 necessary linear inequalities from
eleven previously retained selector PSD directions. The other 37 held
directions have identically zero mean on the quotient, so this refinement
adds nothing to them. A complete cold replay checks the literal square
expansions, the integer shifts and every implication of a held PSD row.
No new numerical direction or optimizer run is used.

The 25 rows contain 189,283 nonzero integer terms. Their largest absolute
coefficient is 4,789,430. They have not yet been appended to a numerical
or Boolean query. No feasibility or component exclusion follows from
their construction.

## The integer inequality

Let w be an integer vector on the 480 literal selectors, and set

\[
L=\sum_a w_a x_a.
\]

Every Boolean assignment makes L an integer. Hence

\[
(L-k)(L-k-1)\geq0
\]

for every integer k. Averaging over the verified core relabelings and
expanding with `x_a^2=x_a` gives

\[
\sum_a\frac{(2k+1)w_a-w_a^2}{2}\,\overline{x}_a
-\sum_{a<b}w_aw_b\,\overline{x_ax_b}
\leq\frac{k(k+1)}2.
\]

Every displayed coefficient is integral: the product of two consecutive
integers is even. Equal quotient coordinates are combined by addition;
they are not identified as Boolean variables. The only pair-coordinate
substitutions are the 389 previously proved zeros.

This statement applies to arbitrary integer weights. Exhaustive controls
check 15,000 instances with three weights in `{-2,-1,0,1,2}`, every
Boolean assignment, and shifts from -7 through 7. The production records
use the saved 480-coordinate integer vectors.

## Relation to the held square rows

Write m=E[L] and q=E[L^2]. Every held selector direction in this finite
scope has zero constant coordinate. Its earlier PSD row is q>=0.
The shifts k=0 and k=-1 give

\[
q\geq m,\qquad q\geq-m.
\]

Their sum implies q>=0. The record checks this implication coefficient
by coefficient, including each positive primitive normalization factor.
Thus the pair of refined rows preserves the old necessary square row.
This is a refinement of the scalar square condition; strict
nonredundancy relative to every other row of the full model has not been
proved.

For 37 of the 48 held directions, the integer weights sum to zero on
each selector orbit. Therefore m=0 identically for every quotient point.
The integer-shift expression then equals `q+k*(k+1)`. Its minimum is q,
so every shift follows from the existing PSD row. These 37 directions
are recorded and skipped without another search.

The remaining eleven directions have nonzero mean coefficient vectors.
For each, the construction keeps k=-1 and k=0. It also uses the exact
minimizer `floor(m)` at the earlier Schur/path proposal when that shift
is different. This gives three extra shifts, -3, -2 and 1, for a total
of 25 rows. The complete finite scope is eleven directions with these
declared shifts. It is not the entire integer-quadratic cone.

## Exact construction and limits of the proposal

For each of the eleven directions, the source rebuilds its literal
diagonal and off-diagonal square coefficients. It then compares the
quotient square with the previously saved PSD row and its positive
divisor. Each refined row is checked independently through the identity
between its gap and `q-(2*k+1)*m+k*(k+1)`.

All 25 rows have positive exact gaps at the earlier Schur/path proposal.
That proposal already violates later PSD rows and is not claimed to be
a feasible point of the current model. These gaps select shifts and
check arithmetic; they do not prove strict improvement of the full
model or infeasibility. The invalid vector from the later timed-out
joint query is not used.

The construction compares each primitive row with every current parent
row after the 162 proved edge zeros are substituted. It also compares
the new rows with one another. All 25 are distinct in that literal
comparison. More general linear implication is outside this check.

## Records

Source `experiments/workspace/root_prism_free_f0_selector_integer_refinement.py`
has SHA256
`eb0c41c0448b43a4bd684c791d468e37b9c805c888b86383fb36b33da75560d5`.
The record `f0-selector-integer-refinements01.json.gz` has SHA256
`68d5ea0ca4a9906e74319770924eb91f880e46cec0c3ed2ab269bb1debe7b339`.
Its cold report has SHA256
`04ae2e92eb6f4f32bceb56ca67f5d1351ecd3781da288da1f7390523cfbb1958`.
Both records are in `experiments/logs/root-prism-free/`.

A separate checker reads no subject module. It reconstructs every new
literal row and exact dyadic gap, and checks all 15,200 coefficient
positions in each of the eleven held-row implications. Its report
`f0-selector-integer-refinements-independent-audit.json` has SHA256
`8a45a87eccb55fa4e5362e967ce925f38bfde25a943bb12a1a804cb4fa573cbc`.
