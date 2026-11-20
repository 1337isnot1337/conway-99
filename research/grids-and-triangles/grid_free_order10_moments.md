# Exact PSD separators for the free order-ten proposal

The numerical free-prefix proposal from
[`grid_free_order10_scaled.md`](grid_free_order10_scaled.md) violates four
of the existing order-nine moment blocks. Each violation has an integer
vector and an exact negative rational evaluation. These are four reusable
linear inequalities in the 58 old coordinates.

This rejects the saved proposal. It does not show that the combined count
and moment constraints are infeasible.

## Results

All 1,416 cached blocks were scanned, using the same ordinary, induced,
spectral, and Schur caches as the earlier finite PSD certificates.

| Cache | Block index | Root type | Root graph | Matrix order | Normalized numerical minimum |
| --- | ---: | ---: | --- | ---: | ---: |
| `moments-3-3-512.pickle` | 1 | 5 | edge and isolated vertex | 9 | -0.328229 |
| `induced-moments-3-3-512.pickle` | 0 | 4 | three independent vertices | 18 | -0.019996 |
| `induced-moments-3-3-512.pickle` | 1 | 5 | edge and isolated vertex | 9 | -0.420570 |
| `induced-moments-5-2-512.pickle` | 12 | 29 | four-cycle and isolated vertex | 41 | -0.072017 |

The integer vectors have maximum absolute entry 256. Their supports have
sizes 8, 18, 8, and 33. The exact primitive linear forms and their exact
negative rational values are stored in the certificate; none of these
four sign decisions depends on an eigenvalue tolerance.

Two additional numerical negatives occurred in
`induced-schur-7.pickle`, at indices 409 and 415. Their normalized values
were approximately `-3.58e-7` and `-4.77e-7`. No tested integer direction
gave an exact negative value for these two blocks. They are explicitly
unconfirmed and supply no cut or exclusion.

No exact negative direction was found for the other blocks. This is not
a positive-semidefiniteness certificate for those blocks.

## Exact contraction and point convention

The saved decimal values are read back as binary floating-point numbers.
Each is then interpreted as its exact dyadic rational, with no new
rounding. The result records a common denominator and all 58 integer
numerators. This identifies the proposal being separated exactly; it
does not certify that proposal satisfies the count constraints.

For a cached matrix `M(x)` and an integer vector `v`, the verifier computes

\[
v^TM(x)v=\sum_i v_i^2M_{ii}(x)
        +2\sum_{j<i}v_iv_jM_{ij}(x).
\]

It contracts these integer weights through the cached sparse tensor and
then through the exact ordinary or induced embedding forms. All products
used for the resulting 58 coefficients use Python/object integers.
Division by a positive gcd produces the primitive inequality `L(x)>=0`.
Its value at the exact dyadic proposal is a strictly negative fraction.

As a separate control, all four primitive forms are nonnegative at the
published order-nine point, whose cached moment matrices already have
exact PSD certificates. Their values there are respectively
2,508,090,795; 259,166,259; 292,434,437; and 12,217,835,921.

## Reproduction and scope

The scanner is
[`grid_free_order10_moments.py`](../../experiments/workspace/grid_free_order10_moments.py).
The complete result is
[`grid-free-order10-moments.json`](../../experiments/logs/moments-and-counts/grid-free-order10-moments.json).
It binds the unchanged proposal and all cache files by SHA256 and includes
every accepted integer vector, primitive cut, and exact evaluation.

The exact cut replay does not recompute eigenvectors:

```sh
python experiments/workspace/grid_free_order10_moments.py replay experiments/logs/moments-and-counts/grid-free-order10-moments.json
```

The saved replay passed for all four cuts. The full scan took about
2.16 seconds and peaked near 66 MiB RSS. It read existing caches only;
no LP was run and no new moment block was generated. The original
free-prefix proposal remains unchanged.
