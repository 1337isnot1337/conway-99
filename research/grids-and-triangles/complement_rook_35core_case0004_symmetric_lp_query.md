# One-query driver for the symmetric case 4 LP

The driver is prepared and its full integer-matrix preflight passed.
Preparation did not call an optimizer. It binds the complete matrix from
`complement_rook_35core_case0004_symmetric_lp.md`: 276,792 variables,
590,165 rows, and 4,121,379 nonzero entries.

## Exact matrix construction

The driver reconstructs all inputs and all 60 integer row cuts. It then
streams every row into integer COO arrays, checking the full row and
label hashes. Only after those checks does it convert the sparse layout
to integer CSC arrays. No coefficient is converted to floating point
during this preparation.

Each CSC array has its own dtype, shape, and SHA256 binding. The exact
array cache is 5,788,962 compressed bytes. Preparation took 12.42 seconds
with observed peak RSS 298,216 KiB. A separate cold preflight rebuilt
every row and every CSC array and matched all bindings.

The cache is a reproducible temporary solver input. The committed source,
sizing preparation, query model, and original certificates suffice for
the cold replay; that replay does not depend on the cache surviving.

## One numerical query

The driver permits one HiGHS call with one thread and a solve limit of
at most 60 seconds. Cache loading, coefficient conversion, and solver
initialization are timed separately. It records actual solve time and
peak RSS. There is no follow-up optimization or SAT call.

If the LP is numerically optimal, it saves the full numerical selector
and edge vector and reports residuals. It makes no exact feasibility
claim. A numerical point is not a binary incidence or a graph.

If the LP is numerically infeasible, the driver preserves its numerical
ray and tries integer reconstruction. No exclusion is accepted merely
from the numerical status.

## Complete exact ray gate

For the physical matrix \(A\), row right-hand sides \(b\), equality rows,
and upper rows, the verifier requires

\[
A^Tr\ge0,\qquad r_i\ge0\text{ on every upper row},
\qquad b^Tr<0.
\]

All selector and edge variables have lower bound zero. The sign
condition on each upper row is exactly its nonnegative slack-column
condition. Thus the verifier checks all 276,792 physical variable
coefficients and all 552,658 upper-row slack coefficients. It uses Python
integers for the products and sums.

Reconstruction works only on the numerical ray's nonzero support.
Common denominators are accumulated incrementally and refused as soon
as they exceed 4,096 bits. Integer/rational construction has a separate
15-second budget, and all exact candidate checks together have a
60-second budget. An incomplete reconstruction or check leaves the case
unresolved. The source includes an exact positive Farkas control and
three invalid sign/column controls.

Any accepted integer ray must then pass the separate cold replay, which
reconstructs the complete integer matrix before checking the ray again.
Even a verified contradiction concerns only this indexed case 4 core.

## Files and preflight

Source:
`experiments/workspace/complement_rook_35core_case0004_symmetric_lp_query.py`

Prepared model:
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-symmetric-lp-query-model.json`

The optimizer-free preflight can be repeated with a fresh output path:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_symmetric_lp_query.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-symmetric-lp-query-model.json \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0004-symmetric-lp-query-preflight-new.json
```

At preparation freeze, no symmetric case 4 optimizer query has run.
