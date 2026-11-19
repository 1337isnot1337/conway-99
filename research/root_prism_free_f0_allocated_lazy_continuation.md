# Lazy incidence continuation with optimal potential allocations

This is a new preparation for the same conditional component-zero
incidence problem. All 480 first-component selectors remain free. The
second component and its fiber alignment remain unrestricted. The
scope is the globally prism-free, \(F\)-free split \(18+18\) shell.

The package changes the treatment of saved shared potentials and the
shared-query time schedule. It does not change the original Gram,
packing, or motif constraints. Preparation and cold replay call no
optimizer or incidence solver.

## Preserved formula and certificates

The seed retains all 2,916 inequalities from the last bounded-lazy
terminal result and all 12 subsequently certified gap-64 inequalities.
It contains 2,640 individual-row inequalities and 288 signed shared-row
inequalities. Every individual potential is checked against the complete
signature domain. The signed coefficients are independently reconstructed
from all 24 integer shared-potential families and their 12 verified core
relabelings.

The 5,340 old explanation clauses are retained in their original order.
Their parent CNF hash is reproduced before adding the gap-64 seed
explanations. The seed adds 24 necessary clauses and no auxiliary
variables:

| Quantity | Prepared value |
|---|---:|
| Primary signature selectors | 480 |
| Total Boolean variables | 28,308 |
| Original incidence and direct-cut clauses | 56,994 |
| Retained and new explanation clauses | 5,364 |
| Total clauses | 62,358 |
| Literal occurrences | 588,636 |
| DIMACS bytes | 2,739,501 |

The initial CNF SHA256 is
`5ecf9df873686109d14280d98a733400fd2d459292ff6c3aea863ada631c445e`.
The finite explanation CNF is not claimed equivalent to the complete
integer-inequality registry. Each SAT candidate is checked against that
registry before any LP runs.

The last saved incidence only supplies an exact seed-control check. It
is neither fixed nor preferred by the new solver formula. Its parent
UNKNOWN result is unchanged.

## Decision order for each Boolean candidate

The quadratic allocation theorem is proved in
`research/root_prism_free_f0_quadratic_allocation.md`. For a saved
potential family, define

\[
Q_v(z)=\sum_{ab}w_{ab}^{+}z_a z_b-\sum_a d_a z_a.
\]

Every actual completion has \(Q_v(z)\ge0\). At a Boolean candidate,
allocating each positive edge weight to an absent endpoint whenever
possible gives a necessary linear inequality whose violation is exactly
\(-Q_v(z)\).

The continuation uses this order:

1. Check the returned complete CNF assignment, original incidence,
   current clause prefix, and every registered individual or signed
   inequality. Any violated registered inequality gives exact clause
   explanations. That candidate receives no quadratic or LP work.
2. If the full linear registry passes, check every retained quadratic
   family and all 12 transports with integer arithmetic. For every
   negative \(Q_v\), construct the optimal endpoint allocation, retain
   its signed inequality permanently, and add exact clause explanations.
   That candidate receives no row LP.
3. If all quadratic inequalities pass, run the existing complete
   60-row box-separation pass. Retain only directly checked integer cuts
   or exact rational row boxes.
4. If all 60 row boxes exist, run the shared-edge sequence described
   below. An exact shared obstruction contributes its 12 signed cuts
   and the complete new potential orbit. An exact rational shared box
   stops the loop as a partial incidence result.

The potential registry has an explicit hash chain, separate from the
linear-cut and clause registries. Each candidate records the complete
quadratic values and its portfolio prefix. The cold replay reconstructs
the coefficients, endpoint choices, normalized cuts, registration maps,
and explanations before accepting any formula change.

Every future shared potential is registered only after the exact shared
certificate and full-domain lift have passed replay. Identical potential
orbits are recognized without adding duplicate families. The maps
transport valid inequalities; they impose no automorphism condition on
an unknown graph.

## Reserved shared-query allowance

The shared sequence keeps the same maximum 60-second allowance per
candidate. Setup and exact phase replay consume that allowance.

| Actual time remaining after setup | First action | If no exact result follows |
|---|---|---|
| At least 20 seconds | One original feasibility call, capped at \(\min(10,r/4)\) seconds | One bounded-potential call using the actual remainder |
| Positive and below 20 seconds | One bounded-potential call using the remainder | Stop unresolved |
| No time remaining | No optimizer call | Stop unresolved |

There is no retry and no original feasibility call after the bounded
call. The bounded model and exact reconstruction are unchanged. A
numerical infeasibility status does not establish an exclusion. A zero
bounded objective or failure to recover a strict integer gap does not
establish feasibility. Only an exact rational shared box or a strict
integer support gap is accepted.

The scheduling choice uses earlier timing observations without claiming
a matched-input comparison. Eight successful original phases took
1.38–5.64 seconds. The two separate bounded-only calls took about 8 and
11.5 seconds on different inputs. The new schedule preserves a short
original-first opportunity while explicitly reserving a fallback.

These are cooperative limits. Actual phase and overall overruns are
recorded rather than hidden.

## Limits, controls, and proof scope

The planned run limits are unchanged: 180 seconds overall, at most 1,000
SAT refinements and 100 complete row passes, at most 10 seconds per SAT
call, and at most 60 seconds per individual-row or shared phase. The
formula ceilings remain two million clauses and one million variables.

The controls verify the 20-second scheduling boundary and exact-only
status handling. Portfolio controls reconstruct all 24 initial families,
reproduce the three historical allocation detections, and check a new
integer-potential orbit, duplicate recognition, and cold registration
replay. The artificial growth control calls no optimizer and is not a
new numerical research result.

An arithmetic timing control measured 0.185 seconds for three complete
288-predicate candidate evaluations and 5.54 seconds for portfolio
construction and validation. These are local measurements of the
control run, not a prediction of production throughput. The complete
historical scan added no exclusion beyond the retained individual-row
registry.

AST controls confirm that nine existing gate functions are unchanged,
including primary-candidate inspection, exact clause explanation, and
explanation replay. The entire fresh-proof wrapper is unchanged except
for importing the new continuation. The changed scheduling and quadratic
paths require their own source review.

Incremental UNSAT remains uncertified. It can support a conditional
component-zero exclusion only after one fresh proof-enabled query on
the fully reconstructed final formula, direct DRAT checking, and a
separate cold reconstruction, retained-input inclusion check, and DRAT
replay. A SAT incidence or shared rational box is not a 99-vertex graph.

## Files and cold preparation replay

The source files use the prefixes
`root_prism_free_f0_allocated_lazy_*`,
`root_prism_free_f0_shared_reserved_fallback.py`, and
`root_prism_free_f0_quadratic_portfolio*` under
`experiments/workspace/`. The hash-bound registry, model preparation,
controls, and replay records are under `experiments/logs/root-prism-free/`.

The preparation can be replayed without an optimizer:

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_allocated_lazy_continuation.py replay \
  --preparation experiments/logs/root-prism-free/f0-allocated-lazy-continuation-preparation.json.gz \
  --output /tmp/f0-allocated-lazy-preflight.json
```

This preparation contains no production run. Its manifest binds every
source and control used for the subsequent review gate.
