# Exact local moment distributions for all 33 small six-root models

The immutable 48-cut count point passes every complete high-mask presence moment model whose structural maximum population is at most four. The new calculation covers 32 roots; the previously published root-49 certificate covers the remaining root. Together they give nonnegative integer weights on all 1,115 labelled structural atoms and satisfy all 511 root-orbit equations.

This is a finite local moment result. It neither constructs an \(\operatorname{srg}(99,14,1,2)\) nor proves that the count point extends to one.

## New 32-root result

The single authorized BigInt evaluation finished in 1.099 seconds with status EXACT_ALL_SMALL_ROOT_MOMENT_DISTRIBUTIONS.

All 1,035 weights are retained in the result: 954 are positive, 81 are zero, and none is negative. All 1,035 individual presence moment equations and 492 quotient equations hold exactly. Root type 99 has zero root mass and zero moments. Each of the other 31 roots has positive mass.

A separate artifact verifier passed in 0.108 seconds. It does not import the query or use its Möbius inversion. It checks the supplied weights directly against every induced-count form and moment equation, reconstructs all 2,290 alternative product partitions, and repeats the literal supported/zero domain census. That census checks 4,975 degree-at-most-four monomials, 3,940 structural zeros, and 3,987 five-class exclusions. The verifier uses the hash-bound preparation for product coefficients and automorphism factors; it does not claim an independent regeneration of the global tensor cache.

| Root type | Labelled root mass | Positive weights | Zero weights | Reduced probability denominator |
| ---: | ---: | ---: | ---: | ---: |
| 43 | 7983360 | 1 | 0 | 1 |
| 52 | 6819120 | 65 | 0 | 6819120 |
| 53 | 1330560 | 1 | 0 | 1 |
| 59 | 1330560 | 16 | 0 | 221760 |
| 62 | 1663200 | 34 | 4 | 831600 |
| 63 | 1363824 | 74 | 0 | 1363824 |
| 69 | 5455296 | 134 | 0 | 5455296 |
| 70 | 1496880 | 24 | 1 | 1496880 |
| 71 | 665280 | 16 | 0 | 332640 |
| 72 | 166320 | 1 | 0 | 1 |
| 74 | 1513512 | 62 | 3 | 1513512 |
| 76 | 681912 | 25 | 8 | 681912 |
| 77 | 1513512 | 80 | 6 | 1513512 |
| 79 | 166320 | 7 | 2 | 1540 |
| 80 | 1846152 | 110 | 24 | 1846152 |
| 82 | 1363824 | 84 | 12 | 1363824 |
| 83 | 4390848 | 64 | 0 | 4390848 |
| 84 | 1197504 | 37 | 3 | 1197504 |
| 85 | 166320 | 9 | 0 | 27720 |
| 86 | 1363824 | 21 | 0 | 681912 |
| 87 | 166320 | 9 | 0 | 27720 |
| 88 | 149688 | 6 | 2 | 24948 |
| 89 | 299376 | 17 | 0 | 149688 |
| 90 | 166320 | 16 | 12 | 83160 |
| 92 | 149688 | 8 | 0 | 1386 |
| 93 | 316008 | 25 | 0 | 158004 |
| 94 | 16632 | 2 | 3 | 154 |
| 95 | 16632 | 3 | 0 | 154 |
| 96 | 266112 | 1 | 0 | 1 |
| 97 | 133056 | 1 | 0 | 1 |
| 98 | 16632 | 1 | 0 | 1 |
| 99 | 0 | 0 | 1 | 0 |

The last column is the common denominator after dividing all weights by the labelled root mass and cancelling their common gcd. A zero denotes the zero-mass model, for which no probability normalization is defined.

## What is proved

For each root \(H\), every high neighborhood mask has size at least three and therefore contains at most one exterior vertex. The complete structural atom domain \(\Omega_H\) consists of all subsets of high masks compatible with the visible common-neighbor caps. In these 33 cases, every five-mask subset violates a cap, so every atom has size at most four.

The preparation reconstructs every required moment \(m_T\) from exact induced graph counts through order ten. The full finite distribution is uniquely determined by
\[
w_A=\sum_{\substack{T\in\Omega_H\\T\supseteq A}}
(-1)^{|T|-|A|}m_T.
\]
The saved weights satisfy \(w_A\ge0\) and
\[
m_T=\sum_{\substack{A\in\Omega_H\\A\supseteq T}}w_A
\]
for every supported \(T\). Every unsupported monomial is structurally zero.

Consequently every polynomial depending only on these high-mask presence variables and nonnegative on \(\Omega_H\) has nonnegative expectation at this point. Since all atoms have size at most four, its restriction to the domain is determined by the supplied moments. Testing further inequalities within these same presence-only local models cannot separate the current point.

The model does not prescribe a joint induced graph among all selected high vertices, the remaining low-neighborhood exterior vertices, or consistency of full local realizations across different roots. Stronger structural domains or moments can still impose additional conditions.

The published root-49 result adds 80 atoms, 19 quotient equations, 74 positive weights, and six zero weights. The combined 33-root totals are therefore 1,115 atoms, 511 quotient equations, 1,028 positive weights, and 87 zero weights.

## Binding and replay

The count point is the published file
prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json,
Git blob c881dae3be05cf289fcc45a99d72c405ac863c46,
SHA-256 0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df.

| Artifact | Git blob |
| --- | --- |
| Preparation manifest | 968f9da6554f71ca13c3cb177f0b7b5a25bd40a4 |
| Generic preparation/query source | 34085dd6833ab816968ede0ba4637e44713b37fc |
| Exact preparation | 537b722f2dd4f964c5fa053d5398e41c60b4ed9d |
| Full 32-root result | c87f5b759a000f0fa2a8ad197bf6a82b9fc538c4 |
| Separate artifact verifier | f56bb705385d64fae612b4dd03c5d1c72699e171 |
| Artifact replay result | f1ab196c6a140e31d3a69c6d51007d33877d91ac |
| Published root-49 result | 1b80dd8bc11ac4e396d987431fd93e56f9a04eb1 |

The independent arithmetic replay uses only the preparation, result, and immutable count point:

~~~sh
node experiments/workspace/small_roots_packing_moment_recovery_replay.js \
  experiments/logs/moments-and-counts/order10-small-roots-packing-moment-recovery-preparation.json \
  experiments/logs/moments-and-counts/order10-small-roots-packing-moment-recovery-result.json \
  experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json
~~~

The Node entry point verifies the exact Git blob of each input before computing. No optimizer, new tensor generation, or global catalogue reconstruction is needed.
