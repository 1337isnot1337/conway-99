# Eighteen exact cuts from the six-root moment family

## Result and scope

All 55 prepared blocks of order at most 512 were generated and scanned.
Eighteen blocks give exact negative integer directions at the new rounded
prism-zero count witness. Their eighteen induced-count inequalities have
also passed an independent reconstruction of every supported product.

Sixteen of the eighteen fixed inequalities are negative at the separate
exact `x521 = 0` count witness. Thus the new family rejects both saved
points. It does not exclude all prism-zero count points or the whole
`x521 = 0` face. It does not establish graph nonexistence.

This is a complete scan of the fixed 55-block subfamily described in
`grid_free_order10_r6s2.md`. Seven larger blocks remain outside this
package. No root or flag was pruned because of its value at the test
point, and the saved tensors are independent of that point.

## Generation and exact separation

The run generated 1,042,819 lower-triangle entries and 991,475 tensor
nonzeros. It finished in 68.572 seconds, within the authorized 180-second
budget, with peak RSS 294,600 KiB. All 55 selected roots finished. There
was no timeout or unconfirmed numerical negative direction.

Numerical eigensystems selected candidate directions only. Each accepted
integer vector was checked on the exact integer moment matrix. Its
quadratic form was then contracted to a primitive integer form in the
48,965 unlabelled induced catalogue counts. The source verifies the
positive normalization divisor and the strictly negative value exactly.

The source does not replace two-vertex diagonal moments by first moments.
Some of those flags can occur twice at one root. Their square includes
both coincident-copy and disjoint-copy terms.

| Root type | Flags | Nonzero vector entries | Value at prism-zero point | Value at `x521 = 0` point |
| --- | ---: | ---: | ---: | ---: |
| 96 | 37 | 36 | -2,240,114,046 | -2,114,022,935 |
| 71 | 65 | 53 | -8,355,350 | 18,514,007 |
| 76 | 78 | 64 | -726,930,714 | -474,753,856 |
| 83 | 115 | 115 | -465,491,221 | -428,257,795 |
| 49 | 127 | 124 | -134,091,394 | -43,155,020 |
| 68 | 147 | 140 | -1,722,441,654 | -1,370,387,248 |
| 69 | 150 | 141 | -75,592,115 | -38,131,389 |
| 60 | 173 | 152 | -1,053,534,896 | -830,839,297 |
| 56 | 179 | 169 | -8,622,799,554 | -6,899,554,484 |
| 91 | 187 | 128 | -213,856,470 | 4,699,734 |
| 61 | 191 | 187 | -336,183,877 | -297,318,825 |
| 81 | 207 | 136 | -5,601,682,284 | -5,118,978,928 |
| 58 | 227 | 217 | -11,276,364,364 | -8,944,610,338 |
| 66 | 249 | 212 | -5,857,706,264 | -3,409,524,778 |
| 50 | 269 | 269 | -349,112,628 | -250,999,611 |
| 75 | 286 | 286 | -1,341,533,640 | -1,140,734,707 |
| 73 | 307 | 291 | -2,037,813,148 | -1,264,240,870 |
| 57 | 466 | 466 | -13,324,604,308 | -11,884,626,020 |

These are values of the primitive induced-count forms, not normalized
eigenvalues. The two points have hashes:

```text
prism-zero rounded point:
3f75ad72024829c91995f3b22d50f89cd709af6b6d9d3b0806c5ee05f3097326

x521-zero rounded point:
ee8e22f070e0529be5be8bf14c853c6ad9ed97127570223abf6e1529ab8857f9
```

## Independent construction checks

The independent audit enumerates flag masks directly, merges every
positive and negative adjacency prescription on a literal union of two
flags, and enumerates all remaining edges. It does not use the producer's
extension-table transport construction or overlap enumerator.

The first audit checks all 62 flag domains, 2,164 sampled products in
both orders, and 352 sampled products with nonzero order-ten terms. It
also independently reproduces the rook-graph example with flag value two,
first moment 72, and second moment 144.

A saved-tensor replay then verifies every negative vector and induced
form against the retained tensors. This replay is an arithmetic check;
it is not an independent tensor reconstruction.

The final gate reconstructs all 374,505 lower-triangle entries supported
by the eighteen vectors, using the independent literal-prescription
oracle. It compares each fresh entry with the retained tensor, but
accumulates every quadratic coefficient from the fresh result. All
eighteen complete induced-count forms, their positive divisors, and
their negative values agree.

This reconstruction finished in 159.033 seconds, within its 300-second
budget, with peak RSS 379,692 KiB. No eigensystem, producer transport,
producer product routine, optimizer, or dense core-count reduction was
used to obtain the proof values.

## Frozen package

The whitelist and hashes are in
`experiments/logs/moments-and-counts/prism-zero-order10-r6s2-manifest.json`.
The package includes the exact builder, bounded scan driver, independent
oracle audit, fresh-product replay driver, preparation reports, immutable
55-block cache, cut certificate, and both replay logs.

Key sources in `experiments/workspace/`:

- `grid_free_order10_r6s2.py`
- `grid_free_order10_r6s2_scan.py`
- `grid_free_order10_r6s2_independent_audit.py`
- `grid_free_order10_r6s2_fresh_replay.py`

Key artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Cut certificate `prism-zero-order10-r6s2-scan.json` | `839b2de78eb081edbf6e39c1f0085f5f1d56ee787a7eed58ec39cb41c0fb3708` |
| Unpruned 55-block cache | `84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c` |
| Independent domain/product audit | `cd136ea6249c173ce8a956c20c73c793f214754eedd44cd0a747904dd04b001d` |
| Fresh negative-product reconstruction | `286bd12ea30bee3825c97507fb5781f3ec36396eb580fc0c5ec58772c660b550` |

The preparation and all run inputs retain their original hashes. The
seven-root continuation, generic point scanner, and flag-range checks
are separate work and do not change this 55-block result.
