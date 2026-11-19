# Strengthened F0 query preparation

Checkpoint 87 accepts the completed query as UNKNOWN with no primary or additional vector. Independent terminal replay passes. The accepted model remains the exact checkpoint 84 model: 68,934 variables, 257,594 rows, raw SHA256 `4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2`.

## Completed production query

[Run 44633211291](https://github.com/1337isnot1337/conway-99/actions/runs/44633211291) executes checkpoint 86 once. The measured native call takes 175.039379657 seconds, within the separately declared 180-second allowance. The query worker takes 181.206623257 seconds; its owner finishes in 181.417421365 seconds inside 300 seconds. The separate terminal replay takes 0.622638523 seconds before serialization and 0.716249547 owner seconds. Its controls and all owners pass. The complete driver takes 182.318110117 seconds inside 480 seconds.

The [root acceptance](../experiments/logs/root-prism-free/f0-strengthened-query-root-acceptance01.json) checks all frozen inputs and 77 output cross-references, exact native response text and reconstructed wire, the empty primary/additional vector inventories, and every required owner outcome. The original integer-control token is preserved and checked exactly. All 33 small output files are committed without re-serialization; the exported model is losslessly recoverable through the [restoration record](../experiments/logs/root-prism-free/f0-strengthened-query-model-restoration01.json).

The [actual terminal profile](../experiments/logs/root-prism-free/f0-strengthened-query-terminal-profile01.json) records search starting at 19.69 seconds and main search at 19.96 seconds. The solver reports 137,871 conflicts, 414,040 branches, 633,121,867 Boolean propagations, 226,781,327 integer propagations and zero LP iterations. Most of the native allowance was spent searching. The changes in rows, symmetry parameter, solver clock and CI execution prevent attributing the difference from the earlier baseline to any single cause.

UNKNOWN supplies no mathematical feasibility or infeasibility conclusion. No unchanged retry is authorized. Prepared short four-exterior channels, full triangle-support equations and cap-one common-neighbor forest constraints are the next formulation work. Their literal supports and complete native representation must be checked before a subsequent changed-model query.

## Completed preflight and one-call authorization

[Preflight run 44632464085](https://github.com/1337isnot1337/conway-99/actions/runs/44632464085)
executes checkpoint 85 once. The worker completes in 6.357763164 seconds and
the process owner in 6.534583334 seconds. Native transport takes 5.576695360
seconds and reproduces all 38,374,405 accepted model bytes. The owner exits
successfully, reaps the child and stops its process group with no overrun.
CpSolver construction and optimizer calls are both zero.

The [root acceptance](../experiments/logs/root-prism-free/f0-strengthened-query-preflight-root-acceptance01.json)
checks the complete actual receipt chain and original export bytes. Root also
reads and compares all ten native parameter text values directly. The large
control token is checked with exact integer arithmetic; the report is never
re-serialized through a JavaScript number. Twelve original small files are
preserved. The duplicate transported model is exactly restorable from the
already committed model archive using the
[restoration record](../experiments/logs/root-prism-free/f0-strengthened-query-preflight-model-restoration01.json).

The [terminal checker source review](../experiments/logs/root-prism-free/f0-strengthened-query-replay-independent-source-review02.json)
passes after all 503 source lines and actual inherited receipt contracts are
checked. Root reads the complete production driver and workflow. The
[workflow review](../experiments/logs/root-prism-free/f0-strengthened-query-production-workflow-root-review01.json)
checks all 27 checkout paths and 25 exact dependencies.

The [production gate](../experiments/logs/root-prism-free/f0-strengthened-query-root-gate01.json)
and [request](../experiments/logs/root-prism-free/f0-strengthened-query-ci-request01.json)
authorized exactly one query and separately owned independent terminal
replay; that authorization is now consumed. The query keeps the exact accepted model. Its clock/allowance/owner
limits are 175/180/300 seconds. Independent controls have a 15-second owner;
the complete independent replay has a 120-second phase and 135-second owner.
The CI driver acceptance bound is 480 seconds and the outer job timeout is
12 minutes. All phase files remain available if a phase fails. No retry or
second native call is authorized. The completed production outcome is recorded above.

## Why this query is different

The [baseline profile](../experiments/logs/root-prism-free/f0-boolean-query-baseline-profile-independent-review01.json) checks the previous complete query log. Search started at 36.41 seconds and occupied most of the allowance. That run was not stopped in presolve. It returned UNKNOWN without a vector.

The new query uses the accepted 89,544-row append. It retains presolve, one worker, seed zero, probing zero and linearization zero. It explicitly disables native symmetry processing, which previously used the default level two. The solver clock changes from 180 to 175 seconds, leaving five seconds for return overhead inside a separately measured 180-second native allowance. This is not a pure row-only comparison and is not a parameter sweep.

## Frozen execution contract

The [runner](../experiments/workspace/root_prism_free_f0_strengthened_query.py) and [configuration](../experiments/logs/root-prism-free/f0-strengthened-boolean-query-configuration01.json) bind the actual accepted native model and all preparation, owner, cold and root receipts. A complete independent [source review](../experiments/logs/root-prism-free/f0-strengthened-query-independent-source-review01.json) reads the runner, configuration, reused transport and process-group supervisor, and preflight workflow. It finds no blocker.

The [preflight workflow](../.github/workflows/conway99-strengthened-query-preflight.yml) checks fifteen exact dependencies in a seventeen-file sparse checkout, compiles the pinned Python, installs the pinned runtime, and invokes the prepare mode once. The worker has 60 seconds inside a 75-second process-group owner. It checks exact parameter transport, signed/empty/large-integer vector controls, native response transport, terminal classification, full native validation and byte-for-byte model export. It never constructs CpSolver or calls solve.

The checkpoint 85 [root gate](../experiments/logs/root-prism-free/f0-strengthened-query-preflight-root-gate01.json) and [request](../experiments/logs/root-prism-free/f0-strengthened-query-preflight-request01.json) permitted that preflight only. First-attempt and expected-parent guards prevent an unchanged retry. Exact output bytes must be retained, including the control integer `18014398509481987`, which cannot be safely round-tripped through a binary64 JSON number.

The separate production gate binds the actual successful preflight report and owner. The production runner has a 300-second process-group owner and requires at least 180 seconds of native allowance plus 60 seconds of finalization reserve before its only solve call. It preserves exact native response text and every native integer vector before parsing. The separately saved protobuf wire is explicitly identified as reconstructed from that text.

Every returned vector is checked against all domains and all 257,594 rows with Python integer arithmetic. The [independent terminal checker](../experiments/workspace/root_prism_free_f0_strengthened_query_replay.py) uses separate indexed arithmetic and protobuf only. It does not import the query, transport helper or native solver module. The [production CI driver](../experiments/workspace/root_prism_free_f0_strengthened_query_ci.py) invokes one query and then separately owned cold controls and full replay. Its [root source review](../experiments/logs/root-prism-free/f0-strengthened-query-ci-root-source-review01.json) finds no blocker. The prepare mode, production driver and separate terminal checker have now completed successfully. Their actual owned receipts are bound in the root acceptance above.

## Separate triangle-support diagnostic

The [bounded support ledger](../experiments/logs/root-prism-free/f0-spectral-triangle-support-ledger01.json) checks the 132 accepted edges that require an exterior triangle when present. Forty-eight were already zero. Each of the remaining 84 retains at least one support after accepted triangle covers and initial zeros are applied. One pass reaches a fixed point with zero new edge zeros. The complete 429,105-byte report and serialization finish in 6.743 seconds, within the declared 30-second and 16 MiB bounds.

Root verifies the exact report/finalization bytes, the entire saved target partition and every saved survival disposition. The source already has a complete independent method review. This is a source-reviewed diagnostic, not a separate full-domain mathematical replay. No new row is added. Reusing the complete support tables in a future model will require separate literal reconstruction. A surviving support does not imply feasibility.

## Scope

A returned vector can establish only feasibility of the exact Boolean exterior relaxation. General exterior pair caps and a compatible second shell component remain unchecked by this model. Native INFEASIBLE is an unproved diagnostic without an independently checked proof. No graph, whole-component exclusion or unrestricted solution follows from this preparation.
