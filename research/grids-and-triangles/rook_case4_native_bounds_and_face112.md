# Case 4: one further integer zero and the 112-zero closure

The saved native-row batch supplies five exact bounds. An independent
standard-library checker reconstructs all 2,271 original native constraints,
the two proved parity equalities, the 1,103 surviving coordinates, and all
1,143 objective definitions. It checks every coefficient of each bound.
It imports no subject source and calls no optimizer.

The 111 earlier zeros and the proofs of `H1 = H2 = 1` remain explicit,
hash-bound premises. This audit does not repeat their earlier proofs.
The subsequent propagation wrapper does replay that premise chain before
using the new restrictions.

## Exact bounds

For finite row bounds `l <= A x <= u`, unit variable bounds, an integer row
multiplier vector `m`, and a positive denominator `D`, let

\[
r = Dc-A^T m,\qquad
B = \sum_{m_i\ge0}m_i u_i+\sum_{m_i<0}m_i l_i
    +\sum_j\max(r_j,0).
\]

Then `D c^T x <= B`. This calculation does not assume that the proposed
multipliers satisfy a numerical dual-feasibility tolerance. Each accepted
certificate saves all nonzero multipliers and the complete residual hash.

| Objective | Exact upper bound | Boolean consequence |
| --- | ---: | --- |
| `x663` | `239/256`, refined to `2/3` | `x663 = 0` |
| `x259 + x590` | `31387/16384` | Sum at most one |
| `x259 + x591` | `1` | Already implied by Gram row 580 |
| `x259 + x593` | `1` | Already implied by Gram row 580 |
| `x259 + x732` | `1` | Already implied by Gram row 580 |

Original Gram row 580 has quota one and includes columns 259, 591, 593
and 732. Its nonnegative terms already forbid the last three pairs.
Only the pair `(259, 590)` needs integer rounding to strengthen the real
relaxation. All four pair rows are retained in the propagation ledger so
that its relation to the saved five-certificate batch is explicit.

## Short proof for column 663

The denominator-six refinement has no positive box correction. Its 111
nonzero multipliers use 110 original Gram rows and the equality `H1 = 1`.
The independent audit expands this combination on all 1,214 original
columns. After the 111 previously proved zeros are substituted, it is

\[
3x_{663}+\sum_{a\in S}x_a=2,\qquad |S|=86,\quad 663\notin S.
\]

Nonnegative integrality gives `x663 = 0`. Consequently the 86-column sum
equals two. Unit upper bounds are not needed for this short deduction.
The complete set `S`, the original row combination, all 1,214 integer
coefficients, and the corrections on 38 prior-zero columns are in
`rook-case4-face111-native-bounds-independent-replay.json`.

## Complete exact propagation

The new propagation preparation preserves all 2,271 original native rows
and all 178,533 registered coordinate covers. It has two unit-sum parity
equalities, four certified pair capacities, and 112 zero-axiom rows.
The existing propagation engine and sequential-reason verifier are
unchanged. There are no probing assumptions or numerical presolve facts.

The single authorized forward closure took about 0.625 seconds. It reached
a complete fixed point with exactly the 112 initial zeros, no ones, and
no contradiction. A separate cold replay checked all 112 sequential
reasons and the complete fixed-point claim. The augmented premises are
integer-derived; the real-box label on the propagation steps refers to
that augmented system.

The remaining inventory has 1,102 variables, 1,966 retained native or added
rows, 164,044 retained coordinate covers, and 10,767,167 nonzero coefficients.
Every original row and cover is retained or has an exact unit-box omission
witness. No new numerical model or optimizer query was needed for this
inventory.

Two preparation attempts stopped before propagation at a JSON comparison
boundary. Integer histogram keys became string keys on serialization; the
first canonical-byte repair still imposed a different key order. Both
sources and diagnostic records are preserved. The final version compares
JSON-decoded values, with an explicit one-expression change and controls.
The mathematical rows, bound coefficients, and resource limits did not
change.

Case 4 remains open. These results exclude one more attachment column and
one additional simultaneous pair selection within its necessary incidence
model. They do not construct a graph or exclude the whole case.
