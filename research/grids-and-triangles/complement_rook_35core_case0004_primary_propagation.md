# Exact primary propagation for case4

This package prepares explicit propagation proofs on the unchanged case4
incidence constraints. It does not run the case4 closure or a solver.
The eight additional fixes reported by the lazy native run have no saved
primary IDs or proof reasons. They are not used as premises here.

## Signed Boolean bounds

Write each original row as

\[
L\leq \sum_j c_jx_j\leq U,\qquad x_j\in\{0,1\}.
\]

Coefficients are integers. Repeated occurrences of a variable are added,
and zero coefficients are removed. Given previously proved assignments,
let `fixed` denote their contribution and let \(F\) be the free variables.
The exact interval bounds are

\[
m=\mathrm{fixed}+\sum_{j\in F}\min(0,c_j),\qquad
M=\mathrm{fixed}+\sum_{j\in F}\max(0,c_j).
\]

If \(m>U\) or \(M<L\), the row contradicts the prior assignments.
For a free variable \(x_a\), setting it to \(b\in\{0,1\}\) changes the
bounds to

\[
m_b=m-\min(0,c_a)+c_ab,\qquad
M_b=M-\max(0,c_a)+c_ab.
\]

If this conditional interval misses \([L,U]\), then \(x_a=1-b\) follows.
This is an interval implication. It does not claim complete integer
feasibility of a row whose interval intersects its bounds.

The 2,271 translated rows preserve all 630 Gram positions, 186 original
signature capacities, 1,365 triple capacities, 30 Gram conflicts and
60 uncapped exterior-row inequalities. A weighted inequality retains its
negative target coefficient. No coefficient or demand is capped.

## Guarded covers

A complete registry record gives

\[
x_a\leq\sum_{b\in S}x_b.
\]

If every cover variable is already zero, then \(x_a=0\). If the target
is one and exactly one cover variable remains free while the others are
zero, the remaining variable is one. A target equal to one with an empty
remaining cover gives a contradiction. A zero target or an already
selected cover member satisfies the clause.

These rules are the signed Boolean interval rules applied to the cover
row. The implementation uses the frozen packed registry directly. It
retains all 178,533 covers, including the 14 initial unit clauses.

## Reason traces and finite bounds

Each assignment records its original row or cover ID, its excluded
Boolean value, and the indices of all earlier assignments used in that
row. Signed-row records also save the original and conditional integer
bounds. A replay reconstructs each original row and checks the excluded
value using direct integer arithmetic. It does not accept a native solver
message as a reason.

The procedure assigns each of the 1,214 variables at most once. There
are at most 1,214 assignment records, optionally followed by one final
contradiction. Each nonterminal sweep makes a new assignment, so at most
1,215 sweeps are possible. A time limit can stop the procedure with a
partial exact trace; such a trace does not claim a complete fixed point.

For a completed fixed point, replay checks every original row and every
registered cover for a remaining one-variable interval implication.
This is completeness for the stated propagation rules. No failed-literal
probing or arbitrary Boolean search is included.

## Controls and scope

The controls compare interval implications with direct truth tables for
94,500 signed-row partial assignments and 2,592 guarded-cover partial
assignments. They include negative and zero coefficients, satisfiable
and contradictory chains, and coefficients of 100 bits. Every reason
chain is replayed separately.

The successful preparation binds the complete original row inventory,
cover registry and existing ledger replay. The first preparation attempt
stopped at an input-schema assertion because the case field is a record,
not an integer. Its source and log are retained. The corrected preparation
checks the case index and matching index explicitly. No case4 closure
ran in either attempt, and this package contains no new selector unit.
