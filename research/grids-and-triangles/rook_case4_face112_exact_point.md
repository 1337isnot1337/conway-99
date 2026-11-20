# An exact positive point for the full 112-zero-face relaxation

The saved numerical basis reconstructs to an exact rational point satisfying
the complete current real selector model. Its common denominator is
145,446,009. Every one of the 1,102 surviving selectors is at least

\[
t=\frac{1,590,562}{145,446,009}>0.
\]

All 112 proved-zero coordinates remain zero. The point has total selector
mass 64, satisfies both parity unit sums and all four certified pair bounds,
and passes every original native row and coordinate cover. This proves
feasibility of the present real relaxation. It gives no binary incidence
or graph.

## Exact reconstruction

The numerical basis supplied 816 active equations \(x_j=t\). These are
assumptions used only to reconstruct one candidate. Substituting them
leaves a 287-by-287 integer system with 2,052 nonzero coefficients. Its
equations consist of 286 original native rows and the first parity unit
sum. A single exact Dixon solve, using rational FLINT arithmetic, determined
the candidate. No additional numerical optimization was performed.

The owned exact child had a fixed 60-second wall limit. It finished in
17.93 seconds, including loading, the exact solve, coordinate restoration
and the complete acceptance checks. The source caps output integer sizes
at 4,096 bits; it does not claim a cap on every internal FLINT integer.
The accepted denominator needs 28 bits and every numerator at most 27 bits.

## Complete acceptance and cold replay

Acceptance checks all 166,010 retained base rows, the 1,102 max-min floor
rows, and all variable bounds. It restores the full 1,214-coordinate vector
and directly checks all 2,271 original native rows and all 178,533 original
coordinate covers. Both proved unit sums and the four pair capacities are
also checked explicitly in the restored coordinates.

A separate fresh replay performs the same exact row checks without a
linear solve or optimizer. It passed in 18.64 seconds. The original
numerical run keeps its unresolved terminal status; this later exact
certificate is a separate artifact.

Because every surviving coordinate is strictly positive, the current
real model cannot imply any further coordinate-zero equation. Further
Boolean restrictions can still exclude this point. For example, parity
inequalities and implications obtained under exact Boolean branch
assumptions are separate restrictions and must be checked individually.

The seven already checked branch implications with guards
\(\{74,75,76,77,176,177,178\}\) aggregate to
\(\sum x_a\leq x_{535}\). This point satisfies that inequality: the two
numerators are 11,133,934 and 80,420,920, respectively. This evaluation does
not claim that all branch-derived inequalities have been tested.

## Bindings

Source `rook_case4_face112_basis_reconstruction.py` has SHA256
`6e8ac4d29fa14bf9c1ba2793a3f86c1e53854995cecb4bd30ae7e193352f3ee4`.
The complete text/AST ledger records that only proposal construction and
the point inspector changed from the earlier reviewed constructor; its
solve, watchdog and replay routines are unchanged.

The exact point is
`rook-case4-face112-basis-run01/candidate.json`, SHA256
`bb81664e8ea9faec6878ee98ec36c5ae844535e805f78fabe7c475a1f83d8ebb`.
Its `exact_check.original1214_selector_numerators` field, together with
`common_denominator`, is the full rational certificate.
