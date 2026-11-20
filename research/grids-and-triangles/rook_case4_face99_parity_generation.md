# Complete case-4 LP with two integer covers

This preparation adds exactly the two proved parity covers to the complete
selector LP on the 99-zero face. The old model, its exact interior point,
and all previous query records remain unchanged.

The two covers are necessary for nonnegative integer incidences. Each follows
from an explicitly checked sum of 33 or 35 original Gram equations:

\[
2q_1^{\mathsf T}x+\sum_{a\in H_1}x_a=45,
\qquad
2q_2^{\mathsf T}x+\sum_{a\in H_2}x_a=47.
\]

After the previously proved zero coordinates are substituted, both cover sums
must be odd nonnegative integers. The new rows are therefore
\(\sum_{a\in H_i}x_a\geq1\). Each support has 42 columns. Their upper bounds
of 42 are redundant under the unit box. The direct integer verifier rebuilds
every coefficient on all 1,214 original columns; its certificate and the
complete 41,041-equation parity scan are separate frozen inputs.

These rows exclude the previously saved fractional point. That fact supplies
no new coordinate-zero premise. All 1,115 surviving original selectors remain
independent variables. No basis equation, candidate support, orbit equality,
or symmetry restriction is added.

## Exact model accounting

| Quantity | Parent | With the two covers |
| --- | ---: | ---: |
| Surviving selector variables | 1,115 | 1,115 |
| Base rows | 167,935 | 167,937 |
| Base nonzeros | 11,012,058 | 11,012,142 |
| Native rows retained from the original inventory | 1,966 | 1,966 |
| Coordinate covers retained in the pool | 165,969 | 165,969 |
| Proved zero original columns | 99 | 99 |

The first 167,935 rows and every corresponding coefficient, index, bound,
origin label, and column ID are exact array prefixes. New row IDs 167,935 and
167,936 are the two integer covers. The original 2,271 native constraints and
178,533 coordinate covers remain accounted for by the parent model's exact
retention or unit-box omission witnesses.

The new builder is `rook_case4_face99_parity_model.py`. It verifies the frozen
parent hashes, repeats both direct integer proofs, checks the entire original
integer stream, and saves the two-row suffix. Its cold mode rebuilds the
parent from the original published inputs and checks every resulting array.
The model cold replay passed in 32.095 seconds. The final driver preflight,
which also rebuilt the complete model and checked native row assembly,
passed in 43.857 seconds with no optimizer call.

The new base stream SHA256 is
`504533469c6359c7c9a1693db7a18c6c62d2ba617f33322495585c8226b14135`.
The arrays archive SHA256 is
`83b44951a8bf8bb5a8d142e1e63b35f19ee1ce6e38744f3933c0f1b14fbdcb12`.

## Bounded query contract

The new driver is `rook_case4_face99_parity_cover_generation.py`. It adds one
variable \(t\) and all 1,115 rows \(0\leq x_j-t\leq1\), then maximizes \(t\).
Thus every original feasible point extends with \(t=0\), and a verified
positive \(t\) would exclude further identically zero coordinates of this
strengthened relaxation.

The complete extended model has 1,116 variables, 169,052 rows, and 11,014,372
nonzeros. Its initial active system has 3,083 rows and 28,291 nonzeros:
all 1,966 retained native rows, both new integer covers, and all max-min rows.
Every one of the 165,969 coordinate covers stays in the complete pool.

After an optimal numerical proposal, the driver evaluates the entire frozen
matrix. It selects at most 512 previously inactive covers by descending
violation, breaking ties by original row ID, and appends them to the existing
solver. It never substitutes the current active subset for the complete
model in an exact primal check.

The prepared limits are unchanged from the reviewed parent driver:

- At most 30 native calls and 120 cumulative solver/existing-ray seconds.
- A 180-second numerical phase, including matrix setup and full-pool scans.
- One worker, with no automatic retry after a nonoptimal result.
- At most 14,848 appended coordinate covers.
- A separate 60-second exact reconstruction stage and 60-second exact
  certificate-check budget.

All numerical proposals, active row IDs, available bases, and solver statuses
are retained. A numerical infeasibility alone is unresolved. An accepted
infeasibility needs a complete exact finite-box certificate and cold replay;
an accepted rational point must satisfy every row and bound of the complete
extended model. A certificate on an active row subset remains valid for the
full model because every active row is a proved necessary row.

The source adaptation is recorded as 18 explicit text replacements. Sixteen
functions, including the numerical run loop, extension construction, full
pool scan, and exact primal reconstruction, are AST-identical to the parent.
The finite-box helper and row assembly helper are unchanged. One initial
source-control script failed because Python's `ast.literal_eval` does not
evaluate the literal expression `29*512`. That attempt is preserved; the
corrected no-import checker evaluates only literal constants, dictionaries,
and integer multiplication, and passes. No mathematical source or model
changed in that correction.

## Scope

This is a necessary incidence relaxation for the single saved 35-core case 4.
A feasible real point is not a binary incidence or a 99-vertex graph. A proved
infeasible strengthened model would exclude this local core/matching case;
it would not by itself settle the other local cores or Conway's problem.

The preparation record, source gate, and terminal query record are separate.
This note does not predict a query outcome.
