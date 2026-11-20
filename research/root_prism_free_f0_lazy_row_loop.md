# Lazy clauses for the free component-zero incidence model

This is preparation for a bounded continuation. It does not contain a
new incidence solve or a component exclusion.

The scope remains component zero in the globally prism-free, F-free
split $18+18$ shell case. All 480 incidence selectors remain free.
No second component, second incidence, or fiber alignment is fixed.
The starting CNF is the original component incidence formula with the
twelve previously certified direct row cuts. It has 28,308 variables
and 56,994 clauses.

## Why the encoding changed

The preceding deficit loop stopped at its declared two-million-clause
limit. Its final formula contained 719 encoded weighted inequalities.
The complete exact registry contained 732 inequalities: 660 individual
row cuts, including thirteen final transports that were not encoded,
and 72 signed shared-edge cuts.

That run remains unresolved. The new preparation retains all 732
proved inequalities in an exact registry. SAT receives clause
consequences of these inequalities. Every returned primary selection
is checked against every registry inequality before any row LP.

The finite collection of clause consequences is not asserted to encode
the full registry equivalently. A SAT assignment that violates a
registered inequality triggers more proved clauses. A SAT assignment
that passes all registered inequalities is only an incidence candidate.

## Direct registry replay

`root_prism_free_f0_lazy_registry.py` reconstructs the mathematical
proofs directly. It does not regenerate any ancestor auxiliary CNF.
The replay checks:

- all 660 integer row potentials and their complete eligible-neighbor
  coefficient lists;
- the exact 647 retained plus thirteen unencoded row-cut provenance;
- six complete shared-edge proof families and their 72 signed cuts;
- the original 171 component Gram positions and the population identity;
- all twelve core relabelings, including their signature actions;
- thirty prior selections that satisfy the original direct-cut formula
  but violate at least one retained exact inequality.

The parent transcript and its terminal manifest are hash-bound. The
lossless transcript archive can restore missing records, but cannot
overwrite a different existing record. Historical UNKNOWN and resource
limit outcomes remain unchanged.

The direct replay rebuilds only the original 56,994-clause formula.
The independent registry audit reconstructs the row coefficients,
transports, Gram positions, population identity, and seed evaluations
without importing the subject builder or invoking a solver.

## Exact clause implications

Write a proved inequality as

\[
\sum_{i=1}^{480} c_i z_i \leq 0,
\qquad z_i\in\{0,1\}.
\]

An individual row inequality is stored in this form as

\[
d_a z_a-\sum_{b\in N(a)} w_b z_b\leq0,
\qquad d_a>0,\quad w_b>0.
\]

For $z_a=0$, the inequality holds automatically. For $z_a=1$, it
is precisely the previously proved row-capacity condition.

A proposed clause fixes some variables when every literal is false.
If those fixed values make the minimum possible left side strictly
positive, every solution of the proved inequality must satisfy the
clause. There are two exact bound calculations.

For the independent bound, an unfixed coordinate contributes

\[
\min(0,c_i).
\]

For the population bound, let $k$ be the number of fixed ones.
Among all unfixed coordinates, choose the $60-k$ smallest
coefficients. Their sum, together with the fixed contribution, is the
exact minimum under $\sum_i z_i=60$. All 480 coordinates participate,
including coordinates with coefficient zero.

The population premise follows from the original diagonal Gram rows.
Every triple selector occurs in exactly three diagonal supports, and
the eighteen diagonal demands all equal ten. Hence

\[
3\sum_i z_i=18\cdot10=180.
\]

The frozen generic helper
`integer_cut_clause_explanations.py` computes and checks both bounds.
Each accepted clause records its originating inequality, transport,
coefficient hash, falsifying-assignment minimum, and strict integer
margin. The population-based clause records its additional premise.

Both clause families are retained. A shorter clause is not assumed to
be stronger. Some population clauses reject a complete selection of
sixty columns. Their validity comes from a proved inequality and the
exact population identity, not from an unsupported decision to avoid
that selection.

## Relabelings and seed formula

