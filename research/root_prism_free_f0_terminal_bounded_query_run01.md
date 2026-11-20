# Exact gap 64 for the latest terminal incidence

The single bounded-only query excludes the saved first incidence from
iteration eighty of the bounded-fallback continuation. Integer
reconstruction gives mixed-row demand 252 and positive shared-edge
capacity 188. Their strict difference is 64.

The cold replay passed and produced twelve necessary inequalities on
the complete 480-selector domain. This is a fixed-incidence exclusion,
with every second component and fiber alignment unrestricted. It does
not exclude component zero or the full split-shell case.

## One distinct query

The query used the previously reviewed generic bounded-potential
implementation. It made one simplex call on one thread, completing in
12.789204 seconds including setup. The sixty-second limit was not
exceeded. The expired original feasibility call was not repeated.

The wrapper and its separate phase record preserve all 2,306 returned
numerical columns. The backend status proposed the potential; only
integer reconstruction establishes the obstruction.

| Rounding scale | Exact integer support gap |
|---:|---:|
| 1 | -135 |
| 2 | -143 |
| 3 | -113 |
| 4 | -106 |
| 6 | -60 |
| 12 | 64 |

The accepted potential has maximum absolute entry twelve. There are
169 positive edge weights among the 1,226 eligible pairs of the saved
incidence. Their weights sum to 188. Any shared fractional completion
assigns each edge a value in $[0,1]$, so it cannot supply the demanded
weighted sum 252. All sums in this comparison are integers.

## Full-domain lift

Extending the potentials by zero to the other signatures and inspecting
all 68,394 universally eligible pairs gives 7,202 positive global edge
weights. The existing exact endpoint-allocation rule converts them into
a necessary linear selector inequality. The saved incidence determines
the potential support and allocation only; it is not a condition in the
inequality's validity statement.

The coefficient gcd is one. Each of the twelve verified core
relabelings produces a transported inequality with exact gap 64 at the
corresponding transported selection. These inequalities have not been
used in a new incidence query in this package.

## Replay and preservation

Cold replay reconstructs the candidate, all 2,916 prior inequalities,
all 5,340 explanation clauses and all sixty rational individual-row
boxes. It reproduces the exact bounded LP, rechecks every integer trial,
and rebuilds the full-domain allocation and all twelve transports.
Neither the preparation replay nor the terminal replay calls an
optimizer.

| Artifact | SHA256 prefix |
|---|---|
| Thin driver | `104d9c16fb7ad85f` |
| Preparation | `df2798c914ad9906` |
| Query wrapper result | `ea36d78c2307448b` |
| Complete numerical and integer phase | `83950bcdc02f674b` |
| Universal inequalities | `2dcb71399b53da20` |

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_terminal_bounded_query.py replay \
  --preparation experiments/logs/root-prism-free/f0-terminal-bounded-query-preparation.json.gz \
  --result experiments/logs/root-prism-free/f0-terminal-bounded-query-run01.json \
  --output /tmp/f0-terminal-bounded-query-run01-replay.json \
  --lift-output /tmp/f0-terminal-bounded-query-run01-cuts.json
```

The parent continuation remains frozen with its original UNKNOWN
status. Its limited numerical answer did not establish this exclusion;
the separate bounded query and exact certificate did. No new SAT query,
component exclusion or graph construction is claimed here.
