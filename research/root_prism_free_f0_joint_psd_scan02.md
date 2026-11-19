# Joint PSD scan: 21 checked rows

The corrected bounded scan retained 21 new necessary inequalities, and exact
cold replay passed for all 89 recorded candidates. There are 16 augmented
selector rows and five full-21-core plus-Schur rows. No minus-Schur row was
retained. The scope remains the global prism-free and F-free split18+18
component-zero stratum, with the other component and its alignment free.

The input is the numerical path-model proposal with SHA256
`bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e`.
No exact feasibility claim is made for that proposal. The preceding linear
query remains UNKNOWN.

## Observed scan coverage

The scan performed one decomposition for each family. The figures below
refer to the matrices passed to the eigensolver; the Schur matrices use the
frozen positive dyadic scaling.

| Family | Smallest numerical eigenvalue | Negative eigenvalues beyond the reporting tolerance | Directions started | Retained rows |
|---|---:|---:|---:|---:|
| Augmented selector | -0.2858065994849107 | 26 | 3 | 16 |
| Full21 plus Schur | -0.004063609107199524 | 1 | 8 | 5 |
| Full21 minus Schur | -1.5798260468585762e-16 | 0 | 4 | 0 |

The selector family reached its 16-row cap. The plus family completed all
eight planned directions. The time limit interrupted the minus family.
The terminal status is `TIME_LIMIT_PARTIAL`: 61.119821922 seconds elapsed,
including a 1.119821922-second cooperative overrun. The recorded prefix has
89 vector/scale attempts, of which 68 had nonpositive literal exact gaps.
The other 21 passed both exact-gap gates and the zero-aware duplicate and
unit-box filters.

No continuation of the unchanged minus scan was performed. Its tiny
numerical negative eigenvalue does not prove either positivity or a useful
negative direction.

## Exact rows and numerical size

The retained rows contain 178,481 nonzero coefficients. The largest absolute
coefficient is 1,298,137,088. Every row records its signed extrema, smallest
nonzero absolute coefficient, exact maximum/minimum ratio, and a positive
dyadic transport scale.

The normalized relative row gap is the exact dyadic gap divided by the
larger of one and the row's absolute unit-box coefficient norm. These gaps
range from approximately 0.00012725 to 0.00171019 for selector rows and from
0.00003350 to 0.00006019 for plus-Schur rows. All 21 exceed the separate
reporting heuristic. The labels do not prove nonredundancy of a row or strict
strengthening of the exact parent feasible set.

Each retained inequality was independently re-expanded through the frozen
literal PSD constructor, summed over the verified quotient orbits, and
evaluated as an exact rational number at the saved binary64 proposal.
The replay also reconstructed the quantization from every saved numerical
direction. The 389 already removed Z coordinates and 162 explicitly proved
Y-zero coordinates retain their exact provenance. Both the literal and
zero-projected row gaps were checked, including the residual identity for
proposal values that are not exactly zero.

Cold replay performed no decomposition or optimizer call. Its recorded wall
time was 284.569923088 seconds; an execution-backend stall was observed during
that interval. The replay completed normally and returned PASS.

## Preserved failed attempt

The first scan under source `555ce146...` completed one decomposition but
failed when saving its first direction checkpoint. A NumPy Boolean in the
reporting field `minimum_is_numerical_zero_scale` was not JSON-serializable.
The only saved result is the initial RUNNING record. That stale record does
not describe the completed computation, and no certificate is accepted from
it.

The corrected source `3bb5b68d...` wraps that one comparison in the built-in
`bool`. A complete AST comparison proves that this is the sole code change.
Thirty actual NumPy metadata records reproduce the old failure and serialize
successfully after the repair. The mathematical filter is unchanged except
for its source binding. The corrected preparation and cold filter replay
passed before the separately authorized corrected scan.

All failed source, preparation, filter, partial-result and stderr files are
preserved. There was no hidden optimizer call or automatic same-model retry.

## Frozen terminal records

- Result: `experiments/logs/root-prism-free/f0-joint-psd-zero-scan02.json.gz`,
  SHA256 `43e590c801ccb85e385253cc475ce6f6bdc09874d10b9c7571170cb2bd06d9a3`.
- Exact replay: `f0-joint-psd-zero-scan02-cold-replay.json`, SHA256
  `a59a5a8c559d2390847074f04e6fd51df38e2cb0bf333b4d2e88fc503068b7ae`.
- Summary: `f0-joint-psd-zero-scan02-summary.json`, SHA256
  `d937bc0cc19a950620a0f6d27c73c7772aa3c6d641e34a1cf76fb788d05f031e`.
- Independent zero-adapter source review:
  `f0-joint-psd-zero-independent-source-review.json`, SHA256
  `f0716b53c4d6b70a6053ae577df52ab59fe51b9304e6a7d716c354b775fee6a2`.

The next prepared overlay may append these 21 rows and the 258 published
core-pair clique rows while retaining all 15,200 variables and the complete
parent row/scaling prefixes. Before any duplicate removal this would have
28,043 rows and 1,086,559 nonzeros. A new linear query requires its own model,
native-transport, and source gates; none is part of this scan result.
