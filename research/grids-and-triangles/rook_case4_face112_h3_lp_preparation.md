# Complete case4 selector LP with the third parity cover

This preparation appends one necessary integer-incidence inequality to the
complete 112-zero-face selector relaxation. It introduces no further fixed
selector, support restriction, or symmetry assumption. The production query
has not been run.

## The appended inequality

Let (H_3) be the sum of the following 27 original selector coordinates:

```
23, 45, 123, 260, 339, 401, 402, 405, 539,
590, 591, 592, 593, 594, 595, 764, 780, 781, 782,
800, 801, 802, 1175, 1176, 1177, 1180, 1183
```

The five original Gram rows 124, 214, 320, 344, and 582 each have quota one.
Their sum has right side five. After substitution of already proved zeros,
its odd-coefficient support is exactly the list above. Nonnegative integer
selectors therefore satisfy (H_3\geq1).

The direct certificate additionally proves, on the same face and using the
two previously proved unit sums,

\[
H_3=1+2(U-x_{803}),\qquad
U=x_{401}+x_{402}+x_{405}+\sum_{a=590}^{595}x_a.
\]

A second exact Gram/unit-sum identity expresses (1-U) as a sum of twelve
nonnegative selector coordinates. Thus (U\leq1) and (H_3\leq3). The lower
bound is equivalent to the ten-term inequality (x_{803}\leq U). The model
retains the original 27-term cover and gives it the certified range

\[
1\leq H_3\leq3.
\]

The upper side follows from existing real constraints. The lower side uses
integrality and strengthens the previous real relaxation. No additional
coordinate zero follows from these identities alone in this package. The
full 1,214-coordinate expansions and the precise prior-zero dependencies
are in `rook-case4-face112-third-parity-cover-certificate.json` and its
separate replay. In particular, zero 663 is not needed by this cover proof.

The saved exact point of the previous model has

\[
H_3=\frac{121793213}{145446009}<1.
\]

The exact gap is (23652796/145446009). This supplies a concrete reason to
query the strengthened model once.

## Complete model and row inventory

The builder `rook_case4_face112_h3_model_v2.py` retains every integer array
entry of the previous 166,010-row model as an exact prefix. It appends row
166010, with 27 coefficients equal to one and bounds [1,3]. The existing
column ordering and all prior row-origin mappings are preserved.

| Inventory | Count |
|---|---:|
| Original optional columns | 1,214 |
| Previously proved zero columns | 112 |
| Remaining selector variables | 1,102 |
| Retained original native rows | 1,960 |
| Retained original coordinate covers | 164,044 |
| Previously proved unit-sum equalities | 2 |
| Previously certified pair capacities | 4 |
| New H3 row | 1 |
| Complete base rows | 166,011 |
| Complete base nonzeros | 10,767,194 |

The cold reconstruction rebuilds the original inputs, all face substitutions,
and every parent row, then replays the direct H3 proof and compares every
stored array. The integer stream is
`0e200a4ed28e0ac7b415c3c886704af512d3a1346a33ff6bfb8a9da3fad53c0a`.
The compressed array file has SHA256
`4e2de2786d3036cf995953791192500cb4aaa5b0c5079f3d97ea465a4cf64e46`.

The first, unqueried preparation remains preserved. Its inherited metadata
counted four rows without a previous99-row origin, although H3 adds a fifth.
Version 2 changes that metadata count to five and checks it on load. The
matrix, bounds, all other metadata, and compressed array bytes are unchanged.
The separate correction record identifies both source hashes.

## Bounded query and exact acceptance

`rook_case4_face112_h3_cover_generation.py` reuses the audited complete112
generation algorithm. A full text-substitution ledger accounts for the new
bindings and dimensions; 17 functions are AST-identical. Four functions
change input/definition metadata, and two further functions change only
scope descriptions. The numerical loop and exact arithmetic are unchanged.

The max-min extension adds one variable (t), with

\[
0\leq x_a-t\leq1,\qquad 0\leq t\leq1,
\]

for each of the 1,102 surviving selectors. Every feasible original point
extends with (t=0). The complete extension has 1,103 variables, 167,113
rows, and 10,769,398 nonzeros.

All native rows, both unit sums, four pair capacities, H3, and the max-min
rows start active: 3,069 rows and 27,969 terms. The exact same 164,044-cover
pool remains available. A numerical point is scanned against every row;
each iteration can add at most 512 violated original cover rows.

The planned single batch retains the existing limits: at most 30 calls,
120 cumulative solver/existing-ray seconds, 180 numerical-phase seconds,
one worker, 60 seconds for exact reconstruction, and 60 seconds for the
cold exact acceptance check. No retry or larger cut family is included.

A numerical infeasibility is unresolved unless a finite-box certificate
passes exact arithmetic. A certificate supported on an active subset is
valid for the full model because the active rows are original model rows.
A rational primal point must pass the entire 167,113-row matrix and all
unit-box bounds. A positive max-min point would certify only the real
selector relaxation; it would not supply a binary incidence or a graph.

Preparation and native assembly controls call no optimizer. The production
query remains subject to the separate source/model gate.
