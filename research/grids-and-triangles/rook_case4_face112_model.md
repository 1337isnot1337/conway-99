# Case 4: complete selector model on the 112-zero face

This is a prepared necessary real relaxation for the fixed case-4
35-vertex core. It does not construct an integer incidence design or a
99-vertex graph. No production optimizer call was made during preparation.

## Proved restrictions and complete input coverage

The builder rechecks the complete premise loader for 112 zero columns,
the two equalities `H1 = H2 = 1`, and four pair capacities. The new zero
is column 663. Its exact proof is

\[
3x_{663}+\sum_{a\in S}x_a=2,\qquad |S|=86.
\]

Nonnegative integrality forces `x663 = 0`. The pair `(259, 590)` is
forbidden by the exact box bound `31387/16384 < 2`. The three other saved
pairs already follow from original Gram row 580. They remain explicit
for correspondence with the saved certificates. The derived 86-column
sum is not added as a separate LP row; it follows from the retained
equalities after column 663 is zero.

All 2,271 original native rows and all 178,533 registered coordinate
covers are reconstructed. The only substitutions are the 112 proved
zeros. A row is omitted only when its lower and upper bounds contain
its entire exact unit-box range. A coordinate cover is omitted when
its guard column is proved zero. Each omission has a saved witness.

The complete forward propagation and separate exact replay found no
further fixed coordinates. There are no positive-selector assumptions,
numerical-support restrictions, or symmetry identifications.

| Row family | Retained | Omitted as tautologies |
| --- | ---: | ---: |
| Original Gram equations | 396 | 234 |
| Original-signature capacities | 184 | 2 |
| Core-triple capacities | 1,320 | 45 |
| Exact Gram pair conflicts | 2 | 28 |
| Uncapped exterior-row inequalities | 58 | 2 |
| Original coordinate covers | 164,044 | 14,489 |
| Proved unit-sum equalities | 2 | 0 |
| Certified pair capacities | 4 | 0 |

The resulting base matrix has 1,102 columns, 166,010 rows and
10,767,167 nonzero integer entries. All row and variable bounds are
finite. The binary theorem `x663 = 0` and the rounded pair bound can
remove fractional points from the earlier real model; preservation
of that earlier feasible set is not claimed.

Explicit arrays transport every column and row from the published
99-zero two-cover model. Thirteen columns and 1,931 old rows are removed
by proved-zero substitution and tautology checks. The four certified
pair rows have new row origins. The two old parity rows retain their
origins and now have their proved equality bounds.

## Cold reconstruction

Preparation writes integer CSR arrays and a canonical integer-row
stream hash. The separate cold check reconstructs the entire matrix
from the original inputs and proof chain, compares every array, and
checks all original-row omission and transport records.

The matrix stream SHA-256 is
`a3201523bbd3c70bab8206808c5b004010a84006de0641965dc0cdb79cd6cb9e`.
The model is `rook-case4-face112-model01/model.json`; its cold replay
is `rook-case4-face112-model01-cold-replay.json`.

## Prepared bounded query

The proposed query maximizes `t`, with `0 <= t <= x_j <= 1` for every
one of the 1,102 surviving selectors. Its complete extended matrix has
1,103 variables, 167,112 rows and 10,769,371 nonzeros.

The initial active system contains the 1,960 retained original native
rows, both unit sums, four pair capacities and all 1,102 max-min rows:
3,068 rows and 27,942 nonzeros. All 164,044 retained coordinate covers
remain in the external pool. Every numerical candidate is checked
against that complete pool before further rows are selected.

The unchanged limits are 30 native calls, 120 cumulative solver and
existing-ray seconds, 180 numerical-phase wall seconds, at most 512
new covers per call, and at most 14,848 added covers. Exact recovery
and cold exact checking each have a separate 60-second limit. A
nonoptimal numerical call stops the generation loop.

A finite-box dual certificate from an active subset is valid for the
complete model. A proposed rational primal point is accepted only
after checking the complete extended matrix and restoring all original
coordinates. A numerical status by itself is not an exclusion or an
exact feasible point.

The exact substitution ledger checks the entire new driver against
the previously reviewed parity driver. Eighteen functions are unchanged
after three scope-string updates, including the numerical loop, bound
and primal reconstruction, and terminal replay. Fresh code covers the
new source/model bindings, the active-row partition, and the new
builder interface. Preflight binds the just-completed full cold model
instead of repeating that rebuild. Terminal exact replay still
reconstructs every input array.

The 111-face preparations and all earlier query outcomes remain
unchanged. A separate source/model gate is required before this
prepared numerical query is run.
