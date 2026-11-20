# Pair caps and exact edge-circuit cuts

The prepared Boolean shared-edge model has all original selectors, eligible
edges, activation inequalities, degree equations and mixed equations. It also
has the certified prism zeros and core-pair clique rows. It does not yet have
every exterior common-neighbor cap. A vector satisfying that model therefore
needs further checks before the fixed-exterior residual inspector applies.

## Necessary pair inequality

Let `a,b` be two selected exterior signatures. Write `c` for the number of
their common neighbors in the fixed eighteen-vertex component. Write `D`
for the exterior adjacency matrix. The exterior block of the strongly
regular graph equation gives, for distinct vertices,

\[
c+(H_2^T H_2)_{ab}+(D^2)_{ab}+D_{ab}=2.
\]

The unspecified second-component contribution is nonnegative. Hence

\[
|N_D(a)\cap N_D(b)|+D_{ab}\leq 2-c.
\]

Distinct allowed signatures have `c` equal to zero, one or two. An eligible
edge has `c<=1`. These facts also follow directly from the frozen domain.

## Positive-edge witnesses

Choose `t` equal to zero or one. If `t=1`, include the edge `ab` in the
witness. Choose `m=3-c-t` distinct common exterior neighbors, and include
both incident edges from each chosen neighbor to `a,b`. All these edges
being present would give

\[
(D^2)_{ab}+D_{ab}\geq m+t=3-c>2-c.
\]

For the resulting edge set `E`, every graph in the current F0 scope must
satisfy

\[
\sum_{e\in E} y_e\leq |E|-1.
\]

This inequality needs no selector guard. Endpoint activation already makes
each edge zero when either endpoint is absent. Other edges can only increase
the common-neighbor count, so the inequality also holds in larger graphs.

| Common core neighbors `c` | Include `ab` | Chosen common exterior neighbors | Witness edges | Upper bound |
|---|---:|---:|---:|---:|
| 2 | 0 | 1 | 2 | 1 |
| 1 | 1 | 1 | 3 | 2 |
| 1 | 0 | 2 | 4 | 3 |
| 0 | 1 | 2 | 5 | 4 |
| 0 | 0 | 3 | 6 | 5 |

The two-edge case is covered by the existing common-core-pair constraints.
The other rows give triangle, four-cycle, five-edge diamond and `K2,3`
witnesses when their stated signature intersections hold. These are
necessary conditions, not a complete description of exterior realizability.

## Prepared exact inspector

`experiments/workspace/root_prism_free_f0_boolean_shared_pair_caps.py` takes
the complete saved array of 68,934 integers. Selector entries are at indices
0 through 479. The sixty existing parent auxiliaries occupy indices 480
through 539. The 68,394 edge entries start at index 540, in the complete
frozen lexicographic edge order.

The inspector reconstructs the signature and edge domains from the fixed
core. It checks the population, all 171 original Gram entries, all 480 degree
equations and all 8,640 mixed equations. It then checks all 1,770 pairs among
the sixty selected vertices. For every violated pair, it enumerates both
possible values of `t` and every minimum-size witness among the present
common neighbors. Duplicate edge sets are merged while all witness origins
are retained. Each cut has exact integer activity one above its upper bound
on the supplied candidate.

The query's separate exact row checker remains responsible for the complete
parent constraints and auxiliaries. Passing this inspector means only that
the exterior pair caps pass. The second-component residual conditions and
the full graph equations remain separate obligations.

## Controls and current status

The controls enumerate all 1,024 simple graphs on five vertices for each of
three signature layouts. The designated pair has zero, one or two common
core neighbors. Direct dense multiplication for `D^2+D` supplies the
independent reference for all 3,072 assignments. All reported violating
pairs agree.

The controls also examine all edge subsets of 4,992 reported minimal
witnesses. The complete witness violates its designated pair cap; every
proper subgraph satisfies that cap. The control report is
`experiments/logs/root-prism-free/f0-boolean-shared-pair-cap-controls01/report.json`,
SHA-256 `5bf0c8f0f64c0ffdafc6d600ce88f883fffe9bd062eb3a54199f7d6d8aa937dd`.
Its owner finishes in 0.767 seconds and reaps the child under a thirty-second
limit. No optimizer is imported or called.

No production edge assignment has been inspected with this source. No new
production circuit, graph or whole-component exclusion is claimed here.
