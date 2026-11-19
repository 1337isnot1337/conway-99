# A numerical real-relaxation diagnostic for case 4

Both tested real relaxations of 35-core case 4 were numerically feasible.
Neither numerical point passed the attempted exact rational
reconstruction. This checkpoint therefore proves neither real feasibility
nor infeasibility, and excludes no local core.

The purpose was to check whether a linear obstruction was immediately
available before doing more binary search. No such obstruction was found.
Only case 4 was tested; there was no LP sweep.

## Complete rows and two separate variants

The inventory uses all 1,214 attachment columns of the frozen case-4
domain. Its 397 distinct Gram equations cover all 630 upper-triangular
positions of the full 35-by-35 Gram target, including the empty zero row.
It also contains 186 original-signature capacities, 12 additional
core-triple capacities, and 1,214 individual upper bounds. All variables
are nonnegative, so these upper-bound rows impose \(0\le x\le1\).

Triple families omitted from the explicit capacities are covered by a
quota-one Gram pair, exactly as in the original binary model. The saved
inventory includes the complete coverage lists and checks them against
the frozen original model metadata. It does not build another CNF.

The first variant contains only these original continuous constraints.
The second also contains the 30 certified binary no-good inequalities
\(x_i+x_j\le1\). Those inequalities hold for binary graph incidences;
they are not asserted to hold throughout the original fractional cone.
Their direct integer negative-vector certificates are retained and
checked separately.

For exact ray extraction, each upper-bound or capacity row receives one
nonnegative slack variable. Both variants are expressed as
\(Ez=b,\ z\ge0\). A future infeasibility claim from this source must pass
the exact integer test

\[
E^{\mathsf T}y\ge0,\qquad b^{\mathsf T}y<0.
\]

No such certificate is claimed here.

## Observed results

Both runs used HiGHS with one thread, presolve disabled, zero objective,
and an eight-second requested limit per variant.

| Variant | Rows | Columns including slacks | Nonzeros | Solve time | Maximum equality residual | Maximum capacity violation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original continuous constraints | 1,809 | 2,626 | 19,018 | 0.662 s | \(7.82\times10^{-14}\) | \(4.89\times10^{-15}\) |
| With 30 binary no-good rows | 1,839 | 2,656 | 19,108 | 0.598 s | \(9.53\times10^{-14}\) | 0 |

The solver returned `kOptimal` for both zero-objective problems. Direct
rational reconstruction with denominator limits through \(10^6\) did not
satisfy every row exactly. The saved numerical points and residuals are
diagnostic evidence only. No integrality conclusion follows from them.

The optimizer-free replay rebuilds the complete inventory and binds both
numerical records. It explicitly reports that no exact feasibility or
infeasibility certificate is present.

## Frozen artifacts

The source is
[`complement_rook_35core_case0004_lp.py`](../../experiments/workspace/complement_rook_35core_case0004_lp.py),
SHA256 `cba1a71b01cb48e33bfd0a82113b35d3c5b846176dfb244369660d8762320d02`.
The compressed model is
[`complement-rook-35core-case0004-lp-model.json.gz`](../../experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lp-model.json.gz),
SHA256 `18e7b79a7e83c1c40f0c0c29301703400f26b42401f0b07a2f21783a298119a6`.
The adjacent result, preparation/run/replay logs, and artifact manifest
preserve the complete row inventory and the two numerical points.

Replay without an optimizer, using a new output file:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_lp.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lp-model.json.gz \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lp-result.json \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lp-replay-new.json
```
