# One direct540 query: frozen preparation

The query source is
[root_prism_free_f0_direct_literal_query.py](../experiments/workspace/root_prism_free_f0_direct_literal_query.py),
SHA-256 d53a51dadb01e267baaca8cfcc51a2aab8ff654b74bae605a482d8d110853db6.
It contains the one-call driver, optimizer-free preparation, and a separate
owned cold-replay mode. No production query had run when this preparation
note was frozen.

## Mathematical target and authority

The target is the complete direct literal model: 540 variables, 4,681 linear
constraints and 454,152 coefficient terms. All 480 selectors are free. The
other 60 variables are the exact auxiliaries for 12 large cuts. All 4,416
certified original literal cuts are active from the start.

The accepted cold report
`f0-direct-literal-model01-cold/report.json`, SHA-256
2c67cbf7eaae08cad0bfd6d47c32de0606b91486a2731f452806de0c3add8254,
and its accepted owner, SHA-256
2da83ed1808634d2bf02e7ef44465ad38c4f198fde9202d719d4b2596c22e863,
are the artifact-validation authority. They reconstructed every plan and
model byte. The original preparation owner remains UNKNOWN; the query loader
explicitly checks that preserved status rather than relabeling it.

The exact model has raw SHA-256
de9e9f0f9deb2e7dc1c41866c959c5264de2b7fef7d11d3c9c0d8772aa0bbe3e.
It is fully published as `model.pb.gz`, SHA-256
34724b46df693d930de465d2d3b7473ae8742a322aa7006e21e0aa780f1c1bd6.
The exact plan archive has SHA-256
bd921d7d8f16c64bd866e0ec319b1cc3db37450cf5a6c884a37a9f40044c48d7.

No count or Fourier variables, edge variables, external row pool, objective,
hint, symmetry fixing, or visitation clause is added.

## Bounded search

The future production phase permits exactly one native solve call. Its owner
has 300 seconds, including input loading, construction, search, saving and
exact inspection. Native solving has a separate maximum of 180 wall seconds,
clipped to the remaining owner allowance with an eight-second finalization
reserve.

The pinned OR-Tools version is 9.15.6755. The source keeps one worker, seed
zero, probing level zero and linearization level zero. These parameter and
native-budget helpers, including installed serialization controls, are
AST-identical to the reviewed full-Fourier query. This retains the previous
search tactic while changing the mathematical formulation. It does not
claim a performance improvement.

The worker constructs the native model through public constructors,
validates it, exports it and checks the full exported-file hash before the
solve. There is no automatic retry. Native INFEASIBLE is saved as
`UNPROVED_NATIVE_INFEASIBLE`; it is not a mathematical exclusion.

## Candidate handling

If native solving returns a vector, the complete 540-integer array is saved
atomically before the direct arithmetic check. The response, parameters,
actual model and wall-time records remain separate artifacts.

A timely candidate must satisfy all variable domains and all 4,681 native
rows. The exact inspector independently evaluates all 172 original
Gram/population equations, 90 motif conflicts and 4,416 original cuts with
Python integers. It also checks all 4,410 zero-pair consequences and the
derived incidence-profile counts. A passing result is
`EXACT_DIRECT_LITERAL_INCIDENCE`.

That status establishes a selection satisfying these first-incidence
conditions. It does not establish an exterior graph, matching compatibility,
or a complete Conway99 graph. The root's separately prepared matching and
fixed-exterior oracles remain subsequent steps. This query does not invoke
them or add new clauses from them.

A native or owner deadline never turns an unchecked saved vector into an
accepted query result. The separate cold phase can inspect a saved vector
exactly while preserving the original owner outcome.

## Preflight and replay

The optimizer-free preparation/preflight passed. Its report is
`f0-direct-literal-query-preparation01/report.json`, SHA-256
2f41de87c0036ac66aa48cb6921ee3ce04d0fa3a01b998b46ec4367c5cac11d1.
The owner completed and reaped its child in 3.161 seconds with zero overrun.
No CpSolver or solve call was made.

The preflight bound the accepted model cold, compared every native variable
and row with the exact plan, checked the installed parameter text/wire
roundtrips, and repeated public construction, validation and whole-export
byte equality. The source-only AST control report is
`f0-direct-literal-query-source-controls01.json`, SHA-256
09c0a4b26571541245450de4333c2a6bf413bbe4d5c673510b4fe1490482e01c.

After the future query terminates, a separate 60-second owner will replay its
saved parameters, actual-model hash, response and timing records. Any
candidate is checked again against the complete direct arithmetic target.
No optimizer is called during replay. Incomplete or failed records are
preserved; an unsuccessful replay cannot promote a numerical result.

The preflight's raw `actual-model.pb` stays local. Publication records its
exact restoration from the already published model archive instead of
duplicating the same raw protobuf.
