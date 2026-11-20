# Exact downdate preparation for the remaining first-local matchings

The bounded preparation covered all 22 unresolved matchings of the first
local eight-set in 59.48 seconds. It accounted for 17,612,727 column pairs
and exported 1,863 additional binary conflicts. Every exported conflict
has a directly checked integer negative vector for the full Gram
remainder. No solver was called, no full CNF overlay was built, and no
additional matching case was excluded.

All 22 Gram matrices have exact rank 31. Every single attachment column
passes its one-column downdate test, so no unit exclusions were produced.

## Scope and method

The indexed cases are precisely the first 28 cases excluding the six
already checked UNSAT cases \(0,1,2,3,8,21\). Their local eight-set is
fixed; each case retains its complete original attachment domain. The
domains and case ordering are rebuilt and compared with the frozen
32-case prefix and the complete 2,521-core index.

For each case, the source verifies the same four kernel equations used
in `complement_rook_35core_gram_downdate.md`. It saves an exact positive
31-dimensional quotient, a complete rational LDL factorization, and an
integer inverse identity. All arithmetic uses unbounded integers and
exact fractions.

Every single-column leverage is checked. Every pair is then classified
by original-signature multiplicity, shared core triples, and shared
quota-one Gram pairs, and its two-by-two Schur condition is evaluated.
The exported binary clauses are only failures that are not already
detected by those three elementary tests. They remain logical
consequences of the original full Gram equations. No claim of semantic
independence is made.

Each certificate stores the original model and domain hashes, the full
Gram matrix, every attachment column, quotient identities, all pair
classifications, and a direct negative vector for every exported clause.
The fragment uses the original primary column numbering. The original
counter variables and clauses were not rebuilt or altered in this
preparation.

## Complete results

| Case | Attachment columns | New binary conflicts |
|---:|---:|---:|
| 4 | 1,214 | 30 |
| 5 | 1,157 | 92 |
| 6 | 1,160 | 27 |
| 7 | 1,230 | 86 |
| 9 | 1,284 | 839 |
| 10 | 1,160 | 490 |
| 11 | 1,257 | 22 |
| 12 | 1,193 | 57 |
| 13 | 1,203 | 21 |
| 14 | 1,267 | 65 |
| 15 | 1,286 | 8 |
| 16 | 1,228 | 28 |
| 17 | 1,330 | 10 |
| 18 | 1,265 | 26 |
| 19 | 1,271 | 6 |
| 20 | 1,264 | 7 |
| 22 | 1,291 | 8 |
| 23 | 1,360 | 10 |
| 24 | 1,336 | 10 |
| 25 | 1,399 | 11 |
| 26 | 1,332 | 5 |
| 27 | 1,325 | 5 |
| Total | | 1,863 |

The per-case compressed certificates total 1,538,304 bytes. The run had
a 120-second wall-time budget and saved each completed case before
continuing. Its terminal record marks all 22 requested cases complete,
with no unprocessed case. It does not treat a passed Schur test as an
incidence witness.

## Case 2 proof support

A separate annotated reconstruction of the original case 2 formula
matched its exact CNF hash and assigned every one of its 23,913 retained
input clauses to a unique counter group. The retained proof uses:

| Constraint family | Groups used | Retained input clauses |
|---|---:|---:|
| Gram equalities | 361 | 23,222 |
| Original-signature multiplicity | 33 | 147 |
| Additional core-triple capacities | 11 | 544 |

It touches all 34 nonsaturated core coordinates, all 202 original
signatures present in its domain, and 1,286 of 1,287 primary columns.
This does not expose a small row-supported obstruction. An absent
counter does not remove dependence on the complete domain, which was
itself filtered using the chosen matching.

The already recorded uncolored-core comparison has 28 distinct
isomorphism classes for these 28 matchings. No direct full-core
isomorphism transfer is available. No new isomorphism search was run.

Finite matching coverage does provide shorter conditional patterns.
In particular, local edges \((0,4)\) and \((1,5)\) occur together only
in cases 2 and 3, both excluded. That actual-graph consequence and its
transports are separate from this downdate census and from entailment
by an older weak joint CNF.

## Artifacts and replay

Source:
`experiments/workspace/complement_rook_35core_downdate_census.py`.
Certificates, fragments, incremental progress and terminal coverage:
`experiments/logs/grids-and-triangles/complement-rook-35core-first-local-downdates01/`.
The generation log is the adjacent file with suffix `-generation.log`.

The proof-family source and report are
`complement_rook_35core_case0002_proof_support.py` and
`complement-rook-35core-case0002-proof-support.json` in their respective
workspace and log directories.

Replay of one completed case rebuilds the whole domain, verifies the
positive quotient, repeats all pair tests, checks every exported
negative vector, and compares the exact fragment bytes. It uses no
solver. Choose a new output path:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_downdate_census.py replay \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-first-local-downdates01 \
  --case 9 \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0009-downdate-independent-replay.json
```
