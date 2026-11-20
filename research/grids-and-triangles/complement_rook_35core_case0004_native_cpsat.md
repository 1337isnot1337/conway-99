# Native Boolean formulation of indexed 35-core case 4

This package prepares a candidate generator for the remaining 64-vertex
incidence problem. It retains the complete 1,214-column domain. It does
not specify edges among those 64 vertices. A feasible assignment is a
partial incidence witness, and this package makes no exclusion claim.

The previous complete coordinate-cover CNF has 134,852 variables and
439,604 clauses. Its hash is
`5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2`.
The new formulation uses only the 1,214 primary Boolean variables.
OR-Tools receives the cardinality and integer linear constraints
directly; the preparation introduces no counter variables.

## Exact constraint coverage

For each admitted attachment column $h_a$, let $x_a$ indicate that
the corresponding exterior vertex is selected. Let

\[
G=12I+2J-B^2-B
\]

for the fixed 35-vertex core adjacency matrix $B$. The complete Gram
equations are

\[
\sum_a x_a h_a h_a^{\mathsf T}=G.
\]

The native constraint list is as follows.

| Family | Native constraints |
|---|---:|
| Upper-triangular Gram positions, including empty zero rows | 630 |
| At most one attachment per original 27-core signature | 186 |
| At most one selected column containing each nontrivial core triple | 1,365 |
| Previously certified two-column Gram conflicts | 30 |
| Exact exterior-row inequalities, with their original integer weights | 60 |
| Complete retained coordinate-difference cover clauses | 178,533 |
| **Total** | **180,804** |

Of the 630 Gram positions, 234 are the identity $0=0$. They are
represented by true empty conjunctions. No constant Boolean variable
is needed. The 396 nonempty equations are all distinct.

The old CNF explicitly encodes 12 triple capacities. Its other 1,353
triple capacities follow from quota-one Gram pair equations. The new
model retains all 1,365. For each of the previously implied rows, the
preparation saves the exact pair and verifies that the triple support
is contained in that pair's support. Thus these additional explicit
rows do not remove a previously allowed Boolean assignment.

Each of the 60 exterior-row inequalities is used in its original form

\[
\sum_b w_b x_b \ge d x_a.
\]

Its native linear expression is \(\sum_b w_bx_b-dx_a\), with lower
bound zero. The upper bound \(\sum_b w_b\) is automatic for Boolean
variables and adds no restriction. The model does not cap or round
the integer coefficients.

All 178,533 cover clauses are taken from the frozen complete ledger.
The preparation replays every ordered-coordinate origin, duplicate,
and same-target subsumption witness before writing a temporary clause
stream. It frees the large ledger before allocating the native model.
Every cover is then added individually. No list of the 12,887,146
cover-literal occurrences is retained in Python.

## Verification and limits

The exporter writes a binary `CpModelProto`. A separate standard
protobuf parser reads those bytes and checks all 1,214 Boolean domains
and all 180,804 constraints against the exact input rows. It also
checks that the model has no objective, assumptions, solution hint,
search strategy, extra enforcement literal, or symmetry field.
The native model validator must accept the model.

Cold replay reconstructs the complete attachment domain, all row-cut
certificates, the full cover ledger, and the exported binary proto.
It requires an identical proto hash. The installed OR-Tools wrapper,
native extension, bundled libraries, protobuf parser, and versions are
bound in the preparation record. No package is installed or changed.

The separate small controls check 58 complete Boolean assignments for
the cardinality, weighted, cover, and empty-support forms. Two further
controls use a genuine nine-vertex rook graph: its incidence assignment
is accepted, and deleting one selected column is rejected. These are
small controls, not queries of case 4.

The preparation refuses an exported proto larger than 80 MB. It also
checks a 180-second preparation limit and a 1 GiB observed process RSS
limit at preparation stages. These are checked limits, not an operating
system memory sandbox. The intended later production query uses one
worker, a 60-second solver limit, no objective, and no prescribed
incidence assignment. Preparation and query remain separate.

Any later feasible result must pass the frozen exact incidence
inspector: all 35-by-35 Gram entries, 64 distinct original signatures,
all core-triple capacities, attachment counts \((4,40,20)\), all 30
conflicts, all 60 uncapped integer inequalities, and all cover origins.
The inspector does not construct a 99-vertex graph. A CP-SAT
`INFEASIBLE` or `UNKNOWN` status is not an accepted exclusion of case 4.

## Prepared model

The full preparation and exported-byte audit passed in 66.60 seconds,
with a peak process RSS of 439,336 KiB. The binary proto has 27,434,194
bytes and hash
`b98aa8f1b6ea6e156e5bccb19b88080e543e9514e9797627813a684ff3d7fc73`.
The model record hash is
`a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476`.

A separate cold reconstruction reproduced every proto byte in 41.65
seconds, with peak RSS 442,732 KiB. The cold replay record hash is
`a6627477382b47013a0b26984826a565df879b0f226dc2ad505da318e751b5a7`.
These preparation results include no production solve.

## Replay

The source is
`experiments/workspace/complement_rook_35core_case0004_native_cpsat.py`.
Its `controls`, `prepare`, and `replay` commands are separate. It has no
production solver command. The preparation and cold replay logs bind
the exact commands, model record, installed runtime, and binary proto.

```bash
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_native_cpsat.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-native-cpsat-model.json \
  --output /tmp/conway99-case4-native-cpsat-independent-replay.json
```

The input model and every output path must be preserved; the commands
refuse to overwrite an existing output.
