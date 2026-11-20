# Bounded native candidate query for case 4

The query wrapper uses the frozen native model from
`complement_rook_35core_case0004_native_cpsat.md`. It adds no constraint
and fixes no incidence assignment. Its preparation record binds the
model, complete cold replay, runtime, source files, and controls.

The installed OR-Tools helper can export a binary model but does not
offer a binary import method. The owned query child therefore rebuilds
the native model from its exact inventory and complete cover stream.
Before solving, it exports the rebuilt proto and requires the frozen
hash
`b98aa8f1b6ea6e156e5bccb19b88080e543e9514e9797627813a684ff3d7fc73`.

The solve stage has a 60-second limit and one worker. No objective,
assumption, solution hint, or graph symmetry constraint is added. A
separate parent process applies a 180-second hard wall to the child's
imports, reconstruction, solve, and exact candidate inspection. The
wrapper reuses the previously checked owned-child watchdog. On timeout,
the parent saves `UNKNOWN` before terminating and reaping its child.
It does not use a partial child response. Process RSS is recorded; it
is not an operating system memory limit.

A feasible result is accepted only after the existing exact inspector
checks the original incidence equations and every certified conflict,
weighted cut, and coordinate cover. It is then saved as a partial
64-column incidence witness. The remaining exterior graph is still
unspecified. `INFEASIBLE` and `UNKNOWN` leave case 4 unresolved because
this wrapper does not produce an independently checked infeasibility
proof.

The terminal replay repeats no production solve. It cold-rebuilds the
native model, checks all outcome and process bindings, and directly
rechecks any saved feasible incidence. Preparation and query are
separate commands. The preparation package contains no production
outcome.

The source is
`experiments/workspace/complement_rook_35core_case0004_native_cpsat_query.py`.
Its prepared source hash is
`63e4b7ce073973dd184ad94185e7475d449d72f5a6013f3d5fc8d1d1edf82601`;
the query preparation hash is
`e222ebdad0db2706fe5decdd454d1de3369f476ff3118165f6f68a0e1c003ef0`.
