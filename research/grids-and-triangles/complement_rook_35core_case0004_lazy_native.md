# Case4 native candidates with lazy coordinate covers

This package prepares a smaller candidate generator for the unresolved
35-core matching case4. It does not exclude that case. It does not supply
a completion of the remaining 64 vertices.

The preceding full native query returned UNKNOWN. Its saved response did
not contain phase logging, so the 4,074 branches and zero conflicts do not
identify how much time was spent in presolve, probing or main search.
The present preparation changes where the proved coordinate covers are
checked. It preserves the full native model as an immutable reference.

## Initial formula and external registry

The initial formula has 1,214 Boolean column selectors and 2,285 native
constraints. It retains the original 2,271 constraints:

| Family | Constraints |
| --- | ---: |
| Complete 35-core Gram positions, including empty zero rows | 630 |
| At most one attachment for each original signature | 186 |
| Core-triple capacities | 1,365 |
| Certified two-column Gram conflicts | 30 |
| Original, uncapped integer exterior-row inequalities | 60 |

All 1,365 triple capacities are present. The 1,353 capacities previously
implied by quota-one Gram rows are retained explicitly. The initial
formula also contains the 14 proved absent-column units.

The complete registry contains all 178,533 retained coordinate-cover
clauses. Each record stores a two-byte target index and a 152-byte
little-endian cover bitmap. A record `(a, S)` means

\[
\neg x_a\;\lor\;\bigvee_{b\in S}x_b.
\]

The exact original ledger proves the coordinate-difference implication,
the weakening of positive demands to one, and every same-target
subsumption. Its canonical clause-body hash is checked before the packed
registry is accepted. The packed registry is 27,494,082 bytes before
compression and 3,285,546 bytes after deterministic gzip compression.
The initial native prefix is 108,494 bytes before compression.

The helper reconstructs the prefix from the complete exact row inventory.
Preparation also compares every original variable and the first 2,271
constraints with the frozen full native model. Cold replay independently
reconstructs the registry from the complete cover ledger and reconstructs
the prefix. It performs no production query.

## Candidate loop

The separate driver prepares one owned child process. The limits are at
most eight native calls, ten seconds per call, one worker, a requested
120-second child budget, and a hard 180-second parent wall. The parent
wall includes imports, reconstruction, solving and inspection. Search
progress logging is enabled. RSS is recorded; it is not an operating
system memory limit.

Each call uses a fresh solver without an objective, hint, assumptions or
graph symmetry constraints. Every feasible response is saved as all
1,214 Boolean values. The driver checks the initial mathematical rows
and all currently encoded clauses, then evaluates every registry record.

If a candidate violates registered covers, the driver proposes every
newly violated clause as one batch. It checks the resulting totals of
25,000 encoded covers and two million literal occurrences before adding
any clause. The totals include the 14 initial units. A rejected batch
adds nothing and ends the run with an unresolved resource status. An
accepted batch adds only proved necessary clauses. There are no
visitation blocks.

The driver records both sorted encoded membership and chronological
clause insertion order. They are different objects after multiple
batches. It reconstructs a standard protobuf in chronological order and
compares its bytes with the native solver model before and after each
call. No auxiliary variables are added.

A candidate is accepted only if every cover holds and the frozen full
inspector passes. This includes all original Gram entries, distinct
original signatures, triple packing, derived attachment counts, all
30 Gram conflicts, the 60 uncapped weighted inequalities and the complete
coordinate-cover family. The accepted object would still be only a
partial incidence design.

UNKNOWN stops the loop immediately. INFEASIBLE is recorded as a native
solver outcome without a checked mathematical exclusion. Any finite
prefix remains a necessary relaxation of the complete cover formula.

## Controls and replay

The helper controls evaluate a packed test registry on all 16 assignments,
check two atomic resource refusals, and solve a tiny known feasible native
model. The separate driver controls compare three native and standard
protobuf prefixes, with a chronological insertion order different from
sorted membership. They also check all five solver-status decisions and
response text parsing. The driver controls perform no solver call.

Cold terminal replay uses no solver. For a completed child it reconstructs
each recorded prefix, checks its exact bytes and clause order, parses the
saved response, and recomputes every candidate and batch decision. A
hard timeout is bound to the persisted UNKNOWN record and reaped child;
an unfinished child transcript does not become an accepted result.

Preparation and production are separate commands. The preparation
manifest records zero production queries. A future terminal package must
record the actual outcome separately.

## Reproduction

The frozen helper replay is:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_lazy_native.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lazy-native-model.json \
  --output /tmp/case4-lazy-native-replay.json
```

The prepared driver is
`experiments/workspace/complement_rook_35core_case0004_lazy_native_loop.py`.
Its `run` and `replay` commands require the frozen
`complement-rook-35core-case0004-lazy-native-loop-preparation.json`.
The package manifest binds the complete paths, hashes, controls and cold
replay artifacts. No earlier case4 source or result is modified.
