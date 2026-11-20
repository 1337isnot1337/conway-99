# Center 355: visible neighborhood matchings

The saved eight-neighbor witness admits ten visible matching extensions.
Eight use two exterior matching edges; two use three. Every listed
extension passes the visible common-neighbor caps and contains no induced
triangular prism. This does not complete the graph, identify the three
neighbors in the other shell component, or exclude center 355.

## Matching requirement

Center 355 has fixed-component signature `{6,11,13}`. The induced edge
`6--13` already pairs two of these three neighbors in its neighborhood.
The remaining core site, 11, must pair with exactly one selected exterior
neighbor. In the saved witness that neighbor is signature 475,
`{11,14,15}`.

Seven selected exterior neighbors remain. The three neighbors in the other
shell component induce either zero or one edge. They therefore require
three or one partners among those seven exterior neighbors. The remaining
four or six exterior vertices form two or three disjoint matching edges.
Every such edge joins disjoint fixed-core signatures: its endpoints already
have center 355 as their unique common neighbor.

The eight saved exterior signatures are:

| Local index | Domain index | Fixed-component signature |
|---:|---:|---|
| 0 | 69 | {0,14,17} |
| 1 | 73 | {1,2,8} |
| 2 | 174 | {2,7,17} |
| 3 | 201 | {3,4,7} |
| 4 | 212 | {3,5,12} |
| 5 | 284 | {4,10,12} |
| 6 | 435 | {9,10,15} |
| 7 | 475 | {11,14,15} |

Index 7 is already paired to core site 11 and cannot lie in an exterior
matching edge.

## Complete diagnostic on this fixed witness

The diagnostic enumerated all 105 two-edge matchings and all 105 three-edge
matchings on the other seven vertices. It retained the complete ledger.

An edge must join disjoint signatures, belong to the frozen exterior-edge
domain, and avoid the previously certified edge-zero set. A visible
common-neighbor violation after adding a single edge also rejects that
edge. An induced prism after adding a single edge was only recorded; it
was not used to reject a complete matching. Every surviving complete
matching received all visible cap and induced-prism checks.

| Matching size | Complete cases | Rejected by edge filters | Passing |
|---:|---:|---:|---:|
| 2 | 105 | 97 | 8 |
| 3 | 105 | 103 | 2 |
| Total | 210 | 200 | 10 |

The seven surviving potential edges, in local indices, are
`01,03,13,14,15,16,24`. All ten matchings made from them pass the full
visible tests; there are no further joint cap or prism rejections.

The complete diagnostic took 0.600 seconds within its 10-second bound.
The two three-edge witnesses are

```text
{(0,3),(1,5),(2,4)}
{(0,3),(1,6),(2,4)}.
```

For example, the first has exterior edges
`69--201`, `73--284`, and `174--212`. Signature 475 pairs with
core site 11. Signature 435 is the only exterior neighbor left to pair
with the other shell component.

The original diagnostic draft and its preparation remain archived and
unqueried. The executed v2 conservatively avoids single-edge prism
pruning. Neither version imposes any equality between literal edges that
share an averaged coordinate.

## Independent verification of every positive

A separate standard-library checker imports neither diagnostic source.
It rebuilds the 30-vertex partial adjacency matrix directly from the
frozen core, signatures and matching edges for all ten positive records.
It checks all 435 pair caps for each record, the neighborhood degrees,
the required one or three unmatched exterior vertices, and every pair
of disjoint visible triangles for an induced prism.

All ten passed, for 4,350 pair-cap checks in total. A direct nine-vertex
rook control finds its six induced prisms. The independent check took
1.101 seconds. It verifies every claimed positive; it does not independently
repeat the 200-case rejection ledger.

## Scope of a free local matching extension

A free version would retain all 218 original neighbor bits and all
18 exact mixed equations, population eight and 5,495 pair conflicts.
It would add independent matching bits for eligible pairs of candidate
neighbors with disjoint signatures. Matching bits require both endpoint
bits. Each selected exterior neighbor containing core site 11 has no
exterior matching partner; each other selected neighbor has at most one.
The number of matching edges is two or three. The complete visible
adjacency must satisfy all pair caps and contain no induced prism.

The ten saved witnesses already satisfy those stated requirements.
A new feasibility call with only this free version would therefore
reproduce an established local positive. Additional information from
the other component or compatibility between different centers would
be needed to make that next model stronger. No such model or new solver
call is part of this package.

The exterior triangle count is not new here:
[the existing triangle-neighborhood note](grids-and-triangles/triangle_root_constraints.md)
already proves `t(C)=32-f`. In the globally prism-free case `f=0`,
so the sixty-vertex exterior has 32 triangles.

## Frozen records

- Executed source:
  `experiments/workspace/root_prism_free_f0_local_center355_matching_diagnostic_v2.py`,
  SHA256 `34f1dc03eb2d729149f1f651506918603a7e9b1b288cf07921d255a44305fe17`.
- Preparation:
  `experiments/logs/root-prism-free/f0-local-center355-matching-diagnostic02-preparation.json`,
  SHA256 `8e0d59bc051713a06ceaf3377d7803396e3f8da19b951864400f81e0c44aba2a`.
- Complete result:
  `experiments/logs/root-prism-free/f0-local-center355-matching-diagnostic02.json`,
  SHA256 `18375b3c9f1a32eb62abdd7ea118f609dd712cee080227bb23d41cf910fc0d5d`.
- Independent source:
  `experiments/workspace/root_prism_free_f0_local_center355_matching_independent.py`,
  SHA256 `5bd6dc58181ab426f3d97ff75480eceafe1376bcd808d16993cc42fc80f2cc77`.
- Independent result:
  `experiments/logs/root-prism-free/f0-local-center355-matching-independent01.json`,
  SHA256 `3aff336dc7611d5b42af2100cc75bca9ce41197b13ad7749e287cb6593d66579`.

The earlier eight-neighbor SAT witness and its cold replay remain in
[their separate package](root_prism_free_f0_local_center355_result.md).

