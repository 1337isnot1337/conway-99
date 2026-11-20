# No-LP tactic on the frozen character-count target

## Purpose and scope

The first lightweight run returned UNKNOWN without an integer candidate. Its native log records 112,695 LP iterations and 4,531 branches. This preparation tests a different search tactic on the same target: explicitly set `linearization_level=0`. These counters motivate the experiment; they do not establish a speed advantage or identify a single cause of the previous outcome.

The official [OR-Tools parameter source](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto) labels `no_lp` with `linearization_level:0`. The installed 9.15.6755 parameter descriptor has field number 90 and default value 1. Preparation verifies that the native parameter object prints an explicit zero and that the generated protobuf preserves it through text and binary round trips. It checks all seven explicit fields at time limits 0.25, 10, and 172 seconds. No model or solver is constructed by these parameter controls.

## Unchanged mathematical target

Both raw protobuf hashes remain unchanged: target `a738d318b6b8de471ee7383f1e6ea11949eed8f8ccf4892814fa2eac268ed153` and initial subset `9d1e6a031d5c2c83a47982477d51b34fba42edf1bbcdae1bccfa9906745badfe`. All 18,444 domains, 34,398 target constraints, 34,281 initial constraints, and 117 external rows are preserved. No endpoint-star constraint or other later family is added.

The search retains one worker, seed zero, probing level zero, a 180-second owned budget, at most twelve native calls, and at most sixteen exact violated pool rows appended after each returned integer point. Every later call requires a larger certified prefix. The separate terminal replay retains its 60-second owned limit. No unchanged retry is scheduled.

## Source controls

The substitution ledger checks the complete new query and replay text against their frozen parents. The accompanying AST audit finds thirteen unchanged query functions, including `worker`, `run`, `load_target`, `provisional_record`, `evaluate_proto`, and `pool_scan`. The search parameter function differs by the one explicit zero assignment. Configuration, preparation labels, and controls record that change and its provenance. The replay adds an assertion that the saved parameter field is explicitly present and zero.

Inside the inherited-helper control, the added assignment is removed from a temporary AST before comparison with the old parameter helper. Thus the parameter helper is identical after the declared delta, rather than literally unchanged. The separate full-source audit reports this distinction explicitly through its changed-function list.

The optimizer-free cold preflight checks the actual target and initial archives, all domains, and exact initial-subset and pool coverage. It passed within its owned limit. The previous sources, preparation, result, and cold replay remain unchanged.

## Acceptance

A returned native integer vector is saved before costly checking. It remains provisional even if it passes every target constraint. Count feasibility requires the separate exact restored-parent arithmetic receipt. That receipt must bind this query's actual preparation hash, `123c940a34b590c944316a2fd606e5febcf1cedbdea3ec0f828d41b115068f37`; the historical first-query receipt preparation cannot be reused with an incorrect provenance field. A count witness would still require the separately gated literal-incidence lift, and would not itself construct the graph.

This package is preparation only. A production query requires the coordinator's separate source and preflight gate.
