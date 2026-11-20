# The zero-grid point also passes all cached projector blocks

The exact integer count point in
[the original zero-grid certificate](grid_free_order_nine.md) also satisfies
the 832 cached root-conditioned spectral and Schur projector blocks.
Together with the original 584 ordinary and induced moment blocks, this
gives 1,416 verified blocks at the same point. Its grid and broken-rook
counts remain zero.

This is feasibility of the stated finite relaxation. It does not construct
a graph or certify every possible order-nine inequality. The earlier
certificate and its sources remain unchanged.

## The additional matrices

For a hypothetical adjacency matrix `A`, the matrices

\[
Q_-=27I-9A+J,\qquad Q_+=44I+11A-2J
\]

are positive semidefinite. Their nonzero eigenvalues are respectively
63 and 77. Both annihilate the constant vector. They satisfy

\[
Q_-(A+4I)=0,\qquad Q_+(A-3I)=0.
\]

Fix a labelled seven-vertex root. For each allowed outside neighborhood
mask, take the indicator vector of that full neighborhood class. The
spectral block uses these vectors and the seven individual root vectors.
Sum their Gram matrices under `Q_-` or `Q_+` over all embeddings of the root.
This gives a necessary PSD matrix whose entries use induced counts of at
most nine vertices.

The Schur block first removes the span of the seven root vectors from the
projector Gram form. The root Gram matrix depends only on the fixed root
type. The construction uses its exact rational inverse and a positive
common denominator. An actual root embedding has a positive definite root
Gram matrix, so the residual form is PSD. Root types with no embedding
contribute zero. The cached construction is `spectral_flags.py`.

There are 208 root types and two projectors for each. The spectral and
Schur caches therefore contain 416 blocks each. Their largest matrix
orders are 135 and 128.

## Eight explicit kernels and a positive quotient

Each matrix has eight exact kernel vectors at this count point. In the
spectral blocks, use the constant vector and the coordinate expressions
of `(A+4I)e_j` or `(A-3I)e_j`, for the seven root vertices `j`.
On a neighborhood-class coordinate with mask `s`, these eight entries are

\[
(1,s_0,s_1,\ldots,s_6).
\]

On the root coordinates, the last seven columns are `B+4I` for the
negative projector and `B-3I` for the positive projector. Here `B` is the
root adjacency matrix. In the Schur blocks, only the neighborhood-class
coordinates remain, so the displayed mask rows give the full kernel
matrix `K`.

The verifier checks `MK=0` using integer arithmetic for every block.
The class masks zero and the seven singleton masks give eight pivot rows
of `K` with determinant one. Thus `K` has rank eight.

Delete those eight rows and columns from `M`, obtaining a principal
matrix `N`. Every vector can be changed by a vector in `ker(M)` so that
its pivot coordinates vanish. Consequently `M` is PSD if and only if
`N` is PSD. The verifier certifies each nonempty `N` as positive definite.

For each `N`, the saved upper-triangular integer matrix `T` has nonzero
diagonal. Exact multiplication gives `D=T^T N T`, and every row satisfies

\[
D_{ii}-\sum_{j\ne i}|D_{ij}|>0.
\]

Thus `D` is positive definite by strict diagonal dominance, and invertible
congruence proves the same for `N`. The largest reduced order is 127.
The eight exhibited kernels are therefore the full kernel in every block.

Floating-point Cholesky proposes `T` during generation. The accepted
certificates and their replay use exact integer equalities and strict
integer inequalities. The numerical screen alone is retained as a probe,
not as a proof.

## Integer construction and file binding

The point uses the same induced embedding normalization as the original
certificate: each induced unlabelled count is multiplied by the graph's
automorphism order. Signed projector coefficients require an absolute
overflow bound. The verifier computes every coefficient row's sum of
absolute values with Python integers. It uses a fixed-width sparse product
only when the bound is below `2^63`; otherwise it uses Python integer sums.
Kernel and congruence products always use arbitrary-precision integers.

An independent construction audit checks normalization and the quotient
argument. It also verifies all 416 seven-root projector matrices as
positive definite and checks the inverse-product arithmetic used when
the Schur cache was generated. Its largest second-product bound is
37,226,952, below the signed 64-bit limit. At the actual count point,
391 final block products require the arbitrary-precision fallback; the
largest absolute accumulation bound is 7,805,674,304,074,973,652,480.

The certificate binds each cache by SHA-256 and each reduced integer
matrix by SHA-256. It stores the original integer point, the kernel pivot
rows, and every integer congruence. The canonical gzip file is deterministic.
Generation completed and then reread and verified all 832 saved blocks.

## Replay

```sh
make verify-grid-free-projectors
```

The underlying command is

```sh
python experiments/workspace/grid_free_projector_certificate.py \
  --certificate experiments/logs/moments-and-counts/grid-free-projector-certificate.json.gz
```

Add `--write` to regenerate congruences. Replay performs no optimization
and does not search for a graph. The original count equations and 584-block
certificate remain available through `make verify-grid-free-relaxation`.
