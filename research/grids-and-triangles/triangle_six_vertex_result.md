# Thirty six-root triangle-projector results

At the immutable count point with SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`,
all 180 matrices in the prepared six-root family are positive semidefinite.
The single query took 27.511392 seconds under its 60-second bound.
The separate cold replay took 22.483380 seconds.

This covers exactly the 30 six-vertex catalogue roots containing a triangle
and all their 2,374 intersecting-triangle classes. It does not cover the
other 32 six-vertex roots. Every class was retained before the count point
was loaded. There was no optimizer call or separating inequality.

## Exact checks

The six families are Kminus, Kplus, the scalar class Gram matrix N,
the triangle projector Q, and the two kernels conditioned on all six
root-vertex vectors. The [preparation note](triangle_six_vertex_projectors.md)
gives their formulas, literal product normalization and finite coverage.

For each block, the query contracts the sparse induced-count form using
Python integers and computes the entire integer characteristic polynomial
det(tI+M). Every coefficient is nonnegative. Since M is real symmetric,
a negative eigenvalue would give this polynomial a positive real root.
A nonzero polynomial with all coefficients nonnegative has no positive
real root, so this is an exact PSD certificate.

The query also checks all 127,647 lower-triangular entries of the
coefficient partition at this point, all 540 root-point-star kernel
conditions, and all 76 core-triangle zero rows. The constant class vector
is not assumed to be a kernel.

Cold replay reloads the bound model and count point, recomputes every
integer matrix and polynomial, and compares them with the stored result.
It does not repeat tensor generation or claim independent reconstruction
of every literal product. The preparation's 756 separate host controls
remain the direct product controls.

The scalar N family is already implied by the complete scalar flag
family and exact SRG extension identities. The [explicit class reduction](triangle_scalar_flag_span.md)
records that dependency. Checking N here gives a direct certificate at
the fixed point; it is not counted as a new independent condition.

## Exact nullities

| Root type | Order | Kminus | Kplus | N | Q | Minus Schur | Plus Schur |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 220 | 1 | 1 | 59 | 6 | 7 | 7 |
| 51 | 176 | 10 | 10 | 64 | 15 | 16 | 16 |
| 52 | 110 | 7 | 7 | 46 | 12 | 13 | 13 |
| 53 | 52 | 4 | 4 | 30 | 9 | 10 | 10 |
| 60 | 139 | 13 | 13 | 63 | 18 | 19 | 19 |
| 62 | 86 | 8 | 8 | 44 | 13 | 14 | 14 |
| 67 | 150 | 1 | 1 | 51 | 6 | 7 | 7 |
| 68 | 122 | 4 | 4 | 49 | 9 | 10 | 10 |
| 69 | 114 | 10 | 10 | 56 | 15 | 17 | 17 |
| 70 | 77 | 5 | 5 | 39 | 10 | 11 | 11 |
| 71 | 78 | 14 | 14 | 45 | 18 | 20 | 20 |
| 72 | 43 | 8 | 8 | 30 | 12 | 14 | 14 |
| 76 | 75 | 8 | 8 | 37 | 13 | 14 | 14 |
| 77 | 91 | 8 | 8 | 49 | 13 | 15 | 15 |
| 79 | 50 | 6 | 6 | 31 | 11 | 12 | 12 |
| 80 | 109 | 13 | 13 | 59 | 18 | 19 | 19 |
| 83 | 92 | 1 | 1 | 40 | 6 | 7 | 7 |
| 84 | 75 | 4 | 4 | 40 | 9 | 10 | 10 |
| 85 | 44 | 3 | 3 | 28 | 8 | 9 | 9 |
| 86 | 74 | 2 | 2 | 36 | 7 | 8 | 8 |
| 87 | 57 | 11 | 11 | 39 | 15 | 17 | 17 |
| 88 | 47 | 4 | 4 | 29 | 9 | 10 | 10 |
| 90 | 53 | 9 | 9 | 35 | 14 | 15 | 15 |
| 93 | 60 | 5 | 5 | 38 | 10 | 11 | 11 |
| 94 | 36 | 10 | 10 | 29 | 14 | 16 | 16 |
| 95 | 24 | 1 | 1 | 19 | 6 | 7 | 7 |
| 96 | 44 | 2 | 2 | 25 | 6 | 8 | 8 |
| 97 | 39 | 4 | 4 | 26 | 8 | 10 | 10 |
| 98 | 26 | 2 | 2 | 19 | 6 | 8 | 8 |
| 99 | 11 | 11 | 11 | 11 | 11 | 11 | 11 |

The nullities are read from the exact characteristic polynomials.
They are not numerical rank estimates. Root type 99 has zero matrices
in this count point; it was retained in every family.

## Artifacts and replay

The query source is
`experiments/workspace/triangle_six_vertex_query.py`, SHA256
`0382ac1df28bb3ad952dd530057ecb8c69c4d7898ac2ebcc5730a2cf59d053d3`.

The model is
`experiments/logs/moments-and-counts/triangle-six-vertex-preparation01/model.json.gz`,
with compressed SHA256
`865fd8b034387d297ea0bdac4774e5d370c621b46720f241d3733b5b02d34a67`.

The complete result is saved losslessly as
`experiments/logs/moments-and-counts/order10-six-root-vertex-query01.json.gz`.
Its compressed SHA256 is `4a6b440cb93b2d123fef2b7b052faff0808d4e4ccb44f20bada3d7d3caad6764`.
The decompressed JSON has 35,943,301 bytes and
SHA256 `dfadc5df3b56124e659d989adfac601b3160885217a6823e3b1d86cfccdf3642`.
It contains all matrices and all polynomial coefficients.

The cold replay is
`experiments/logs/moments-and-counts/order10-six-root-vertex-query01-replay.json`,
SHA256 `49ca3c28717270934f0a36618abc648dcbdce4a4bf5db22359583dac3bf276f3`.

To use the unchanged replay CLI, first decompress the result archive to
the corresponding .json path. Run triangle_six_vertex_query.py in replay
mode with the preparation directory, immutable point, decompressed result
and a new output path. The driver refuses to overwrite an existing output.

The count point survives these necessary finite conditions. No graph
construction or nonexistence proof follows from this result.
