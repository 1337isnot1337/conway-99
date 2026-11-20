# Five-root conditioned query result

The immutable integer count point
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`
passes all eight complete five-root intersecting-triangle conditioned
blocks.

| Root type | Order | Exact rank | Exact nullity |
| --- | ---: | ---: | ---: |
| 26 | 56 | 50 | 6 |
| 27 | 44 | 35 | 9 |
| 28 | 26 | 18 | 8 |
| 32 | 34 | 24 | 10 |
| 33 | 34 | 28 | 6 |
| 34 | 28 | 21 | 7 |
| 35 | 19 | 8 | 11 |
| 37 | 16 | 8 | 8 |

The single query took 0.06459765599720413 seconds. A cold replay took
0.038498706999234855 seconds. It reproduced every integer matrix entry,
every characteristic-polynomial coefficient, all nine core-triangle
zero rows, and all 40 root point-star kernel checks.

The result stores all eight full matrices and the coefficients of
det(tI+M). Those coefficients are nonnegative. Since the matrices are
symmetric, this certifies positive semidefiniteness exactly.

The result path is
`experiments/logs/moments-and-counts/order10-five-root-triangle-query01.json`,
SHA256 `bbdf949677fe0d2baae328677bb67dd907590d5362db0450a4a00ff248c67a63`.
The source is
`experiments/workspace/triangle_projector_five_root_query.py`,
SHA256 `ca578502aa0048428f2bb3a7a13b4d5fd969870adc6f82b1c92b7dbf804c7a54`.

All 257 classes from the point-independent preparation were retained.
There was no point-dependent pruning or numerical eigenvalue acceptance.
No optimizer was called. The replay did not regenerate the coefficient
tensors.

See [the preparation and normalization proof](triangle_projector_five_root_conditioning.md).
This result concerns the stated finite block family at one count point.
It does not establish a 99-vertex graph or resolve the Conway99 existence
question. The six-root family is a separate preparation.
