# Selector PSD scan 01

The single reviewed spectral scan produced 32 exact valid moment inequalities.
Each inequality is strictly violated by the saved binary64 IPM proposal when
that proposal is interpreted losslessly as a rational array. This is a cut
certificate, not a feasible point or a component exclusion.

The proposing array comes from the numerically optimal IPM run. Its exact
linear reconstruction remains unresolved. Cut validity does not use the
array's feasibility; it follows from the augmented-square identity proved in
`root_prism_free_f0_selector_psd_cuts.md`.

## Scope and actual work

The scan expanded the complete 481-by-481 augmented selector matrix. It made
one symmetric eigendecomposition and used the frozen rounding scales. It
returned in 5.242007 seconds, within the external 60-second process bound.
There was no optimization call.

The scan stopped at its cap of 32 retained rows. It reached directions zero
through four of the at-most-eight-direction plan; it did not exhaust all
planned direction/scale combinations. Every attempted distinct row in this
prefix was retained after its exact gap check. Finding these rows does not
certify anything about the remaining eigenvalues or directions.

All 32 certificate vectors have augmented constant coordinate zero. Thus
these particular rows already follow from Z being PSD. They have zero right
side and a total of 196,350 nonzero quotient coefficients. The row supports
range from 29 to 9,395 variables. The largest absolute coefficient is
91,273,080, which fits in 27 bits. All coefficients are exact integers.

The five first-scale certificates use only 36, 16, 14, 48 and 20 nonzero
integer vector entries respectively. Their quotient rows have 63, 31, 29,
108 and 52 terms. The denser rescalings are retained separately because their
integer vectors give different exact inequalities.

No row enters a linear model automatically. A separate cut-augmented model
must preserve the frozen baseline and all existing inequalities, and its
source and exact acceptance must be reviewed before another optimization.

## Exact replay and archive

The replay recomputed every vector's literal coefficients, orbit sums,
positive normalization divisor and 389 certified zero substitutions. It then
checked the quotient gap against an independent full-coordinate expansion
over all 480 selectors and 114,960 pairs. All 32 exact gaps are positive in
the left-side-minus-right-side convention.

The raw result SHA-256 is
`7f8a2a22007539a67075aeb122ace3f81f800490723b8ca2c3a510c19ef45997`.
Its deterministic gzip archive has SHA-256
`5c74497bb70d44bf2fac7002ed16b4657500c4af2518cab196684c9346449e79`.
It stores the complete 13,777,345-byte result in 965,499 bytes. A fresh
restoration and exact replay reproduced the first replay byte for byte.
The original raw scan remains unchanged.

The result records the numerical input hash
`20674e3a41842e42232df60e24abf3f34a5a5c8ec9a16a258d4906bb58562fd9`.
That input is available byte-exactly through the separate IPM run archive.
There is no additional dependency on a live optimizer.

To restore the scan certificate:

```bash
python experiments/workspace/root_prism_free_f0_selector_psd_scan_archive.py unpack \
  --source experiments/logs/root-prism-free/f0-selector-psd-cuts-scan01.json.gz \
  --output /tmp/f0-selector-psd-scan01-restored.json \
  --report /tmp/f0-selector-psd-scan01-restore-report.json
python experiments/workspace/root_prism_free_f0_selector_psd_cuts.py replay \
  --preparation experiments/logs/root-prism-free/f0-selector-psd-cuts-preparation.json \
  --numeric /tmp/f0-second-moments-ipm-run01-restored/numerical.json \
  --result /tmp/f0-selector-psd-scan01-restored.json \
  --output /tmp/f0-selector-psd-scan01-replay.json
```

The output paths must be fresh. These commands use no eigendecomposition or
optimizer. A successful replay proves the recorded necessary inequalities
and their exact proposal gaps only.
