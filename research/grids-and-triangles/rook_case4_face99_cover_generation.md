# Bounded row generation on the 99-zero face

This preparation uses the complete frozen face99 selector LP. It retains
1,115 selectors and all 167,935 non-tautological rows. The 99 omitted columns
are independently proved zero. No numerical support choice, incidence
symmetry, or additional zero assumption enters the model.

The prepared max-min model introduces one variable t with 0<=t<=1 and the
1,115 rows 0<=x_j-t<=1. Every original feasible point extends with t=0.
The extended model has 1,116 variables, 169,050 rows and 11,014,288 nonzero
integer coefficients. The initial numerical prefix consists of all 1,966
native rows and the 1,115 extension rows: 3,081 rows and 28,207 nonzeros.
The complete pool contains the other 165,969 coordinate covers.

After an optimal numerical proposal, the driver scans every original and
extension row. It appends at most 512 previously inactive covers, ordered by
decreasing violation and then original row ID. A persistent solver retains
its basis. The limits remain 30 native calls, 120 cumulative solver and
existing-ray seconds, and 180 seconds for the numerical phase including
bootstrap and scans. A separate exact reconstruction stage has 60 seconds.
No numerical query is part of preparation.

An exact infeasibility certificate using a prefix is valid for the complete
model because every prefix row is an original necessary row. Dual
multipliers are expanded by zero on omitted rows before the finite-box
check. A zero max-min bound may prove a smaller face; the exact residual
and endpoint slack checks determine that conclusion. A rational point is
accepted only after all 169,050 rows and every bound pass exact arithmetic.
Restoring the 99 zero coordinates gives the full 1,214-selector vector.
This would remain a fractional incidence witness, not a binary completion
or a graph.

The new driver is a copy of the previously reviewed face81 driver with
explicit model hashes, dimensions, zero-premise bindings and scope text
changed. A separate read-only checker compares the entire source and AST
under that listed substitution map. Limits, options, numerical loop,
exact acceptance and cold transcript replay are unchanged.

The forced-upper-capacity census does not alter this model. Its 170
equalities all follow from the existing Gram equations on the same face.

## Preparation and cold replay

```sh
python experiments/workspace/rook_case4_face99_reuse_control.py --output /tmp/rook-case4-face99-reuse.json
python experiments/workspace/rook_case4_face99_cover_generation.py prepare --model experiments/logs/grids-and-triangles/rook-case4-face99-model01/model.json --arrays experiments/logs/grids-and-triangles/rook-case4-face99-model01/arrays.npz --output /tmp/rook-case4-face99-generation-preparation.json
```

The prepared query remains withheld until the source/model review gate.
No outcome is inferred from preparation or from the earlier LP attempts.
