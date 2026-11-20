# Conditioning the triangle projector on a root triangle

## Necessary matrix

Let \(Q\) be the triangle-index projector scaled by 210. It satisfies

\[
Q\succeq0,\qquad Q^2=210Q,\qquad Q_{T,T}=120.
\]

Fix a triangle \(T\). The Schur complement of its diagonal entry gives

\[
K_T(U,V)=120Q_{U,V}-Q_{T,U}Q_{T,V},\qquad K_T\succeq0.
\]

Writing \(q=Qe_T\), this is \(K_T=120Q-qq^{\mathsf T}\). Since
\(Qq=210q\) and \(q^{\mathsf T}q=25200\),

\[
K_T^2=25200K_T,\qquad \operatorname{rank}(K_T)=131.
\]

The row and column indexed by \(T\) vanish.

The present family uses the two four-vertex roots that contain a triangle: type 14, a triangle with an isolated vertex, and type 15, a triangle with a pendant vertex. Each root has a unique triangle. The selected triangle therefore moves with each labelled root embedding; no graph automorphism assumption is used.

## What the conditioning adds

For a root embedding, let \(n_C\) be the number of triangles in full class \(C\), and let

\[
M_{C,D}=\sum_{U\in C,V\in D}Q_{U,V}.
\]

The value \(v_C=Q_{T,U}\) is constant within a class. The class records the triangle's intersection with the root and every outside vertex's root-neighborhood mask, which determine its overlap and cross edges with \(T\).

For each embedding,

\[
120M-\operatorname{diag}(v)\,nn^{\mathsf T}\operatorname{diag}(v)\succeq0.
\]

Summing over root embeddings gives the new necessary condition

\[
120\sum M-\operatorname{diag}(v)
       \left(\sum nn^{\mathsf T}\right)\operatorname{diag}(v)\succeq0.
\]

The subtraction uses ordinary triangle-class count second moments. These distinguish counts of triangle pairs from the weighted sums already present in the unconditioned \(Q\) blocks.

Conditioning only after averaging would subtract a product of mean counts. The difference is the class-count covariance matrix under a diagonal congruence, so the per-embedding condition is stronger. It requires no division by the number of root embeddings and remains defined when that count is zero.

For the triangle-plus-isolate root, merely adding the fixed triangle as an extra averaged row is redundant. If \(z_U\) are Gram vectors for \(Q\), then the incidence identities give

\[
\sum_{U\cap H=\varnothing}z_U=2z_T.
\]

That identity follows by inclusion-exclusion from \(\sum_{U\ni v}z_U=0\) and \(\sum_Uz_U=0\). It does not remove the per-embedding second-moment subtraction above.

This establishes a strengthening of the tested matrix conditions at the abstract moment level. The preparation does not claim that it separates the current count point or that it is independent of every other available flag inequality.

## Complete finite model

The frozen full-class domains are retained unchanged:

| Root type | Full triangle classes | Lower entries |
|---:|---:|---:|
| 14 | 41 | 861 |
| 15 | 34 | 595 |
| Total | 75 | 1,456 |

Classes include triangles meeting the root in zero, one, two or three vertices whenever the literal cap constraints allow them. The fixed-triangle classes are retained as zero rows.

Each product involves the four roots and two triangles, hence at most ten vertices. The coefficients are reconstructed directly from literal induced graphs. For each unlabelled triangle pair and each labelled root map, the constructor adds

\[
120Q(U,V)-Q(T,U)Q(T,V).
\]

An unordered distinct pair contributes once to an off-diagonal entry and twice to a class diagonal. Diagonal pairs contribute once. The resulting coefficient multiplies the unlabelled induced count of the union graph. There is no further automorphism factor or free-label divisor.

No aggregated parent \(Q\) tensor is divided or used to infer the new coefficients.

## Verification and workload

The point-independent preparation finished in 5.296 seconds. It contains 11,211 nonzero coefficients, from 18,700 labelled decompositions. The constructor checked 37,400 literal cross values against their class values. The fixed-triangle rows vanish coefficientwise.

Nineteen small-host controls compare the induced-subset contraction with independently ordered triangle-pair sums. A separate source, which imports no tensor constructor, checks six ten-vertex hosts. It counts every induced subset on four through ten vertices and verifies both full matrices by direct labelled-root and ordered-pair enumeration. Those controls finished in 8.138 seconds.

The source and model are frozen. No count point was loaded during preparation.

## Gated query

The separate query driver is restricted to the immutable 48-cut count point and this exact two-block model. It uses unbounded integer contraction and exact characteristic polynomials. If a block is not positive semidefinite, it reconstructs an integer negative vector and an exact induced-count inequality. Its cold replay checks those same certificates without regenerating tensors.

The proposed point query is one run with a 30-second limit, followed by a separate exact replay. It requires the coordinator's gate. No query result is part of this preparation package.
