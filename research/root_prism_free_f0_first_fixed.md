# First fixed incidence with the full second component domain

## Scope

This model conditions on the saved 60-triple incidence for component
zero, then leaves the second component incidence free. Both shell
components are component zero, with identity relative fiber alignment.
The broader setting is the globally prism-free, $F$-free, split
$18+18$ shell case. The model has 5,472 possible six-neighbor columns.

The first incidence is the checked point in
`experiments/logs/root-prism-free/f0-incidence-case00-run01/result.json`.
It has 60 distinct triples, the exact 18-component Gram matrix, and all
90 saved local motif restrictions. It is an incidence point, not a
completed graph. Fixing it is a restriction for a construction attempt.
No claim is made that it represents every possible first incidence.

The second component retains all 480 admissible triples. No second
design is fixed and no graph symmetry is imposed. In particular, the
fractional control described below imposes no equality or orbit
condition on a binary solution.

## Variables and equations

Write the first design as $a_0,\ldots,a_{59}$, and write the full second
triple domain as $b_0,\ldots,b_{479}$. A pair $(i,j)$ is eligible
exactly when its three-fiber occupancy vectors add to $(2,2,2)$.
There are 5,472 eligible pairs. The associated binary variable
$x_{ij}$ selects the six-neighbor column $(a_i,b_j)$.

Every outside vertex has exactly three neighbors in each component.
Two outside vertices cannot have the same first triple, because they
would share three common neighbors. Thus the 60 distinct first triples
label the 60 outside vertices, and

\[
\sum_jx_{ij}=1\qquad(0\le i<60).
\]

For each second triple, a derived binary selector $v_j$ satisfies

\[
\sum_ix_{ij}+(1-v_j)=1.
\]

This signed exact-one equation enforces both
$v_j=\sum_ix_{ij}$ and the required second-triple multiplicity bound.
All 480 second selectors remain available.

Let $G$ be the residual Gram matrix of the complete 39-core. The
first-component Gram block holds identically once all 60 first row
quotas hold, because the fixed first design has already been checked.
The second Gram block is imposed on the derived selectors. Its 171
upper-triangular positions reduce to 150 distinct nonempty equalities;
empty supports have quota zero and are checked separately.

All 324 cross-component equations are imposed directly:

\[
\sum_{i,j:\ s\in a_i,\ t\in b_j}x_{ij}
=2-\mathbf1_{\lfloor s/6\rfloor=\lfloor t/6\rfloor}.
\]

The three central vertices have no outside neighbors, so their 114
upper-triangular Gram positions are zero. These facts account for all
780 upper-triangular positions, or all 1,521 entries of $G$. The 60
first row quotas also force the total number of selected columns to be
60. No additional population counter is necessary.

## Packing and motif restrictions

Two selected outside columns may share at most two core vertices. The
model covers every one of the 7,140 triples of shell vertices:

| Coverage reason | Core triples |
| --- | ---: |
| At most one candidate column | 2,466 |
| Fixed first row quota | 60 |
| Second component link | 480 |
| A contained quota-one Gram pair | 3,558 |
| Explicit mixed triple capacity | 576 |

Each explicit capacity is an at-most-one constraint on every candidate
column containing that triple. A quota-one first-component pair is
valid for this coverage because the fixed first design and the 60 row
quotas reproduce its full Gram block exactly.

The saved component motif package contains 78 $F$-conflicts and 12
prism conflicts. The first design avoids all 90. The second selectors
receive the corresponding 90 binary clauses. These clauses use the
previously replayed visible motifs and cap-forced missing edges; they
do not treat unspecified outside edges as absent.

## Exact positive controls

The saved fractional control has common denominator 144, with 2,916
positive paired-column weights and 234 second triples of positive
weight. The new preparation independently evaluates every one of its
1,590 linear cardinality rows, all 90 second motif inequalities, and all
1,521 full Gram entries. They all hold exactly.

That rational point is a control for the primary linear specification.
It is not a Boolean assignment or a CNF satisfiability witness. In
particular, fractional feasibility cannot establish the existence of a
second incidence design.

The preparation also reuses the frozen exhaustive signed-link
controls, small cardinality-size controls, and the direct nine-vertex
rook incidence control. Deleted and repeated actual columns are
rejected by the exact incidence inspector. No SAT solver is called by
preparation, construction, or replay.

## Encoding size and replay

There are 5,472 paired-column variables and 480 derived second
selectors. Sequential cardinality counters use one shared monotone
auxiliary pool.

| Constraint family | Rows | Auxiliary variables | Clauses |
| --- | ---: | ---: | ---: |
| Fixed first row | 60 | 5,412 | 16,236 |
| Second component link | 480 | 5,472 | 16,416 |
| Second component Gram | 150 | 27,828 | 56,460 |
| Cross Gram | 324 | 158,004 | 328,284 |
| Mixed triple packing | 576 | 21,072 | 62,640 |
| Second component motifs | 90 | 0 | 90 |
| Total, including primary variables | 1,680 | 223,740 variables | 480,126 |

The formula has 1,117,380 literal occurrences. Each counter's actual
variable, clause, and literal counts must agree with the exact size
preparation. The source streams one counter at a time and records
clause-block hashes. It does not retain the full clause list in memory.

The built formula has exactly those counts and occupies 8,321,269
bytes. Its SHA256 is
`65683cfd4c60654b20eebf4261079833a4bd9f4ebf2d5babe446983e209a469a`.
The cold domain/specification/CNF replay reproduced the same hash and
all clause-block counters. No solver query is part of this package.

The source is
`experiments/workspace/root_prism_free_f0_first_fixed.py`. The preparation
and built model are under
`experiments/logs/root-prism-free/f0-first-fixed*`.
The built-model record binds the exact CNF, source dependencies, frozen
input certificates, column order, and complete constraint specification.
A cold replay reconstructs those inputs and streams a fresh CNF before
comparing its exact hash and counters.

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_first_fixed.py replay \
  --model experiments/logs/root-prism-free/f0-first-fixed-built-model.json \
  --output /tmp/f0-first-fixed-cold-replay.json
```

## Required interpretation of a later solve

A SAT assignment must pass the full primary inspector. The inspector
checks the fixed first row assignment, all derived second selectors,
all Gram entries, complete triple packing, all known 99-vertex caps,
and the two saved motif families. It also reports any further visible
prism or $F$ found in the resulting partial graph.

Even a passing incidence point still needs the 240 edges of an
8-regular graph on the 60 outside vertices. It is not a solution of
the original graph problem.

A checked UNSAT result would exclude only this fixed first incidence,
component-zero second shell, and identity fiber alignment. It would not
exclude all component-zero incidences, all component pairs, or the
entire split case.

There is also a separate necessary exterior equation for the fixed
first incidence $H_1$, with shell adjacency $A_1$:

\[
H_1D=2J-H_1-A_1H_1,\qquad D\mathbf1=8\mathbf1.
\]

It follows from the mixed core/outside equations and does not depend on
the second incidence. A separate coordinator-owned test of that
condition can reject the first design before this coupling model is
solved. Neither model assumes that unspecified exterior edges vanish.
