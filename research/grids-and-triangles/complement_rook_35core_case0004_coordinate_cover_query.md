# One query of the complete coordinate-cover model

## Prepared formula

The separate query wrapper binds the complete streamed case4 formula:
134,852 variables, 439,604 clauses, and 13,546,364 literal occurrences.
Its full CNF SHA-256 is
`5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2`.

The model preserves every clause of the frozen 60-cut formula and adds all
178,533 retained coordinate-cover clauses. The complete census and exact
subsumption witnesses are described in
`complement_rook_35core_case0004_coordinate_covers.md`.
The model's separate cold reconstruction has already passed.

This package prepares one fresh proof-capable query with a 60-second limit
including clause loading. It contains no result from that query. The previous
case4 UNKNOWN results remain unchanged.

## Wrapper and resource limits

The wrapper is
`experiments/workspace/complement_rook_35core_case0004_coordinate_cover_query.py`,
with SHA-256
`eb352386f55c5a1fd6ddb9c692ad934d8eef87904c00e86122172dc1ebc1f9d8`.
Its preparation record is
`experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-query-preparation.json`,
with SHA-256
`da135f734508b5116df69e27b132948672dc738e3e07594cd1c5bbc26ad3a42f`.

The preparation checks the source and model bindings, reads every CNF clause,
and checks the complete variable, clause and literal inventory. It took
5.714 seconds with peak RSS 75,600 KiB. Five small exact parser examples,
six rejected malformed streams, and 384 coordinate-demand weakening cases
passed. These controls invoke no solver.

The query streams one clause at a time into one fresh Glucose4 instance.
It does not allocate a Python list of the 13.5 million literal occurrences.
There are no assumptions, phase preferences, extra clauses or automatic
retries. If loading reaches the deadline, the outcome is UNKNOWN and the
wrapper does not solve a partial formula. After full loading, the remaining
time is passed to an interruptible solve.

Direct DRAT verification and the separate cold DRAT verification each have
their own 60-second checker limit. Rebuilding and checking the input formula
are recorded separately from the solver interval.

## SAT interpretation

A SAT point is a partial 64-column incidence. The remaining 64-vertex graph
has not been constructed. The direct inspector checks:

- All 1,225 entries of the 35-core Gram matrix, original-signature
  multiplicities, all selected-column triple constraints, and the derived
  attachment counts 4, 40 and 20.
- The original 27-core incidence identities.
- All thirty certified Gram conflicts and all sixty original integer row
  inequalities, using their uncapped weights and demands.
- All 239,299 unique same-target covers, all 476,766 positive coordinate
  origins, and all fourteen forced-absent targets.

The coordinate origins use their explicitly recorded weakening to demand
one. This inspector does not silently replace those clauses with stronger
cardinality restrictions.

## UNSAT interpretation

A solver UNSAT response is recorded before proof verification and is not
an exclusion by itself. The direct checker verifies the raw proof against
the full bound formula and extracts a retained input/proof pair. The wrapper
then checks each retained input against the complete formula, using exact
normalized clause bytes.

The separate replay cold-rebuilds the old incidence model, the thirty Gram
conflicts, the sixty integer row cuts and their threshold encodings, every
coordinate-cover origin and subset witness, and the complete streamed CNF.
Its full hash must match the prepared formula. The replay checks retained
input inclusion against that rebuilt formula and verifies the retained DRAT
proof. Only that completed sequence can exclude indexed 35-core case4.

Input attribution distinguishes original incidence clauses, Gram conflicts,
weighted row-cut clauses and coordinate covers. It also records whether all
retained inputs were already available in the original incidence formula or
the old 60-cut formula. Duplicate clauses are assigned to their earliest
available family. There is no claim of old-formula entailment when a proof
uses a genuinely added necessary condition.

## Commands

After the separate source/model gate, one query can be made with a fresh
result directory:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_coordinate_cover_query.py solve \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-query-preparation.json \
  --directory experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-query-run01 \
  --seconds 60 --checker-seconds 60
```

Cold result replay also requires a fresh output path:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_coordinate_cover_query.py replay \
  --preparation experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-query-preparation.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-query-run01/result.json \
  --output experiments/logs/grids-and-triangles/complement-rook-35core-case0004-coordinate-cover-query-run01-cold-replay.json \
  --checker-seconds 60
```

All outcomes remain scoped to case4. They do not settle the other first-local
matchings, another local-set orbit, or the Conway99 problem.
