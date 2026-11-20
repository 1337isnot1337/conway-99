# Combined exterior query: unresolved after one bounded run

[Run 44641648177](https://github.com/1337isnot1337/conway-99/actions/runs/44641648177), executing checkpoint 91, returned **UNKNOWN with no candidate vector**. The native call took 600.251 seconds, below its 610-second allowance. The query owner took 606.894 seconds, below its 720-second bound. The independent terminal checker passed. This is an unresolved search result, not a graph, component exclusion, or proof of infeasibility.

The [root terminal acceptance](../experiments/logs/root-prism-free/f0-combined-extensions-query-root-acceptance01.json) binds the complete result, all owners, original response text, reconstructed response wire, empty native vector snapshot, source, configuration and actual accepted preflight. The [terminal map](../experiments/logs/root-prism-free/f0-combined-extensions-query-terminal-git-blobs01.json) preserves all 33 original small files, totaling 95,005 bytes. The duplicate 39,306,083-byte raw model is losslessly recoverable from the already committed accepted archive; its [restoration record](../experiments/logs/root-prism-free/f0-combined-extensions-query-model-restoration01.json) binds both the actual query transport and independent raw-byte check.

## Exact model and execution

The queried model has 80,730 variables, 297,470 linear constraints and 3,310,380 coefficient occurrences. Its raw SHA-256 is `2961c95ce21c39f8ea8bda29ed3ac98c5075b921dedc96f71035f1b90f77ddb6`. Its complete native preparation and independent row replay were accepted at checkpoint 90. The query does not modify these bytes.

The configuration sets four search workers, seed zero, presolve enabled, probing level zero, linearization level zero and symmetry level zero. The solver clock is 600 seconds; the query owner reserves 60 seconds for finalization. There is one native call and no automatic retry.

| Phase | Actual seconds | Bound seconds |
| --- | ---: | ---: |
| Native call | 600.251 | 610 |
| Query owner | 606.894 | 720 |
| Independent controls owner | 0.115 | 15 |
| Independent terminal owner | 0.717 | 135 |
| Complete CI driver | 607.794 | 900 |

Every child was reaped and every owned process group stopped. All overrun fields are zero. The exact integer controls include the literal token 18014398509481987, which is preserved in original bytes; parsed JavaScript numbers were not used to reserialize the controls.

The independent checker compares original native text with the separately reconstructed protobuf response and the saved primary/additional integer arrays. All are consistent with UNKNOWN and zero vectors. It also checks the complete actual runtime and parameter artifacts and the actual transported model. Root verifies every original output hash and 77 nested artifact references. The response wire is explicitly labeled as reconstructed from native text; it is not an original native binary export.

## What the search log says

Search began at 20.70 seconds. The final response records 249,617 conflicts, 653,311 branches, 1,377,059,285 Boolean propagations and 505,978,694 integer propagations. Peak query-process memory was 2,191,972 KiB. These counters describe this run; they do not certify coverage of the whole finite search space.

The [complete search log](../experiments/logs/root-prism-free/f0-combined-extensions-query-run01/child.stdout.log) shows three full-problem subsolvers: `default_lp`, `max_lp` and `no_lp`. The top-level setting `linearization_level: 0` did not remove the portfolio's LP variants. Their reported LP iteration counts are 300,959 and 12,899. The final response's `lp_iterations: 0` therefore must not be read as saying no worker used LP. This is concrete evidence to inspect an explicit worker portfolio before the next differently formulated query; no replacement parameter set is frozen here.

## Earlier accepted preflight

[Run 44640850513](https://github.com/1337isnot1337/conway-99/actions/runs/44640850513) executed checkpoint 90 once. It recovered the full accepted model, passed public native parse/validation and complete-byte comparison, and checked exact integer/response controls. Its worker and owner took 5.614 and 5.781 seconds under 60/75-second bounds. It constructed no CpSolver and made no optimizer call. All twelve original outputs are preserved through the [preflight acceptance](../experiments/logs/root-prism-free/f0-combined-extensions-query-preflight-root-acceptance01.json).

## Scope and continuation

This formulation covers the fixed component-zero exterior relaxation in the globally prism-free, F-free split18+18 branch. General original exterior pair caps and a compatible second component are not certified by this query. The other component types and the unrestricted existence question remain open. Even a future accepted vector would still need those graph conditions checked; a future native INFEASIBLE response would need a separate proof before exclusion.

The one-call gate is consumed. No unchanged retry is authorized. A new append is being prepared from independently verified recorded-triangle capacities and a separately checked target-edge total bound. Those rows were absent from this queried model.
