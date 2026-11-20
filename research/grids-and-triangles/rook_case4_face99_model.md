# Complete selector model on the 99-zero face

The new model substitutes exactly the 99 columns proved zero by the short
Gram/triple identities and the 14 empty-cover units. It keeps the complete
original selector relaxation. It does not restrict a numerical support,
fix an unproved selector value, or impose symmetry.

The model has 1,115 variables, 167,935 rows and 11,012,058 nonzero integer
coefficients. All variables have bounds \(0\le x\le1\). Every row has
explicit finite integer lower and upper endpoints.

## Exact correspondence with the original model

The preparation replays all 99 zero proofs from the original published
inputs. It then substitutes those zeros into every one of the 2,271 native
rows and 178,533 coordinate covers. A native row is omitted only when its
entire remaining unit box lies between its original endpoints. The exact
minimum and maximum values are recorded as its omission witness.

A coordinate cover has the form

\[
\sum_{b\in F_a}x_b-x_a\ge0.
\]

It is omitted only when its target \(a\) is proved zero. For a retained
target, all proved-zero support columns are removed and the remaining
inequality is kept. The row's finite upper endpoint is the size of its
remaining support; this is a unit-box tautology. No active cover has an
empty support on this face.

Zero extension maps every feasible point of the reduced model to a
feasible point of the full original real relaxation. Conversely, every
feasible point of the original relaxation has the 99 proved zeros and
restricts to this model. These are statements about the linear relaxation,
not about a graph completion.

## Complete row inventory

| Original family | Original rows | Retained | Omitted with exact witness |
|---|---:|---:|---:|
| Gram equations | 630 | 396 | 234 |
| Original-signature capacities | 186 | 186 | 0 |
| Triple capacities | 1,365 | 1,322 | 43 |
| Gram pair conflicts | 30 | 4 | 26 |
| Uncapped exterior-row inequalities | 60 | 58 | 2 |
| Coordinate covers | 178,533 | 165,969 | 12,564 |

The 1,966 retained native rows contain 25,977 nonzero coefficients. All
165,969 retained covers are stored separately by their original registry
IDs, so a later constraint-generation query can validate the complete pool.

## Bindings and scope

The builder is `experiments/workspace/rook_case4_face99_model.py`. It uses
the unchanged published-input recovery routines and the new exact seed
verifier. Its row construction differs from the previous 81-zero builder
only in the checked zero proof, resulting dimensions, counts and bindings.

The canonical integer row stream has SHA256
`1698c93e04c5a4682d595952a8628806da2231c801f2f7e4519db8bc09d466de`.
The arrays archive has SHA256
`7e75bbb360d91d6a4a424262c2c61ad5d7e0e13942a7b80a8ca39ec731ebf4af`.
The model JSON has SHA256
`c417a08853096bbb7a6d8148aca80a5f08249c19f2978f3f49a86ec0c20c301b`.

Preparation finished in 25.909 seconds with a peak reported memory of
350,588 KiB. The same 6,216 exact box controls and 626 cover-linearization
controls passed. Preparation makes no optimizer call and accepts no
numerical or rational feasible point. A separate cold reconstruction checks
the original premises, every omission witness and every sparse array.

The frozen model files are under
`experiments/logs/grids-and-triangles/rook-case4-face99-model01/`.
No new LP query is included in this preparation.
