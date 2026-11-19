# Triangle vertex projectors on thirty six-vertex roots

This preparation uses exactly the 30 six-vertex catalogue roots that contain a triangle. Their 2,374 triangle classes are unchanged from the frozen [six-root triangle-conditioning domain](triangle_projector_six_root_conditioning.md). It does not claim coverage of all 62 six-vertex root types.

Each class contains every triangle with the specified nonempty root intersection and sorted outside-neighborhood masks. There is no count-point pruning. A class has at most two outside vertices, so two class triangles together with the root use at most ten vertices. This is the first vertex-projector extension in this sequence whose coefficients can involve the new order-ten count coordinates.

## Kernels and conditioning

The construction retains six families over every root:

- The two triangle kernels \(K_- = B^T(27I-9A+J)B/9\) and \(K_+=B^T(44I+11A-2J)B\).
- The scalar class-count Gram matrix \(N\).
- The unconditioned triangle-kernel projector \(Q\).
- The two kernels obtained by projecting off the span of all six root-vertex vectors.

The formulas and normalization are those of [the complete five-root construction](triangle_all_five_vertex_projectors.md), with a six-by-six root Gram matrix. Before either inverse is used, the constructor checks all six leading principal minors and verifies the exact inverse identity. It then forms the entrywise corrections
\[
M_- - \frac{1}{9}
  \bigl(c_{-,C}^TG_-^{-1}c_{-,D}\bigr)_{C,D}\circ N,
\qquad
M_+ -
  \bigl(c_{+,C}^TG_+^{-1}c_{+,D}\bigr)_{C,D}\circ N.
\]
Positive denominators are cleared and a common positive gcd is removed. The correction uses the full second-moment matrix \(N\), not products of first moments.

The six point-star vectors are kernels of \(Q\) and of both vertex-conditioned families. A triangle inside the root gives a zero row in each vertex-conditioned matrix. The constant class vector is not assumed to be a kernel, because triangles disjoint from the root are absent.

## Reuse and coefficient comparisons

The old six-root source supplies the same ordered partial-injection enumerator and the same class domains. Its source hash is checked before use. Every old class record is retained unchanged, including its core-triangle cross values.

The old cache contains core-triangle-conditioned \(Q\), not a separate scalar \(N\) tensor. The new common product pass therefore constructs \(K_-\), \(K_+\), \(N\) and unconditioned \(Q\) together. For each root, it verifies the coefficientwise identity
\[
11M_Q+110M_-+3M_++10N=2310\operatorname{diag}(p).
\]
It then reconstructs every old conditioned-\(Q\) coefficient as
\[
\det(C)M_Q-\bigl(q_U^T\operatorname{adj}(C)q_V\bigr)_{U,V}\circ N
\]
and compares the entire sparse tensor to the frozen old model.

The old enumerator recorded 239,743 distinct entry/type contributions before deleting zero conditioned-kernel coefficients. Scalar contributions are positive, so this gives an exact expected scalar support of 239,743 positions. The new construction checks this support count separately at every root. It does not treat that support census as an existing scalar tensor.

All ordered extension products retain the two outside-label stabilizers. Their product is divided out only after summing by induced type. Direct host controls separately enumerate labelled root embeddings and actual ordered triangle pairs, including ten-vertex hosts.

## Scope and bounded construction

There are 127,647 lower-triangular entries per family. The conservative union-candidate bound is 2,967,175. The constructor uses the five fixed chunks from the old six-root package:

| Chunk | Root types | Classes | Candidate bound |
|---|---|---:|---:|
| 0 | 50, 94, 95, 97, 98, 99 | 356 | 668,994 |
| 1 | 51, 62, 72, 79, 85, 86 | 473 | 595,870 |
| 2 | 67, 71, 80, 84, 88, 90 | 512 | 577,880 |
| 3 | 60, 69, 76, 77, 93, 96 | 523 | 574,887 |
| 4 | 52, 53, 68, 70, 83, 87 | 510 | 549,544 |

The configured construction bounds are 60 seconds per chunk and 180 seconds overall, with one worker. Every completed root and chunk is saved before continuation. A timeout preserves the completed prefix and cannot claim whole-family coverage.

The planned exact checks comprise 360 positive root-Gram leading minors, 2,160 inverse entries, 28,488 root-to-class cross entries and 255,294 lower-triangular correction coefficients. There are 38 internal core-triangle rows in each Schur family.

The inventory is experiments/logs/moments-and-counts/order10-six-root-vertex-projector-inventory.json. Its historical old_control_seconds field records the original complete chunk duration, including both construction and controls. It is not a measurement of the controls alone. The inventory's model-size estimates are not generated-model outcomes.

The new constructor is experiments/workspace/triangle_six_vertex_projectors.py. All old sources and models remain unchanged. Construction loads no count point and calls no optimizer. A point query requires a separate frozen source/model gate; no point-query outcome is part of this note.

## Completed preparation

The single construction completed all 30 roots in 172.114 seconds. The five chunk durations were 34.340, 30.957, 31.529, 34.257 and 33.099 seconds. Each completed root and chunk has its own retained artifact.

The preparation verifies 239,743 coefficientwise partition identities and 958,972 exact divisions by outside-label stabilizers. All 30 old conditioned-Q tensors are recovered exactly. There are 756 direct literal host controls, including ten-vertex hosts. Both root Gram matrices are positive definite at all roots, with 360 positive leading minors and 2,160 checked inverse entries.

The six family tensors contain 124,084, 239,743, 239,743, 239,743, 236,020 and 236,971 sparse terms in the order Kminus, Kplus, N, Q, minus Schur and plus Schur. The raw combined model has 23,497,393 bytes and SHA256 c0c518ad5c4446a3318261bfa4664b4c7299542e08af9b43471152f8bcf1bfc4. Its deterministic gzip has 6,090,305 bytes and SHA256 865fd8b034387d297ea0bdac4774e5d370c621b46720f241d3733b5b02d34a67.

The separate triangle_six_vertex_query.py driver is prepared for one exact query of the 180 matrices. Its proposed 60-second limit is explicit: the cubic dimension proxy is 1.938 times the completed five-root family, whose exact query took 17.198 seconds. That proxy is a workload estimate, not a query outcome. The driver preserves partial results if its deadline is reached. A separate source/model gate remains required before it runs.

