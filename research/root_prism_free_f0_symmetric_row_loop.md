# Free incidence continuation with shared-row cuts

This separate continuation retains all 480 free component-zero
incidence selectors. It starts from the complete original incidence
formula, the 12 earliest row cuts, the 36 later individual-row weighted
cuts, and the 12 signed cuts from the exact shared-edge contradiction.
No prior incidence or second component is fixed.

The preparation exposes a bounded search and exact replay. A main
query is not part of the preparation package.

## Signed-cut encoding

A necessary signed inequality has the form
$\sum_a c_a z_a\leq0$. It is equivalent to the positive-weight literal
threshold

$$
\sum_{c_a<0}(-c_a)z_a+
\sum_{c_a>0}c_a(1-z_a)
\geq\sum_{c_a>0}c_a.
$$

The adapter calls the already checked positive-weight decision-graph
encoder on the absolute primary IDs. It then substitutes a negated
primary literal for every positive coefficient, only within the new
cut clauses. Negative coefficients retain positive primary literals.
All auxiliary IDs remain unchanged. One fresh guard is forced true.
This Boolean substitution preserves the encoder's existential
equivalence proof and adds no separate restriction on the original
selectors. An inequality with no positive coefficient is a tautology.

The actual signed clauses passed 11,207 complete primary assignments
across 785 small formulas, including both signs, zero coefficients,
large weights, unused ID gaps, and resource refusal. A separate
read-only review accepted the conversion, substitution, fresh guard,
and auxiliary-ID handling.

## Initial formula

| Item | Exact count |
| --- | ---: |
| Original free incidence selectors | 480 |
| Earlier direct row cuts | 12 |
| Individual-row weighted cuts | 36 |
| Signed shared-row cuts | 12 |
| Variables before the signed suffix | 40,932 |
| Signed-suffix auxiliary variables | 12,204 |
| Total variables | 53,136 |
| Clauses before the signed suffix | 78,222 |
| Signed-suffix clauses | 20,052 |
| Total clauses | 98,274 |
| Literal occurrences | 287,244 |
| DIMACS bytes | 1,795,463 |

The CNF SHA256 is
`70d626cccaff274c7df91c9c1c6665f44a0b75367918d987e71df121681d8c47`.
The preparation is
`experiments/logs/root-prism-free/f0-symmetric-row-loop-preparation.json.gz`,
SHA256
`ac320bcd92d1e801fc027ca7776ad97ebe978628b530caa67ceb5d770c992a55`.

The preparation reconstructs the complete original domain and formula,
replays every initial cut, and checks the signed suffix. It also
tests the dynamic shared-edge helper against the previously frozen
1,220-edge contradiction, including the complete ray and all 12
published selector-cut transports. This control calls no optimizer.

## Search stages

Each SAT result is checked against the original Gram, occupancy and
motif conditions, all retained individual-row inequalities, and every
signed selector cut. Its exact point is saved before separation.

The first separation stage processes all 60 selected target rows.
It reuses the frozen individual-row routine. Numerical LP results
can propose integer potentials or rational row boxes, but every
accepted object passes exact arithmetic checks. Necessary individual
cuts receive all 12 verified core transports and are added to the
free-selector formula.

Only a complete pass with 60 exact row boxes and no obstruction
reaches the shared-edge stage. That stage constructs one undirected
variable for each eligible edge among the selected signatures. It
retains all 1,080 mixed equations, all 60 degree equations, and edge
bounds from zero to one. It uses one fresh bounded LP call.

A feasible numerical result stops as unresolved unless rational
reconstruction passes every equation and bound. An exact rational
shared-edge point stops the loop with a necessary partial incidence,
not a graph. A numerical infeasibility result requires a complete
integer Farkas certificate. Its row potentials are then extended by
zero to the full signature domain, and every positive edge weight is
allocated over all 68,394 eligible edges. The resulting universal
selector cut and all 12 core transports are replayed before insertion.

The selected incidence determines potential support and endpoint
allocation only. It is not a hypothesis of a retained cut. The loop
adds no visitation block, orbit equality, or graph-symmetry condition.

## Bounds and terminal meanings

The prepared limits are at most 20 incidence queries, ten seconds per
SAT call, 60 seconds per individual-row pass, 60 seconds per shared
LP, and 180 seconds overall. The overall clock includes input checks,
bootstrap, exact verification, and cut construction. Cooperative
overruns are recorded.

The loop stops on an unresolved numerical or SAT status, a failed
exact check, a resource limit, a time or incidence limit, an exact
symmetric row box, or incremental UNSAT. It does not broaden a
search after one of those outcomes. Encoding limits refuse a cut
without returning a partial formula; they impose no mathematical
constraint on the selectors.

The individual and signed cut registries are separate. Every
transport records its origin and its retained index. Every incidence
is checked against its actual current cut prefix. The cold replay
reconstructs those prefixes, every row witness or integer ray, each
global lift, and the exact final CNF.

Incremental UNSAT remains uncertified. The separate proof driver
rebuilds the complete final necessary formula, runs a fresh
proof-enabled query, and checks DRAT. A second cold rebuild checks
retained-input inclusion and DRAT again. Only this complete gate can
exclude component zero under the stated conditional hypothesis.

## Sources and scope

The new files under `experiments/workspace/` are:

- `root_prism_free_f0_signed_threshold.py`, the signed-literal adapter.
- `root_prism_free_f0_shared_row_separator.py`, the dynamic LP and exact lift.
- `root_prism_free_f0_symmetric_row_loop.py`, preparation, search, and cold replay.
- `root_prism_free_f0_symmetric_row_loop_certificate.py`, fresh proof and retained replay.

They preserve all earlier frozen sources and artifacts. The hypothesis
is component zero in the globally prism-free and $F$-free split
$18+18$ shell. No statement here excludes another component, the
connected shell cases, or the unrestricted Conway99 problem.
