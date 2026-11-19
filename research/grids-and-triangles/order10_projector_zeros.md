# Principal projectors through order ten

The exact induced-type catalogue has 48,965 types through order ten.
The two principal-projector tests exclude only one: a nine-vertex rook
graph together with an isolated vertex. Thus this test adds no new
forced zero in the zero-grid count model.

## Exact test

For a graph with the target parameters, the adjacency eigenvalues are
14, 3, and -4. Both integer matrices

\[
P_-=27I-9A+J,\qquad P_+=44I+11A-2J
\]

are positive semidefinite. Their nonzero eigenvalues are respectively
63 and 77. Every induced adjacency matrix inherits the corresponding
principal-matrix inequalities.

For a real symmetric matrix $M$, compute $\det(tI+M)$. The matrix is
positive semidefinite exactly when all polynomial coefficients are
nonnegative. Necessity follows by multiplying the factors $t+\lambda_i$.
Conversely, a negative eigenvalue would give a positive root, impossible
for a monic polynomial with nonnegative coefficients. Integer
characteristic polynomials therefore give an exact sign test.

The [scanner](../../experiments/workspace/order10_projector_zeros.py)
uses FLINT integer matrices. It checks three explicit matrix controls
and both projector tests on all 512 induced subsets of the nine-rook.
It records a digest of every polynomial in catalogue order.

| Order | Positive definite for both | Singular and positive semidefinite | Excluded |
|---|---:|---:|---:|
| 0 through 8 | 1,224 | 0 | 0 |
| 9 | 5,310 | 1 | 0 |
| 10 | 42,428 | 1 | 1 |

The two singular types are the rook graph and the rook graph with one
pendant vertex. Their negative-eigenspace projector has nullity one;
their positive-eigenspace projector is positive definite.

The excluded type is the rook graph with an isolated vertex. Give each
rook vertex weight 2 and the isolated vertex weight -1. The quadratic
form for $27I-9B+J$ is $-8$, an explicit integer contradiction. This is
also implied by the familiar fact that every vertex outside an induced
rook graph has exactly one neighbor in it.

The scan does not test all higher-order moment inequalities, and it
does not decide the count model or graph existence.

## Replay

```sh
.venv/bin/python experiments/workspace/order10_projector_zeros.py \
  --output /tmp/order10-projector-zeros.json
```

This regenerates the catalogue before the exact scan. To reuse an
existing catalogue made by `subgraph_counts.build(10)`, pass
`--catalogue /absolute/path/to/catalogue.pickle`.

The saved [result](../../experiments/logs/moments-and-counts/order10-projector-zeros.json)
contains all exceptional graph rows, both characteristic polynomials,
the negative integer vector, and the complete outcome distribution.
