# Independent replay of the prism-zero count point

The coordinator independently replayed the repaired order-ten count
witness without importing its finder, repair routine, or optimizer.
All checks passed. The replay is separate from the exact PSD certificate
for the selected cached blocks.

The saved point has 48,965 nonnegative integer induced counts. Every
one of the 180,445 original extension equations holds, and every order
from zero through ten has the required binomial total. Direct triangle
enumeration identifies 1,443 catalogue types containing a prism; all
of their counts are zero.

The replay also reconstructs every induced count from the 550-entry
ordinary-core vector using the exact reduced forms. It reconstructs
each of the 549 ordinary core coordinates from its injective form and
automorphism order. These operations use Python integers. No numerical
status enters the result.

The complete replay took 16.04 seconds. The witness SHA-256 is

```text
62faca107e3f5a7f560c009133e2da563aa16619382b7778f7ff53aa1cd75db7
```

The source is `experiments/workspace/audit_prism_zero_count_witness.py`.
The output is
`experiments/logs/moments-and-counts/prism-zero-repair-root-audit.json`,
with an adjacent log. The exact PSD replay is saved separately in
`prism-zero-psd-root-replay.log` in the same directory.

## Reproduction

The direct count replay needs only the small catalogue. Rebuild it with
the same catalogue source and pickle protocol:

```sh
.venv/bin/python - <<'PY'
import pickle
import sys
sys.path.insert(0, 'experiments/workspace')
from subgraph_counts import build
with open('/tmp/conway99-order10-catalogue.pickle', 'wb') as stream:
    pickle.dump(build(10), stream, protocol=4)
PY
.venv/bin/python experiments/workspace/audit_prism_zero_count_witness.py \
  --witness experiments/logs/moments-and-counts/prism-zero-repair-witness.json \
  --catalogue /tmp/conway99-order10-catalogue.pickle \
  --output /tmp/prism-zero-count-replay.json
```

To reconstruct all counts from the core vector as well, add
`--cache /tmp/conway99-order10-reduced.pickle`. The
[original probe note](grid_free_order10_probe.md) gives the full
reduction build recipe. The saved coordinator replay used this option.

These checks establish a feasible point of the specified finite count
relaxation. The [separate PSD certificate](grid_free_order10_prism_zero_psd.md)
covers 1,416 cached blocks using its order-nine prefix. Neither result
supplies edges of a 99-vertex graph or covers every possible inequality.
