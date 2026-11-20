# Exact external-row generation for the F0 count model

This preparation retains the complete necessary count model while moving
117 dense inequalities out of the initial native search model. A candidate
is accepted only after exact integer checks of the full target and the
restored original parent. Native infeasibility has no independent proof and
does not exclude the component stratum.

The mathematical scope is a globally prism-free, F-free SRG(99,14,1,2)
with a split 18+18 shell containing component zero.
A count witness does not certify a common literal incidence or a completed
graph. Only the held finite family of PSD directions is enforced; the full
PSD cones are not enforced.

## Why this formulation was prepared

The first signed-character query ended UNKNOWN without an integer vector.
Its native log records 68.6353 seconds in named probing phases. An exact
input census found that the 92 held PSD rows and 25 integer refinements
contain 1,066,362 of the 1,308,488 linear terms. That is a term-count
observation. The log does not attribute wall time to individual row
families or prove that those rows caused the limit.

The new query changes both the initial row set and the recorded probing
parameter. It does not claim a speed improvement before execution. The
mathematical target also adds the two certified joint tables and the
coupled count domains described below.

## Full target and initial subset

All 18,444 native variable IDs retain their previous meaning:

| IDs, inclusive at the left and exclusive at the right | Meaning |
|---|---|
| `[0,15038)` | Original bounded orbit counts |
| `[15038,15941)` | 903 trivial-character product targets |
| `[15941,16059)` | 118 signed populations |
| `[16059,18444)` | 2,385 same-character product targets |

The immutable full target and the initial native subset have these sizes:

| Quantity | Full target | Initial native subset |
|---|---:|---:|
| Variables | 18,444 | 18,444 |
| Linear constraints | 31,066 | 30,949 |
| Multiplication constraints | 3,288 | 3,288 |
| Allowed-tuple tables | 44 | 44 |
| Total constraints | 34,398 | 34,281 |
| Linear terms | 1,308,492 | 242,130 |
| Maximum absolute row box sum | 16,269,245,368,499 | 9,000 |

The difference is exactly the 117 external rows. Every other full-target
constraint starts active. There is no saved candidate, solution hint,
objective, or arbitrary visitation constraint.

The 42 old basic tables are omitted because projecting each retained
refined character table onto its count columns gives exactly the old
allowed tuples. The preparation checks this equality for every table and
records the omitted and retained native row IDs. It does not remove any
old linear or multiplication constraint.

## Two joint tables and the common phase

The inherited equations fix the populations of selector-orbit unions
`{0,1}` and `{6,7}` to three. The separately certified tables enumerate all
three-subsets of each 24-member union. Each table has 176 allowed tuples,
with 22 count coordinates and six signed coordinates. The native target
retains both tables.

The character group has four common phases `(a,b,ab)`, with `a,b` in
`{-1,1}`. Applying one phase to every signed population of the same
character leaves every count and same-character product unchanged.
Homogeneous character-Gram rows acquire one common sign, and every local
or joint table is permuted. The two first-union sign sums are odd because
that union has population three. Exactly one common phase makes both
positive. Thus the target can impose

\[
1\le L_0+L_1\le3,\qquad
1\le L_{38}+L_{39}\le3.
\]

Here `L_j` denotes the local signed-population ID, whose native ID is
`15941+j`. The target includes these two rows explicitly. Filtering the
first joint table by these same rows leaves exactly 44 of its 176 tuples;
the second joint table retains all 176. All 42 refined individual tables
retain their complete tuple lists. There are 19,551 retained table tuples
in total.

This is one common phase for the whole assignment. It is not an independent
sign choice for each selector orbit and does not assume an automorphism of
a completed graph. The two normalization rows preserve a representative
of every feasible unnormalized count assignment. They are not restrictions
satisfied by every labelled signed assignment.

## Exact domains

For each retained table, the preparation computes its exact coordinate
projections. For a coordinate occurring in several tables, it intersects
those projections with the old integer domain. These are necessary
coordinate domains; no claim of full table-system consistency follows from
their intersection.

Every multiplication target receives the exact product set of its factor
domains. A square uses `{v*v}`, rather than the Cartesian product of two
independent copies of a domain. No product target is a factor of another
product, so this forward pass has no circular dependence.

The complete coupled-union census supplies 46 additional count domains.
The two coordinates 5699 and 5812 have domain `{0,1,2}`; the other 44 have
domain `{0,1,2,3}`. These are separately bound census consequences, not
deductions from the individual-table projections. Their original pair-orbit
IDs and certified domains are recorded in the plan.

In total, 3,638 domains change: 304 table-coordinate domains, all 3,288
product-target domains, and 46 census domains. The target has 3,355 domains
with holes and no fixed variable. Every domain change has a finite table,
product, or census witness. The source checks signed-64-bit bounds for
every native coefficient, endpoint, row box sum, and product.

## Exact candidate and row handling

The frozen external pool consists of the 92 held PSD rows and all 25
integer refinements. Their coefficients and endpoints remain identical to
the parent. The plan records parent-to-target and target-to-initial row
maps, along with unchanged column maps.

The owned query permits at most 12 calls within 180 seconds, with one
worker, seed zero, and `cp_model_probing_level=0`. The deadline includes
child imports, construction, serialization, search, and exact arithmetic.
An eight-second finalization reserve limits each requested native call;
the owner still enforces the complete hard deadline.

After a call returns, the driver saves every returned integer coordinate
before parsing the complete response or doing any acceptance work. It then
checks the actual active native prefix and evaluates all 117 external rows
with Python integers. A rejected candidate can add at most 16 violated
rows, chosen in frozen pool-ID order. A later call requires a strictly
larger certified prefix. No unchanged-prefix retry is allowed.

A candidate with no external violation must pass the full target, all
original parent native constraints, and the original mathematical
inspector. That inspector restores the original count coordinates and
checks the complete inherited obligations. A native INFEASIBLE status
remains unproved. An UNKNOWN, late, failed, or interrupted child is not
accepted. Saved incomplete candidates remain available for a separately
scoped arithmetic check.

The standalone terminal replay checks every completed prefix and every
recorded integer violation in chronological order. It preserves the
owner's terminal status and does not promote a partial or late candidate.
For a timely accepted count witness, it repeats full-target and original-
parent acceptance. It invokes no optimizer.

## Frozen preparation

The preparation constructs both models through the installed public
OR-Tools constructors. It compares every emitted variable domain and
constraint against the exact target maps and calls native validation
without constructing a solver. The cold replay independently reconstructs
the new domain/row maps from the bound records and compares both archived
protos. It binds the earlier complete proof records rather than repeating
their local-subset censuses.

The 1,625 exhaustive small controls check signed products, repeated-factor
squares, table holes, exact domain restrictions, and public-constructor
transcription. Driver controls check 118 prefix-growth cases, rejection of
an already-active violated row, integer gaps above `2^53`, and the actual
parameter/response serialization. The unchanged owned-supervisor controls
are bound from the previous frozen preparation.

Key artifacts are `f0-character-pool-model01/plan.json.gz`, the full and
initial protobuf archives in that directory, its preparation and cold
reports, and `f0-character-pool-query-preparation01/preparation.json`.
The preparation has no production solver call. Terminal outcomes are
recorded separately and cannot change these frozen inputs.
