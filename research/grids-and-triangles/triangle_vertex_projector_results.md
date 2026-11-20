# Exact triangle-projector results at the saved count point

Both vertex-derived triangle kernels pass the exact tests at the unchanged
integer count point with SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.

The first query tested all nine full four-root blocks for each kernel,
together with the four blocks conditioned on an internal triangle.
All 22 matrices are positive semidefinite. The single query took
1.095 seconds; cold replay took
0.810 seconds.

The second query removed the entire span of the four root vertex vectors
inside each embedding before summing. All 18 stronger residual blocks
are positive semidefinite. The query took 1.050 seconds;
cold replay took 0.936 seconds.

Every matrix was contracted with Python integers and retained in full.
Exact coefficients of det(tI+M) were recomputed during cold replay.
All constant-vector checks passed. The second query also verified all
72 root point-star kernel equations and every internal-triangle zero row.
No separator was found, and no optimizer was called.

The nullities below agree between the two kernels. This coincidence at
one point does not prove that the two matrix inequalities are redundant.

| Root type | Full order | Unconditioned nullity | Internal-triangle nullity | All-root-vertex nullity |
| --- | ---: | ---: | ---: | ---: |
| 8 | 107 | 5 | not applicable | 9 |
| 9 | 93 | 6 | not applicable | 13 |
| 10 | 72 | 7 | not applicable | 13 |
| 11 | 49 | 8 | not applicable | 12 |
| 12 | 79 | 7 | not applicable | 17 |
| 13 | 58 | 8 | not applicable | 14 |
| 14 | 41 | 10 | 11 | 14 |
| 15 | 34 | 10 | 11 | 14 |
| 16 | 41 | 11 | not applicable | 15 |

The point still has no known graph realization. These calculations certify
only the stated finite matrix families. They do not establish all
order-ten necessary conditions.

## Frozen files

The constructions and their scope are described in
[the two-kernel note](triangle_vertex_projectors.md) and
[the root-vertex conditioning note](triangle_vertex_root_schur.md).
The product preparation retains every one of the 574 full triangle
classes and checks the old Q and scalar tensors coefficientwise.

The first result has SHA256
`4bfa499485f9149485f882074dc421128df5ee539d2262f576acb1b04e3e5538`.
The second has SHA256
`4b23092065e6a6be80165261ef7cab6925d6c7ced7c81adb8be1103c72f72a2d`.
Their exact JSON bytes are stored in deterministic gzip archives with
`.json.gz` filenames. Decompress each archive before passing it to its
unchanged replay driver. The replay records identify the source,
preparation, model, and point hashes.
