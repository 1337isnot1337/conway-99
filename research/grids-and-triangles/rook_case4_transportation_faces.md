# Transportation faces of the case4 attachment model

This is an exact, optimizer-free reduction of the 1,214-column attachment
model for local matching case4. It does not decide whether that case has a
completion. The preparation verifies 105 transportation projections, one for
each of the 35 core vertices and each pair of the three nine-point grids.
No feasible projected flow is claimed to lift to a joint incidence solution.

## Projection from the original Gram equations

Write the original nonnegative column weights as \(x_h\). Each admitted
attachment column \(h\) contains exactly one point in each grid \(R,S,T\).
The preparation checks this property for every original column. It also
reconstructs all 630 Gram supports from the 35 diagonal supports.

Fix a core vertex \(v\) and two different grids \(A,B\). For
\(a\in A,b\in B\), put

\[
w_{ab}=\sum_{h:\{v,a,b\}\subseteq h}x_h.
\]

Each column containing \(v\) contributes to exactly one cell. Consequently
the literal Gram equations give the margins

\[
\sum_b w_{ab}=G_{va},\qquad
\sum_a w_{ab}=G_{vb},\qquad
\sum_{a,b}w_{ab}=G_{vv}.
\]

These identities include the cases \(v=a\) or \(v=b\). Every row and column
support partition is checked directly against its original Gram support.
No symmetry of the incidence weights is imposed.

The first closure stage uses only nonnegativity and these Gram equations.
It represents an unbounded supported cell by capacity \(M+1\), where
\(M=G_{vv}\). This does not change the projected feasible set: the margins
already give \(w_{ab}\le M\).

The second stage adds only the following original bounds:

- If \(v,a,b\) are three distinct sites, their cell has capacity one. For
  a cell containing several columns, this is the original triple-packing
  inequality. A singleton cell uses its original selector upper bound.
- If the set \(\{v,a,b\}\) has two sites, the cell is exactly the support
  of their Gram equation. Its Gram quota is a valid upper bound.

The second stage starts with the zeros proved by the first. Both stages
start without any external numerical or Boolean propagation premise.
The entire argument therefore applies to nonnegative real column weights;
the second stage additionally uses the stated triple and unit-box bounds.

## Exact cut certificates

Let \(r_a,c_b\) be the margins, and let \(u_{ab}\) be the active cell
capacities. For sets of row and column sites \(P,Q\), the margin equations
give

\[
c(Q)-r(P)+\sum_{a\in P,b\notin Q}u_{ab}
=\sum_{a\notin P,b\in Q}w_{ab}
 +\sum_{a\in P,b\notin Q}(u_{ab}-w_{ab})\ge0.
\]

If the left side is negative, the projection is infeasible. If it is zero,
every incoming cell \((a\notin P,b\in Q)\) is zero, and every outgoing
cell is saturated. The implementation uses only the zero-cell conclusion.
In particular, a saturated capacity-one cell does not identify which of its
members is selected.

Every recorded cut is expanded into original rows: column Gram margins
minus row Gram margins, plus the original capacity inequalities for the
outgoing cells. The replay computes all 1,214 coefficients. Every negative
coefficient must refer to a previously proved zero; its earlier event is
recorded. All remaining coefficients are nonnegative. A zero right side
therefore forces every positive-coefficient column to zero. A negative
right side would give a contradiction.

The Gram-only stage never uses a finite-capacity premise. A feasible flow
has total at most \(M\), so a cell of capacity \(M+1\) cannot be saturated.
An infeasible minimum cut of value below \(M\) cannot cross such a cell
either. The recorded Gram-only combinations are checked to contain no
outgoing capacity terms.

## Flow and closure completeness

The flow helper uses deterministic integer augmenting paths. No LP or SAT
solver is called. All margins and capacities are integral, and every flow
uses at most 14 unit-or-larger augmentations.

For a feasible flow, the residual graph has row-to-column capacity
\(u-w\) and column-to-row capacity \(w\). A zero-flow cell of positive
capacity can become positive precisely when its column endpoint can reach
its row endpoint in this residual graph. Such a path closes a residual
cycle. Residual-closed reachable sets give the exact zero-cell cuts above.

Each stage repeats all 105 projections until no new zero appears. Every
retained zero event fixes at least one previously unfixed column, so there
can be at most 1,214 zero events. A completed stage stores a feasible flow
for every final projection. Replay checks its margins and all residual
cycles, proving that no further zero cell is available from any of these
projections at that stage. This is completeness for the specified closure,
not for all consequences of the attachment system.

The forward and replay phases each have a separate 60-second limit. A
partial run retains only the exact deductions already recorded. An
exclusion is accepted only after the signed-row and prior-zero replay.

## Preparation and controls

The frozen preparation reconstructs all 1,214 columns, 630 Gram supports
and 1,365 triple supports from the published native model. Across the 105
projections, it records 1,862 supported cells and 16,266 column occurrences.
The capacity sources are 320 Gram rows, 107 singleton bounds and 1,435
triple rows. Three projections have zero total margin.

The independent truth domain in the small flow controls enumerates every
integer box flow for every 2-by-2 capacity matrix with entries in
\(\{0,1,2\}\). All 6,885 margin/capacity cases pass: 1,215 are feasible
and 5,670 have an exact infeasible cut. All 2,088 emitted zero-cut controls
agree with the cells that vanish in every enumerated flow. A 3-by-3
perfect-matching control verifies that all nine cells remain possible.

Files:

- `experiments/workspace/rook_transportation_faces.py`: pure flow and cut
  routines, with exhaustive small controls.
- `experiments/workspace/rook_case4_transportation_faces.py`: complete
  projection construction, bounded closure and original-row proof replay.
- `experiments/logs/grids-and-triangles/rook-case4-transportation-faces-preparation01/`:
  frozen domain and preparation report.

The preparation alone runs no case4 flow closure and proves no additional
case4 zero or exclusion.

```bash
python experiments/workspace/rook_case4_transportation_faces.py preflight \
  --directory experiments/logs/grids-and-triangles/rook-case4-transportation-faces-preparation01 \
  --output /tmp/rook-case4-transport-preflight.json
```
