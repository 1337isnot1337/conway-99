# An exact positive point for the complete case4 selector relaxation

The frozen case4 relaxation has an exact rational point on its proved
99-zero face. Every other selector is strictly between zero and one.
The common denominator is

\[
D=1\,661\,041\,997,
\]

and its minimum positive selector is

\[
t=\frac{17\,835\,088}{D}>0.
\]

The largest selector is \(1\,031\,155\,712/D<1\). There are exactly
1,115 positive selectors and 99 zero selectors, and their sum is 64.
The complete original 1,214-coordinate point is saved in `candidate.json`.

This proves feasibility of the current real selector relaxation. It also
rules out further forced-zero or forced-one selector coordinates from
that same relaxation. It does not give a binary incidence design,
exterior adjacency matrix, or 99-vertex graph.

## Reconstruction

The earlier bounded row-generation run saved a numerical basis. Its
1,116 nonbasic row constraints comprised 829 lower extension rows
\(x_j-t=0\) and 287 original native row bounds. The latter comprised
148 upper and 139 lower bounds. All 1,116 columns were basic.

The preparation treats these active rows as a proposal. Substituting the
829 proposed equalities leaves a 287 by 287 integer system with 2,120
nonzero coefficients. Its unknowns are 286 other selectors and \(t\).
The preparation saves every original active row ID, its selected bound,
the full coefficients, and the reduced coefficients. It also checks
15,552 small alias-substitution controls.

One fresh exact child solved this saved system using
`fmpq_mat.solve(..., algorithm="dixon")`. The rational linear solve took
0.135 seconds; the child, including input checks and full point
acceptance, took 10.985 seconds. No optimizer or alternative basis was
used. The common denominator has 31 bits; the largest numerator has
30 bits. The code limits output integers to 4,096 bits; it does not
claim a bound on all internal Flint arithmetic.

The active-row proposal is not used as a feasibility premise. Acceptance
requires exact evaluation of every original constraint, including rows
that were inactive or absent from the numerical solver prefix.

## Exact acceptance

The child and a separate optimizer-free replay both checked:

- All 169,050 rows of the extended face model and all 1,116 variable bounds.
- All 2,271 original native rows: 630 Gram positions, 186 original-signature
  capacities, 1,365 triple capacities, 30 certified pair conflicts, and
  60 uncapped exterior-row inequalities.
- All 178,533 original coordinate-cover clauses interpreted as linear
  inequalities on the unit box.
- All 1,214 original selector bounds, all 99 proved zeros, population 64,
  and strict positivity of \(t\).

The separate replay took 9.561 seconds and called neither an optimizer
nor a linear solver. Both checks use the frozen source and public input
bindings; the original full-matrix cold rebuild belongs to the preceding
face99 package. The new replay also checks the original native rows and
cover registry directly.

The saved point need not be optimal for the max-min objective. Its
positive value suffices to show that no surviving coordinate vanishes
on every point of this relaxation.

## Files and replay

The source is
`experiments/workspace/rook_case4_face99_basis_reconstruction.py`
(SHA256 `1cbeb11b23e0033fa23d10ce24aedf1585ad0119d0433f296febf722231a67b6`).
The preparation is under
`experiments/logs/grids-and-triangles/rook-case4-face99-basis-preparation01`.
The terminal result and complete point are under
`experiments/logs/grids-and-triangles/rook-case4-face99-basis-run01`.

The candidate SHA256 is
`0b627484317e65562500fbbbbd594e4a95dbfa809576fae52f6c7ccdbe7191e7`.
The terminal result SHA256 is
`3b3a27f53eb68b568c912e94d26902aa50bdca22e1e5b290afe80dd085da24f0`.
The separate replay SHA256 is
`2804da9ac0e976d7dc566b3be9cabef861ed24727221db72d4fc5da26f3a438d`.

From the repository root, write a fresh replay output:

```sh
python experiments/workspace/rook_case4_face99_basis_reconstruction.py replay \
  --preparation experiments/logs/grids-and-triangles/rook-case4-face99-basis-preparation01 \
  --directory experiments/logs/grids-and-triangles/rook-case4-face99-basis-run01 \
  --output /tmp/rook-case4-face99-basis-replay.json
```

The production query is complete and is not repeated by this command.
