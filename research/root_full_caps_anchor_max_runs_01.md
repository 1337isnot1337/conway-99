# First maximum-anchor zero-count batch

All four tested maximum-anchor cases returned `UNKNOWN`. No graph, UNSAT
return, or excluded case resulted. The new maximum-anchor cases 0 through
6 were not run.

These are cases of the new union-preserving convention in
`root_full_caps_anchor_max.md`. They are not the entire old rooted cases
with the same indices. The original eleven-case run and the separate
two-case lex pilot remain unchanged; their outcomes are in
`root_full_caps_runs_01.md`.

## Formula and scope

The builder retains every clause of the complete rooted case, appends
its audited matching-stabilizer lex overlay, and then appends 84 negative
units. These units set precisely the cell-side variables to zero. They
are the necessary maximum-anchor count bounds for partitions without
one-parts. The 42 cell diagonals remain variables.

The builder checks that every selected stabilizer generator preserves the
set of 84 negative units. It binds the frozen base manifest, both earlier
terminal batches, the maximum-anchor certificate, the lex analysis, and
all relevant sources. No chosen incidence witness, graph automorphism,
grid existence, or new graph equation is imposed.

| New case | Partition | Variables | Clauses | Result | Actual seconds | Conflicts | Decisions |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| 7 | 2+2+2 | 982,934 | 1,976,516 | UNKNOWN | 60.276 | 136,878 | 447,088 |
| 8 | 2+4 | 972,476 | 1,945,138 | UNKNOWN | 60.404 | 125,344 | 352,829 |
| 9 | 3+3 | 976,525 | 1,957,286 | UNKNOWN | 63.974 | 155,933 | 454,795 |
| 10 | 6 | 967,338 | 1,929,722 | UNKNOWN | 60.981 | 104,867 | 330,095 |

The runs were sequential, with Glucose4 and proof production enabled.
Each requested budget was 60 seconds, including parsing and solver
initialization. The recorded time for case 9 includes delayed
interruption; it was not silently replaced by the requested limit.
The coordinator measured 246.918 seconds in total and exited normally.

The exact CNF hashes are:

- Case 7: `d3158630bd82c517dd8f76175a0dd34438d20c104497b874c8fc576c754ed073`.
- Case 8: `7258c064da41b85d31d728b8aeaebe84f631910d78043827e22c70ef42f78c3c`.
- Case 9: `f62b5928324f75adbcefa49935824d95ddf6ed8abe9d923d1f4ed407e5d3bbf4`.
- Case 10: `02ba0632ff5922893bc71270f6ed3b9b91d5551d0f492813291c88c20f5f726b`.

Case 10's base-plus-lex prefix reproduces the earlier lex pilot's exact
CNF hash before the 84 negative units are appended. The other three
prefixes have the exact sizes predicted by the same frozen lex analysis.

## Files and verification paths

Sources:

- `experiments/workspace/root_full_caps_anchor_max_solve.py`
- `experiments/workspace/root_full_caps_anchor_max_certificate.py`

Records under `experiments/logs/root-full-caps-anchor-max/`:

- `build-summary.json`
- `case-07-model.json` through `case-10-model.json`
- The four corresponding `case-XX-build.log` files
- `batch-run.log`
- `run-01/batch.json`
- The four `run-01/case-XX-result.json` and `run-01/case-XX.log` pairs
- `run-01-summary.json`

The summary verifies all result/model hashes and the consistency of
terminal status, case scope, times, statistics, and CNF bindings.

A SAT return would trigger exact verification of all 99 vertices and
every pair equation. An UNSAT return would trigger direct DRAT checking
and retention of a proof core. The separate certificate wrapper rebuilds
the base, lex overlay, and maximum-anchor units, checks their exact
hashes and retained-clause inclusion, then checks the trimmed proof.
Neither path was triggered here. No proof artifact is claimed for the
four `UNKNOWN` outcomes.
