# Complementary triangle-projector result

The immutable integer count point with SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`
passes all nine full complementary triangle-projector blocks.

| Root type | Block order | Exact nullity |
| --- | ---: | ---: |
| 8 | 107 | 0 |
| 9 | 93 | 0 |
| 10 | 72 | 0 |
| 11 | 49 | 0 |
| 12 | 79 | 0 |
| 13 | 58 | 0 |
| 14 | 41 | 5 |
| 15 | 34 | 4 |
| 16 | 41 | 2 |

The single exact query took 0.5266811590045108 seconds. A cold replay took
0.3966376219977974 seconds and reproduced all first moments, all matrix
entries, and every coefficient of det(tI+M). Every coefficient is
nonnegative. Symmetry makes this a certificate of positive semidefiniteness.

The full result is
`experiments/logs/moments-and-counts/order10-triangle-projector-complementary-query01.json`,
SHA256 `3cc32f16d5c0a3bd1b0848ed4fb5b7c0b2981a0b487f187099168589a92022fb`.
The preparation retains all 574 classes and adds only their exact first
moments to the frozen full Q tensor. See
[the normalization proof](triangle_projector_complementary.md).

No optimizer or new pair-product enumeration was used. This certifies the
listed finite matrices at one count point and gives no graph-existence
conclusion.
