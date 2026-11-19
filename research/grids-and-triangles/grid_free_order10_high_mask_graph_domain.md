# Complete high-vertex graph domain above an independent six-set

## Scope

This preparation retains the edges between high vertices, as well as their root neighborhoods.
It gives a finite necessary domain for every graph with parameters `(99,14,1,2)`.
It uses no prism or `x521` assumption.
It constructs no exterior completion and excludes no full graph.

The earlier [presence-only system](grid_free_order10_high_mask_packing_witness.md) has an exact rational feasible witness at the saved count point.
The new system adds induced-edge information to the same complete high-class domain.
The [direct moment package](grid_free_order10_high_mask_graph_moments.md) supplies its exact right-hand sides.

## Necessary finite domain

Fix six ordered independent vertices.
For an outside vertex, its mask is the subset of these six vertices adjacent to it.
A high vertex has a mask of size at least three.
There are 42 possible high masks.
Each high class contains at most one vertex, since two equal masks would give at least three common neighbors.

Each pair of roots has two common neighbors.
Thus the selected high masks use each root pair at most twice.
They use at most thirty root-pair incidences in total.
Each selected mask uses at least three, so there are at most ten high vertices.
Distinct high masks intersect in at most two roots.

These conditions leave 90,776 labelled presence configurations in 249 root-permutation orbits.
The presence census and all orbit maps are frozen in the earlier packing packages.
For each representative, the new search assigns every possible edge between its high vertices.
An edge is eligible only when its endpoint masks intersect in at most one root.

Let `B` be the adjacency matrix on the six roots and the selected high vertices.
The root subgraph is empty, and its incidence to high vertices is fixed by the masks.
Every retained graph satisfies the following exact tests:

- Every adjacent pair has at most one common neighbor inside `B`.
- Every nonadjacent pair has at most two common neighbors inside `B`.
- Every vertex has degree at most fourteen inside `B`.

The common-neighbor tests include root/high pairs and high/high pairs.
They count every common neighbor already present in this induced graph.
All three conditions are necessary for a Conway graph.
Vertices outside this core can only increase its common-neighbor counts.
Every empty high-edge graph passes, so the construction retains the entire preceding presence domain.

## Complete enumeration

A C++ inclusion/exclusion search enumerates every eligible edge choice.
After adding an edge, it checks every affected pair quota.
A violated quota cannot be repaired by adding more edges, which justifies pruning.
The recorded edge order and complete input bind the result to each presence representative.

A separate Python search uses another edge order and rebuilds the literal adjacency matrix.
It checks every pair directly after each included edge.
Both searches give the same edge-count histogram for every one of the 249 representatives.
They retain 157,711 high-edge graphs before any quotient by a presence stabilizer.
The C++ run takes 0.059 seconds, and the independent Python run takes 5.16 seconds in the recorded environment.

| High vertices | Presence representatives | Retained graphs | Largest edge count |
| ---: | ---: | ---: | ---: |
| 0 | 1 | 1 | 0 |
| 1 | 4 | 4 | 0 |
| 2 | 7 | 10 | 1 |
| 3 | 18 | 41 | 2 |
| 4 | 43 | 223 | 3 |
| 5 | 67 | 939 | 4 |
| 6 | 66 | 3,802 | 6 |
| 7 | 33 | 9,868 | 7 |
| 8 | 8 | 16,595 | 8 |
| 9 | 1 | 16,303 | 10 |
| 10 | 1 | 109,925 | 12 |

A third pass saves every graph as a code in its complete eligible-edge table.
It checks uniqueness and reproduces both earlier histogram lists.
The saved domain arrays contain 157,711 codes, 250 atom offsets, and 249 edge tables.
They support later checks without another graph search.

## Induced patterns and exact feature matrix

The moment rows describe every induced pattern on the six roots and at most four high vertices.
The 73 presence representatives of these sizes admit 279 labelled high-edge graphs.
Explicit root permutations and each presence stabilizer reduce these to 200 rooted induced-pattern orbits.
All 720 permutations of the six root labels are included.

For a row orbit `R` and a retained graph `H`, define `C[R,H]` as follows.
Count every subset of the high vertices of `H` whose rooted induced pattern belongs to `R`.
The subset size is fixed by the row.
These coefficients are integers between zero and sixty.
The constant row is one on every column.

The full matrix has 200 rows, 157,711 columns, and 7,291,472 nonzero entries.
Every column passes two complete checks.
For each subset size `q`, its row sum is the binomial coefficient `choose(k,q)`.
After aggregation over high-edge patterns, it equals the earlier presence-only coefficient column.

The construction transports each subset through the saved root-permutation paths.
It then uses the explicit stabilizer lookup for its induced edge code.
A separate colored-graph canonicalization checks 26,049 subsets from 631 control columns.
The controls include every small pattern and larger extremal columns.

Identical full feature columns can share one nonnegative mass variable.
Exact deduplication leaves 18,427 columns and 782,041 nonzero entries.
The saved inverse map retains the destination of every original graph column.
This reduction uses equality of coefficients and needs no graph-isomorphism claim.

The 200 rows are independent over the rationals.
For each row pattern, choose the domain column consisting of that pattern itself.
Order these columns and rows by the number of high vertices.
The resulting square minor is triangular, with diagonal entries one.
The preparation checks this minor exactly.

## Normalization and root-label averaging

For a fixed labelled pattern `T`, every high mask is distinct.
Consequently a root embedding determines at most one outside vertex for each free label.
The total indicator count equals `Aut(F_T) * n(F_T)`, where `F_T` is the full unrooted induced graph.
Automorphisms that move the root set remain part of this factor.
No division by the number of free labels is valid here.

For a root-label orbit `R`, the exact right-hand side is

\[
b_R=|R|\,\operatorname{Aut}(F_T)\,n(F_T).
\]

Average any domain column over all 720 root permutations.
Every fixed pattern in `R` then has expectation `C[R,H]/|R|`.
Thus nonnegative masses satisfying `C*w=b` reproduce all individual pattern moments after this uniform lift.
The operation averages labels of a fixed root, and assumes no automorphism of the unknown host graph.

All 200 right-hand sides at the saved point are positive.
Independent literal embedding counts check their automorphism factors.
Their aggregates reproduce all 73 earlier presence-only right-hand sides.

## Frozen files and next query

The domain and feature preparation runs no optimizer.
The next query asks whether nonnegative masses on all 18,427 distinct columns satisfy all 200 equations.
An exact rational witness would certify only this finite relaxation.
An integer separator must be checked on every original domain column before any count inequality is claimed.

The [manifest](../../experiments/logs/moments-and-counts/order10-high-mask-graph-domain-manifest.json) binds the sources, inputs, results, arrays, and this note.
The direct moment normalization has a separate manifest and independent review.

| Frozen result | SHA-256 |
| --- | --- |
| Independent graph census | `8d8139a148fe12678561433766f3aa70f260266c196f7671b727d41ea856d673` |
| Complete graph domain | `39fb9f237327616f83917a15644c36a2f397d5c938720b4dff9278d4262d94f8` |
| Pattern orbit table | `86248876874c7b3ded078aec9e189de6f9728302137bb857ffe1500ad519400b` |
| Complete feature result | `fc5c2876dfdbfe6b9237a0ebfa610742fda9e3127bd00d6b0676e6e2ee576596` |
| Feature arrays | `bd2971d442d8fb0a0059f946b93e4e11046c211bf77b6f1a128694f8792cc68e` |
