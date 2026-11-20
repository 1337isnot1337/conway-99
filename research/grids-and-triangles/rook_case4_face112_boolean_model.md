# Complete Boolean formula on the 112-zero face

The new formula preserves every clause of the earlier complete 99-zero
model and adds the proved integer restrictions. It has 135,022 variables,
441,164 clauses and 13,556,679 literal occurrences. Preparation, exact
suffix reconstruction, parent-byte checking, source review and cold
model replay pass. The subsequent single bounded query is UNKNOWN.

This remains a model of the 64 exterior incidence signatures for indexed
35-core case four. It does not contain the full exterior adjacency graph.
A checked SAT answer would give an incidence witness. A checked UNSAT
proof would exclude this indexed core, not every possible Conway graph.

## Parent and added constraints

The retained parent has 134,852 variables and 439,689 clauses. It contains
all original native constraints, all 178,533 coordinate covers and the
99 proved selector zeros. Every byte after its original DIMACS header
is copied unchanged. The old complete original-encoder cold certificate
is bound by its hash; this preparation does not repeat that domain census.

The suffix contains exactly these clauses:

| Constraint | Clauses | New auxiliary variables |
|---|---:|---:|
| Thirteen further negative primary units | 13 | 0 |
| Two parity sums equal to one | 952 | 0 |
| `x259+x590<=1` | 1 | 0 |
| At most two among the 86-column support S | 423 | 170 |
| At least two among S | 86 | 0 |
| Total | 1,475 | 170 |

After the 112 zeros, the parity supports have 35 and 41 columns, with
31 in common. Two positive clauses impose the lower bounds. Their
pairwise upper bounds produce 950 distinct negative binary clauses.
No auxiliary variable is needed for these two exact-one constraints.

The separate bound certificate gives
`x259+x590<=31387/16384<2`. Boolean integrality permits the appended
negative pair clause. Three other pair bounds from the same scan are
already consequences of original Gram row 580 and are not appended.

The refined column-663 identity is

\[
3x_{663}+\sum_{a\in S}x_a=2,\qquad |S|=86.
\]

It uses original Gram equations and the proved first parity equality.
Thus column 663 is zero and the sum over S is exactly two. The other
twelve new zeros come from the earlier 42-row Gram identity. Every
bound coefficient and the 1,214-coordinate identity have an independent
integer replay. No numerical point or assumed graph symmetry is used
as a premise.

## Transparent encoding of the sum of two

For the first 85 inputs, the encoder introduces two prefix bits. They
record that at least one, or at least two, inputs in that prefix are
true. The clauses propagate the first bit, propagate the second bit,
and force the second bit when a new true input follows a prefix already
containing one. A further true input is forbidden after the second bit.
The first second-bit is false.

If three inputs were true, these implications would force a conflict
at the third. If at most two are true, their actual prefix counts give
a satisfying assignment to every auxiliary bit. This proves both
directions of the at-most-two encoding. The new IDs are exactly 134853
through 135022, beyond every parent variable.

At least two true inputs is equivalent to the following 86 clauses:
delete each input in turn and require a true input among the remainder.
With zero or one true input, a clause fails. With at least two, every
clause holds.

The implementation checks all 508 primary assignments for lengths two
through eight. Accepted assignments receive their explicit prefix-bit
extension; rejected assignments produce a unit-propagation conflict.
These controls invoke no SAT solver. A separate source and arithmetic
checker reconstructs the production suffix without importing the encoder.

## Formula and proof gates

The parent CNF has SHA256
`f3467d02ca6763391668c0cdac0a395dab23688d831b25107fcf04ea1c94ac22`.
All 439,689 parent clause lines and 57,874,444 body bytes remain intact.
The new suffix has SHA256
`2ea386a2d14faee1314747433bc52b989fff4d81b934898d55d521235860a848`.
The full 57,922,938-byte CNF has SHA256
`aa4a35139c75ecb857ed55af73bd20411d267fd20fa6b2593ef16a7485c528ef`.
The large reproducible CNF is kept outside the tracked source tree;
the tracked model records its exact generation and hashes.

The query driver reuses the preceding proof-capable CaDiCaL300 driver.
Its text and AST substitutions are recorded. Child ownership, resource
limits, proof export and direct/cold DRAT checks remain unchanged.
The native SAT inspector additionally checks all 112 zeros, both parity
sums, the pair exclusion and the 86-column sum.

The numerical query budget is one 180-second owned SAT child, including
setup and export. There is no automatic retry. An UNSAT answer requires
a direct checked proof, exact retained-input inclusion, a separately
rebuilt full formula and a cold checked proof. Each proof-check phase
has its recorded 60-second budget. A timeout, partial proof or failed
checker yields no case exclusion. The saved tiny proof passes the
unchanged DRAT binary; preparation runs no new solver query.

## Frozen records

- Overlay source: `experiments/workspace/rook_case4_face112_boolean_overlay.py`,
  SHA256 `6e96e8712b1af1bf355de8b69ac2dac358b73e27f8e68c9d500037ab7117d150`.
- Model: `experiments/logs/grids-and-triangles/rook-case4-face112-boolean-preparation01/model.json`,
  SHA256 `d4b3b0a8df5663a703932bfb4c5afcc27093fffe3304f5bdda50c9180a93cdb2`.
- Cold model replay: `experiments/logs/grids-and-triangles/rook-case4-face112-boolean-preparation01-cold.json`,
  SHA256 `485cf967289bbabd728f7648d8b84cd2bd7fbdfd0492628b9c0ddb9734629fc1`.
- Query source: `experiments/workspace/rook_case4_face112_boolean_query.py`,
  SHA256 `c79ff548abf28ee4300b974e3f4a4e864647a4690b5ab3c8b8b0efa920c7f4b9`.
- Query preparation: `experiments/logs/grids-and-triangles/rook-case4-face112-boolean-query-preparation.json`,
  SHA256 `7039ecf70eb0ec50d21f537c9979cf157223a3214dc7b82fb6bd11f4c00b9c7c`.
- Independent overlay and driver reports:
  `rook-case4-face112-boolean-independent-review.json` and
  `rook-case4-face112-boolean-query-independent-review.json` in the same
  log directory, SHA256 `740a45f4996bb1ff7b8589309856e6f7e9e553697ba44cda3830496c47f607bc`
  and `fb7f5903e23dda3b8c80fa2d1c59e03d58c8eb1e8d39489f2eea006c29684a11`.

## Terminal query

The one authorized CaDiCaL300 child loads all 441,164 clauses in 6.526
seconds, then reaches its 180-second limit without returning SAT or
UNSAT. The parent saves UNKNOWN before killing and reaping the child.
The total parent interval is 181.932 seconds, including supervision and
terminal writes. No partial proof is accepted and no retry is queued.

A separate cold replay reconstructs the complete new formula, rechecks
its mathematical premises, and verifies the unresolved process record
in 4.708 seconds. It calls no solver or proof checker. Case four remains
open.

The terminal result is
`experiments/logs/grids-and-triangles/rook-case4-face112-boolean-run01/result.json`,
SHA256 `39fb9259a7b108affd650f8acb5d33a3685b3429977c907ac0a6e1c709a1017b`.
The cold report is
`experiments/logs/grids-and-triangles/rook-case4-face112-boolean-run01-replay.json`,
SHA256 `75d8b8952044c1279b38676bdbd3f19211f677cbb514930dc9d8587507f816e1`.
