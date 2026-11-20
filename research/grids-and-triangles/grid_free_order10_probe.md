# The first order-ten zero-grid count probes

Both bounded linear probes returned UNKNOWN. Neither produced an exact
count witness, a negative-count certificate, or an infeasibility proof.
The existing order-nine zero-grid certificate remains valid within its
stated scope; this computation does not establish its extension.

## Exact input reduction

The complete cap-compatible catalogue through order ten has 48,965
unlabelled types, including 42,430 types of order ten. There are 549
ordinary core-count coordinates, defined by minimum degree at least three.
The earlier catalogue has 57 such coordinates, leaving 492 new ones.

The existing exact deletion recurrence in `core_counts.py` generates
ordinary and induced count forms in these coordinates. Its induced
matrix has shape `48965 x 550`, including the constant coordinate, and
common scale `10! = 3628800`. Generation took approximately 266 seconds
after the catalogue build. The code checks the complete earlier graph,
automorphism, and core ordering. It also checks that all earlier ordinary
forms agree and that the earlier induced forms differ only by the exact
factor `10!/9! = 10`.

The first probe fixes the published 58-entry order-nine point, including
its constant coordinate. The second leaves all older core counts free
except the rook and broken-rook coordinates, which are zero. It therefore
tests a larger zero-grid count relaxation. It does not impose new
order-ten moment matrices.

## Necessary inequalities and acceptance gate

Every induced count must be nonnegative. The preprocessing substitutes
the fixed coordinates exactly and uses nonnegative ordinary core counts.
A zero-constant row with only nonpositive coefficients forces each
corresponding coordinate to zero. A row with nonnegative constant and
only nonnegative coefficients is redundant. Remaining rows are scaled
by their exact coefficient L1 norm only for the numerical solver.

The numerical objective maximizes a common normalized margin. The
first model has 492 active coordinates and 37,793 inequality rows. The
second has 547 active coordinates and 45,053 rows. Neither preprocessing
run forced an additional zero coordinate.

The original extension equalities and possible congruences are not all
imposed separately in these linear programs. A numerical candidate must
therefore pass a separate exact acceptance gate. After rounding the core
coordinates to integers, the checker evaluates all induced forms, checks
nonnegativity and divisibility, checks every binomial total, and replays
all 180,445 original marked-extension equations. A free-prefix witness
would also need new checks of its changed order-nine moment matrices.
It would not inherit the saved PSD certificates automatically.

## Recorded outcomes

| Prefix condition | Active coordinates | Inequalities | Solver time, seconds | Outcome |
| --- | ---: | ---: | ---: | --- |
| Published order-nine point fixed | 492 | 37,793 | 31.583 | Time limit; no certified conclusion |
| Earlier counts free, grid counts zero | 547 | 45,053 | 31.853 | Time limit; no certified conclusion |

Each requested solver budget was 30 seconds. The numerical solver
reported no primal solution. The independent source audit checks the
coordinate mapping, exact substitutions, zero propagation, scaling,
and acceptance gate. It does not turn a timeout into an exclusion.

## Reproduce the probe

The large reduced matrix is a rebuildable temporary input. It is not
needed for replay of the older order-nine certificate.

```sh
.venv/bin/python - <<'PY'
import pickle
import sys
sys.path.insert(0, 'experiments/workspace')
from subgraph_counts import build
from core_counts import reduce_counts
data = build(10)
reduced = (data, *reduce_counts(data, 99, 14))
with open('/tmp/conway99-order10-reduced.pickle', 'wb') as stream:
    pickle.dump(reduced, stream)
PY
.venv/bin/python experiments/workspace/grid_free_order10_probe.py \
  --reduced-cache /tmp/conway99-order10-reduced.pickle \
  --output /tmp/grid-free-order10-probe.json --seconds 30
```

Saved source/status audit:
[`grid_free_order10_independent_audit.md`](grid_free_order10_independent_audit.md).
The output and construction logs are in
`experiments/logs/moments-and-counts/grid-free-order10-*`.
