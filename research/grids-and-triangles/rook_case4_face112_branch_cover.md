# Boolean branch cover on the 112-zero rook incidence face

The two proved unit sums give a complete cover by 64 remaining positive
patterns. These are 31 common-support singletons and 33 pairs. Every Boolean
solution of indexed incidence case 4 satisfies exactly one retained pattern.
This is a branch cover, not a claim that a retained pattern is feasible.

## Cover identity

Let H1 and H2 be the supports of the two proved equalities

\[
\sum_{a\in H_1}x_a=\sum_{a\in H_2}x_a=1,
\qquad x_a\in\{0,1\}.
\]

Before removing coordinate 663, put

\[
C=H_1\cap H_2,\qquad A=H_1\setminus H_2,\qquad B=H_2\setminus H_1.
\]

Their sizes are 32, 4 and 10. The four members of A are
259, 260, 261 and 262. There are exactly two cases.

If a member of C is one, both unit sums force every other member of their
union to zero. There is one singleton pattern for each member of C.

If every member of C is zero, exactly one member of A and exactly one
member of B are one. There is one positive pair pattern for each member
of A times each member of B.

These 32 + 40 = 72 patterns are mutually exclusive and cover every Boolean
solution. The proof uses no relabeling or graph-automorphism assumption.
Variables outside the two supports remain unrestricted.

The proved zero at coordinate 663 removes one singleton. Four previously
certified forbidden pairs remove four pair patterns:

\[
(259,590),\ (259,591),\ (259,593),\ (259,732).
\]

The complete direct row-box check described below removes three further
pairs. Thus 64 patterns remain.

## Direct check of all 40 pairs

The preparation checks all 40 pairs from A times B against all 2,271
original native rows, for 90,840 exact row evaluations. The 112 proved
zero coordinates are fixed to zero and the two members of the tested
pair are fixed to one. Every other variable retains its full Boolean
box. No propagation or additional negative assignment is used.

For a row with coefficients c and bounds l and u, the conditional minimum
and maximum are

\[
m=\sum_{\text{fixed one }a}c_a+
  \sum_{\text{free }a}\min(c_a,0),\qquad
M=\sum_{\text{fixed one }a}c_a+
  \sum_{\text{free }a}\max(c_a,0).
\]

The pair is impossible if m > u or M < l. Every reported contradiction
stores the original row index, family, source, complete row hash and
exact conditional interval.

Six pairs fail this direct test. Three are the previously recorded
pairs from Gram row 580, associated with fixed-core pair (25,30).
Its quota is one, while either selected pair contributes two.

The other three are

\[
(262,594),\ (262,595),\ (262,733).
\]

All three violate original Gram row 584, associated with fixed-core pair
(25,34), also with quota one. The selected pair gives conditional minimum
two. These exclusions already follow from the original native system;
no new premise is introduced.

The exact rational bound for (259,590) supplies the fourth previously
certified pair exclusion. It does not fail a single original row-box
test. The preparation retains that distinction.

| Disposition | Patterns |
|---|---:|
| Proved zero at 663 | 1 |
| Previously certified forbidden pairs | 4 |
| Additional direct original-row exclusions | 3 |
| Retained for branch propagation | 64 |
| Complete original cover | 72 |

## Complete propagation input

The proposed propagation batch retains all 1,214 literal primary variables,
all 2,271 original native rows and all 178,533 registered coordinate covers.
It also retains the two exact unit sums, four certified pair constraints
and 112 explicit zero rows from the frozen unbranched closure.

One further exact row is appended:

\[
\sum_{a\in S}x_a=2,\qquad |S|=86.
\]

Its proof is the independently replayed identity

\[
3x_{663}+\sum_{a\in S}x_a=2,
\]

after applying the proved zero at 663. Every nonzero multiplier in that
identity uses an equality row. The equality therefore does not come from
rounding an upper bound into an unjustified equality.

The common input has 2,390 integer rows and 29,074 term occurrences, in
addition to the complete cover registry. A branch appends one or two
explicit equality rows x_a = 1, with its original pattern ID and column
stored as provenance. These assumptions are conditional. Assignments
derived within a branch are not global zeros or ones.

The branch order is fixed: increasing original pattern ID, using sorted
common singletons followed by A-major, B-minor pairs. The eight excluded
patterns remain in the ledger with their reasons and are skipped by the
future batch.

The proposed forward batch has a 60-second cooperative budget. The unchanged
audited engine checks time at every native row and every 128 cover records.
Every completed branch trace and any returned partial trace must be retained.
A separate cold pass must replay all inference reasons before a branch
contradiction is promoted. A fixed point is only exhaustion of these
propagation rules; it is not a Boolean solution or a graph completion.

No production branch propagation, SAT solve or optimizer call is part of
this preparation.

## Sources and exact scope

The preparation source is
experiments/workspace/rook_case4_face112_branch_scope.py,
SHA256 291be1d8b93acebd859fc642b953acd463e40fd62cecdb3e57c7c14e86a31e8a.

The complete ledger is
experiments/logs/grids-and-triangles/rook-case4-face112-branch-preparation01.json,
SHA256 5e8bf7a32063cda146b18de2a4b3ee7c4b2a043d5076a5d4a9a9e4ca678144c2.

It uses the unchanged propagation and reason checker
complement_rook_35core_case0004_primary_propagation.py,
SHA256 3e4b8a5118c0ee8e37aee03d5f265128b53af9ae8ffc169393fe2d731062d8f7.

The premise loader is rook_case4_face112_primary_closure_v3.py,
SHA256 405f732445043762db0c52cbc0cfdc159dcb945351925afdcc57af7c9606b3f9.
Its completed preparation is bound at SHA256
b005a338bd10a61769718afb0f6cab7c39b2f7b86bf46cee228a951398fd585c.

The new scope preparation took 11.086 seconds. Its small controls check 735
Boolean assignments over varied common and difference-set sizes, including
all 90 satisfying assignments. Every satisfying assignment has exactly one
cover pattern. A separate cold preparation replay checks the complete
72-pattern ledger and all 40 pair-box calculations.

This preparation concerns indexed 35-core incidence case 4. It does not
exclude that case or resolve the 99-vertex graph problem.