Each of the twelve verified core relabelings maps the complete
signature domain to itself. The clause and its coefficient vector are
transported in the same direction. The exact integer bound is then
checked again. This transports a necessary implication; it does not
assert a symmetry of an unknown completed graph.

Both explanation families are generated for every registry violation
of the thirty saved seed selections. All twelve transports are checked.
Duplicate literal lists are removed, including duplicates of existing
primary-only base clauses.

The resulting initial formula has:

| Quantity | Value |
|---|---:|
| Primary selectors | 480 |
| Total variables | 28,308 |
| Base clauses | 56,994 |
| Added explanation clauses | 1,212 |
| Total clauses | 58,206 |
| Literal occurrences | 261,828 |
| New auxiliary variables | 0 |
| DIMACS bytes | 1,403,385 |

The initial DIMACS SHA256 is
`d5fb704ee9284e5230bbaea384b39f167358460e282b2e641a7e29d076cb216f`.
Every seed selection is rejected by a checked clause. No seed selection
or complement is fixed as an incidence.

Adapter controls check 4,236 transported exact implications and 22,662
explicit Boolean implication cases. They use no SAT solver. The prior
generic-helper controls and independent audit remain dependencies.

## Bounded continuation protocol

The prepared limits are 180 seconds overall, at most 500 SAT calls,
and at most twenty full row passes. A SAT call receives at most ten
seconds. Individual-row passes and shared-edge LPs each receive at most
sixty seconds, within the remaining overall budget. The original
one-million-variable and two-million-clause ceilings remain unchanged.

For each SAT candidate, the runner checks the returned full CNF
assignment. It then saves an independent primary inspection of the
original incidence and the actual explanation-clause prefix. It
evaluates all registry inequalities before using any inspector that
would reject an unencoded inequality violation.

If a registry inequality is violated, the runner adds both exact
explanation families and their verified transports. It makes no row LP
call for that candidate. At least one new clause must reject the current
candidate, which already satisfied the old clause prefix.

When every registered inequality holds, the existing exact row
separator may run. Newly proved row cuts enter the registry before
their explanations are generated. Only a complete pass with sixty
exact rational row boxes can invoke the symmetric shared-edge LP.
An exact shared ray gives the previously proved full-domain selector
cut and its twelve transports. An exact shared-edge point stops the
loop as a necessary-relaxation witness, without claiming a graph.

The runner stops on UNKNOWN, an uncertified numerical outcome,
resource or budget limits, or an error. It preserves all exact cuts,
candidate prefixes, clause proofs, row witnesses, and shared-edge
records. It makes no Gram-equality shifts and adds no visitation blocks.

## Replay and UNSAT gate

The cold replay reconstructs the original formula and directly checks
the complete initial mathematical registry. It deterministically
regenerates the seed clauses, every later clause batch, and all registry
updates. It checks each candidate against its actual saved prefix and
replays every integer obstruction or rational witness. The final CNF
hash is recomputed from these necessary constraints.

Incremental UNSAT is uncertified. The separate wrapper first performs
this complete reconstruction, then runs one fresh proof-enabled query
for at most sixty seconds. Direct DRAT checking has its own sixty-second
bound. A separate cold replay reconstructs the formula again, verifies
that each retained input clause belongs to it, and checks the retained
proof under a further sixty-second bound.

Only a successful fresh proof and both proof checks could exclude the
stated component-zero stratum. They would not exclude all shell
components or solve the unrestricted Conway99 problem.

## Files and preparation

- `experiments/workspace/root_prism_free_f0_lazy_registry.py`
- `experiments/workspace/root_prism_free_f0_lazy_clauses.py`
- `experiments/workspace/root_prism_free_f0_lazy_row_loop.py`
- `experiments/workspace/root_prism_free_f0_lazy_row_loop_certificate.py`
- `experiments/logs/root-prism-free/f0-lazy-registry.json.gz`
- `experiments/logs/root-prism-free/f0-lazy-row-loop-preparation.json.gz`
- `experiments/logs/root-prism-free/f0-lazy-row-loop-preflight-replay.json`

The preparation and cold preflight invoke neither an optimizer nor an
incidence solver. A new bounded query requires the coordinator's source
and preparation review.
