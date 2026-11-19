# Complete F0 selector-pair packing bounds

The single exact scan completed all 9,353 retained selector-pair orbits
in 7.19 seconds. Its separate cold replay passed all 9,353 certificates
in 8.85 seconds. No orbit remains unqueried in this family.

The result gives Boolean-valid necessary upper bounds for pair
populations in the fixed F0 model. It neither constructs an incidence
nor excludes F0.

## Exact bounds

| Maximum compatible pair objects | Number of retained pair orbits |
|---:|---:|
| 1 | 36 |
| 2 | 304 |
| 3 | 2,506 |
| 4 | 407 |
| 5 | 140 |
| 6 | 5,216 |
| 12 | 744 |
| **Total** | **9,353** |

The bounds improve 8,509 original orbit-size boxes and 8,251 explicit
upper bounds in the frozen character-pool plan. The latter comparison
uses the unchanged reduced count-column IDs and exact interval domains
from plan SHA256
`b3179e520d5913530c7d3cfae27529b5717be26c763de024b725c38959aa2aef`.

The complete ledger contains 170,661 subset recurrences and occupies
7,552,492 uncompressed bytes. Every record retains the full compatibility
graph, a literal zero-pair witness for each missing edge, the anchor
neighborhood, its exact clique certificate, and a partial selector set
attaining the claimed bound under the pair-zero premises.

## Comparison with endpoint activation

Many tighter boxes are already immediate consequences of endpoint
activation. For a pair orbit \(R\) between distinct selector orbits
\(O_i,O_j\), literal transitivity makes each endpoint degree constant:
\[
d_i=\frac{|R|}{|O_i|},\qquad d_j=\frac{|R|}{|O_j|}.
\]
Since \(z_a z_b\leq z_a,z_b\),
\[
P_R\leq \min(d_i N_i,d_j N_j).
\]
The separate comparison uses the current explicit upper bounds on
\(N_i,N_j\) and checks every endpoint degree directly.

| Comparison | Pair orbits |
|---|---:|
| Cross-orbit pairs | 9,033 |
| Within-orbit pairs | 320 |
| Packing bound below endpoint activation | 1,427 |
| Packing bound below both activation and the current pair box | 1,409 |
| Current-box improvements already covered by endpoint activation | 6,842 |
| Within-orbit improvements over current profile-derived domains | 0 |

Thus 1,409 of the new bounds go beyond both the current explicit box and
this simple activation consequence. This is not a redundancy test
against every existing equation, table, product, or inequality.

The activation comparison completed in 1.64 seconds. It consumed the
frozen complete certificates, without reconstructing compatibility
graphs or repeating a clique search.

## Proof and replay scope

The compatibility graph has one vertex for every literal pair in the
specified pair orbit. Two vertices are adjacent exactly when their
endpoint union contains no previously proved-zero selector pair.
Repeated endpoints are retained correctly. Every set of active pair
objects is a clique.

All twelve actual core actions preserve each finite graph and act
transitively on its vertices. Therefore an optimum clique can be moved
to the anchor. This uses literal domain relabelings, not automorphisms
of a hypothetical 99-graph.

The helper certifies the exact clique number by the deletion/neighborhood
recurrence. The cold replay independently rebuilds every compatibility
graph from literal endpoint unions, checks every transported action, and
checks all saved recurrences plus their clique witnesses. It performs no
maximum-clique search.

The existing 389 zero pair orbits are inherited premises. Their 4,410
literal zeros consist of 4,320 directly checked quota-one Gram
consequences and 90 prior cold-checked binary-motif consequences.
No new motif census or optimizer was run.

## Integration fields

The result's `summary.improved_current_bounds` contains the 8,251 rows
`{pair_orbit, count_column, old_upper, new_upper}`. A later model can
intersect its existing interval domain with the certified upper bound,
preserving any holes. This report does not mutate the frozen model.

The gzip JSONL ledger contains all 9,353 bounds, including those that do
not improve the current box. Its fields `count_column` and
`maximum_compatible_pair_objects` give the reduced count ID and exact
bound. Its order matches the frozen preparation's retained-orbit list.

## Immutable records

- `f0-pair-orbit-packing-scan01.json.gz`:
  `1bbba3061689f8faaf8fadcf556c0097d2b190673ab063a675259c007508b2bb`.
- `f0-pair-orbit-packing-scan01-ledger.jsonl.gz`:
  `4c53542bc89575b799b9e3d8b5905ae3dfe9782aa954db9d9afdf2a07c83d839`.
- `f0-pair-orbit-packing-scan01-cold.json`:
  `c684243851efa7e12e9b9e5c7f857532421c1954233a5d9d6e24acfe5c826843`.
- `f0-pair-orbit-packing-activation-comparison01.json.gz`:
  `f3907e807f14befeab0ba7ef9409eef9d39c3b734e08e8d0af87d4bc173bffb1`.

The preparation package and its source-review gate remain unchanged.
