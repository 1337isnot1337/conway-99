# First complete-root batch and lex pilot

All thirteen bounded solves returned `UNKNOWN`. They found no graph and
produced no UNSAT result. All eleven rooted normalization cases remain
open. The time limits do not establish exhaustion of any case.

## Original eleven-case batch

The complete model and coverage argument are in `root_full_caps.md`.
Every formula has 960,414 variables and 1,908,864 clauses. The differences
between cases are six positive units specifying the canonical matching
at the chosen near anchor.

The cases ran sequentially with Glucose4, proof production enabled, and
a requested wall budget of 180 seconds per case. The budget includes
CNF parsing and solver initialization. Measured times can slightly exceed
the request because interruption and cleanup are not instantaneous.

| Case | Matching partition | Result | Actual seconds | Conflicts | Decisions |
| --- | --- | --- | ---: | ---: | ---: |
| 0 | 1+1+1+1+1+1 | UNKNOWN | 180.330 | 384,322 | 885,927 |
| 1 | 1+1+1+1+2 | UNKNOWN | 180.675 | 416,153 | 921,274 |
| 2 | 1+1+1+3 | UNKNOWN | 180.220 | 384,517 | 882,279 |
| 3 | 1+1+2+2 | UNKNOWN | 180.227 | 144,750 | 373,872 |
| 4 | 1+1+4 | UNKNOWN | 182.588 | 312,239 | 782,998 |
| 5 | 1+2+3 | UNKNOWN | 180.252 | 391,062 | 1,024,763 |
| 6 | 1+5 | UNKNOWN | 180.300 | 486,168 | 1,087,257 |
| 7 | 2+2+2 | UNKNOWN | 180.413 | 422,219 | 992,354 |
| 8 | 2+4 | UNKNOWN | 180.357 | 360,876 | 894,981 |
| 9 | 3+3 | UNKNOWN | 181.754 | 426,759 | 952,481 |
| 10 | 6 | UNKNOWN | 180.681 | 332,588 | 791,836 |

The batch began at `2026-11-19T03:35:19.422994Z` and ended at
`2026-11-19T04:08:32.960372Z`. The coordinator measured 1,993.537 seconds,
including work between cases. The process exited normally.

Each terminal result was saved before the next case began. The batch
records bind every result to the model, exact CNF hash, and source hashes.
No incomplete candidate was reported as a graph.

## Two-case stabilizer lex pilot

The overlay and its independent audit are described in
`root_full_caps_lex.md`. It preserves each original case through coordinate
relabeling. Case 0 has stabilizer order 46,080 with eleven generators;
case 10 has order 12 with two generators.

The pilot retained every original clause and appended the audited lex
clauses. It used the same Glucose4 configuration and proof setting, with
60 seconds per case. No maximum-anchor count constraints were included.

| Case | Variables | Clauses | Result | Actual seconds | Conflicts | Decisions |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 0 | 983,647 | 1,978,574 | UNKNOWN | 60.248 | 116,258 | 525,598 |
| 10 | 967,338 | 1,929,638 | UNKNOWN | 60.425 | 159,950 | 393,423 |

The pilot began at `2026-11-19T04:08:56.597784Z` and ended at
`2026-11-19T04:10:57.954975Z`. Total elapsed time was 121.356 seconds.
The process exited normally. Both cases remain open.

The exact pilot CNF hashes are:

- Case 0: `09db5a40adb876277fe69a3fb0e037e08bda96c1c8c3cbab4290f8653d5ff625`.
- Case 10: `1b0c0d202fd349174098fbbceb4accfeff5a4eb749fc4df8b4c3a56091e90631`.

These runs do not establish that the overlay improves solving time. The
budgets differ from the first batch, and neither version reached a
terminal SAT or UNSAT result. Conflict and decision counts describe the
runs; they are not a measure of the fraction of the search space covered.

## Archived records

The original model and run are recorded in:

- `experiments/logs/root-full-caps/model.json`
- `experiments/logs/root-full-caps/run-01/batch.json`
- `experiments/logs/root-full-caps/run-01/case-XX-result.json`
- `experiments/logs/root-full-caps/run-01/case-XX.log`
- `experiments/logs/root-full-caps/batch-run.log`

The lex sources and run are recorded in:

- `experiments/workspace/root_full_caps_lex_solve.py`
- `experiments/workspace/root_full_caps_lex_certificate.py`
- `experiments/logs/root-full-caps-lex/analysis.json`
- `experiments/logs/root-full-caps-lex/case-00-model.json`
- `experiments/logs/root-full-caps-lex/case-10-model.json`
- `experiments/logs/root-full-caps-lex/run-01/batch.json`
- `experiments/logs/root-full-caps-lex/run-01/case-XX-result.json`
- `experiments/logs/root-full-caps-lex/run-01/case-XX.log`
- `experiments/logs/root-full-caps-lex/batch-run.log`

The combined summary is
`experiments/logs/root-full-caps/run-01-summary.json`. Its generation
checked all thirteen result hashes, source bindings, model/CNF bindings,
statistics, time fields, and explicit `UNKNOWN` status. This is an
integrity check of the recorded outcomes, not an UNSAT proof.

Both run helpers contain complete candidate validation and direct proof
checking paths. Neither path was triggered by these runs. The retained
proof wrapper would independently rebuild the exact base and overlay,
check retained-clause inclusion, and verify DRAT if a future run returns
UNSAT. No proof artifact is claimed for an `UNKNOWN` outcome.

The separately audited maximum-anchor convention is documented in
`root_full_caps_anchor_max.md`. It changes the eleven-case coverage
convention and was not tested by either batch above.
