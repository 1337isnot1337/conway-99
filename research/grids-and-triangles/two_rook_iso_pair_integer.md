# A bounded completion search for two rook-isomorphic grids

The existence of two disjoint rook grids joined by a rook-isomorphic
matching remains unresolved. A 60-second integer completion run found
two partial binary points, checked them on all 99 vertices, and added
1,939 necessary common-neighbor clauses before reaching its budget.
Neither point is a strongly regular graph.

## Fixed incidence and edge variables

The 18-point core and its forced 81-column incidence are described in
[the completion note](two_rook_iso_completion.md). There are nine
diagonal signatures, each occurring once, and 36 ordered nonadjacent
rook pairs, each occurring twice. The two copies of each repeated
signature are distinct vertices. All 81 outside vertices are present;
there are no selection variables.

Their internal degree must be twelve. The mixed common-neighbor
equations and pair caps leave 3,060 possible outside edges. The
initial integer model requires every mixed equation, every exterior
degree equation, and the following packing condition: the two copies
of a signature cannot have any additional outside common neighbor.
They already share their two core neighbors. This supplies 2,772
binary at-most-one clauses.

No graph symmetry is assumed. In particular, the nine diagonal
vertices are not required to form a rook graph, and no orbit equality
is imposed. The full initial CNF has 147,060 variables including
cardinality auxiliaries and 297,684 clauses. Its SHA-256 is

```text
b4ffd43eba9f37a39f14af2d9ca2c96a3e4785a03edea9b379c0336c9ca4d633
```

## Complete checks of the two binary points

Every returned point is assembled into a 99-point adjacency matrix.
Both points have degree fourteen at every vertex and satisfy all
common-neighbor equations involving a core vertex. The remaining
outside/outside equations fail:

| Point | Search elapsed seconds | Defective pairs | Pairs above their allowed quota |
| --- | ---: | ---: | ---: |
| 1 | 49.97 | 2,178 | 984 |
| 2 | 59.24 | 2,093 | 971 |

The saved points include all 486 selected outside edges, their tip
graphs, and complete defect histograms. A separate standard-library
replay reconstructs each graph and verifies these numbers exactly.

## Necessary refinement clauses

For an outside pair `a,b`, let `c` be the number of their common core
neighbors. Every completion must satisfy

\[
c+C_{ab}+\sum_w C_{aw}C_{bw}\le2.
\]

When a point violates this inequality, choose `3-c` present terms
from its direct edge and its outside common-neighbor paths. Forbid
the simultaneous presence of their edges. This clause is necessary
for every completion; it does not depend on treating a partial point
as a graph solution.

The run produced 1,939 distinct clauses in this way. The replay checks
the named endpoints, paths, candidate-edge membership, and the exact
`c + number of selected terms = 3` witness for each clause. It also
reproduces the clauses from the saved points.

The run ended `UNKNOWN` at 60.07 seconds. No UNSAT result or graph
existence claim follows from it.

## Files and replay

The frozen search source is
`experiments/workspace/two_rook_iso_pair_integer.py`. The saved run is
`experiments/logs/grids-and-triangles/two-rook-iso-pair-integer.json`,
with its execution log beside it.

```bash
python experiments/workspace/two_rook_iso_pair_integer_replay.py \
  experiments/logs/grids-and-triangles/two-rook-iso-pair-integer.json
```

The initial CNF is reproducible from the frozen source. The full CNF
was kept as an execution artifact under `/tmp`; its hash above binds
the reported run to the encoding.
