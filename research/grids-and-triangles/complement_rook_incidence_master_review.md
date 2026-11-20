# Independent review of the incidence-master pilot

The prepared runner and proof wrapper pass this review. This is a
mathematical and implementation audit, not a solver outcome or an
exclusion of the complementary-rook core.

The reviewed runner is `complement_rook_incidence_master.py`, SHA-256
`01476233b9cf838e2d45d0583dcd0c5cc6bd3a3c5226164a36ed2e1d4cfd6594`.
The reviewed wrapper is `complement_rook_incidence_master_certificate.py`,
SHA-256 `f5ddd52ab89f6911dc522bbd83f894466719b72890a192fd2d4387aebf2db15c`.
The small executable review binds both files through the prepared
manifest. It does not instantiate a solver or parse the large oracle CNF.

## Master coverage

An independent dense construction of the 27-point core reproduces its
Gram matrix and all 252 signatures among the 729 triples. Each signature
has one point from each of the three nine-point classes. Distinct
outside vertices cannot repeat a signature of size three: that would
give them three common neighbors in the core.

The 180 master equations have the following form.

| Pair of classes | Positive pair equations | Quota |
| --- | ---: | ---: |
| First rook, second rook | 36 | 2 |
| First rook, complementary rook | 72 | 1 |
| Second rook, complementary rook | 72 | 1 |

Every omitted off-diagonal Gram entry is zero. No admissible signature
contains such a pair, so those entries hold without extra equations.
For any core point, summing its margins against either other class
counts each selected signature containing that point once. The sum is
eight. These identities recover all 27 diagonal Gram entries. Summing
the nine diagonal equations in one class gives 72 selected signatures.
Thus the master imposes exactly the incidence Gram conditions on the
complete signature domain. It does not impose an additional bound on
the parameter `a`.

The executable review checks these statements as integer coefficient
identities. It also regenerates the small master serialization, giving
1,332 variables, 2,520 clauses, and SHA-256
`9145f5a1e7f5c2e7a482a9d38baa86f4c39949482baf172d73e0ac8e3989ec9f`.

## Conditional oracle and signed cuts

Every extracted design is checked against all 729 Gram entries. The
oracle receives all 252 signed selector values. Selected signatures
are positive assumptions; all other signatures are negative assumptions.
The oracle contains the unchanged bound joint model. It receives no
visitation blocks, master cuts, symmetry restrictions, or extra graph
constraints.

If an assumption core is returned, the runner checks that each signed
literal belongs to this complete assignment. It then starts a fresh
proof-enabled solver on the original base CNF plus exactly those unit
clauses. That solve uses no assumptions and no learned clauses from
the reusable oracle. This avoids the cumulative assumption-proof issue
documented in the separate small controls.

If the core units are `l_1,...,l_m`, a verified contradiction implies
the necessary selector clause `-l_1 or ... or -l_m`. The sign handling
is correct for positive and negative core literals. The executable
review checks all 256 combinations of four-literal core signs and
Boolean assignments.

The runner verifies the fresh proof with DRAT, checks that each retained
input clause belongs to the explicit unit-augmented formula, and writes
the certificate before adding the resulting clause to the master.
The pilot result separately records the actual master mutation.

The replay wrapper rechecks the selected incidence and signed units,
rebuilds the frozen base formula, matches its exact hash and metadata,
appends the same units, and matches the full augmented-CNF hash. It
then checks retained-clause inclusion and verifies the retained DRAT
proof. This is sufficient to bind a future cut to the intended base
model. This review has not replayed a future pilot proof.

## Partial points and termination

A SAT oracle result is only a point of the necessary model. The runner
reconstructs the full 99-point adjacency matrix and checks degrees,
core incidence, all pairs involving the core, and all remaining pair
defects. A zero-defect point stops as a candidate for independent
verification. A defective point remains explicitly partial.

The negative clause on the 72 selected signatures excludes exactly
that incidence design because the master population is fixed at 72.
The runner marks this clause as an exploratory visitation block, not
a theorem. Master exhaustion after any such block makes no class
exclusion claim. Even exhaustion using only certified cuts requires a
separate proof of the resulting master formula before publication as
an exclusion.

UNKNOWN in the master, conditional oracle, or fresh proof solve stops
the pilot. A DRAT timeout, rejection, or other exception stops it as an
error. No unverified cut is inserted. Certificates for earlier cuts
remain separate. The eight-design limit is explicitly reported as
bounded exploration. The source never promotes any of these terminal
states to a whole-core exclusion.

## Reproduction

```sh
python experiments/workspace/complement_rook_incidence_master_review.py \
  --manifest experiments/logs/grids-and-triangles/complement-rook-incidence-master-model.json \
  --output experiments/logs/grids-and-triangles/complement-rook-incidence-master-review.json
```

The checked report is
`experiments/logs/grids-and-triangles/complement-rook-incidence-master-review.json`.
The dense-domain and signed-clause checks pass. No large formula was
parsed or rebuilt, and no solver was called during this audit.
