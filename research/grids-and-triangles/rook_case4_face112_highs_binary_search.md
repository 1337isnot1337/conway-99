# Binary incidence search on the 112-zero case4 face

This package prepares a HiGHS mixed-integer feasibility search with every
remaining selector binary. It seeks an exact incidence assignment for the
fixed case4 core. It does not construct the exterior graph, and a numerical
infeasibility status does not exclude the case.

## Exact initial model

The model retains 1,102 original selector coordinates after the 112 proved
zeros. No root action identifies variables and no branch-positive
assumption is imposed. The objective is zero.

The initial matrix has 2,195 rows and 27,515 nonzero coefficients:

| Row family | Rows |
| --- | ---: |
| Original native rows after exact zero substitution | 1,960 |
| The two proved parity equalities | 2 |
| Four proved pair capacities | 4 |
| Disjoint-guard inequalities from the checked branch traces | 227 |
| The proved 86-column sum equal to 2 | 1 |
| The sparse third-parity inequality | 1 |

The third-parity row is
\[
x_{803}\le x_{401}+x_{402}+x_{405}
+x_{590}+x_{591}+x_{592}+x_{593}+x_{594}+x_{595}.
\]
Its frozen direct proof expands five original Gram equations and proves
H3 = 1 + 2(U - x803), with H3 odd and nonnegative. This proof already
holds on the prior 111-zero integer face; it does not require zero663.

All 1,966 inherited native, equality, and pair rows were compared
coefficientwise against the saved full 112-face array. The 311 omitted
original native rows have the same exact unit-box witnesses as that
array. The complete cover pool contains 164,044 rows. The other 14,489
original covers have a proved zero target. The pool's complete ordered
list of original IDs was compared to the saved full array.

The preparation rebuilds only the compact rows and the cover-ID ledger.
It does not repeat the original signature-domain or graph census.

## Exact acceptance and cover generation

HiGHS receives all 1,102 variables with integer type and bounds [0,1].
The native preflight reads the model back and verifies every coefficient,
bound, objective coefficient, and integrality flag. All input numerical
coefficients are exactly represented integers; the smallest nonzero
coefficient is 1.

A numerical proposal within the prepared rounding tolerance supplies a
candidate Boolean vector. Rounding does not establish feasibility.
Acceptance restores all 1,214 original coordinates, sets the proved
zeros to zero, and checks with Python integers:

- all 2,271 original native rows;
- the two parity equalities, four pair capacities, and 112 zero rows;
- the 86-column equality, all 227 grouped cuts, and the H3 row;
- all 178,533 original coordinate covers.

This is 2,618 explicit integer rows plus the complete original cover
registry. Any violated native or already active cover row stops the
search without accepting the proposal.

If only omitted covers are violated, the driver appends the first
512 violated unseen original cover IDs, or all remaining violations
if there are fewer. Every appended row is reconstructed directly from
the immutable original registry. The driver does not add heuristic
no-goods or constraints extracted from floating-point tolerances.

## Limits and terminal meanings

The unchanged reviewed supervisor owns one child with a hard
180-second wall deadline. That deadline includes imports, input
validation, native initialization, solves, cover scans, and result
writes. The child makes at most 30 native calls, with at most 14,848
covers appended between calls. It uses one thread.

Before each call, the native time-limit option is set to the remaining
owned wall time. The parent deadline is authoritative even if the
native runtime counter has different cumulative semantics. A timeout,
late child exit, invalid proposal, or native infeasibility status
remains UNKNOWN. There is no automatic dual extraction or backend retry.

Every completed numerical proposal is preserved before exact inspection.
A complete accepted point has a separate exact witness artifact.
A separate owned cold pass, limited to 60 seconds, reconstructs the
integer rows and checks the original covers by direct literal
membership. It verifies all saved exact scans and all appended-cover
choices. This cold pass does not call an optimizer.

The generic native-audit record uses the historical field name
runtime_before_any_solve. In the initial preflight it is zero. In a
post-append audit it records the accumulated native runtime at that
audit. The field is not used for acceptance or time budgeting.

## Controls and frozen preparation

Three tiny HiGHS calls test the new backend path. The equation 2x = 1
is infeasible when x is binary. A separate three-variable model first
returns a point violating an external cover, then returns the unique
correct point after that cover is appended. Native readback verifies
integrality and the appended coefficients. Nonfinite, fractional, and
outside-box proposals are rejected by the decoding controls.

The existing owned-child supervisor controls are bound and reused.
They were not run again. The production model's native runtime is
zero in the saved preparation.

The compact model is bound to SHA256
195bf6c2c274100686087fd71a22f488f7aaee28025e39e490d7751bffcbceb6.
The complete query preparation is bound to SHA256
f6d28c3a44ab75dc27a3005577aee4cf0f0be01d9056cc9e1e4f3c3fb97edfac.
The source, all proof inputs, runtime binary, limits, options, and
native readback are recorded there.

The first compact-model preflight stopped before saving a model because
its omitted-row metadata used a different field name. That source is
preserved as rook_case4_face112_highs_binary_model_preflight_v1.py.
The correction uses the frozen witness field names and changes no row.

## The H3 branch diagnostic

The H3 row was also checked against all 64 previously cold-verified
branch fixed points. It causes no immediate contradiction and no new
single-row forced literal. Independent enumeration of the remaining
coordinates on that ten-term row checks all interval conclusions;
there are 254 such Boolean completions in total.

The first diagnostic attempt stopped at the continuation records'
different forward-hash field. Both source versions and the failure
record are preserved. The corrected diagnostic reads the two frozen
schemas explicitly. It performs no propagation or optimizer call.

These results concern one exact incidence relaxation and its saved
conditional traces. They do not resolve graph existence.
