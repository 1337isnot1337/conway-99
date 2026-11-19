# Two source rows with two common core neighbors

This projection couples two exterior vertices of the complementary-rook
27-core. It retains all 252 binary incidence selectors and their full
Gram constraints. No complete incidence design or graph automorphism is
assumed.

## Exhaustive choice of the two sources

Fix the first-grid point `R0` and the second-grid point `S4`. Their core
Gram entry is two, and they have no common neighbor within the core.
Every completion therefore contains exactly two exterior signatures

\[
(0,4,t),\qquad t\in\{1,2,3,5,6,7,8\}.
\]

The two tips are distinct, since exterior signatures cannot repeat. Their
unordered pair has exactly 21 possibilities.

Four explicit core relabelings preserve the normalized ordered pair
`(R0,S4)`. Two preserve the first two grids individually. The other two
interchange these grids and also send point labels `0` to `4` and `4` to
`0`, so the normalized signature is again `(0,4,t')`. They divide the 21
tip pairs into the following eight cases:

| Case | Representative tips | Number of labeled tip pairs |
| --- | --- | ---: |
| 0 | `(1,2)` | 4 |
| 1 | `(1,3)` | 1 |
| 2 | `(1,5)` | 4 |
| 3 | `(1,8)` | 2 |
| 4 | `(2,5)` | 2 |
| 5 | `(2,6)` | 2 |
| 6 | `(2,7)` | 2 |
| 7 | `(2,8)` | 4 |

The coverage artifact stores all four core and signature permutations,
every one of the 21 members, a transport to each member, and its source-row
ordering. The independent audit checks every transport and all eight
complete domain hashes. This reduction relabels a hypothetical graph; it
does not require that graph to possess the relabeling as an automorphism.

## Coupling the completed neighborhoods

Each selected source receives the full
[single-row projection](complement_rook_row_projection.md): all 27 mixed
equations, exterior degree eleven, neighbor packing, and a perfect
matching of its eight chosen neighbors that have source overlap zero.
Both row systems use the same 252 incidence selectors.

The two sources already share two core vertices. They are nonadjacent and
cannot have a common exterior neighbor. For every common candidate `w`,
the model therefore imposes

\[
y_{s,w}+y_{t,w}\leq1.
\]

The two primary row-edge domains are disjoint: their only possible shared
graph edge would join the two sources, and that edge is ineligible. No
primary row edge can also be a matching edge in either source row.

Matching copies from the two row systems retain separate variables. A
zero copy says nothing about an edge outside that source's neighborhood.
If a copy is active, both endpoints belong to that source neighborhood.
The disjointness constraints prevent a copy for the same graph edge from
being active in the other neighborhood. Thus the two systems do not
impose conflicting interpretations of a graph edge.

## Checked outcomes

Every case returned SAT and passed exact partial-graph validation.

| Case | Variables | Clauses | SAT return time, seconds | Incidence parameter a |
| --- | ---: | ---: | ---: | ---: |
| 0 | 63,002 | 137,120 | 0.156 | 12 |
| 1 | 61,730 | 133,881 | 0.170 | 16 |
| 2 | 63,002 | 137,127 | 0.169 | 15 |
| 3 | 63,688 | 138,787 | 0.381 | 15 |
| 4 | 64,274 | 140,365 | 0.180 | 17 |
| 5 | 64,274 | 140,381 | 0.246 | 18 |
| 6 | 64,274 | 140,371 | 0.159 | 22 |
| 7 | 64,960 | 142,038 | 0.131 | 16 |

Each proof-enabled run had a 20-second budget including CNF parsing and
solver bootstrap. No run returned UNSAT or UNKNOWN.

Each witness specifies 72 incidence columns, both complete source rows,
and the eight matching edges. The resulting 99-point partial graph has
327 edges. Its core vertices and the two sources have degree fourteen;
its other exterior rows remain incomplete. The checker verifies all 729
Gram entries, all 4,851 partial pair caps, and both seven-edge source
neighborhoods. A separate verifier reconstructs these matrices without
importing a SAT builder.

All 21 labeled tip-pair choices therefore survive this projection. These
results add no exclusion or bound for the complementary-rook boundary.

## Artifacts and replay

The builder is
`experiments/workspace/complement_rook_duplicate_row_projection.py`.
The independently reconstructed coverage/domain audit is
`experiments/workspace/complement_rook_duplicate_row_projection_audit.py`.

The coverage is
`experiments/logs/grids-and-triangles/complement-rook-duplicate-row-coverage.json`.
Each case uses the `complement-rook-duplicate-row-i` prefix for its model,
result, build log, and solve log in that directory.

Replay the saved SAT witnesses directly with:

```sh
.venv/bin/python experiments/workspace/complement_rook_duplicate_row_replay.py \
  --output experiments/logs/grids-and-triangles/complement-rook-duplicate-row-independent-replay.json
```

This replay checks the manifest and source bindings, rebuilds the complete
signature domain, and checks the partial matrices and all saved source
transports. The large generated CNFs are not required to replay the
partial witnesses.
