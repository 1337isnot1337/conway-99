# The prism-zero count face x521 = 0

This package prepares a separate feasibility probe of the frozen
order-ten prism-zero count model with the additional equality `x521=0`.
The single run produced an exact integral count witness on this face.
The complete model was then rebuilt and the witness replayed exactly.

## Result and limits

HiGHS returned `kOptimal` after 13 IPM iterations and 17.999773 seconds.
Rounding the core coordinates gave nonnegative integral counts for all
48,965 catalogue types. The integer checker passed all 180,445 original
extension equations, level totals, the original DP bounds, all 59 required
zeros including `x521=0`, and all 25 retained cuts. The smallest retained
cut value is 1,156,044. No repair or second LP call was needed.

A separate process reconstructed the parent model, reproduced the new
numerical model hash, and replayed this entire count witness. It called
no optimizer. The frozen witness SHA-256 is
`ee8e22f070e0529be5be8bf14c853c6ad9ed97127570223abf6e1529ab8857f9`.

This proves feasibility of this finite count system on `x521=0`.
It does not construct a graph or certify PSD. The two moment-family
scans, if performed, belong to a separately named package and do not
alter this model or its one-call outcome.

The mathematical motivation is the exact identity
`x521=e24+3*e222` from
[`root_prism_free_edge_components.md`](root_prism_free_edge_components.md).
Under global prism-freeness, this face contains precisely those edge-type
count vectors with no edge of type `222` or `24`. In particular, it is a
necessary count face for the new globally minimum-edge cases `33` and
`6`. It is not a consequence of choosing a minimum among only the
fourteen edges at one fixed root.

## Frozen parent and the one change

The parent is
`grid_free_order10_prism_zero_moments_loop.py`, source SHA-256
`a65dc6b31ebebe7bcd14398f685537f642081a7517c2e0ec94eb96246ad6e473`.
Its preparation is
`prism-zero-order10-ipm-zero-closure-preparation.json`, SHA-256
`fce82618e5beef610d70fadbf7b0e5d955a43496c05c3621b78ee270ff87c820`.

The wrapper calls that frozen model constructor and requires exact
agreement with its metadata and numerical model hash. It retains all
47,645 rows, all 25 certified cuts, and the 58 prism-containing core
zeros. It then changes only the numerical upper bound of stored column
518, corresponding to ordinary coordinate 521, from one to zero.
The lower bound was already zero.

The ordinary-variable scale remains the original positive DP bound,
19,404. It is not set to zero. No coefficient, row scale, right-hand
side, objective, or other column bound changes. The new motif inequality
`3*x1+2*x521<=4158` is not added, and no further zero propagation is
inserted.

| Property | Parent | New face |
| --- | ---: | ---: |
| Rows | 47,645 | 47,645 |
| Stored columns | 547 | 547 |
| Free columns | 491 | 490 |
| Matrix nonzeros | 5,430,251 | 5,430,251 |
| Certified retained cuts | 25 | 25 |
| Required ordinary core zeros | 58 | 59 |
| DP scale for coordinate 521 | 19,404 | 19,404 |

The parent numerical model hash is
`62664e9c7d7fd5abe9ca61585e10f0d3714bbd72509dca0e7a54d725cbd5943e`.
The new hash is
`2b4b89146c8be779db343b053a0fa7600a14b71cd376d9572d4bf8ee4967b8e4`.
Restoring the one changed upper bound reproduces the parent hash exactly.

## Controls

The small scaling control checks 125 exact rational assignments in three
scaled variables. Exactly 25 lie on the new coordinate-zero face. It
checks that the bound change does not mutate the original bounds or
positive DP scales and that every row evaluation is unchanged.

The preparation also independently replays the parent's last exact
integer count witness. It verifies all 48,965 induced counts, all
180,445 original extension equations, level totals, original DP bounds,
and all 25 retained exact cuts. The smallest cut value is 629,575. This
known point has `x521=116`, so it is a positive control for the parent
model and is correctly excluded by the new face.

Preparation took 23.807 seconds, with peak resident memory 1,195,556 KiB.
It called no optimizer. The hash-bound local cache holds the unchanged
exact count data and the prepared numerical model, allowing the bounded
run to avoid reloading the large reduction. The source can reconstruct
this model for an independent exact witness replay.

## Run and proof gates

The runner permits one sequential HiGHS IPM feasibility call, with one
thread, presolve, no crossover, and a limit of 120 seconds. It has no
separator loop and no hidden dual-ray solver call. It saves the terminal
numerical status and all returned primal and dual arrays.

A numerical optimum is followed by an exact integer check of the rounded
core vector. That check imposes all 59 zeros, all original DP bounds,
every induced count, every original extension equation, and all 25 cuts.
Only a passing check is called an exact count witness. Such a witness
still is not a graph or a PSD certificate.

A numerical infeasibility status is only an indication. It cannot
exclude the count face without a separately extracted and exactly
replayed dual certificate. A time limit or other nonoptimal status is
recorded as unresolved. No additional root SAT batch is part of this
package.

## Files and replay

- `experiments/workspace/root_prism_free_x521_face.py`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-preparation.json`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-preparation.log`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-model-manifest.json`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-result.json`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-run.log`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-solver-data.json.gz`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-proposal.json`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-rounded-counts.json`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-full-replay.log`
- `experiments/logs/moments-and-counts/prism-zero-order10-x521-face-result-manifest.json`

Preparation:

```bash
.venv/bin/python experiments/workspace/root_prism_free_x521_face.py prepare
```

The one bounded run uses the separate command:

```bash
.venv/bin/python experiments/workspace/root_prism_free_x521_face.py run --seconds 120
```

If it produces an exact count witness, an independent reconstruction and
integer replay use:

```bash
.venv/bin/python experiments/workspace/root_prism_free_x521_face.py replay-witness --rebuild
```
