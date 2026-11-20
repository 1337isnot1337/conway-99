# Forced upper capacities on the 99-zero face

The complete census of the 105 saved transportation flows gives 330 cells
whose positive upper capacity is forced. They represent 170 distinct
equalities on full original column supports. Every equality already follows
from the Gram equations after the 99 certified zero columns are removed.
The census yields no additional zero, forced-one column, independent affine
constraint, or contradiction.

The input is the frozen terminal seeded transportation result. Each of its
105 projections uses one of the 35 core vertices and one of the three pairs
of original nine-point grids. Each original attachment column belongs to
one supported row-column cell in each relevant projection. Literal Gram
equations supply the margins. Pair, diagonal, triple or singleton bounds
supply the recorded capacities. Feasibility of a projection does not imply
that its flows lift to a common attachment-column assignment.

## Exact criterion

Fix a feasible transportation flow f with row margins r, column margins c
and upper capacities u. The residual graph has a row-to-column arc when
f<u, and a column-to-row arc when f>0. For a positive-capacity cell (i,j):

- If f(i,j)<u(i,j), the saved flow itself disproves a forced upper bound.
- If f(i,j)=u(i,j) and row i reaches column j, the path together with the
  reverse arc of (i,j) gives a residual cycle. A positive exact change along
  this cycle decreases that cell while preserving every margin and bound.
- Otherwise, let P and Q be the rows and columns reachable from row i.
  The cell (i,j) leaves P for the complement of Q. Residual closure gives
  f(P,Q-complement)=u(P,Q-complement) and f(P-complement,Q)=0. Hence
  c(Q)-r(P)+u(P,Q-complement)=0. The same cut identity forces every
  outgoing cell, including (i,j), to its upper bound in every feasible flow.

This is a complete classification for a fixed transportation projection.
The helper saves an explicit decreasing cycle or a closed cut for each
saturated positive cell. Zero-capacity cells are recorded separately.

## Original-column certificate

For a forced target cell, the wrapper combines the original column-margin
Gram rows, the negatives of the original row-margin Gram rows, and all
outgoing capacity bounds except the target. The resulting upper bound is
minus the target capacity. Adding the target membership row makes every
remaining column coefficient nonnegative. Negative coefficients are allowed
only on the 99 previously proved zero columns, with the premise recorded.
This proves that the target population is at least its capacity. Its
original capacity row supplies the opposite inequality.

Every coefficient is checked on all 1,214 original attachment columns.
The proof never treats the saved numerical or integral flow as an actual
joint incidence assignment. No case4 max-flow or optimizer call occurs in
this census: it uses the frozen exact flows. Tiny controls enumerate all
6,885 tested two-by-two margin/capacity instances and compare the criterion
against every feasible box flow. Two three-by-three controls distinguish
flexible complete matching support from forced diagonal matching support.

## Complete counts

| Classification | Cells |
| --- | ---: |
| Inactive zero cells | 23 |
| Strict slack in the saved flow | 1,087 |
| Explicit decreasing residual cycle | 422 |
| Forced positive Gram capacity | 320 |
| Forced positive triple capacity | 10 |
| Total | 1,862 |

The 330 positive forced cells yield 170 distinct full-support equalities.
Of these, 168 match a single Gram row on the proved face. The other two are
the following population-one identities, where C denotes the sum of all
attachment columns containing the indicated core sites:

\[
C_{5,15,27}=C_{5,27}-C_{9,27}=2-1=1,
\qquad
C_{7,11,27}=C_{7,27}-C_{14,27}=2-1=1.
\]

The separate redundancy checker expands each identity in all 1,214
coordinates. Every discrepancy is supported on the previously proved 99
zeros. Thus all 170 upper equalities add zero affine rank to the frozen
face99 Gram model. The face99 LP remains unchanged.

## Replay

The complete census replay reconstructs each original-row certificate and
reclassifies every saved cell. It calls no max-flow routine or optimizer:

```sh
python experiments/workspace/rook_case4_transportation_upper_faces.py replay --directory experiments/logs/grids-and-triangles/rook-case4-transportation-upper-preparation01 --output /tmp/rook-case4-upper-replay.json
python experiments/workspace/rook_case4_upper_face_redundancy.py replay --certificate experiments/logs/grids-and-triangles/rook-case4-upper-face-redundancy.json --output /tmp/rook-case4-upper-redundancy-replay.json
```

The terminal census and both exact replays pass. This result concerns only
the fixed local core, its 99-zero face and these 105 projections. It does
not exclude case4 or a full Conway graph.
