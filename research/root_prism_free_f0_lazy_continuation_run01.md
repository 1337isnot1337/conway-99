# Terminal UNKNOWN from the first lazy continuation

The single authorized continuation stopped after 55.679 seconds. A
shared-edge LP reported numerical infeasibility, but the frozen exact
recovery routine did not certify an infeasibility ray. The result is
UNKNOWN, and component zero remains unresolved.

The result does not imply that the final incidence is feasible or
infeasible. No clause or selector inequality was added from the
uncertified numerical answer. Any later recovery must be a separate
artifact; this run and its UNKNOWN status remain unchanged.

## Exact progress before the stop

All 480 first-incidence selectors remained free. The scope is still
component zero in the globally prism-free, F-free split $18+18$ shell.
No second component, second incidence, or fiber alignment was fixed.

| Result | Count |
|---|---:|
| SAT candidates checked against the actual prefix | 17 |
| Registry-only refinements without a row LP | 3 |
| Complete sixty-row passes | 14 |
| New exact individual-row obstructions | 15 |
| Exact rational individual-row boxes | 825 |
| New exact shared-edge rays | 5 |
| Exact shared-edge feasibility witnesses | 0 |
| New individual cuts, including transports | 180 |
| New signed cuts, including transports | 60 |
| Final individual-cut registry | 1,188 |
| Final signed-cut registry | 168 |
| Final total registered inequalities | 1,356 |

The fourteen passes include the terminal pass, which has sixty exact
individual-row boxes. The terminal selection satisfies all 1,356
registered inequalities. Its subsequent shared-edge outcome is the
uncertified numerical infeasibility that stopped the run.

Each of the five earlier exact shared rays was replayed with integer
arithmetic, lifted to the complete 480-signature domain, and transported
under all twelve verified core relabelings. The finite clause prefixes
contain only proved implications.

## Formula and limits

The formula grew from 58,974 to 59,442 clauses, with 28,308 variables
throughout. Its 2,448 explanation clauses contain no new auxiliary
variables. The final formula has 363,516 literal occurrences and
1,820,506 DIMACS bytes.

The final CNF SHA256 is
`24cf3a35390b72ba17d18e33e3c62eddd7cf0c00970de9227d94320ceefe7031`.

The run stopped because of the exactness gate, before its time,
row-pass, SAT-call or formula-size limits. Peak process RSS was
173,136 KiB. There was no incremental UNSAT answer, so no fresh SAT
proof query or DRAT check was invoked.

## Replay and preservation

The cold replay passed. It reconstructed the inherited mathematical
registry and original incidence base, checked all seventeen candidate
prefixes, and reproduced all later cuts and clause explanations. It
replayed every retained integer obstruction, rational row box and
certified shared ray, and matched the final CNF hash.

The replay also checks the terminal numerical record without converting
it into an exact result. The saved candidate, all sixty row boxes,
numerical shared-edge record and actual formula prefix remain bound by
their original hashes.

All 62 transcript JSON or gzipped-JSON records are preserved in a
deterministic lossless archive. Their original size is 6,646,460 bytes;
the archive is 1,270,371 bytes. The rebuildable final CNF is omitted.

The bundle source checks every member hash and permits restoration only
under the fixed transcript prefix. It writes missing files, preserves
equal existing files, and refuses unequal existing files. The narrow
restore controls passed. Its optional cold-replay mode restores the
records and invokes the frozen mathematical/CNF replay.

| Artifact | SHA256 prefix |
|---|---|
| Terminal result | `3bb8993020226640` |
| Transcript archive | `0f487420999a7028` |
| Transcript manifest | `66cb41a2f1d4b058` |

The exact reason the numerical ray failed recovery is a separate
arithmetic investigation. It requires no repeat of this LP query.
