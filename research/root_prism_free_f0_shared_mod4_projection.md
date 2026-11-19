# Full-domain projection modulo four

The complete degree and mixed equality system gives no new selector congruence modulo four beyond the original Gram equations. This is an equality-only result on all 68,394 eligible edge variables. It does not impose edge activation, nonnegativity, upper bounds, or integrality.

## Exact calculation

The matrix contains 480 degree rows and 8,640 mixed rows. The original Gram module contains 172 augmented rows, including the population row. All rows and their original integer right-hand sides are reduced modulo four.

| Quantity | Exact value |
|---|---:|
| Original edge rows | 9,120 |
| Edge columns | 68,394 |
| Unit pivots modulo four | 7,713 |
| Independent surviving coefficient-two pivots | 18 |
| Zero-edge residual rows | 1,389 |
| Doubled even rows | 18 |
| Retained zero-edge obligations | 1,407 |
| Obligations with nonzero selector RHS | 197 |
| Obligations outside the original Gram module | 0 |
| Gram unit pivots | 132 |
| Gram even pivots | 0 |

The calculation took 7.005 seconds. Its owned child was reaped after 7.140 seconds. The separate checker took 9.733 seconds, with its owned child reaped after 9.830 seconds. No optimizer or native numerical library was imported. The full compressed certificate is 178,220 bytes.

## Why the generators are complete

The producer carries each edge row, its original-row multipliers, and its selector RHS through the same operations over Z/4. An odd pivot is a unit, so it can be normalized and eliminated without division by two. Rows whose low coefficient plane vanishes are deferred.

The producer then subtracts twice the unit rows to remove remaining coefficient-two entries in unit columns. The residual edge matrix is twice a binary matrix. Binary elimination gives its even pivots and zero residuals. The exact zero residuals, together with twice every surviving even row, generate the full left kernel over Z/4. They form a generating set; no claim that they are a free basis is needed.

Every generated obligation is saved, including zero RHS obligations. Every surviving even row is also saved with its original-row multipliers, half-edge mask, and RHS. These extra rows provide independent rank witnesses.

## Independent checks

The checker imports no producer, bit-plane core, or domain producer. It validates the frozen, hash-bound list of 480 signatures, then independently reconstructs the targets, complete edge set, original rows, and Gram rows. It does not re-enumerate admissible triples from all combinations. For every obligation it directly contracts the original-row multipliers using disjoint coefficient-state masks. This checks all edge coefficients and the exact selector RHS modulo four.

It also contracts every Gram witness and checks Gram-module membership with dense unit Gauss-Jordan elimination followed by a binary even residual basis. This differs from the producer's low/high bit-plane elimination.

A reversed original-row order independently reconstructs the full binary row span. Every one of the 18 saved even row combinations is checked directly. Their half-edge masks are independent modulo that span. The checker therefore independently confirms the unit rank and the even-rank lower bound.

Completeness of the full modulo-four kernel generating set follows from the reviewed producer algorithm and its exhaustive small controls. The cold checker does not perform a second full modulo-four elimination. The core controls cover all 256 two-by-two matrices over Z/4, their full kernels, and every ambient membership. Separate checker controls cover all 256 matrices and 4,096 membership cases.

## Evidence

The immutable source and configuration bindings are in [the configuration](../experiments/logs/root-prism-free/f0-shared-mod4-configuration01.json). The accepted preparation and bounded root gate precede the calculation.

- [Producer report](../experiments/logs/root-prism-free/f0-shared-mod4-run01/report.json), SHA256 `1a106db963058c58d30b00c9baa4113cc24a0e49d77c20b0b1d1078f32af3b75`.
- [Complete certificate](../experiments/logs/root-prism-free/f0-shared-mod4-run01/certificates.json.gz), SHA256 `8d00a9973fcc8fbd81c46f4959570a7651ee9dd0392b5fed88fdf000fdf16579`.
- [Independent cold report](../experiments/logs/root-prism-free/f0-shared-mod4-run01-cold/report.json), SHA256 `addda32b70e0bde2444ab39b9535d5c08e6565867e86295f09663d6c76ae2083`.

The separate [two- and three-primary corollary](root_prism_free_f0_shared_two_three_primary.md) uses these rank witnesses together with the accepted rational and characteristic-three calculations. It does not change the scope or status of these immutable reports.
