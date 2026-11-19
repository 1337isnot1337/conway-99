# Binary incidence model for the first 35-vertex core

This model tests necessary binary incidence conditions for one of the
2,521 indexed local cores. It does not model the graph among the 64
remaining vertices. A feasible point is a partial incidence witness; an
infeasibility certificate excludes only the indexed core and its verified
relabelings.

The complete attachment construction and the forced population counts
are proved in
[`complement_rook_35core_domains.md`](complement_rook_35core_domains.md).
The new implementation is
[`complement_rook_35core_incidence.py`](../../experiments/workspace/complement_rook_35core_incidence.py).
It leaves the earlier star and joint-completion sources unchanged.

## Fixed case and variables

Case zero uses original signature indices

\[
(0,1,9,10,18,20,26,27)
\]

for the eight added core vertices. In that order, their matching is

\[
\{\{0,2\},\{1,5\},\{3,7\},\{4,6\}\}.
\]

Every admitted attachment column has its own binary variable. All 1,206
columns are retained. Their attachment counts are 16 columns with zero
local attachments, 611 with one, and 579 with two. This describes the
candidate domain; a feasible selection must instead have counts
$(4,40,20)$.

The CNF contains all 630 unordered Gram equalities, with identical
equations deduplicated. These are 394 positive equations and one empty
zero equation. It also contains 186 explicit at-most-one constraints for
original signatures with multiple choices.

All 1,347 nontrivial core-triple capacities are covered. For 1,335 of
them, the model metadata identifies a containing Gram pair with quota
one and checks the inclusion of their variable supports. The remaining
twelve capacities are encoded explicitly. The source uses a single fresh
auxiliary-variable pool for the sequential counters.

| Formula component | Clauses |
|---|---:|
| Exact Gram equalities | 214,392 |
| Original-signature multiplicity | 2,823 |
| Additional triple capacities | 618 |
| Total | 217,833 |

There are 1,206 primary variables and 106,697 variables in total.
Population 64 and attachment counts $(4,40,20)$ follow from the Gram
rows; no separate population counter is added. No assumption on the
parameter $a$, no extra spectral cut, no orbit equality, and no fixed
64-column design is imposed.

## Controls and certificate scope

The preparation checks 896 complete primary assignments against the
small equality and at-most-one counter encodings. A separate positive
control uses an actual nine-vertex rook graph, a five-vertex induced core,
and its four remaining incidence columns. The exact Gram model accepts
that assignment and rejects it after one selected column is deleted.

The saved preparation binds the source hashes, full local-core index,
compressed domain prefix, case-zero domain, Gram target, and exact CNF.
A cold reconstruction reproduced the domain and CNF bytes. The model
record is
[`complement-rook-35core-incidence-case0000-model.json`](../../experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-model.json).

For SAT, the direct verifier requires 64 selected columns with distinct
old signatures, checks all 1,225 dense Gram entries, and checks all 2,016
selected-column pairs for overlap at most two. The pair check covers
every triple capacity, including those omitted from the CNF because a
Gram equality implies them. It also checks the attachment counts and the
729 Gram entries of the reconstructed 72-column old-core incidence.
It records the parameter $a$ without adding a restriction on it.

For UNSAT, the runner obtains a proof from a fresh solver with no
assumptions. It checks DRAT and retains the used input clauses. A separate
replay reconstructs the entire case-zero domain and formula, verifies the
full CNF hash and retained-clause inclusion, and checks the retained DRAT
proof. An unchecked solver status is not an exclusion. A timeout is
recorded as UNKNOWN.

Preparation replay:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_incidence.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-incidence-case0000-model.json \
  --output /tmp/complement-rook-35core-case0000-preparation-replay.json
```

The main model has not been solved in the preparation checkpoint.
