# Fixed F0 local conflict inventory and complete cold replay

The single production inventory covered all 42 representative centers and
all 480 literal centers through the verified actual-core transports. It
finished in 7.331973371 seconds. The separate cold replay reached its
ten-second deadline after completing 20 centers. Each of those 20 saved
records agrees exactly with the production record. The replay report took
11.353739616 seconds including preservation of its partial output.

A separately reviewed suffix wrapper then rebuilt only the remaining
22 centers in 4.385070098 seconds. It checked the complete reconstructed
record exactly. Together the immutable 20-center prefix and fresh suffix
give a complete cold replay without recomputing a completed center.
The original timeout report remains unchanged. No run loaded a fractional
point or called an optimizer.

## Conflict counts

The following counts sum over all 480 centers. Each center has its own
neighbor variables, so these are conflict incidences rather than counts
of distinct quotient inequalities.

| Layer | Pair conflicts | Triangles in the conflict graph |
|---|---:|---:|
| Mixed-quota and lifted-Gram cliques | 4,423,098 | 71,397,750 |
| After published core-pair cliques | 4,559,838 | 72,131,382 |
| After published path-prism rows | 4,617,834 | 72,942,966 |
| After semantic motif-selector conflicts | 4,627,338 | 72,996,522 |

Of the 61,476 retained literal path conflicts, the mixed and lifted rows
cover 2,112. Adding the published core-pair cliques raises this to 3,480.
The remaining 57,996 path conflicts add edges to the local conflict graphs.

The 90 motif-selector conflicts yield 14,832 local center incidences.
The mixed and lifted rows cover 4,572; core-pair cliques increase that count
to 5,328. The path rows cover no further motif-conflict incidences.
Thus 9,504 motif conflicts remain outside these recorded homogeneous
inequalities. They remain valid semantic conflicts. This is not a claim
that all consequences of the complete linear model were examined.

Across the 42 representative graphs, adding the path layer creates
72,045 triangles containing a new edge. Adding the motif layer creates
another 4,826 such triangles. These counts suggest a bounded triangle-clique
family to examine after a separate gate. They do not establish linear
independence of the corresponding inequalities. No triangle witnesses,
maximal cliques, induced odd cycles, or local eight-neighbor selections
were enumerated.

The full listed conflict graphs have degeneracy between 46 and 64.
There are 11,658 separate neighbor variables across the representatives,
with at most 339 at one center. All eighteen mixed demands and the implied
local exterior degree eight are retained.

## Frozen records

The source is
`experiments/workspace/root_prism_free_f0_local_conflict_inventory.py`,
SHA256
`6e7a638c0c9045f82aceb37d4eceb749ad8911be4b65abeb52dd7be829f18036`.

The complete production record is
`experiments/logs/root-prism-free/f0-local-conflict-inventory01.json.gz`,
SHA256
`cbfdad339ab84cb7eeb6b221e10be3c4c1db4fb70932de3a28e62ee4642cb7e0`.
Its uncompressed canonical record has SHA256
`8db1e5eaa05b4573dff5c582425651973c43238059a77c834b2bbd3bac1dbbe2`.

The incomplete replay report is
`experiments/logs/root-prism-free/f0-local-conflict-inventory01-replay.json`,
SHA256
`4717dc11e6f40007d58befc3ae968ceaaadb805c0548f797817846b3a0843be9`.

The suffix replay centers, in the frozen order, were
45, 46, 47, 50, 51, 52, 53, 57, 58, 63, 336, 338, 339, 342, 343, 344,
345, 346, 347, 354, 355 and 356. The coordinator separately reviewed and
authorized the one ten-second suffix replay.

Its source is
`experiments/workspace/root_prism_free_f0_local_conflict_suffix_replay.py`,
SHA256
`8a11e514ae7c8b56c001411ea7df8ee82a4e216a641584227ac8e13185829687`.
The complete replay report is
`experiments/logs/root-prism-free/f0-local-conflict-inventory01-suffix-replay.json`,
SHA256
`ae85e2c9cbe19b72ad23231c6ee28ac135098eb078088780d4bd0988bd28cb5e`.

The necessary local constraints do not characterize an SRG completion.
These results do not settle graph existence or the fixed F0 branch.
