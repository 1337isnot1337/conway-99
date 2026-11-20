# Case4 transportation closure: twelve more zero columns

The complete transportation closure proves twelve additional attachment
columns absent. It does not exclude case4. The exact run and replay use no
LP or SAT optimizer.

The first stage, using only Gram equations and nonnegative weights, recovers
the same 70 zero columns proved previously. The second stage, adding triple
capacities and selector upper bounds, reaches 88 zero columns. Six of those
18 additional zeros were already proved by the published
[two-Gram-plus-triple certificate](rook_case4_triple_saturation_face.md).
The other twelve are

```
101 115 121 126 133 140 145 149 788 793 799 804
```

The 88 transportation zeros overlap the 14 previously proved empty-cover
units in exactly three columns: 352, 354 and 957. Their union has 99 columns.
The transportation run itself does not use the empty-cover units as premises.

## Three short deductions

Let \(C_{ij}=\sum_{h\supseteq\{i,j\}}x_h\), and define \(C_{ijk}\)
in the same way. Pair sums have their literal Gram quotas; triple sums have
upper bound one. All weights below need only be nonnegative real numbers.

The following three expressions have upper bound zero:

\[
\begin{aligned}
C_{12,27}-C_{8,27}+C_{8,13,27}&\le1-2+1=0,\\
C_{13,27}-C_{8,27}+C_{8,12,27}&\le1-2+1=0,\\
C_{14,27}-C_{7,27}+C_{7,11,27}&\le1-2+1=0.
\end{aligned}
\]

Expansion on all 1,214 original columns gives coefficients in
\(\{-1,0,1\}\). For the first two expressions, the only negative
coefficients are on the six already published zero columns
1021, 1027, 1034, 1041, 1054 and 1061. The first expression forces
101, 115, 121 and 126 to zero; the second forces 133, 140, 145 and 149
to zero. Their other positive terms were already known to vanish.

For the third expression, all 21 negative terms are among the 70 Gram-only
zeros. Its positive terms are exactly 788, 793, 799 and 804. They therefore
vanish as well.

The standalone checker
`experiments/workspace/rook_case4_transportation_short_faces.py` verifies
these identities without calling the transportation code. It first rechecks
the old three-row and four-row Gram proofs, then the published triple
saturation, and finally these three deductions. It rebuilds all 630 Gram
and 1,365 triple supports and records every coefficient and earlier-zero
premise. No selector upper bound is needed by these six short proofs.

## Complete projected check

The main closure checks all 35 core vertices and all three pairs of grids,
as specified in [the preparation note](rook_case4_transportation_faces.md).
It takes two sweeps in each stage: 420 exact flow calls in total. Every
nontrivial proof comes from the R/S projection at core vertex 27. The other
projections remain part of the coverage and final fixed-point checks.

The forward run finished in 1.373 seconds. A separate 1.343-second replay
checked all six recorded signed-row certificates, their prior-zero
induction, and all 210 terminal projection flows. Every remaining cell in
each terminal projection can be positive in some flow of that projection.
This does not imply simultaneous feasibility of the attachment model.

Frozen results:

- `rook-case4-transportation-faces-run01.json`: full trace and terminal flows.
- `rook-case4-transportation-faces-run01-replay.json`: exact complete replay.
- `rook-case4-transportation-short-faces-certificate.json`: six short full-domain
  identities, independent of flow discovery.
- `rook-case4-transportation-short-faces-replay.json`: standalone identity replay.

All four are under `experiments/logs/grids-and-triangles/`. The complete
artifact list is in `rook-case4-transportation-terminal-manifest.json` in
the same directory. A continuation with the 99-zero union is a separate
model and is not part of this run.
