# First complete component-pair incidence query

The single bounded query ended **UNKNOWN**. It produced no incidence
point, no UNSAT proof, and no exclusion. The complete component-zero
pair with identity fiber alignment remains unresolved.

This query used all 39,168 compatible columns and left both component
incidence designs free. It did not repeat the earlier 792-variable
fixed-design restriction. Its conditional scope remains two copies
of component zero in a globally prism-free, \(x_{521}=0\), split
eighteen-plus-eighteen triangle shell. It does not cover every possible
component pair or the connected thirty-six-vertex shell.

## Formula and verification before the run

The formula has 1,478,076 variables, 3,173,640 clauses, and 7,370,472
literal occurrences. The built DIMACS file is 60,721,371 bytes. Its
SHA256 is

`31a59090b935889b97515d20f5d03cdb02f5fc9b33a321ea30ded8b20c16b4b8`.

The reduction, support census, and encoding counts are recorded in the
[preparation note](root_prism_free_f0_pair_gram_model.md). The
[build note](root_prism_free_f0_pair_gram_build.md) records the streaming
assembler, complete primary inspector, positive controls, and cold
rebuild that reproduced the complete hash.

The coordinator separately read the preparation and builder, checked
their mathematical scope and necessary constraints, hashed the actual
DIMACS file, and checked the model and cold-replay bindings. These
reviews are saved as `f0-pair-gram-model-coordinator-review.json` and
`f0-pair-gram-build-coordinator-review.json` in the root-prism-free logs.

## Single bounded result

| Item | Observed value |
|---|---:|
| Fresh solver | Glucose4, proof enabled |
| Assumptions | None |
| Query budget, including bootstrap | 180 seconds |
| Complete streamed bootstrap | 10.361147 seconds |
| Interrupt callback | 180.002828 seconds |
| Solver returned | 181.332038 seconds |
| Cooperative overrun | 1.332038 seconds |
| Total wrapper time, including release and result saving | 181.917247 seconds |
| Restarts | 430 |
| Conflicts | 124,029 |
| Decisions | 834,495 |
| Propagations | 942,577,968 |
| Peak process RSS | 557,360 KiB |
| Terminal status | UNKNOWN |

The runner hashed the exact clause bytes as it inserted all 3,173,640
clauses into the fresh solver. Bootstrap did not exhaust the budget.
The timer requested interruption at the specified deadline; the
recorded cooperative overrun is retained rather than rounded away.

The wrapper was prepared to allow a direct DRAT check and a separate
cold complete-formula/retained-input/proof replay, each with a hard
120-second limit. Neither proof stage ran because the query did not
return UNSAT. Its SAT branch would use the complete primary inspector
and record any additional visible prism or \(F\) defect. That branch
also did not run.

No second query, continuation, or other component-pair test followed.

## Artifacts

- Runner:
  [root_prism_free_f0_pair_gram_solve.py](../experiments/workspace/root_prism_free_f0_pair_gram_solve.py).
- Result:
  [f0-pair-gram-run01/result.json](../experiments/logs/root-prism-free/f0-pair-gram-run01/result.json).
- Terminal log:
  [f0-pair-gram-run01.log](../experiments/logs/root-prism-free/f0-pair-gram-run01.log).

The result SHA256 is
`805bc0eff024c9d80acf9107843b79066ee05da85fc26e26b52cc12d3167c430`.
The runner SHA256 is
`5e7e3f39eb0a1e79892fdb7db5f356e723e749fc72280134b8de728d90dcf6f1`.

## An equivalent encoding option, not a second run

The full formula was left unchanged. A separate row-sum observation
can reduce a future encoding without restricting its primary points.
For each first-component core vertex, the local diagonal quota gives
ten exterior neighbors. Each paired second-component triple has size
three, so the actual cross-row sum is thirty. The target cross row
also sums thirty. Therefore the 324 cross upper bounds already force
all cross equalities.

Removing only the redundant cross lower-bound counters would give
935,196 variables and 2,358,780 clauses with the same sequential
encoding convention. The preparation did not build or solve this
variant. Smaller size alone does not imply faster search: retaining
redundant lower bounds may improve propagation.
