# Complete five-root triangle-class scope

The census retains all 21 cap-valid five-vertex root types and every
triangle class meeting its root. It contains 1,296 classes, with maximum
matrix order 205 and 64,296 lower entries per kernel. It loads no count
point, creates no product tensor, and makes no graph-symmetry assumption.

The earlier five-root Q preparation included the eight root types
containing an internal triangle. Their 257 classes and every literal
representative agree exactly with the present census. The 13 other root
types contribute 1,039 additional classes and 59,437 lower entries.
These roots cannot be conditioned on an internal triangle, but they
still have the two vertex-derived triangle kernels and may be
conditioned on all five root vertex vectors.

A class is specified by a nonempty clique S in the root and the sorted
multiset of root-neighborhood masks of the 3-|S| outside triangle
vertices. Each outside mask contains S. The constructor retains a
class precisely when its literal root-plus-triangle graph satisfies
all visible common-neighbor caps. It records every attempted class
and the reason for every rejection. This gives the complete necessary
domain; cap compatibility is not a graph completion claim.

Root labels are retained. A single class has outside-label stabilizer
equal to the product of the factorials of repeated-mask multiplicities.
For a product with a and b outside slots, the conservative number of
partial-injection/cross-edge candidates is

    sum_q binom(a,q) binom(b,q) q! 2^((a-q)(b-q)).

The largest pair union has nine vertices. The total conservative bound
is 1,498,182 candidates. It is 108,481 for the eight old root domains
and 1,389,701 for the 13 added domains.

| Root type | Classes | Candidate bound |
| --- | ---: | ---: |
| 17 | 205 | 548990 |
| 18 | 159 | 305732 |
| 19 | 111 | 144308 |
| 20 | 67 | 51425 |
| 21 | 33 | 12036 |
| 22 | 113 | 133298 |
| 23 | 79 | 67095 |
| 24 | 72 | 48468 |
| 25 | 48 | 23348 |
| 26 | 56 | 40096 |
| 27 | 44 | 22931 |
| 28 | 26 | 7487 |
| 29 | 41 | 16278 |
| 30 | 51 | 23322 |
| 31 | 25 | 5286 |
| 32 | 34 | 12070 |
| 33 | 34 | 12070 |
| 34 | 28 | 7786 |
| 35 | 19 | 4015 |
| 36 | 35 | 10115 |
| 37 | 16 | 2026 |

The empty five-root has 205 classes. For each chosen root vertex,
the two outside masks may assign each of the other four root sites
to the first vertex, the second, or neither; interchanging the two
outside vertices gives (3^4+1)/2=41 possibilities. There are five
choices of the root vertex, giving 205.

## Bounded next preparation

The complete census took 0.620 seconds. Its SHA256 is
`09d44f9ae753f23b400d168486cd54ca813b12857536488a8b3064995c390efb`.

The proposed fixed seven-root chunks are:

- Chunk 0: 17, 28, 31, 34, 35, 36, 37; candidate bound 585705.
- Chunk 1: 18, 20, 21, 26, 29, 30, 32; candidate bound 460959.
- Chunk 2: 19, 22, 23, 24, 25, 27, 33; candidate bound 451518.

The authorized preparation limit is 60 seconds per chunk and
120 seconds overall. It will build Kminus, Kplus, N and Q together,
check that the eight old conditioned Q tensors are recovered exactly,
and form all-five-root-vertex Schur tensors only after exact positivity
and inverse checks for the root Grams. Every completed root and chunk
will be saved. No point query is part of this scope package.
