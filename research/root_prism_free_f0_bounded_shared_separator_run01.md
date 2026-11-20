# Exact separation of the continuation's terminal incidence

The single bounded-potential query found an exact obstruction to the
saved sixty-triple first incidence. Integer reconstruction gives demand
215 and positive shared-edge capacity 182, so the strict gap is 33.
The cold replay passed and produced twelve necessary inequalities on
the complete 480-selector domain.

This excludes the saved first incidence with every second component and
fiber alignment left free. It does not exclude component zero or the
split-shell case. The earlier feasibility-query UNKNOWN remains
unchanged; this is a separate exact result from a different LP.

## Query and reconstruction

The query used the frozen 2,300-variable bounded-potential model with
1,220 inequalities. One simplex call, on one thread, completed in
7.987 seconds including setup. The sixty-second budget was not exceeded.
The backend reported optimality, but certificate acceptance used only
the subsequent integer support-gap calculation.

All 2,300 returned numerical columns are preserved as hexadecimal
floats. Rounding only the 1,080 potential entries gave the following
exact trials; the common integer divisor was one in every trial.

| Scale | Integer demand | Positive edge capacity | Gap |
|---:|---:|---:|---:|
| 1 | 15 | 152 | -137 |
| 2 | 14 | 145 | -131 |
| 3 | 58 | 180 | -122 |
| 4 | 108 | 233 | -125 |
| 6 | 116 | 190 | -74 |
| 12 | 215 | 182 | 33 |

The accepted potential has maximum absolute entry twelve. Of the 1,220
eligible internal edges, 132 have positive integer weight. Their weights
sum to 182. Every hypothetical shared completion has edge values in
$[0,1]$, so its weighted contribution cannot reach the required 215.
No floating-point tolerance enters that contradiction.

## Universal selector inequalities

The accepted potentials were extended by zero from the saved sixty
triples to all 480 admissible triples. The lifting routine inspected all
68,394 universally eligible unordered edges. There are 7,198 positive
edge weights in this complete domain.

For a positive edge internal to the saved selection, the routine
allocates its weight to one fixed endpoint. For a positive edge leaving
the selection, it allocates the weight to the outside endpoint. Actual
edge indicators are bounded by either endpoint selector, so these
allocations give a necessary linear selector inequality. The saved
selection determines the potential support and allocation; it is not a
hypothesis of the resulting inequality.

The coefficient gcd is one. All twelve verified core relabelings give
inequalities with exact gap 33 at the corresponding transported saved
selection. No incidence variable is fixed, and no completed graph is
assumed to have a symmetry. These cuts have not been added to a new
incidence query in this package.

## Cold replay and bindings

The optimizer-free replay reconstructs the full target domain, checks
all actual degree-row identities, and reproduces the bounded model and
its controls. It then reconstructs all six integer trials from the saved
numerical potentials, checks the strict gap, and reproduces the full
edge allocation and all twelve transports.

| Artifact | SHA256 prefix |
|---|---|
| Frozen source | `bbdf21247d98cff4` |
| Exact model | `c433fa3d8dc960df` |
| Preparation | `ddce4b389df86078` |
| Query result | `fdcf7105748e809f` |
| Universal cuts | `9029303e60cbf124` |

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_bounded_shared_separator.py replay \
  --preparation experiments/logs/root-prism-free/f0-bounded-shared-separator-preparation.json.gz \
  --result experiments/logs/root-prism-free/f0-bounded-shared-separator-run01.json \
  --output /tmp/f0-bounded-shared-separator-run01-replay.json \
  --lift-output /tmp/f0-bounded-shared-separator-run01-cuts.json
```

The original result and cold replay retain their UNKNOWN status. This
package changes neither the frozen continuation formula nor its query
records. There was no new SAT query, no retry of the feasibility LP, and
no claim of a full graph or a component-wide exclusion.
