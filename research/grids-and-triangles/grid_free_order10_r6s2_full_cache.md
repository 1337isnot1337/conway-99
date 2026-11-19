# Complete r6s2 cache and reusable separator

The point-independent cache now contains all 62 six-vertex roots in the
prepared r6s2 family. It has 14,348 flags, 3,913,479 lower-triangular
entries, and 4,036,437 nonzero tensor coefficients. The largest block has
1,248 flags. No root or flag was removed using a count point.

This is the family defined in [the preparation note](grid_free_order10_r6s2.md):
each flag has at most two free vertices, and each free vertex has degree
at least three in the entire flag. For a two-vertex flag, its mutual edge
contributes to this degree. Completeness here refers to this family. It
does not assert that every order-ten moment inequality has been included.

## Immutable continuation

The first 55 blocks and their 18 exact separating inequalities remain
unchanged. Their results and independent reconstruction are recorded in
[the 55-block result note](grid_free_order10_r6s2_results.md).

The separate continuation generated these seven remaining blocks:

| Root type | Flags | Lower entries | Tensor nonzeros |
|---:|---:|---:|---:|
| 45 | 614 | 188,805 | 182,236 |
| 46 | 676 | 228,826 | 196,924 |
| 64 | 783 | 306,936 | 227,195 |
| 40 | 810 | 328,455 | 352,634 |
| 44 | 938 | 440,391 | 415,596 |
| 39 | 1,093 | 597,871 | 674,672 |
| 38 | 1,248 | 779,376 | 995,705 |

Generation took 181.083 seconds under the 300-second bound. All seven
blocks completed; no timeout or resume was needed. Peak process memory
was 448,540 KiB. Generation used the small catalogue and the frozen
product builder. It used no count point, dense core reduction,
eigensystem, or optimizer.

The new cache is a separate file. The combined manifest references it
and the unchanged 55-block cache by SHA256. It does not rewrite either
cache.

Relevant files:

- `experiments/workspace/grid_free_order10_r6s2_remaining.py`
- `experiments/logs/moments-and-counts/prism-zero-order10-r6s2-seven-preparation.json`
- `experiments/logs/moments-and-counts/prism-zero-order10-r6s2-seven-generation.json`
- `experiments/logs/moments-and-counts/prism-zero-order10-r6s2-seven-blocks.pickle.gz`
- `experiments/logs/moments-and-counts/order10-r6s2-full-cache.json`

The combined manifest SHA256 is
`8f8d0b3e2e509fb617962f744e6df7ca56d401bc67a2916f16ab124dafb486d0`.
The new seven-block cache SHA256 is
`e12e59749eebbf53fbd314e8063bc402900abf54c80016cd9e1cee99ce1a2447`.

## Reusable scanner

`experiments/workspace/grid_free_order10_r6s2_point_scan.py` exposes:

```python
scanner = FullScanner(data, raw, scale, cache_path, reduced_hash)
result = scanner.scan(proposal_path, output_path, seconds=180)
replay = scanner.replay(output_path)
```

Use the combined JSON manifest as `cache_path` to scan all 62 blocks.
The constructor also accepts an individual cache and reports its smaller
scope explicitly. `data`, `raw`, and `scale` use the existing order-ten
core-reduction conventions. The proposal uses the existing free-prefix
schema, with all 550 core coordinates reconstructed exactly from its
stored binary floating-point values.

The constructor checks the cache hashes, root sets, complete flag-domain
cardinalities, literal flag graphs, induced types, and tensor layout.
It checks that each stored flag is admissible and that all flag keys are
distinct. Equality with the independently audited full domain size then
establishes domain coverage for each root.

The scanner forms matrices with Python integer arithmetic. Numerical
eigenvectors only propose integer directions. An exported inequality
must pass an exact negative quadratic-form check, an exact contraction
to induced counts, and an exact reduction to the 550 core coordinates.
Every gcd used to normalize an inequality is positive. Zero rows are
removed only after checking that every entry in that row is exactly
zero. In particular, the scanner does not replace second moments by
first moments for the nonbinary flags.

The output distinguishes:

- completion of the requested cache;
- completion of the original selected 55-root subfamily;
- completion of the full 62-root family.

A bounded scan that finds no exact separator does not certify positive
semidefiniteness. A timed-out scan preserves only completed block
records. `replay` checks the exact exported inequalities using the saved
tensors; it does not reconstruct their products independently.

The scanner source SHA256 is
`7bb2542e4e69cadade0f096ee578252a804a1c0ff2e0e2d555ce943886654a11`.

## Cache-only controls

The control driver is
`experiments/workspace/grid_free_order10_r6s2_point_scan_control.py`.
Its report is
`experiments/logs/moments-and-counts/prism-zero-order10-r6s2-point-scan-control.json`.
It passed in 4.428 seconds without loading the dense reduction.

The controls verify all 62 cached flag domains and independently rebuild
315 saved product entries across the seven new roots using the literal
edge/nonedge oracle. Of these entries, 62 contain an order-ten term.
They also replay all 18 earlier negative quadratic forms through the
new matrix interface and check a rank-one moment matrix with flag value
two, whose first and second moments differ.

A separate read-only review of the scanner passed. It checks domain
coverage, preservation of nonbinary diagonals, exact sign acceptance,
gcd normalization, and the three completion flags. Its source-bound
record is
`experiments/logs/moments-and-counts/prism-zero-order10-r6s2-point-scan-independent-review.json`.
That review ran no constructor, tensor regeneration, or solver.

The product checks are sampled controls, not an independent reconstruction
of every new tensor entry. The independent source audit and earlier
fresh reconstruction remain separate. Core-form reduction through the
new scanner is reserved for the next shared-load loop preparation; the
cache-only controls do not claim to have performed that step.

No new LP has been run by this cache-generation package. The count
witnesses, existing cuts, and seven new tensors do not constitute a
99-vertex graph or an exclusion of all such graphs.
