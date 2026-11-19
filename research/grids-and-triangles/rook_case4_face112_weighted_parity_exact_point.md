# Exact point after the two weighted parity cuts

The complete 112-zero-face selector relaxation, including both new weighted-parity consequences, has an exact rational point. This is a real relaxation witness. It is not a Boolean incidence or a Conway99 graph.

The common denominator is 337,510,679. The max-min coordinate is
`t = 3,684,393 / 337,510,679 > 0`.
Every one of the 1,102 surviving selector coordinates is at least t. The 112 previously proved zeros remain zero.

## Reconstruction and acceptance

The preceding numerical run remains frozen as UNRESOLVED. It supplied one valid numerical basis and no accepted exact result. This separate computation used that saved basis only; it made no optimizer call.

The reconstruction identified 813 candidate equations x_j = t and a 290 by 290 integer residual system with 2,087 nonzero entries. The aliases and active-row choices are proposed point constraints, not universal consequences. The residual system includes the active H1 equality, H3 lower endpoint and the new 50-term parity cover lower endpoint. The 48-term rounded-capacity row is retained in final acceptance even though its endpoint was not selected.

Exactly one FLINT Dixon solve took 0.210 seconds. The owned child, including imports and full acceptance, took 14.02 seconds and terminated within its 60-second limit. The denominator has 29 bits; no bound on every internal elimination integer is claimed.

The separate cold arithmetic replay took 12.995 seconds. It called neither an optimizer nor a linear solver. It checked all of the following from the frozen rows and candidate:

- All 167,115 rows of the complete extended model and all 1,103 extended variable bounds.
- All 2,271 original native constraints and all 178,533 original coordinate covers.
- All 1,214 original selector coordinates, the 112 certified zeros and population 64.
- Both parity equalities, all four certified pair bounds, the original 27-term H3 support and both newly appended original-coordinate rows.
- Strict positivity of t.

Thus no further coordinate can be identically zero throughout this particular real relaxation. Boolean consequences may still strengthen it.

## Immutable records

The source is `experiments/workspace/rook_case4_face112_weighted_parity_basis_reconstruction.py`, SHA-256
`7668aeb593bb46644a233b4cbfeb7663743c67529105003a0ece62d28fbbed6c`.
The reuse ledger records 20 explicit substitutions and 12 unchanged function ASTs. The root source gate is
`rook-case4-face112-weighted-parity-basis-root-review.json`, SHA-256
`7139a03ab92c0333bb95d1638e12b7e108fd1d53e703b19b4d3823cbe0eb8c83`.

The candidate is
`experiments/logs/grids-and-triangles/rook-case4-face112-weighted-parity-basis-run01/candidate.json`,
SHA-256 `3cd4d391e5b372f6ff0d2df11ebd16fccec1b7122527864fef76e33eae72312b`.
It stores every rational coordinate using exact decimal-string integers. The candidate's original pending-replay status is preserved; the adjacent separate replay report is the completed acceptance record.

The complete numerical model, numerical terminal and its cold transcript replay are published in their own package. This exact-point package does not alter them or include any later parity-cycle search.
