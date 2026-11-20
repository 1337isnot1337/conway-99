# Complete-row LP preparation for the 50 remaining low branches

This package prepares a stronger conditional LP for the 50 branches that
survived the smaller native-row pilot. No production solve is part of this
preparation. The zero-solve native preflight passed once, with all children
reaped.

## Exact domain

The earlier complete branch proof covers every scoped Boolean solution by
191 axis-aligned boxes. The original Gram rows 214, 344, and 582 give

\[
H_{27}+2Q=3,
\qquad
Q=x_{260}+x_{399}+x_{403}+x_{406}+x_{761}+x_{762}
  +x_{763}+x_{764}+x_{765}+x_{803}.
\]

The supports of H27 and Q overlap at column 764. Among the 191 boxes,
54 have H27 equal to one and 137 have H27 equal to three. The smaller LP
pilot excluded four of the 54 low branches with independently checked
integer row combinations. This preparation retains exactly the other 50
low branches. It makes no claim that any surviving box is feasible.

The cached matrix preserves all 167,121 rows of the accepted six-cut
extended relaxation. It appends six already proved rows: H42 at most five,
the 44-term H42 strengthening, and the four Boolean pair inequalities from
the smaller pilot. The resulting matrix has 167,127 rows and 10,769,860
nonzero coefficients. It keeps 1,102 surviving selector coordinates and
the artificial floor coordinate. The 112 previously proved zeros remain
explicit premises. The floor is fixed to zero; there is no positive floor
assumption. All 164,044 retained coordinate-cover rows remain in the exact
prefix, whose previous proof accounts for the original cover universe.

The four appended pair rows are

\[
x_{261}+x_{803}\leq1,\quad x_{262}+x_{803}\leq1,\quad
x_{339}+x_{765}\leq1,\quad x_{761}+x_{1183}\leq1.
\]

## Completed preflight

The single preflight checked every old array prefix against the accepted
exact-point bindings, appended only the six declared rows, and checked all
native coefficients and endpoints. It used bounded NumPy row getters and
made no solver call. All 50 complete column-bound resets passed, including
the fixed floor.

| Measurement | Observed value |
|---|---:|
| Measured preflight phase | 39.903844445 seconds |
| Hard-owner duration | 40.177507356 seconds |
| Peak reported RSS | 521,684 KiB |
| Native coefficient-audit blocks | 653 |
| Largest returned getter payload | 332,456 bytes |
| Cached compressed matrix | 4,662,374 bytes |
| Free disk at child completion | 794,562,560 bytes |
| Native solver calls | 0 |

The source and controls preserve an earlier tiny-control failure. HiGHS
returned a zero placeholder when the selected row had no entries. The
repaired transport accepts that placeholder only when the native count,
expected exact count, index, and value all certify an empty selection.
A nonzero placeholder is rejected. No full-matrix attempt was repeated.

## Proposed bounded pilot

The separate query configuration proposes one native matrix load and at
most one solve for each of the 50 boxes, in the frozen order. Before every
call, all 1,103 column bounds are reset and read back. No new consequence
is fed into later branches during the batch.

The limits are two requested native seconds per branch, 120 cumulative
native seconds, a 240-second forward phase under a 300-second owner, and
a separate 120-second exact replay under a 150-second owner. Lossless
compressed numerical vectors and bases have a 128 MiB transcript budget.
Every complete numerical record is durable before exact certificate work.
The numerical ray routine is called only after the solver reports that a
ray already exists. There is no extra ray solve or automatic retry.

## Exact acceptance

For a signed integer row multiplier vector lambda, the checker combines
upper endpoints for positive multipliers and lower endpoints for negative
multipliers. This gives a valid inequality g times x at most d. It then
minimizes that integer linear form over the entire saved conditional box.
Only an exact minimum strictly greater than d excludes the branch.

The certificate restores all 1,214 original coordinates. Its coefficient
vector is explicitly a representative modulo the 112 proved zero
equalities, and the artificial floor term vanishes because its two bounds
are zero. No numerical dual feasibility is assumed. The independent cold
source binds the complete prior branch cover, re-expands the three Gram
rows defining each positive guard, and checks every retained integer
combination directly.

A certified pair-guard exclusion yields its corresponding pair inequality.
A certified singleton-764 exclusion yields x764 equal to zero. If all 50
remaining low branches are excluded, the four earlier exclusions complete
the low-face rejection, giving H27 equal to three and Q equal to zero.
The 137 high boxes still prevent a whole-case exclusion claim.

The arithmetic controls cover 675 signed-combination/box cases across
27 distinct three-coordinate boxes. There are 46 contradictory
combination/box cases; this is not a count of distinct empty boxes. Separate
controls execute the actual independent cold certificate function with
positive and negative multipliers, a nonidentity coordinate map, and a
fixed floor. Seven altered gap, coefficient, endpoint, orientation, or
guard records are rejected. Binary-format controls preserve signed zero,
small and large floating values, nonfinite observations, and basis codes
exactly. None of these controls loads the case matrix or invokes an
optimizer.
