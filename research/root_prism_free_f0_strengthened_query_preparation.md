# Strengthened F0 query preparation

Checkpoint 85 authorizes one zero-solve native preflight. The production optimizer query is not authorized by this checkpoint. The accepted model remains the exact checkpoint 84 model: 68,934 variables, 257,594 rows, raw SHA256 `4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2`.

## Why this query is different

The [baseline profile](../experiments/logs/root-prism-free/f0-boolean-query-baseline-profile-independent-review01.json) checks the previous complete query log. Search started at 36.41 seconds and occupied most of the allowance. That run was not stopped in presolve. It returned UNKNOWN without a vector.

The new query uses the accepted 89,544-row append. It retains presolve, one worker, seed zero, probing zero and linearization zero. It explicitly disables native symmetry processing, which previously used the default level two. The solver clock changes from 180 to 175 seconds, leaving five seconds for return overhead inside a separately measured 180-second native allowance. This is not a pure row-only comparison and is not a parameter sweep.

## Frozen execution contract

The [runner](../experiments/workspace/root_prism_free_f0_strengthened_query.py) and [configuration](../experiments/logs/root-prism-free/f0-strengthened-boolean-query-configuration01.json) bind the actual accepted native model and all preparation, owner, cold and root receipts. A complete independent [source review](../experiments/logs/root-prism-free/f0-strengthened-query-independent-source-review01.json) reads the runner, configuration, reused transport and process-group supervisor, and preflight workflow. It finds no blocker.

The [preflight workflow](../.github/workflows/conway99-strengthened-query-preflight.yml) checks fifteen exact dependencies in a seventeen-file sparse checkout, compiles the pinned Python, installs the pinned runtime, and invokes the prepare mode once. The worker has 60 seconds inside a 75-second process-group owner. It checks exact parameter transport, signed/empty/large-integer vector controls, native response transport, terminal classification, full native validation and byte-for-byte model export. It never constructs CpSolver or calls solve.

The [root gate](../experiments/logs/root-prism-free/f0-strengthened-query-preflight-root-gate01.json) and [request](../experiments/logs/root-prism-free/f0-strengthened-query-preflight-request01.json) permit that preflight only. First-attempt and expected-parent guards prevent an unchanged retry. Exact output bytes must be retained, including the control integer `18014398509481987`, which cannot be safely round-tripped through a binary64 JSON number.

A later production gate must bind the actual successful preflight report and owner. The production runner has a 300-second process-group owner and requires at least 180 seconds of native allowance plus 60 seconds of finalization reserve before its only solve call. It preserves exact native response text and every native integer vector before parsing. The separately saved protobuf wire is explicitly identified as reconstructed from that text.

Every returned vector is checked against all domains and all 257,594 rows with Python integer arithmetic. The [independent terminal checker](../experiments/workspace/root_prism_free_f0_strengthened_query_replay.py) uses separate indexed arithmetic and protobuf only. It does not import the query, transport helper or native solver module. The [production CI driver](../experiments/workspace/root_prism_free_f0_strengthened_query_ci.py) invokes one query and then separately owned cold controls and full replay. Its [root source review](../experiments/logs/root-prism-free/f0-strengthened-query-ci-root-source-review01.json) finds no blocker. These sources remain unrun at this publication; the terminal checker's separate peer review and actual preflight acceptance are still required before production.

## Separate triangle-support diagnostic

The [bounded support ledger](../experiments/logs/root-prism-free/f0-spectral-triangle-support-ledger01.json) checks the 132 accepted edges that require an exterior triangle when present. Forty-eight were already zero. Each of the remaining 84 retains at least one support after accepted triangle covers and initial zeros are applied. One pass reaches a fixed point with zero new edge zeros. The complete 429,105-byte report and serialization finish in 6.743 seconds, within the declared 30-second and 16 MiB bounds.

Root verifies the exact report/finalization bytes, the entire saved target partition and every saved survival disposition. The source already has a complete independent method review. This is a source-reviewed diagnostic, not a separate full-domain mathematical replay. No new row is added. Reusing the complete support tables in a future model will require separate literal reconstruction. A surviving support does not imply feasibility.

## Scope

A returned vector can establish only feasibility of the exact Boolean exterior relaxation. General exterior pair caps and a compatible second shell component remain unchecked by this model. Native INFEASIBLE is an unproved diagnostic without an independently checked proof. No graph, whole-component exclusion or unrestricted solution follows from this preparation.
