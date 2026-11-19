# Exact query of the two core-triangle conditioned blocks

The immutable order-ten count point with SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`
passes both prepared core-triangle conditioned projector blocks.

| Root type | Full class order | Exact rank | Exact nullity |
| --- | ---: | ---: | ---: |
| 14 | 41 | 24 | 17 |
| 15 | 34 | 18 | 16 |

The single query took 0.10285519999888493 seconds. Its result is
`experiments/logs/moments-and-counts/order10-triangle-projector-conditioned-query01.json`,
SHA256 `176a4f6974754833eca479cfee4a7d93442d8c6d462a105611f07fd0b092dff4`.
A separate cold process reproduced all matrix entries and characteristic
polynomial coefficients in 0.0482970259981812 seconds. It did not regenerate
the coefficient tensors.

## Certificate and scope

For each root type, the result stores the full symmetric integer matrix and
all coefficients of `det(t I + M)`. Every coefficient is nonnegative.
Since each matrix is real symmetric, any negative eigenvalue would give a
positive real root of this polynomial; nonnegative coefficients and a
positive leading coefficient forbid that root. The number of initial zero
coefficients gives the stated nullity.

The matrices are the complete 41-class and 34-class sums of the per-embedding
kernel `120 Q - q_T q_T^T`, where `T` is the fixed core triangle. Every
class is retained. Both fixed-triangle rows vanish exactly. The tensor has
1,456 lower entries and 11,211 nonzero induced-count coefficients. Its
construction and normalization are described in
[the preparation note](triangle_projector_core_triangle_conditioning.md).

The query uses Python integers for every count contraction. It uses exact
integer characteristic polynomials; there is no numerical eigenvalue
acceptance test. The negative-vector and primitive induced-form branches
were checked on two indefinite toy matrices, including a zero-diagonal
case. Neither branch was needed for this point.

The constructor had 19 small-host controls. A separate source, which does
not import the constructor, also checked six ten-vertex hosts. For each
host it directly enumerated labelled root embeddings and ordered triangle
pairs, then compared both matrices with the sum over all 848 induced
subsets of orders 4 through 10. These controls test the coefficient
normalization, including the same-class factor of two.

This result establishes positive semidefiniteness only for these two
specified conditioned blocks at this count point. It does not construct a
99-vertex graph or prove feasibility of every order-ten constraint.
The original Conway99 existence question remains open in this work.

## Reproduction

From the repository root, run the source with the installed `python-flint`
dependency:

```sh
python experiments/workspace/triangle_projector_conditioned_query.py replay \
  --preparation experiments/logs/moments-and-counts/triangle-projector-conditioned-preparation01 \
  --point experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json \
  --result experiments/logs/moments-and-counts/order10-triangle-projector-conditioned-query01.json \
  --output /tmp/conditioned-triangle-replay.json
```

The replay checks all bound input hashes and requires a fresh output path.
It accepts the saved exact certificate without another count query,
optimizer call, or tensor generation.
