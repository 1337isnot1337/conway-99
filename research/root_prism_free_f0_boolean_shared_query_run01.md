# First complete Boolean shared-edge query

The first query of the accepted 68,934-variable, 168,050-row model returned
native `UNKNOWN`, with no primary or additional assignment. Its measured
call time was 180.186770506 seconds against the 180-second allowance.
The terminal classification is therefore `UNKNOWN_NATIVE_BUDGET_OVERRUN`.
This classification and the 0.186770506-second overrun are preserved.

The owner finished in 190.987916981 seconds, within its 300-second bound.
The child exited successfully and was reaped. The native response reports
180.130460551 seconds of solver wall time. No second call or retry ran.
There is no feasibility, infeasibility, component-exclusion, or graph
construction conclusion from this attempt.

## Frozen model and search settings

The [model preparation package](root_prism_free_f0_boolean_shared_model.md)
preserves the complete selector parent, all 68,394 Boolean edge variables,
both endpoint activations, all degree and mixed equations, 1,884 proved
edge zeros, and 3,096 literal core-pair clique rows. Independent replay
accepted every appended row and the complete parent bytes before this
query was authorized.

The query imported that exact accepted model through the public native
interface. Native validation succeeded and the complete exported bytes
matched the accepted 33,451,907-byte model. Its SHA-256 is
`4505234d13039159c3191918f7db729819ad6ed25f46e538d91975466d660e83`.
No model row, variable, objective, hint, assumption, or selector fix was
added for the query.

The explicit settings were one search worker, random seed zero, probing
level zero, linearization level zero, and a 180-second time allowance.
Search logging was enabled in both stdout and the response. The actual
parameter text and wire protobuf are saved, together with the complete
parameter descriptor, runtime versions, and Python/native module hashes.

Preparation of the query wrapper had already checked native parameter and
response transport, exact arithmetic above the binary64 integer range,
and rejection of malformed domain or row assignments. It made no solver
call. The production wrapper was prepared to preserve and inspect every
returned primary and additional vector; none was returned.

## Observed search

The native log records main search beginning after 36.41 seconds of
presolve. The presolved model had 67,062 variables, including 67,038
Booleans. The log records use of all 1,884 proved zero rows and all 3,096
literal clique rows.

The response records 60,538 conflicts, 118,934 branches, 243,915,342
Boolean propagations, and 85,514,249 integer propagations. There were no
LP iterations under the frozen linearization setting. These are execution
statistics; they do not establish whether a completion exists.

## Separate terminal replay

The independent checker imports no producer, `CpModel`, or `CpSolver`.
It decodes the accepted model, response, parameters, and parameter schema;
checks the actual runtime bindings; and verifies the completed owner and
the exact recorded overrun. It preserves native `UNKNOWN` and the wrapper
classification. It confirms that no candidate or additional vector was
returned. Its owner completed in 1.774478 seconds with the child reaped.

The result SHA-256 is
`b4029e65079849917b21c61a0120f79d129634d20f39e88ae0523b11b1fce796`;
the production owner SHA-256 is
`564c9c930adb8e123dc0fdd6611f931f37f011b207045f45b2a33e6031edafa4`.
The separate cold report SHA-256 is
`2cafeeeff150a0ca6a11310cf014522c60bd8af699b0ab9322b796c4721ba4a0`;
its owner SHA-256 is
`8feeee544153d3e124d26f53bd384f79cc5055f15969d6bd3e29b85fb39ba49e`.

The full response text, response protobuf, stdout, stderr, owner receipts,
parameter files, and exact model-restoration manifest are retained. The
raw model is recoverable from the already published lossless gzip:

```bash
python experiments/workspace/exact_prefix_suffix_artifacts.py restore \
  --manifest experiments/logs/root-prism-free/f0-boolean-shared-query-run01-publication01/manifest.json
```

The unchanged model will not be retried in this lane. The next proposed
strengthening is a literal transfer of previously certified one-edge and
two-edge prism constraints. That transfer needs its own complete inventory,
proof bindings, construction, and independent checks.
