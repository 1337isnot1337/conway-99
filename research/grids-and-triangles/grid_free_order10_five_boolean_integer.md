# Five-class integer sums at the current count point

The current 48-cut integer count point passes every tested integer-shift
inequality for a signed sum of five distinct high-mask classes over a
six-vertex root. The complete calculation covers 72,699,792 signed sums
and every integer shift. It finds no new inequality against the point.

This is a finite support and coefficient family. It does not cover
arbitrary integer coefficient vectors or construct a graph.

## The inequality and the infinite shift family

For a fixed labelled root embedding, each high-mask count `X_i` is zero
or one. Fix five distinct classes and signs `s_i` in `{−1,1}`. Their
sum `L=sum s_i X_i` is an integer. Therefore, for every integer `k`,

\[
(L-k)(L-k-1)\geq0.
\]

Let `g` count labelled root embeddings, and let `p` and `q` be the sums
of `L` and `L` squared over those embeddings. The required expression is

\[
F(k)=q-(2k+1)p+k(k+1)g.
\]

When `g>0`,

\[
F(k+1)-F(k)=2((k+1)g-p).
\]

Thus `floor(p/g)` is a minimizing integer shift. If `p/g` is an integer,
the preceding shift ties. Evaluating this exact minimum covers every
integer shift, including negative shifts. Global negation of the signs
maps `k` to `-k-1`, so the first sign can be fixed to one.

The [four-class atom certificate](grid_free_order10_four_boolean_atoms.md)
already supplies nonnegative joint marginals for any four high classes
at this point. Consequently every pointwise nonnegative quadratic using
only those four classes passes. The present test adds five-class support.

## Coverage and arithmetic

All 62 six-vertex roots and all 829 high masks remain in the domain.
There are 4,543,737 five-subsets. The sixteen sign choices for each
subset give 72,699,792 exact minima.

The scanner extracts the existing scalar six-root matrices. Their
constant and high-mask domains are checked against the complete frozen
domain record. Every matrix entry is contracted using Python integers.
The diagonal of each high-mask flag must equal its first moment exactly.
Each first moment must lie between zero and the labelled root count.

For each nonconstant block, the scanner checks that 256 times its largest
entry fits in a signed 64-bit integer. This bounds every vectorized
intermediate: `|p|<=5B`, `|q|<=25B`, the linear term is at most `55B`,
and the constant term is at most `30B`. The entire expression is bounded
by `110B`. If a root count is zero, the whole exact matrix must be zero
before the corresponding family is recorded as zero.

The source does not use a numerical eigensystem or optimizer. A negative
instance would be expanded again through the cached products using
Python integers. Its induced-count form would still require a separate
literal product replay before use in an optimization model.

## Result

| Quantity | Value |
|---|---:|
| Completed roots | 62 |
| Five-subsets | 4,543,737 |
| Signed sums, up to global negation | 72,699,792 |
| Negative minima | 0 |
| Zero minima | 41,887 |
| Scan time | 5.531 seconds |
| Total time | 6.300 seconds |
| Peak RSS | 163,572 KiB |

No timeout or error occurred. The independent source review checks the
minimizer, normalization, exact contraction, and overflow bounds. Its
small controls include 384 synthetic signed tests, 195 negative examples,
and 56 integer-mean ties. These controls are separate from the completed
count scan.

## Files

- Source: `experiments/workspace/grid_free_order10_five_boolean_integer.py`.
- Preparation: `experiments/logs/moments-and-counts/order10-five-boolean-integer-preparation.json`.
- Result: `experiments/logs/moments-and-counts/order10-five-boolean-integer-scan01.json`.
- Independent review: `experiments/logs/moments-and-counts/order10-five-boolean-integer-independent-review.json`.

The point SHA-256 is
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
The result SHA-256 is
`68a5a4bce81c0f66b699193c06963b2c1f4c350865bf79e4ab868d6cd7ddff15`.

```sh
.venv/bin/python experiments/workspace/grid_free_order10_five_boolean_integer.py \
  --preparation experiments/logs/moments-and-counts/order10-five-boolean-integer-preparation.json \
  --output /tmp/order10-five-boolean-integer-replay.json --seconds 60
```
