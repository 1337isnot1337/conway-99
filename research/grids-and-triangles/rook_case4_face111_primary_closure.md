# Complete propagation on the 111-zero face

The single authorized exact closure reached a fixed point with the 111
proved zero columns and no further zero or one assignments. It found no
contradiction. A separate replay checked every reason, the complete final
fixed point, and the remaining row inventory without an optimizer.

## Premises

The direct certificate in `rook_case4_face99_parity_face.py` checks a signed
combination of 42 original Gram equations on all 1,214 coordinates. After
the earlier 99 proved zeros, the combination is

\[
\sum_{a\in H_2}x_a+2\sum_{a\in W}x_a=1,
\]

where

\[
W=\{1062,1063,1064,1065,1066,1067,
1125,1126,1127,1128,1129,1130\}.
\]

Nonnegative integrality forces every coordinate in \(W\) to be zero.
Substitution also proves \(\sum_{a\in H_2}x_a=1\). The first odd cover
remains \(1\leq\sum_{a\in H_1}x_a\leq42\). These are global necessary
conditions for the fixed local core, not branch assumptions.

The closure retains all 2,271 original native rows, both integer cover
rows, all 178,533 registered coordinate covers, and 111 explicit proved
zero rows. The signed interval and guarded-cover rules and their
sequential reason checker are the previously reviewed frozen routines.
No native presolve, failed-literal probe, numerical point or optimizer
enters this calculation.

## Preserved first preparation and exact equality change

The unrun first preparation represented both covers with bounds
\([1,42]\). It remains unchanged. The separately named `v2` source changes
only the second cover's upper endpoint to the proved value 1.

The delta controls compare all 2,384 augmented rows and the complete
cover registry. They check that row 2,272 is the only changed row, that all
111 proved unit rows agree, and that the other 2,383 rows are identical.
A small exact quota-one example checks the new propagation effect and
its independent reason replay. No first-version production closure ran.

## Terminal record

The forward closure took 0.5244 seconds. Its integrated reason and
inventory replay took 1.4284 seconds. The complete invocation, including
input proof checks, took 9.4183 seconds. The separate cold replay took
9.7278 seconds.

The trace has 111 checked assignments, all equal to the starting proved
zeros. It has no new assignment and no contradiction. The real endpoint
interpretation is relative to the augmented integer-derived premises;
it does not assert that the 12 new zeros follow from the old real LP.

| Remaining model inventory | Count |
|---|---:|
| Selector coordinates | 1,103 |
| Native and integer-cover rows | 1,963 |
| Native and integer-cover nonzeros | 25,767 |
| Registered coordinate-cover rows | 164,181 |
| All remaining rows | 166,144 |
| All remaining nonzeros | 10,785,080 |

The native inventory retains 396 Gram rows, 184 original-signature
capacities, 1,320 triple capacities, 3 Gram conflicts, 58 uncapped exterior
row inequalities, and both integer covers. The 14,352 omitted coordinate
covers have proved-zero targets. All 2,271 original native rows and
178,533 coordinate covers are accounted for by the exact projection
inventory. No new numerical model or solve is part of this package.

## Replay

From the repository root, use the installed project Python:

```sh
python experiments/workspace/rook_case4_face111_primary_closure_v2.py replay \
  --certificate experiments/logs/grids-and-triangles/rook-case4-face99-parity-face-certificate.json \
  --preparation experiments/logs/grids-and-triangles/rook-case4-face111-primary-closure-v2-preparation.json \
  --result experiments/logs/grids-and-triangles/rook-case4-face111-primary-closure-v2-run01.json \
  --output /tmp/rook-case4-face111-cold-replay.json
```

The output path must not already exist. The checker reconstructs the
proved premises and original row inventory, checks the saved sequential
trace, and verifies complete exhaustion of the listed propagation rules.
Case 4 and the Conway graph problem remain open.
