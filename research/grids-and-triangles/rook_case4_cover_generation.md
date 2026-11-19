# Bounded row generation for the case4 selector LP

This is a preparation for a different numerical search of the complete case4
real selector relaxation. It makes no new graph exclusion. The earlier full
max-min run stopped without a valid point, basis or exact certificate.

## Exact domain

The published recovery builder gives 1,156 free selectors after 58 proved
zeros. Its 174,208 ranged rows have 11,868,882 nonzero integer coefficients.
The first 1,992 rows are native Gram, multiplicity, triple-capacity, conflict
and exterior-row constraints. The rest are coordinate covers. Every variable
has the finite bounds zero and one.

The separate exact compression certificate retains 125,429 cover rows. It
accounts for every removed row by a final retained native row or a smaller
same-guard cover, together with the unit box. Therefore the compressed and
original systems have the same real feasible points. This equivalence uses no
Boolean rounding.

The max-min extension adds a variable `t` in `[0,1]` and the 1,156 rows
`0 <= x_j - t <= 1`. The objective is to maximize `t`. The complete extended
matrix has 175,364 rows, 1,157 variables and 11,871,194 nonzeros.

## Row-generation contract

The new driver starts with every native row and every extension row. This is
3,148 rows with 29,312 nonzeros. It creates one native HiGHS solver and appends
original rows to that solver, preserving the available basis. It never fixes
a numerical support, chooses an incidence design or adds a symmetry condition.

After an optimal finite numerical proposal, the driver evaluates every row of
the full original extended CSR matrix. It selects at most 512 previously absent
retained covers with violation greater than `1e-7`. Larger violations come first;
original row IDs break ties. The tolerance controls numerical discovery only.
All selected rows are copied from the exact frozen matrix.

The run has at most 30 explicit optimizer calls and 120 cumulative measured
seconds for those calls and existing-ray retrieval. It also has a 180-second
numerical-phase wall budget, including native bootstrap and row scans. A timer
interrupts each call at the smaller remaining budget. Actual elapsed times are
recorded; the code does not conceal native return latency after interruption.
At most 14,848 cover rows can be appended before the last call, so the native
model has at most 17,996 rows.

Each numerical call, its complete active-row list, primal proposal, duals and
basis information are saved before the next update. The saved transcript records
the complete scan and exact appended row IDs. A nonoptimal result stops the
loop. There is no automatic retry. An absent dual ray does not trigger another
optimization to construct one.

## Exact acceptance

The numerical phase is followed by at most 60 seconds of exact reconstruction.
The frozen arbitrary-precision helper is reused without changes.

For a bound or infeasibility proposal, local row multipliers are expanded to
their original global row IDs. All other multipliers are zero. The exact
finite-box check verifies the coefficient of every variable and every bound
contribution. A certificate from the active subset is valid for the complete
system because every active row is an original row. A negative exact upper bound
proves infeasibility; a zero max-min bound can prove additional selector faces.

A rational primal proposal must pass **all 175,364 original extended rows** and
all 1,157 variable bounds. Passing only the active subset or the compressed pool
does not suffice. The result restores the 58 proved zeros to the original 1,214
selector coordinates. Even a successful exact point is a real relaxation
witness, not a binary incidence or a 99-vertex graph.

Failure to reconstruct either outcome remains unresolved. Numerical
infeasibility, finite tolerances and a saved basis are not proofs.

## Preparation and replay

The preparation binds the original recovery source, model and arrays, the full
compression certificate, the retained pool IDs, the max-min helper and exact
checker, and the installed numerical runtime. Small controls inspect native
row insertion in a nonmonotone original-row order without calling the optimizer.
They also test multiplier transport and deterministic selection. The existing
finite-box positive, zero-face and infeasible controls are replayed.

The cold preparation rebuilds the complete original matrix from the published
inputs and compares every array. A later terminal replay rebuilds that matrix,
checks the exact compression and the saved sequence of original-row additions,
then repeats any exact certificate or full rational-point check. Neither replay
calls an optimizer.

Prepared source: `experiments/workspace/rook_case4_cover_generation.py`.
Preparation: `experiments/logs/grids-and-triangles/rook-case4-cover-generation-preparation.json`.
Cold preparation: `experiments/logs/grids-and-triangles/rook-case4-cover-generation-preflight.json`.

At this checkpoint the production query is unrun. Its separate coordinator
source and model gate is required before execution.
