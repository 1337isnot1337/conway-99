# First two-family graph-Schur scan

The single authorized scan produced 17 exact necessary inequalities and finished
in 40.278 seconds, with no time-limit overrun. A separate cold replay rebuilt
both integer kernels and checked all 68 attempted integer vectors and every
retained full480 quadratic identity. No optimizer was called.

The conditional scope is the component-zero, split18+18, globally prism-free
and $F$-free case described in the
[preparation note](root_prism_free_f0_graph_schur_cuts.md). The second component
and its alignment remain free. These results exclude neither that component
case nor a hypothetical SRG(99,14,1,2).

## Recorded outcome

| Family | Retained cuts | Directions visited | Terminal coverage |
|---|---:|---:|---|
| plus, $27I-9A+J$ | 16 | 4 | The per-family cut limit was reached during the fourth direction. |
| minus, $44I+11A-2J$ | 1 | 8 | All eight directions and six scales were checked. |

The scan used one full480 eigendecomposition per family. The plus cut limit did
not skip the minus family. The run made 68 integer-vector attempts in total.
It did not exhaust either positive-semidefinite cone.

The proposing point is the saved numerical result with SHA256
`ca7ebcb40ea0b02054a79f6f6acb83f1f227325f7669b0b9336e3beed6fce5bf`.
Its exact feasibility remains UNKNOWN. Each retained inequality comes from an
integer-vector evaluation of a universally necessary Schur matrix. Its
validity does not depend on the numerical point satisfying the linear model.

## The small minus-family gap

The numerical negative modes of the minus matrix were near rounding scale. Its
one retained cut has the exact full Schur quadratic value

$$
-\frac{5436005415027297}{50082333699369129213952}
$$

at the stored binary64 point interpreted as exact rational coordinates. This
is approximately $-1.0854\cdot10^{-7}$ before normalizing the integer vector.
The sign is exact, but it does not establish that this row removes any point
from the previously feasible set. The row may follow from existing equalities
or other constraints. The terminal record keeps the row and explicitly flags
this possible redundancy.

The plus cuts have larger negative evaluations at this proposal. Their
validity is also the exact Schur identity, rather than the numerical
eigenvalue. No proof of strict improvement of the linear feasible set is made
for this scan.

## Integer coefficients and replay

The 17 primitive rows have 221,953 nonzero coefficients in total. Their largest
coefficient uses 31 bits, below the previously proved 51-bit upper bound. The
smallest nonzero coefficient after the recorded positive dyadic row scaling is
$45/134217728$. All conversions of mathematical coefficients to the proposed
numerical row units are exact binary rationals.

The cold replay:

- Rebuilds the complete 480-coordinate kernels from the fixed 18-core inverse
  certificates.
- Reconstructs every attempted quotient row and every accepted integer gap.
- Expands each full quadratic over all 114,960 unordered pair positions and
  all 68,394 eligible edge positions.
- Checks the positive gcd normalization, all 389 certified zero substitutions,
  deduplication, per-family cut counts, and the frozen source/model bindings.

It makes no eigendecomposition and no optimizer call. The independent
source-and-mathematics review is
`experiments/logs/root-prism-free/f0-graph-schur-independent-source-review.json`,
SHA256
`bd1c2054a9a232559c69c1e6134b926252463fb4b3bb660892566c22f1522855`.
That review did not repeat the scan or its calculations.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `f0-graph-schur-cuts-scan01.json.gz` | `2e743329a4e241f1d7b3c89e1821d9d1e5419cf1417f3a985563e5b1e8376383` |
| Uncompressed scan bytes | `1bd3554ff234cb2c649a8f8e6eeed118eb359508a7924e275e4166f481b99b7a` |
| `f0-graph-schur-cuts-scan01-cold-replay.json` | `c86c7a30030b04702479fc74ba6cee25b1d0be9d84184939eb3e254e56c226f1` |
| `f0-graph-schur-cuts-scan01-summary.json` | `46badd3ea3634215df3d44a8c2714279b06afd32e24af68de667b8d0998a1de2` |

These files are under `experiments/logs/root-prism-free/`. The compressed scan
contains the integer vectors, literal coefficient hashes, primitive rows,
exact rational evaluations, numerical proposing directions, and complete
attempt records.

```sh
python3 experiments/workspace/root_prism_free_f0_graph_schur_cuts.py replay \
  --preparation experiments/logs/root-prism-free/f0-graph-schur-cuts-preparation01.json \
  --proposal experiments/logs/root-prism-free/f0-selector-psd-query-run01/numerical.json \
  --result experiments/logs/root-prism-free/f0-graph-schur-cuts-scan01.json.gz \
  --output /tmp/f0-graph-schur-scan01-replay.json \
  --seconds 120
```

No subsequent linear query is part of this package. The coordinator is
separately checking whether conditioning on the full fixed 21-core gives
stronger matrices before selecting the next model.
