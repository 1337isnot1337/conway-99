# Bounded-only separation for the latest terminal incidence

This is a separate preparation for iteration eighty of the frozen
bounded-fallback continuation. The continuation ended with UNKNOWN at
its time boundary. Its final original-feasibility phase reported
numerical infeasibility but saved no ray. No bounded-potential call ran
before that budget expired.

The new driver never calls the original feasibility routine. It permits
one call to the previously reviewed generic bounded-potential helper,
with at most sixty seconds including driver setup, on one thread. It
preserves the terminal UNKNOWN and all earlier query records.

## Bound candidate and model

Preparation reconstructs the final sixty-triple first incidence and
checks its original Gram and motif conditions. It evaluates every one
of the 2,916 terminal registry inequalities and all 5,340 actual
explanation clauses. The sixty exact rational individual-row boxes are
also replayed. All these checks pass.

The terminal shared record and its explicit original-feasibility child
are checked separately. Neither contains a saved numerical ray or
potential that could support an arithmetic-only repair. The new driver
therefore prepares the different bounded-potential model already
defined by the generic helper.

| Quantity | Count |
|---|---:|
| First-incidence triples | 60 |
| Eligible unordered exterior edges | 1,226 |
| Mixed-row potential variables | 1,080 |
| Positive-capacity variables | 1,226 |
| Total variables | 2,306 |
| Edge inequalities | 1,226 |
| Nonzero coefficients | 8,582 |

The exact model SHA256 is
`ffd339dad0efd917a684510643187ce899b587f47bad2890db484ab8a3643ec3`.
The candidate SHA256 is
`b37dc1249c9b38337a1692328cabde2c4499bdab26a16ec8a373a16ea0d560f0`.

Each first-component triple has weight three. Every mixed demand sums
to twenty-four, and summing each vertex's actual mixed supports gives
three times its degree support. Thus degree eight remains implied.

## Exact acceptance

The generic helper uses potentials in $[-1,1]$ and positive edge
capacities in $[0,6]$. It saves every returned numerical column before
reconstruction, on every backend status. The only accepted obstruction
is a strict integer support gap

$$
\sum_a v_a\cdot q_a
>\sum_{ab}\max(0,v_a\cdot h_b+v_b\cdot h_a).
$$

Cold replay checks all integer trials, then extends a successful
potential by zero to all 480 signatures and recomputes the complete
68,394-edge allocation and twelve core transports. The resulting
selector inequalities would be universal for this component stratum;
the chosen incidence is not fixed in their validity statement.

A zero or uncertified numerical answer remains UNKNOWN. This driver
does not infer a rational shared box from a zero objective, and it does
not claim a component exclusion from a fixed-incidence obstruction.

The controls replay the preceding gap-33 separator, its twelve
transports, the feasible-box identities, the zero-potential point and
the generic helper's status checks. Preparation and cold preflight call
no optimizer.

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_terminal_bounded_query.py replay \
  --preparation experiments/logs/root-prism-free/f0-terminal-bounded-query-preparation.json.gz \
  --output /tmp/f0-terminal-bounded-query-preflight.json
```

The source, current candidate, original row-domain inventory, complete
registry, previous cold replay and terminal manifest are bound by exact
hashes. The new source contains no copied LP solver implementation; its
only optimization entry point is the frozen generic bounded query.
