# Triangle kernels over every five-vertex root

This preparation retains every triangle class that meets a labelled five-vertex root, for all 21 catalogue roots. There are 1,296 classes. No count point was loaded during construction, and no optimizer was called.

The older five-root package covered the eight roots containing a triangle. The present package adds the other 13 roots and retains the older classes unchanged. It constructs the two nonconstant triangle projectors, the scalar class-count Gram matrix, the old triangle-kernel projector, and both vertex-conditioned projector matrices.

## Classes and exact normalization

A class consists of the nonempty set of root vertices in a triangle, together with the sorted multiset of root-neighborhood masks of the remaining triangle vertices. The complete class domain is the frozen ledger in [triangle_all_five_root_scope.md](triangle_all_five_root_scope.md). Every literal extension passes the visible common-neighbor caps. No class is removed because its current count is zero.

Each triangle has at most two vertices outside the root. The union of the root and two class triangles therefore has at most nine vertices. Products are obtained from all partial identifications of the outside vertices, retaining every prescribed edge and nonedge and every admissible remaining edge choice.

Let the outside-mask multiplicities of a class be \(m_1,m_2,\ldots\). Its labelled extension function is the actual triangle-class count multiplied by the stabilizer \(\prod_i m_i!\). For each ordered class pair, the constructor sums all partial identifications and literal completions before dividing each induced-type coefficient by the product of these two stabilizers. Every division is checked exactly. This handles repeated zero and repeated nonzero masks, as well as coincident triangles.

The coefficient of a literal labelled union is its full unrooted automorphism order times the required kernel entry. This counts labelled root embeddings. There is no root-automorphism divisor. The independent host controls instead enumerate labelled root embeddings and actual ordered triangle pairs directly.

## Four basic matrices

Let \(B\) be the point-triangle incidence matrix and \(A\) the adjacency matrix of a hypothetical SRG(99,14,1,2). The vertex projectors in integer normalization are
\[
U_- = 27I-9A+J,\qquad U_+=44I+11A-2J.
\]

The triangle kernels are \(K_-=B^TU_-B/9\) and \(K_+=B^TU_+B\). Their entries for equal triangles, triangles intersecting in one point, and disjoint triangles with \(e\) cross edges are respectively:

| Pair type | \(K_-\) | \(K_+\) | \(Q\) |
|---|---:|---:|---:|
| Equal | 4 | 180 | 120 |
| One common vertex | 0 | 70 | -20 |
| Disjoint | \(1-e\) | \(11e-18\) | \(7e-6\) |

Here \(Q\) is 210 times the projector onto the kernel of \(B\). All three kernels are positive semidefinite. \(N\) is the scalar Gram matrix of the triangle-class counts.

For class first moments \(p\), the constructor checks the exact coefficient identity
\[
11M_Q+110M_-+3M_++10N=2310\operatorname{diag}(p).
\]
It checks all 108,612 nonzero coefficient positions involved. The old eight conditioned \(Q\) tensors are recovered from the new unconditioned \(Q\) and \(N\) tensors, with every coefficient equal to the old frozen model.

## Conditioning on all five root vertices

For either \(U\), its five-root principal matrix \(G\) is checked positive definite by all five leading principal minors before inversion. The exact inverse is stored as \(P/d\) and verified by \(GP=dI\).

For a triangle in class \(C\), the root-to-triangle vector \(c_C\) is constant on the class. Its entries are
\[
c_{-,C}(i)=27\,1_{i\in T}-9|N(i)\cap T|+3,\qquad
c_{+,C}(i)=44\,1_{i\in T}+11|N(i)\cap T|-6.
\]

Projecting the triangle vectors off the root-vertex span gives the necessary matrices
\[
M_- - \frac{1}{9}\bigl(c_{-,C}^{T}G_-^{-1}c_{-,D}\bigr)_{C,D}\circ N,
\qquad
M_+ - \bigl(c_{+,C}^{T}G_+^{-1}c_{+,D}\bigr)_{C,D}\circ N.
\]

The product with \(N\) is entrywise. It is the average of the per-embedding Schur correction. It cannot be replaced by the product of class first moments. Positive denominators are cleared, followed by a common positive gcd reduction.

Every triangle contained entirely in the root has a zero row in both Schur matrices. This is checked coefficientwise. The root point-star vectors are kernels of \(Q\) and the two Schur matrices at a valid count point.

The constant class vector is not assumed to be a kernel: these domains omit triangles disjoint from the root. This differs from the earlier complete four-root triangle domain.

## Construction and controls

The preparation used three fixed chunks of seven roots. Each chunk had a 60-second limit and the whole preparation had a 120-second limit. The chunks finished in 22.474, 20.252 and 23.768 seconds. The complete preparation finished in 69.113 seconds.

The resulting model has 21 blocks in each of six families, 64,296 lower-triangular positions per family, and these sparse coefficient counts:

| Family | Nonzero induced-type coefficients |
|---|---:|
| \(K_-\) | 56,506 |
| \(K_+\) | 108,612 |
| \(N\) | 108,612 |
| \(Q\) | 108,612 |
| Root-conditioned \(K_-\) | 108,018 |
| Root-conditioned \(K_+\) | 108,273 |

All 434,448 stabilizer divisions, 210 positive root-Gram leading minors, and 1,050 inverse identities passed. The 472 direct host controls use 86,610 labelled root embeddings and 420,358 actual ordered triangle pairs. They include 243 nine-vertex hosts. Every class and every root is retained in the reusable cache.

The constructor is experiments/workspace/triangle_all_five_vertex_projectors.py. Its source SHA256 is 88fd70d5badf3b1cdf860123a066e870fb982b9377aa10de2384aeab029a89ba. The preparation is under experiments/logs/moments-and-counts/triangle-all-five-vertex-preparation01. Its full raw model SHA256 is 88430ae5002742a0551c555a0798c07684c730932ee1d546864bf170105b76bd.

## Prepared point check

The separate triangle_all_five_vertex_query.py driver binds the immutable integer count point and all source/model hashes. It contracts with Python integers, checks all 64,296 partition entries at the point, and computes \(\det(tI+M)\) exactly for all 126 matrices. A real symmetric matrix is positive semidefinite exactly when all coefficients of this polynomial are nonnegative.

Any failed matrix must produce an exact integer negative vector and an induced-count form with strictly negative value. That form requires a separate fresh literal-product reconstruction before optimizer use. A timeout or failed assertion preserves an incomplete result and does not certify the unvisited family.

The cold replay recomputes every matrix and characteristic polynomial from the frozen tensors. It does not regenerate or independently verify the product tensors. The direct host controls and source reviews have that separate role.

No point-query outcome is part of this preparation note. Passing these matrices would establish only feasibility for the listed finite necessary conditions.

