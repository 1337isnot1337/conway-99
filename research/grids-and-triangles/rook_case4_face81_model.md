# Case4 selector relaxation after 81 proved zeros

The new model substitutes exactly 81 proved zeros into the complete case4
selector relaxation. It retains 1,133 variables, 1,984 native rows and 168,847
coordinate covers. Its 170,831 rows contain 11,390,157 nonzero coefficients.
This is preparation for a new bounded query. It is not an exclusion of case4.

## Exact premises and row accounting

The frozen three-row and four-row Gram relations prove 70 zero columns using
only nonnegative real Gram weights. Fourteen previously certified empty covers
prove 14 zero columns; the sets intersect in 3 columns. The union therefore has
81 columns. Propagation through all native rows and covers found no additional
assignment. The builder uses the direct Gram and cover certificates, with no
numerical presolve premise or conditional branch.

Every one of the original 2,271 native rows is substituted exactly. A row is
omitted only if its lower and upper bounds contain the entire remaining unit-box
range. The 287 omissions have explicit endpoint witnesses. The remaining rows
are 396 Gram equalities, 186 original-signature capacities, 1,340 triple capacities,
4 Gram conflict inequalities and 58 uncapped exterior-row inequalities.

Every one of the 178,533 registered covers is also accounted for. A cover with a
proved-zero target is a unit-box tautology; this removes 9,686 rows. The other
168,847 covers retain their exact negative target and every remaining positive
literal. Their finite upper endpoints are unit-box tautologies. No same-target
subsumption or additional compression is used in this model.

All coefficients and row bounds are integers. The builder binds the three
published original inputs and the frozen four-Gram certificate. It stores each
retained row's original family and index, all omitted-row witnesses, all original
column identifiers, and a canonical integer row-stream hash. A cold preflight
reconstructs these data before any optimizer call.

## Prepared bounded row generation

The max-min extension adds `0 <= x_j-t <= 1` for every remaining selector and
`0 <= t <= 1`. An original feasible point extends with `t=0`. A verified positive value of `t` proves
that no remaining selector is identically zero in this real relaxation. An exact
zero upper bound can instead expose another face; numerical complementary
slackness alone is not a proof.

The driver starts with 1,984 native rows and 1,133 extension rows, totaling 3,117 rows
and 28,624 nonzeros. It uses one persistent solver and scans all 168,847 covers after
each optimal numerical proposal. It adds at most 512 violated original rows per
round, ordered by violation and then by original row ID. The limits are 30 calls,
120 cumulative solver seconds and180 seconds for the numerical phase. These
limits are unchanged from the first reviewed row-generation query.

Exact reconstruction has a separate 60-second budget. A rational point is
accepted only after all 171,964 original and extension rows, and every variable
bound, pass integer arithmetic. All 1,214 selector coordinates are then restored
by inserting the 81 proved zeros. An infeasibility or zero-face certificate uses
the reviewed finite-box identity on the full matrix, with zero multipliers at
rows absent from the solved prefix. A checked contradiction for a prefix is
also a contradiction for the complete model.

The new driver imports the unchanged native assembly, row insertion, row
selection and bounded-call helpers. Its exact reconstruction and transcript
replay functions have a separate AST comparison against their frozen parents.
The comparison permits only new dimensions, removal of the old compression
argument, and the explicit face scope. The new loading and model-definition
functions still require ordinary source review. Preparation and cold preflight
do not run an optimizer.
