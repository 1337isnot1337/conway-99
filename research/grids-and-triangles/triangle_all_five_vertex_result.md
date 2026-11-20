# Exact point result for all five-root triangle kernels

All 126 matrices in the complete 21-root preparation are positive semidefinite at the frozen integer count point with SHA256 0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df.

The point query completed in 17.198 seconds. A separate process reconstructed all matrices and characteristic polynomials from the frozen tensors in 13.377 seconds. Both checks used exact integer arithmetic. No negative inequality was found and no optimizer was called.

These results concern the listed finite necessary conditions. They do not construct a graph or settle its existence.

## Coverage and certificate

Every triangle class meeting the root is retained: 1,296 classes over all 21 five-vertex roots. Each root has six matrices: \(K_-\), \(K_+\), scalar class-count \(N\), the triangle projector \(Q\), and the two vertex-conditioned Schur matrices.

The checker verifies all coefficients of \(\det(tI+M)\) are nonnegative. Each matrix is real symmetric, so this is an exact positive-semidefiniteness certificate. It also checks 315 point-star kernel vectors, 18 internal-triangle zero rows, and all 64,296 pointwise entries of the projector partition identity. It does not assume that the constant class vector is a kernel of an intersecting-only domain.

The exact nullities are:

| Root type | Order | \(K_-\) | \(K_+\) | \(N\) | \(Q\) | Schur \(K_-\) | Schur \(K_+\) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 17 | 205 | 0 | 0 | 63 | 5 | 5 | 5 |
| 18 | 159 | 0 | 0 | 55 | 5 | 5 | 5 |
| 19 | 111 | 0 | 0 | 43 | 5 | 5 | 5 |
| 20 | 67 | 0 | 0 | 30 | 5 | 5 | 5 |
| 21 | 33 | 0 | 0 | 20 | 5 | 5 | 5 |
| 22 | 113 | 0 | 0 | 47 | 5 | 7 | 7 |
| 23 | 79 | 0 | 0 | 36 | 5 | 5 | 5 |
| 24 | 72 | 0 | 0 | 36 | 5 | 7 | 7 |
| 25 | 48 | 0 | 0 | 26 | 5 | 5 | 5 |
| 26 | 56 | 1 | 1 | 25 | 5 | 6 | 6 |
| 27 | 44 | 4 | 4 | 26 | 8 | 9 | 9 |
| 28 | 26 | 3 | 3 | 19 | 7 | 8 | 8 |
| 29 | 41 | 2 | 2 | 22 | 7 | 7 | 7 |
| 30 | 51 | 0 | 0 | 29 | 5 | 6 | 6 |
| 31 | 25 | 0 | 0 | 17 | 5 | 5 | 5 |
| 32 | 34 | 5 | 5 | 25 | 9 | 10 | 10 |
| 33 | 34 | 1 | 1 | 21 | 5 | 6 | 6 |
| 34 | 28 | 2 | 2 | 20 | 6 | 7 | 7 |
| 35 | 19 | 6 | 6 | 18 | 9 | 11 | 11 |
| 36 | 35 | 0 | 0 | 24 | 5 | 5 | 5 |
| 37 | 16 | 3 | 3 | 14 | 7 | 8 | 8 |

The complete tensors and their independent literal-host normalization controls are documented in [triangle_all_five_vertex_projectors.md](triangle_all_five_vertex_projectors.md). The cold point replay reconstructs the matrices from those tensors; it does not repeat tensor enumeration.

## Frozen files

The query source is experiments/workspace/triangle_all_five_vertex_query.py, SHA256 dc7995de26f4de28668c998ecf34e8ec79687518147b1b60207b86a0a42a08d9.

The full result is archived without loss at experiments/logs/moments-and-counts/order10-all-five-vertex-query01.json.gz. Its archive SHA256 is ad716d8e464d89147b7f409884ee2431ae9a9ee169169ae0ca0192d289f24657. The decompressed JSON is 19,310,418 bytes with SHA256 483f7e3722694fe9a8fc65f020f5d5db9693c1a1b0bfd629c04048a310e55eb3. It contains every integer matrix and every exact characteristic polynomial.

The separate replay is experiments/logs/moments-and-counts/order10-all-five-vertex-query01-replay.json, SHA256 1eb3187ab64d277df3cdccadbc0251af74b8131aed733f5933eba14758cccc99.

To run the unchanged replay, first decompress the archive to the corresponding .json path. Then run the frozen query source in replay mode, passing the preparation directory, the frozen count point, the decompressed result, and a new output path. The replay refuses to overwrite its output. No catalogue regeneration, tensor construction, or optimizer is involved.

The first metadata-only preparation attempt is preserved separately. It stopped on JSON object-key ordering before loading the point. The corrected input validation compares the complete family-key set and retains an explicit iteration order. The product tensors were unchanged.

