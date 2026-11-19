# Case4 symmetric exterior LP: bounded unresolved query

## Outcome

The one authorized query reached the HiGHS time limit. It produced neither an
optimal numerical point nor an infeasibility certificate. Indexed 35-core case4
remains unresolved.

The frozen driver made one LP call with one thread and a requested 60-second
solver limit. Initialization took 1.316 seconds. The solver call took 60.376
seconds, and the complete execution took 61.693 seconds. Peak process RSS was
1,158,320 KiB. The reported solver status is `HighsModelStatus.kTimeLimit`.
The source did not make a second query, call a SAT solver, or promote a numerical
conclusion to an exact one.

## Model and scope

The model keeps all 1,214 attachment-column selectors and one independent real
variable for each of the 275,578 eligible unordered exterior edges. A single
edge variable appears in both endpoint row systems. This enforces agreement
between their mixed and degree equations.

The model contains 276,792 variables, 590,165 rows, and 4,121,379 nonzero integer
coefficients. It preserves the original Gram equalities, signature and triple
capacities, selector bounds, 30 checked binary Gram conflicts, and all 60 exact
exterior-row inequalities from the earlier bounded separation pass. It also
contains both endpoint activation bounds for every exterior edge. Exterior
common-neighbor cap constraints are not part of this LP.

Each hypothetical graph completion supplies a feasible point to this model.
The converse does not hold. An exact feasible real point would be a relaxation
witness, not a graph completion. This run did not establish exact real
feasibility or exact infeasibility.

The integer row stream has SHA-256
`233c802009571ad234596e4eb3bd78f3cda55dda6808102d314fa487b8fa049a`.
The frozen query source has SHA-256
`8baeb16c2a280101b94309ccec4900b8be8fe1a1909bac585f92bee114d28d09`,
and the query model has SHA-256
`4d9d765c41cd93ff86c7b00a9149e5c2964b38198e584b62cb4f9cfdd8015e98`.

## Exact replay

The cold replay passed. It reconstructs the full original row stream and integer CSC
matrix without using the temporary matrix cache. It checks every frozen array
hash and the complete row-stream hash. This verifies which exact relaxation
was submitted; it does not turn the time-limit result into a mathematical
exclusion.

The terminal artifacts are under
`experiments/logs/grids-and-triangles/`:

* `complement-rook-35core-case0004-symmetric-lp-query-run01/result.json`
  records the single query and its unresolved status.
* `complement-rook-35core-case0004-symmetric-lp-query-run01.log` is the query log.
* `complement-rook-35core-case0004-symmetric-lp-query-run01/cold-replay.json`
  and its adjacent log record the optimizer-free integer matrix replay.
* `complement-rook-35core-case0004-symmetric-lp-query-terminal-artifacts.json`
  binds the preparation, gate, query outcome, and replay.

From the repository root, replay to a new output path:

```sh
.venv/bin/python experiments/workspace/complement_rook_35core_case0004_symmetric_lp_query.py replay \
  --model experiments/logs/grids-and-triangles/complement-rook-35core-case0004-symmetric-lp-query-model.json \
  --result experiments/logs/grids-and-triangles/complement-rook-35core-case0004-symmetric-lp-query-run01/result.json \
  --output /tmp/conway99-case4-symmetric-lp-run01-replay.json \
  --check-seconds 60
```

No further query is included in this checkpoint.
