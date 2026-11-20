# Exact compression of the case4 selector LP

The complete case4 selector relaxation can be represented with 127,421 rows
and 8,483,109 nonzeros, preserving its 1,156 variables and its entire real
unit-box feasible set. The previous representation had 174,208 rows and
11,868,882 nonzeros. No optimizer was called during this compression.

All 1,992 native rows remain. The reduction removes 46,787 of the 172,216
coordinate-cover rows. Every removed row has one directly checked witness
among the final retained input rows. The certificate uses no integrality,
rounding, numerical point or symmetry assumption.

## Input domain

The input is the complete published case4 LP after substitution of the 58
proved zero coordinates. Its canonical integer stream has SHA256
`444835c4d3c466dc9bb5c71646da13bf98e6eefdb3a492c51bcf54185b8919d5`.
Its NPZ bytes have SHA256
`fb9ba6b1185f7796e39ac2904f077ad58238e89b0445305a22238c0374dd158f`.

The prior recovery certificate accounts for all 2,271 native constraints and
178,533 original coordinate covers. It proves the 58 substitutions and the
279 native and 6,317 cover box-tautology omissions. The present certificate
starts from the remaining 174,208 rows and accounts for every one of them.

## Three exact implication rules

A coordinate cover with guard a and positive support S is

    0 <= sum_{b in S} x_b - x_a <= |S|.

The upper bound follows from the unit-box bounds. Only its lower bound needs
a retained-row witness.

### Same guard and contained support

If a retained cover has the same guard and support T contained in S, then

    sum_S x - x_a = (sum_T x - x_a) + sum_{S minus T} x >= 0.

This proves both duplicate and strict-support dominance. Recomputing the
support antichains after the 58 zero substitutions removes 1,248 covers.

### Retained Gram quota and unit bounds

Suppose a retained Gram row is sum_E x=q. If |E minus S| <= q-1, then

    sum_S x >= q - sum_{E minus S} x
            >= q - |E minus S|
            >= 1 >= x_a.

The argument also applies when the guard belongs to E. It uses only the
retained equality, nonnegativity and the unit upper bounds.

### Retained weighted row with the same guard

Suppose a retained uncapped exterior-row inequality is

    sum_{b in T} w_b x_b >= d x_a,

where T is contained in S and every coefficient satisfies 0<w_b<=d. Then

    d sum_S x >= sum_T w_b x_b >= d x_a.

This rule never caps or rounds a weight. A row with a positive weight larger
than its demand is not eligible for this rule. Thirteen retained weighted
rows meet the coefficient condition.

## Complete certificate

The native-row screen removes another 45,539 minimal covers: 45,525 by a
Gram quota and 14 by a weighted row. When a cover first dominated another
cover that the native screen later removes, the final certificate replaces
the intermediate witness with that retained native row. Its implication is
checked directly on the original larger support.

The final omission ledger has these counts:

| Direct retained-row witness | Removed covers |
| --- | ---: |
| Gram equality and unit bounds | 45,762 |
| Same-guard contained cover | 1,011 |
| Same-guard uncapped weighted row | 14 |
| Total | 46,787 |

The remaining 125,429 covers form an antichain for each guard. Adding the
unchanged native rows gives 127,421 rows. Every retained row was already in
the input LP, and every omitted row is implied by retained rows and the
unchanged unit box. These two directions prove equality of the projected
real feasible sets.

## Verification and limits

Preparation completed in 27.46 seconds with peak RSS about 403 MiB. The
separate cold replay completed in 9.01 seconds. It reloaded the hash-bound
original matrix, directly checked every omission, checked the final
antichains, rebuilt every compressed sparse array and matched the saved NPZ.
It did not rerun the cover-selection algorithm or call an optimizer.

The compressed NPZ has SHA256
`82f97f6694b6b3648f19651d43546dcaecfc1a97736afd30ce470b2b2bcd968c`.
The deterministic compressed certificate has SHA256
`ecd80cb44cfc6464bab1e8c711229bef2a7da9d9334900f24d422d6a46841834`.

This is an equivalent representation, not a new exclusion or a feasible
point. The full-matrix max-min query remains terminal UNKNOWN. Any further
query needs a separate source and run gate.

Artifacts are under
`experiments/logs/grids-and-triangles/rook-case4-cover-compression01/`.
The source is `experiments/workspace/rook_case4_cover_compression.py`.
