# Accepted targeted one-edge Schur certificates

The single source-gated targeted run proved all 252 supplied one-edge patterns and produced 252 distinct guarded native rows. The frozen outer runner accepted complete ASCII report serialization in 12.982 seconds, within its 60-second limit. The report is 272,662 bytes. There was no retry.

Every certificate reconstructs the actual matrix from the accepted full-core kernel and independently contracts an integer vector with that matrix. All 252 rejections use the plus kernel. All witnesses came from the fixed short-vector list; no cofactor fallback was needed. The main examined 252 matrices and 8,998 proposed short vectors. It did not enumerate other adjacency patterns.

The row for a rejected sole-edge-ab pattern is
\[
x_c+Y_{ab}-Y_{ac}-Y_{bc}\le1.
\]
Its complete native key has lower bound -2, upper bound 1, and four sorted terms. The present edge supplies its endpoint selectors; the isolated selector c remains an explicit guard. Original selector and edge IDs are retained, with edge variable index 540+edge ID.

The canonical row_keys array, serialized by JSON.stringify without a newline, has SHA256:
f8520f41d73c21e652386533388838a8f27837d50eea09726e06bbca909edef0.

None of the 252 present edges is in the committed set of 1,884 literal zero edges. This is only that recorded zero-premise comparison; it does not establish independence from other existing rows.

## Durable outputs

Full report:
experiments/logs/root-prism-free/f0-single-edge-schur-certificates01.json
SHA256 4c3363d7f875c2bf401ed2fba9d508167a1ad618d9ad15e39d21e1d690662b2f
Git blob f9a2cb8034dd051bd9db9097e4a2ec80f481cc5a.

Outer finalization:
experiments/logs/root-prism-free/f0-single-edge-schur-certificates01-finalization.json
SHA256 04c208519361648ce0cf5553c02484d952cdac58c0bd42c4e79258e40c438019
Git blob 4c300ded302df1ac366c94dc1cf84b7a50c32b04.

The exact report text returned by the frozen runner was preserved before publication hashing. The report includes every actual primitive matrix, integer negative vector, exact quadratic value, row key and origin. The separate finalization records the full serialization deadline and confirms all 252 records.

## Scope

This is an independent proof of the supplied 252 rows. It is not a complete eight-pattern census, an absence-of-other-patterns theorem, a graph construction or a component exclusion. Diagnostic saved minor strings and PSD masks were not used for acceptance.

The former complete positive-cube replay remains canceled. A later native append has its own row reconstruction, configuration and acceptance requirements. No native model, optimizer, local runtime, Pyroam or repository ref change occurred in this targeted run.
