# A projector indexed by triangles

## Algebra

In an SRG(99,14,1,2), each vertex lies in seven triangles and each edge lies in one triangle. There are 231 triangles. Let \(B\) be the 99 by 231 point-triangle incidence matrix. Then

\[
BB^{\mathsf T}=7I+A.
\]

Using \(A^2=12I-A+2J\) and \(AJ=14J\) gives

\[
(7I+A)^{-1}=\frac{6I-A}{30}+\frac{J}{315}.
\]

In particular, \(B\) has rank 99. The matrix

\[
Q=210\bigl(I-B^{\mathsf T}(7I+A)^{-1}B\bigr)
\]

is positive semidefinite. The matrix in parentheses is the orthogonal projector onto \(\ker B\), of rank \(231-99=132\).

Expanding the inverse gives

\[
Q=210I-42B^{\mathsf T}B+7B^{\mathsf T}AB-6J.
\]

For two triangles \(T,U\), its entries are

\[
Q_{T,U}=
\begin{cases}
120,&T=U,\\
-20,&|T\cap U|=1,\\
7e(T,U)-6,&T\cap U=\varnothing.
\end{cases}
\]

Distinct triangles cannot share two vertices. When they share one vertex, \(1_T^{\mathsf T}A1_U=4\): an edge between the other vertices would give an adjacent pair two common neighbors. For disjoint triangles, their cross edges form a matching, so \(e(T,U)\) is between 0 and 3.

If \(L\) is the triangle-intersection adjacency matrix, then \(B^{\mathsf T}B=3I+L\) and

\[
B^{\mathsf T}AB=L^2-L-12I,\qquad
Q=7L^2-49L-6J.
\]

The source checks these coefficient identities in the exact adjacency algebra, the entry values, and the trace \(120\cdot231=210\cdot132\).

## Four-root classes

Fix an injectively labelled induced four-vertex root \(H\). Classify every triangle disjoint from the root by the sorted multiset of the three root-neighborhood masks of its vertices.

The three masks are pairwise disjoint. Otherwise a root vertex would be a second common neighbor of two adjacent triangle vertices. Only the zero mask may repeat. Retain every mask size, including zero, one and two.

Let \(Y_H\) be the matrix whose column for a class is its indicator vector on the triangles. Then

\[
Y_H^{\mathsf T}QY_H\succeq0.
\]

Summing this matrix over all labelled embeddings of \(H\) preserves positive semidefiniteness. Its entries are linear induced-count forms through order ten: one triangle uses seven total vertices, two intersecting triangles use nine, and two disjoint triangles use ten.

The independent census enumerates all 64 labelled four-vertex graphs, reduces the cap-compatible ones under all 24 root permutations, and checks every sorted disjoint mask triple. There are nine root types, 352 classes and 7,524 lower-triangular entries.

| Canonical root code | Root adjacency rows | Classes |
|---:|---|---:|
| 0 | 0,0,0,0 | 51 |
| 1 | 2,1,0,0 | 51 |
| 3 | 6,1,1,0 | 44 |
| 7 | 14,1,1,1 | 33 |
| 11 | 6,5,3,0 | 27 |
| 12 | 8,4,2,1 | 51 |
| 13 | 10,5,2,1 | 39 |
| 15 | 14,5,3,1 | 23 |
| 30 | 12,12,3,3 | 33 |

These codes are the minimum six-bit edge codes under root relabeling, not global catalogue identifiers.

## Normalization by direct induced-subset counting

The proposed direct construction avoids a free-label divisor. For each literal catalogue graph \(F\) on seven, nine or ten vertices, enumerate actual triangle sets \(T\), or unordered pairs of distinct triangle sets \(T,U\). Require their complement \(R\) in \(V(F)\) to have four vertices, and enumerate every root-labelled isomorphism \(H\to F[R]\).

For a single triangle add 120 to its class diagonal. For an unordered distinct pair, compute \(q=-20\) for one-point overlap or \(q=7e(T,U)-6\) for disjoint triangles. Add \(q\) to the off-diagonal lower entry when the classes differ, and \(2q\) to the diagonal when they agree.

The coefficient is a count of these actual decompositions inside one unlabelled induced copy of \(F\). Multiply it by \(N_F\). No further factor \(|\operatorname{Aut}(F)|\), and no triangle-label factor, is needed. The root-labelled isomorphisms have already supplied the root multiplicity.

A construction based instead on labelled free-vertex flags needs different bookkeeping. A class with \(z\) zero masks has \(z!\) labelled extensions per actual triangle. Its product entries therefore have a factor \(z!z'!\). One may divide by those factors, or keep them as a positive diagonal congruence. Full-overlap products must retain the stabilizer multiplicity; their diagonal coefficient is not automatically binary.

## Relation to existing tests

This projector is not a direct pullback of a vertex projector through \(B\). Every matrix \(B^{\mathsf T}P B\) vanishes on \(\ker B\), while \(Q\) is \(210I\) on that space. Thus the immediate vertex-projector congruence argument does not remove this family.

This observation does not prove independence from the entire existing scalar and projector flag cone. A representation using other moment matrices might exist. No such representation or separating count point is claimed here.

The family is small enough for a bounded exact construction and point probe. The present package contains only the algebra and complete class census. It contains no pair tensors, count-point contraction, optimizer call, or feasibility conclusion.
