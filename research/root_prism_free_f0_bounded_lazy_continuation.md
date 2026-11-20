# Lazy continuation with bounded shared separation

This preparation retains all 1,356 proved inequalities and all 2,448
explanation clauses from the first lazy continuation. It adds the twelve
universal inequalities from the separate gap-33 certificate and
twenty-four exact clause explanations. All 480 incidence selectors remain
free. No selected incidence, second component, alignment or solver hint
is fixed.

The mathematical scope remains component zero in a globally prism-free,
F-free split $18+18$ shell. The preparation does not establish a
component exclusion or a graph completion.

## Exact registry and preserved prefix

The seed rebuilds the original 56,994-clause direct-cut formula once. It
validates all 1,188 individual-row potentials directly and replays the
fifteen shared-potential proof families, including their complete-domain
allocations and twelve transports. Their inequalities occupy the same
registry indices as before; the twelve new signed inequalities are
appended.

Each of the 2,448 retained clause records is checked against its exact
integer inequality, its core transport and its optional population-60
premise. The reconstructed parent prefix matches the previous final CNF
hash byte for byte. Its clause hash chain is preserved. The starting
registry hash is reset to the complete canonical contents, as in the
earlier continuation.

The old terminal incidence violates one of the twelve new inequalities
by 33. Both the independent and population-60 explanation routines
produce a clause, and all twelve verified core relabelings are applied.
After literal-list deduplication this gives twenty-four new clauses and
6,036 literal occurrences. These are consequences of proved
inequalities. They are not unproved visitation blocks.

| Prepared quantity | Count |
|---|---:|
| Primary incidence selectors | 480 |
| Individual-row inequalities | 1,188 |
| Signed shared-edge inequalities | 180 |
| Total registered inequalities | 1,368 |
| Retained parent explanation clauses | 2,448 |
| New explanation clauses | 24 |
| Total CNF variables | 28,308 |
| Total CNF clauses | 59,466 |
| Literal occurrences | 369,552 |
| DIMACS bytes | 1,844,326 |

The prepared CNF SHA256 is
`71a0a9306664001dcda1c68b1635cbc42e9525ac3133dd3a40ae9b09a0ec0c39`.
No auxiliary variables are added by the lazy explanations.

The seed uses direct mathematical checks and the frozen parent
manifests. It does not recursively rebuild the earlier continuation
formulas or repeat their optimization queries. The saved terminal
candidate is a certificate and prefix control only.

## Shared-feasibility call and bounded fallback

The new helper preserves the existing shared-box feasibility call. It
calls that model at most once for a given candidate. An exact rational
shared box stops the incidence loop with a partial feasibility witness.
An exact reconstructed infeasibility ray enters the existing
full-domain selector-cut lift.

If the first call returns neither exact result, the helper may make one
different call to the bounded mixed-row potential LP. Both phases share
the same sixty-second budget. The second call receives only the time
remaining after the first call and its exact replay. There is no retry
of the original feasibility model.

For the current sixty triples, the helper reconstructs every eligible
unordered edge and verifies every degree-row identity. Each incidence
column has weight three, and each mixed demand sums to twenty-four, so
the degree-eight equation follows from the eighteen mixed equations.
The bounded model uses $v_a\in[-1,1]^{18}$ and capacities
$t_{ab}\in[0,6]$, imposing

$$
t_{ab}\geq v_a\cdot h_b+v_b\cdot h_a.
$$

It minimizes

$$
-\sum_a v_a\cdot q_a+\sum_{ab}t_{ab}.
$$

All returned potential entries are preserved as hexadecimal floats on
every backend status. The frozen reconstruction routine proposes
integer potentials and accepts only a strict exact support gap:

$$
\sum_a v_a\cdot q_a
>\sum_{ab}\max(0,v_a\cdot h_b+v_b\cdot h_a).
$$

A zero numerical objective or failure to reconstruct a separator does
not certify feasibility. It leaves the result unresolved unless the
first phase already supplied a checked rational shared box. The helper
stores both phase records, their file hashes, both call counts and the
combined elapsed time. Cold replay checks each phase separately.

## Unchanged loop and proof semantics

A complete abstract-syntax-tree comparison confirms that the incidence
runner differs from the previous frozen continuation only in its seed
import, source bindings and two descriptive status labels. Its query
logic, candidate checks, prefix replay, cut insertion and limits are
unchanged. The proof wrapper changes only its runner import.

Every returned SAT assignment is checked against the actual CNF prefix
and the original primary constraints. Every registered integer
inequality is then evaluated before a row LP. A violation generates
only exact clause explanations. Individual-row separation runs only
after all registry inequalities hold. Shared separation runs only after
a complete pass produces sixty exact individual-row boxes.

| Bound | Limit |
|---|---:|
| Overall loop time | 180 seconds |
| SAT refinement calls | 1,000 |
| Complete row passes | 100 |
| One SAT call | 10 seconds |
| One sixty-row pass | 60 seconds |
| Combined shared-feasibility/fallback sequence | 60 seconds |
| CNF variables | 1,000,000 |
| CNF clauses | 2,000,000 |

Incremental UNSAT remains uncertified. The separate wrapper rebuilds the
exact final formula, makes one fresh proof-enabled query, checks DRAT,
and requires a separate cold retained-input and proof replay. No
component exclusion is claimed before all those checks pass.

## Controls and preparation replay

The new shared helper replays the gap-33 certificate and all twelve
selector lifts. It reproduces the bounded LP from the saved exact data,
rechecks the earlier known separator and twenty-four feasible-box
controls, and checks the routing of exact, unresolved, running and error
statuses. No optimizer is called by these controls.

The new seed keeps all 59,442 parent clauses unchanged before appending
its twenty-four new consequences. The cold preparation replay repeats
the direct registry, clause-proof and prefix checks and matches the
prepared CNF hash.

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_bounded_lazy_continuation.py replay \
  --preparation experiments/logs/root-prism-free/f0-bounded-lazy-continuation-preparation.json.gz \
  --output /tmp/f0-bounded-lazy-continuation-preflight.json
```

The frozen parent UNKNOWN and the separate exact gap-33 result remain
unchanged. This preparation contains no new incidence or LP query.
