# Reusable scanner for all eleven higher-flag blocks

The combined scanner contains all nine r4s3 blocks and both r2s4 blocks.
The cache has 890 flags, 90,256 lower entries, and 237,362 tensor
nonzeros. Its largest block has order 332.

The source is
`experiments/workspace/grid_free_order10_higher_flags_point_scan.py`,
SHA256
`5d1af5a24c9a509e35b9aeb47e47bd97eb01c09eb51fad32c2a72ceb87075c86`.
It exposes the existing interface:

```python
scanner = FullScanner(data, raw, scale, cache_path, reduced_hash)
result = scanner.scan(proposal_path, output_path, seconds=180)
replay = scanner.replay(output_path)
```

Use the manifest
`experiments/logs/moments-and-counts/order10-higher-flags-full-cache.json`
as `cache_path`. Its SHA256 is
`b5c076fabeee3d88c89f738bdd7f746bab9a8071acee0632dbe37137eddc47b8`.
It references the unchanged nine-root tensor cache and the sixteen
already verified symbolic r2s4 entries. No existing cache is rewritten.

## Cache validation

The constructor checks every flag against the frozen complete domain,
including its order, root masks, graph, induced type, and root-fixing
stabilizer. The first-row coefficient of a flag is one in labelled
induced-embedding coordinates. The coefficient of that flag's own
induced type in its diagonal product equals its root-fixing stabilizer.
Both checks are applied separately, so the stabilizer-two flags retain
their required factors.

All flags and product diagonals remain in the cache. The prism-zero
projection is not applied to this reusable representation. A scan may
remove a row from an eigensystem only after its entire row is checked
exactly zero at the current point.

Coverage is reported by separate fields:

- `covers_complete_r4s3_family` for the nine-root family;
- `covers_complete_r2s4_family` for the two-root family;
- `covers_full11_families` for their union.

The scan reports `complete_r4s3_scan`, `complete_r2s4_scan`, and
`complete_full11_scan`, as well as the existing `complete_scan` field.
Incomplete scans preserve only fully completed block records and exact
accepted cuts.

## Exact acceptance and replay

The proposal is treated as an exact dyadic point represented by its
stored binary floating-point values. Induced counts and all matrix
entries are evaluated with Python integers. Numerical eigensystems
propose directions; they do not certify a sign.

An accepted cut must pass three exact checks: negative quadratic value,
contraction to induced counts, and reduction to the 550 core coordinates.
Every normalizing gcd is positive. The exported core-cut schema matches
the earlier scanners. The original induced form and vector remain in
the result so that a separate literal-product reconstruction can be
performed.

`replay` verifies the exact vector, cached tensor contraction, induced
form, core form, and rational value without recomputing an eigensystem.
It is an arithmetic replay using the saved tensors. It does not claim
independent reconstruction of a new tensor product.

A scan with no accepted negative direction is not an exact PSD
certificate. The two r2s4 matrices at the repaired seed point have a
separate exact principal-minor certificate; that result is not extended
to arbitrary proposals by this scanner.

## Cache-only controls

The control driver is
`experiments/workspace/grid_free_order10_higher_flags_point_scan_control.py`.
Its output is
`experiments/logs/moments-and-counts/order10-higher-flags-point-scan-control.json`.
It passes in 0.451 seconds without loading the dense reduction.

The controls validate the full eleven-block cache, reproduce both exact
r2s4 matrices and their 22 principal minors, and reproduce the
independently reconstructed four-cycle cut through the new matrix API.
No eigensystem or optimizer is used. Core-form reduction through this
new scanner is left to the shared-load loop preparation; the cache-only
controls do not claim that step.

The domain and product proofs are in
[the domain note](grid_free_order10_higher_flags_domains.md) and
[the result note](grid_free_order10_higher_flags_results.md). This package
runs no LP and makes no claim of a graph construction or full
nonexistence proof.
