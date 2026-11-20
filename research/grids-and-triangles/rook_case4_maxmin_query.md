# Complete rook case-four max-min query

The first max-min query of the complete recovered selector model reached its sixty-second solver limit. It produced no valid numerical basis or accepted exact certificate. Case four remains unresolved.

The frozen base has 1,156 variables, 174,208 rows and 11,868,882 nonzero coefficients after 58 proved zero columns are substituted. The extension adds a variable (t), bounds (0\le t\le1), and the rows (0\le x_j-t\le1) for every retained selector. It maximizes (t). No selector support is fixed from a numerical proposal.

The extended model has 1,157 variables, 175,364 rows and 11,871,194 nonzero coefficients. Its mathematical hash is `550972cca292015d484287228700402642d1e3eb52ea3d1b89ed0b74f83dff0c`.

Preparation bound the exact base matrix, all source hashes, Python and NumPy versions, and the loaded HiGHS binary. Exact controls cover a positive max-min point, an exposed zero face, a finite-bound Farkas contradiction, and invalid rational points. No optimizer ran during preparation.

## Bounded result

One production optimizer invocation was allowed. HiGHS was interrupted after 60.091 solver seconds and 1,264 simplex iterations. The complete process used 67.551 seconds and about 1.51 GiB peak resident memory. It recorded neither a valid primal solution nor a valid basis. Consequently no point reconstruction or mathematical infeasibility conclusion was accepted.

The saved result, compressed numerical state, solver log and replay record are in `experiments/logs/grids-and-triangles/rook-case4-maxmin-run01/`. The compressed numerical state has SHA-256 `4a16b14277cc7021dada690b40e69d5b373da9772009e486dd7c5a1395bfb634`.

The stopping limit does not exclude case four. Another solve requires a concrete improvement to the formulation or numerical method. Exact duplicate and implication removal are being examined before extending the solver budget.

## Exact acceptance rules

For any integer row multiplier vector `lambda`, nonnegative integer `gamma`, and ranged rows `L <= Cx <= U`, set
`c=C^T lambda`, `r=gamma e_t-c`, and
`B=sum max(lambda_i L_i,lambda_i U_i)+sum max(r_j,0)`.
The unit variable bounds imply `gamma t <= B`.

A strict negative bound would exclude this indexed selector domain, since each original feasible point extends at `t=0`. A zero bound with positive `gamma` would give exact zero or one implications through the nonnegative slack decomposition. An exactly checked feasible point with `t>0` would prove that no remaining selector is identically zero in this real relaxation. None of these outcomes was obtained in this run.

The sources are `experiments/workspace/rook_case4_maxmin_query.py` and `experiments/workspace/rook_case4_finite_box_certificates.py`. The root query gate and native preparation are retained under `experiments/logs/session-ab2f/`. The [complete base-model recovery](rook_case4_complete_lp_recovery.md) supplies every original capacity and cover.
