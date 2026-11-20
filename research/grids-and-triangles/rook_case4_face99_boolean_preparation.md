# The complete case4 Boolean formula on its proved zero face

This preparation retains the complete existing case4 incidence formula and
adds exactly 85 proved zero units. The formula has 134,852 variables and
439,689 clauses. It concerns indexed 35-vertex core 4, with its existing
fixed local eight vertices and matching. It does not fix an exterior
incidence design.

The full real selector relaxation now has an exact point positive on all
1,115 remaining coordinates. That point does not supply a binary incidence.
The present preparation tests the binary necessary conditions with the
proved face imposed. No coordinate, basis, or value from the real point
enters this Boolean formula.

## The unchanged formula and the additional units

The previous complete formula has SHA-256
`5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2`.
Its 439,604 clause lines are copied byte for byte. The DIMACS header is
adjusted, and 85 negative primary clauses are appended. There are no new
auxiliary variables or graph symmetry conditions.

All 1,214 optional attachment columns remain in the primary domain. The
existing formula represents all 630 upper-triangular Gram positions, 186
original-signature multiplicity rows, 1,365 necessary triple capacities,
30 exact Gram conflict clauses, 60 exact exterior-row inequalities, and
178,533 coordinate-cover clauses. Of the triple capacities, 1,353 follow
from quota-one Gram rows and 12 have separate encodings. No triple capacity
is discarded as a mathematical requirement.

The exact seed verifier rederives 88 zeros from six saved Gram/triple row
combinations and 14 zeros from empty coordinate covers. Their intersection
has size three, so their union has size 99. The 14 cover units were already
in the old formula. The suffix consists of the other 85 columns, with
zero-based column `a` translated to DIMACS unit `-(a+1)`.

The six row-combination proofs are expanded over all 1,214 original
coordinates. Every negative coefficient is justified by an earlier proved
zero. The cover proofs check the positive target demand and every eligible
neighbor product. These are unconditional consequences within this fixed
core; no assumed branch assignment is used.

The new formula has SHA-256
`f3467d02ca6763391668c0cdac0a395dab23688d831b25107fcf04ea1c94ac22`,
57,874,464 bytes, and 13,546,449 literal occurrences. The byte audit recovers
the full old hash from the copied prefix and checks the complete sorted
85-unit suffix. A cold rebuild of the original formula and all unit
premises passed. The overlay controls cover 256 Boolean assignments across
16 small unit suffixes.

## The separately gated query

The prepared driver permits one fresh proof-enabled CaDiCaL300 child with
a 180-second parent wall limit. Imports, clause streaming, bootstrap,
search, and proof export count within that limit. It uses no assumptions,
automatic retries, hints, numerical values, or new symmetry restrictions.
The installed runtime and backend files are hash-bound.

The child and proof checkers have a 3 GiB address-space limit and a 256 MiB
individual-file limit. A completed native binary proof may be at most
64 MiB before export. Exported text and retained proof files may be at most
128 MiB each. A retained input core may contain at most 250,000 distinct
clauses. Crossing a limit leaves an unresolved result. A partial proof is
never accepted as an exclusion.

On a SAT answer, the parent runs the unchanged complete incidence
inspector and additionally checks all 99 zeros. Acceptance requires every
original Gram entry, 64 distinct original signatures, all triple packing,
the original uncapped exterior-row inequalities, and all registered
coordinate covers. Such a point is a partial incidence witness. It does
not specify the remaining exterior graph edges.

On an UNSAT answer, a direct DRAT check has a separate 60-second checker
budget. Its retained inputs are checked for inclusion in the complete
formula. A separate replay then reconstructs the complete original formula
and the 85 exact unit implications, binds the same full hash, checks every
retained input again, and runs a second 60-second DRAT check. Formula
reconstruction time is separate from the proof-checker budget. Only the
successful cold proof replay excludes indexed core 4.

A parent timeout records UNKNOWN before terminating and reaping the owned
child. Memory failures, proof-size refusal, export failure, checker failure,
and unresolved native termination also preserve the open case. This
preparation makes no claim about the production outcome.

## Frozen preparation files

- `experiments/workspace/rook_case4_face99_boolean_overlay.py`
- `experiments/workspace/rook_case4_face99_boolean_query.py`
- `experiments/logs/grids-and-triangles/rook-case4-face99-boolean-preparation01/model.json`
- `experiments/logs/grids-and-triangles/rook-case4-face99-boolean-preparation01-cold.json`
- `experiments/logs/grids-and-triangles/rook-case4-face99-boolean-query-preparation.json`
- `experiments/logs/grids-and-triangles/rook-case4-face99-boolean-query-controls01/tiny-drat.log`
- `experiments/logs/grids-and-triangles/rook-case4-face99-boolean-independent-source-review.json`

The model records the complete source and input hashes, every added zero
and its provenance, the old and new formula hashes, the runtime binding,
and the resource contract. The previously saved tiny backend SAT/UNSAT
controls are hash-bound; the current checker separately passed the saved
tiny proof. Preparation did not repeat a solver call.
