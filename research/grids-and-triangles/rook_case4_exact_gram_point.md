# Exact rational point for the case4 Gram equations

The complete 35-core case4 Gram system has a nonnegative rational solution.
The solution also satisfies every individual bound x_a<=1 and the 46 proved Gram zeros.
It is not a binary incidence design. Original-signature capacities, triple capacities,
exterior-row inequalities and coordinate covers are not claimed by this certificate.
Case4 and the graph problem remain open.

## Domain and result

The domain is the published complete list of 1,214 optional 35-core attachment columns.
Its 630 upper-triangular Gram equations are

```text
sum_a x_a h_a(i) h_a(j) = G_ij,  0<=i<=j<35.
```

The input was recovered from published native model Git blob
`89fece302243da184766735c7517aa67f00a0dbe`, whose raw SHA256 is
`a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476`.
Every column mask was reconstructed from its diagonal row memberships.
All630 pair supports were then rebuilt from those masks and compared exactly.
The recovered row-list SHA256 is
`c3480158f278c92413f662829d281520bd568ae7a3e84edc00b9edb43ccf29ef`.

The final common denominator is

```text
648602182798933000000000000.
```

The saved result contains all1,214 integer numerators. Exactly287 are positive.
None equals the denominator. All630 Gram rows, all1,214 nonnegativity and upper
bounds, all46 Gram zeros, and total mass64 pass exact integer checks.

## Reconstruction assumptions

The published original LP and row-loop records contained numerical proposals only.
No earlier exact rational point was claimed.

This reconstruction uses the positive support of row-loop round0, whose LP contained
the first two exterior-row cuts. The support rule retains values greater than1e-9.
The sole discarded nonzero value is column799 at1.049160758270773e-14.
Setting this coordinate and every other unselected coordinate to zero was an
explicit reconstruction choice. It was not a new theorem that those columns are
globally absent.

The selected287 columns avoid every one of the46 proved zeros.
Exact modular elimination over F65521 finds rank285 and a nonsingular285-by-285
minor, with determinant62807 modulo65521. This is a modular rank and a rational
independence certificate for that minor; no unsupported upper bound on rational
rank is needed.

The two free coordinates were set to

```text
x_1209 = 187003346196 / 1000000000000
x_1210 =   8082175193 / 1000000000000.
```

A single bounded BigInt Bareiss elimination solved the remaining minor.
Every division was exact. The solve completed in1.609seconds and used7,716,280
Bareiss divisions. The final check verifies every original row, so success does not
depend on modular consistency alone or on the accuracy of the numerical proposal.

A fresh verifier, without elimination or optimization, passed in0.175seconds.

## Consequence for integer Gram tests

Let v be any integer35-vector and k any integer. Since every h_a is integral,

```text
(v.h_a-k)(v.h_a-k-1) >= 0.
```

Multiply by the certified nonnegative x_a and sum. The Gram and diagonal equations,
together with total mass64, give

```text
v^T G v - (2k+1) sum_i v_i G_ii + 64 k(k+1) >= 0.
```

Thus every shifted integer quadratic test of this form passes for this core,
for all v and k. More generally, no linear combination of the Gram equations
whose value is nonnegative on every allowed attachment column can contradict
this certified point.

This does not cover higher moments that are absent from the Gram system,
binary selection constraints, shared exterior edges, or the later cover and
row-cut model. Those stronger conditions remain possible sources of an exclusion.

## Reproduction

Use the standalone Node/V8 source
`experiments/workspace/rook_case4_gram_support_reconstruction.js`.
It has no optimizer dependency. The input, preparation, full rational result
and fresh replay are separate JSON files under
`experiments/logs/session-ab2f/rook-case4-gram-support-*`.

```sh
node experiments/workspace/rook_case4_gram_support_reconstruction.js verify \
  experiments/logs/session-ab2f/rook-case4-gram-support-input.json \
  experiments/logs/session-ab2f/rook-case4-gram-support-result.json \
  /tmp/rook-case4-gram-replay.json
```

The source also provides prepare and solve modes. The recorded production solve
was run exactly once, after the coordinator read the source and independently
reproduced the preparation. No shell or numerical optimizer was used during
the outage recovery.
