# An eleven-coordinate form of the column 628 inequality

The frozen column 628 potential has an equivalent form with eleven
nonzero core coordinates and no exterior-degree coordinate. Its nonzero
entries are:

| Core site | Coefficient |
|---|---:|
| R6 | -2 |
| R7 | 1 |
| S0 | -1 |
| S3 | -2 |
| S4 | 2 |
| S5 | -1 |
| S8 | -2 |
| T1 | 1 |
| T2 | 2 |
| Local vertex 0 | 2 |
| Local vertex 5 | 1 |

The corresponding zero-based core indices are
6, 7, 9, 12, 13, 14, 17, 19, 20, 27, and 32.

Every attachment column has exactly one R-neighbor. The target quotas
also satisfy \(\sum_{i\in R}q_a(i)=d_a\). Therefore subtracting one from
all nine R-coordinates of the potential and adding one to its degree
coordinate leaves every product and its right-hand side unchanged.
The original degree coefficient is minus one, so this makes it zero.

Finally, an eligible neighbor has no entry at a position where the
target quota is zero. Set the potential to zero at those positions.
This gives the table above.

The standard-library verifier
`experiments/workspace/complement_rook_35core_case0004_row628_gauge.py`
checks all 458 eligible neighbor products against the original frozen
certificate. All products, all 96 positive coefficients, and the
right-hand side 2 are unchanged. Its exact output is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row628-gauge.json`.
No optimizer is called, and this is an equivalent presentation rather
than a new inequality.
