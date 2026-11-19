# Free incidence loop with exact exterior-row cuts

The prepared model retains all 480 component-zero incidence selectors.
It contains the complete original Gram and motif constraints, the 12
earlier exterior-row cuts, and 36 full weighted inequalities from the
complete row check of the replacement incidence. No first incidence,
second component, or graph symmetry is fixed.

The preparation and cold reconstruction passed. The bounded main loop
has not been run as part of this preparation package.

## Mathematical scope

The model concerns component zero in the globally prism-free and
$F$-free split $18+18$ shell. It is a necessary incidence model.
An incidence point, including one whose separate exterior-row box
relaxations are all feasible, does not specify a graph.

For a selected signature $a$, let $q_a=2\mathbf1-h_a-Ah_a$ be its 18
mixed quotas. Every actual exterior row uses eight distinct selected
neighbors from the complete eligible set $N(a)$. For every integer
potential $v$ with $d=v^Tq_a>0$, it follows that

$$
\sum_{b\in N(a)}\max(v^Th_b,0)z_b\geq d z_a.
$$

This is the only source of new inequalities in the loop. Each vector,
each positive coefficient, and each demand is checked with integer
arithmetic. All 12 transported inequalities use individually verified
core relabelings. They impose no automorphism on the unknown graph.

The initial inequalities have demands 5, 3, and 10 before Boolean
normalization, each with 12 transports. The demand-three family has
all positive coefficients equal to three, so its normalized threshold
is one. The model uses these full inequalities rather than their
weaker saved cover clauses.

## A counting subfamily

For any subset $T$ of the 18 component vertices, each neighbor triple
contributes at most two incidences into $T$, plus one if it lies wholly
inside $T$. Therefore every selected target satisfies

$$
\sum_{\substack{b\in N(a)\\h_b\subseteq T}}z_b
\geq \bigl(q_a(T)-16\bigr)z_a
\qquad\text{when }q_a(T)>16.
$$

Equivalently, with $U$ the complement of $T$,

$$
\sum_{\substack{b\in N(a)\\h_b\cap U=\varnothing}}z_b
\geq \bigl(8-q_a(U)\bigr)z_a
\qquad\text{when }q_a(U)<8.
$$

These are the integer-potential inequalities for
$v=3\mathbf1_T-2\mathbf1$, divided by three. The saved target-349
certificate is one instance: $q_a(T)=17$ and the corresponding
38-term threshold-one clause is necessary. No enumeration of all
subsets $T$ is included in this preparation.

## Exact weighted-threshold encoding

The installed optional pseudo-Boolean interface is unavailable because
its `pindakaas` dependency is absent. The separate encoder uses a
Boolean suffix decision graph instead.

For a guarded inequality $z_a\Rightarrow\sum_i w_i x_i\geq d$,
all weights are positive integers. Capping each weight at $d$ preserves
the Boolean predicate. Dividing the capped weights by their greatest
common divisor and rounding the divided threshold upward also
preserves it.

A suffix node represents the predicate that its remaining variables
supply a remaining demand. Its two child predicates are `lo` when
the next primary bit is zero and `hi` when that bit is one. The node
uses only the forward clauses

```text
(-node OR x OR lo)
(-node OR -x OR hi)
```

Boolean constants are simplified, identical children are aliased, and
the false/true child pair is replaced by the primary bit itself. The
final guard is `(-target OR root)`.

If the root is forced true, the actual primary bits force one child at
each node. The acyclic suffix chain must end at a true terminal, which
proves the weighted threshold. Conversely, a primary assignment that
satisfies the guarded inequality extends by assigning each auxiliary
its actual suffix-predicate value. Thus reverse implications are
unnecessary. The encoding is existentially equivalent to the exact
guarded weighted inequality.

Each new auxiliary ID is larger than the current formula maximum.
The implementation distinguishes Boolean constants from integer
variable one. Its explicit stack avoids recursion-depth restrictions.
A state or formula-size resource limit aborts encoding without adding
a partial cut; it is not a mathematical restriction on the model.

The actual encoder clauses passed 31,582 complete primary-and-guard
assignments across 1,149 small formulas. These controls include empty
domains, impossible demands, large weights, gcd normalization, unused
ID gaps, and resource refusal. A separate read-only mathematical
review accepted the normalization, branch clauses, aliases, and fresh
ID handling.

## Initial formula

| Item | Exact count |
| --- | ---: |
| Free incidence selectors | 480 |
| Original clauses plus 12 earlier cuts | 56,994 |
| New full weighted inequalities | 36 |
| Added clauses | 21,228 |
| Added auxiliary variables | 12,624 |
| Total variables | 40,932 |
| Total clauses | 78,222 |
| Literal occurrences | 227,208 |
| DIMACS bytes | 1,411,145 |

The initial CNF SHA256 is
`14a4d6774f1691c1000405c2e30b50f9c83463eb7ae559510415d94a38cc849e`.
The preparation file is
`experiments/logs/root-prism-free/f0-incidence-row-loop-preparation.json.gz`,
SHA256
`5cbd2258dda48edb400e4aad12c21f727c747041fc7f8e88f01d8f548a759248`.

Cold reconstruction repeated the complete component coverage, rebuilt
the original formula and earlier cuts, replayed all three new integer
certificates and their transports, regenerated every weighted
encoding, and reproduced the DIMACS hash. It called no incidence
solver or optimizer.

## Bounded loop and provenance

The frozen runner permits at most 20 incidence queries, at most ten
seconds per SAT call, at most 60 seconds per complete selected-row
pass, and at most 180 seconds overall. The overall clock includes
initial loading, bootstrap, exact checks, and cut assembly. Cooperative
budget overruns are recorded explicitly.

Each SAT point must first pass the full original incidence inspector,
all earlier cuts, and every currently retained weighted inequality.
All 60 selected rows are then processed in increasing signature order.
A numerical LP can propose a separating integer vector or a rational
row box. The vector is retained only after exact strict-gap replay;
the box is accepted only after every rational equality and bound passes.
All numerical-only outcomes stop the loop as unresolved.

Each accepted vector generates its 12 checked transports. Equivalent
Boolean predicates are deduplicated deterministically, with every
transport mapped to its retained cut index. No visitation block is
added. The earlier incidence points remain controls and provenance,
not restrictions on subsequent selections.

The loop stops on UNSAT, UNKNOWN, error, a resource limit, either
iteration/time budget, or a complete pass with no new exact row
obstruction. Every candidate, row result, cut origin, encoding range,
and final formula hash is retained. A cold replay reconstructs each
cut prefix before checking its saved incidence and regenerates the
complete final formula without an optimizer or SAT query.

## Proof gate

An incremental UNSAT answer remains explicitly uncertified. The
separate certificate driver reconstructs the final formula from the
original model and exact cut certificates, then makes a fresh
proof-enabled query. A direct DRAT check is followed by a separate
cold rebuild, retained-input inclusion check, and DRAT replay.
Only a successful final gate can exclude component zero in this
conditional split case. It cannot exclude other component types or
the unrestricted Conway99 problem.

The bounded search and proof stages use separate records. No completed
loop outcome or new component exclusion is included in this preparation
note.
