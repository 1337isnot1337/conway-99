# Exact propagation after the four-row Gram relation

The new Gram relation and the existing cover units give81 distinct zero
selectors in indexed case4. Deterministic exact propagation through all2,271
original native rows and178,533 coordinate covers reaches a fixed point with
no further assignment and no contradiction.

The forward phase took0.838 seconds. Its81 assignment records and the complete
fixed-point check passed the frozen independent reason checker. A separate cold
replay rebuilt the input rows and checked the Gram premises, trace and final
scope again.

No branch assumption, failed-literal probe, optimizer or native presolve premise
was used. The propagation rule can infer Boolean endpoint consequences in
general. This run needed none: every assignment is valid over the full real
unit box by an exact saturated bound or the separately proved Gram zero.

Substituting the81 zeros and dropping only unit-box tautologies leaves:

| Quantity | Count |
|---|---:|
| Free selectors | 1,133 |
| Native rows | 1,984 |
| Native nonzeros | 26,358 |
| Coordinate covers | 168,847 |
| Total rows | 170,831 |
| Total nonzeros | 11,390,157 |

There are no fixed-one selectors. The inventory accounts for every original
native row and registered cover. These counts describe a smaller, equivalent
real feasible domain; they do not establish feasibility or infeasibility.

The wrapper is `rook_case4_four_gram_face_closure.py`. It imports the frozen
primary rule and reason checker unchanged, adding only70 exact Gram-zero
premise rows. The14 original unit covers overlap those rows at three columns.
The closure certificate and cold replay use the prefix
`rook-case4-four-gram-face-closure-` under the grid experiment logs.

The next max-min preparation will use this proved face. No second optimizer
query is included in the closure package.
