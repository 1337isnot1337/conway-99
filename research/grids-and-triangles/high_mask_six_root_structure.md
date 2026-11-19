# Structure of the high vertices above any six-root

Let \(H\) be any six vertices of a graph satisfying the Conway
common-neighbor caps. For a vertex \(v\) outside \(H\), write
\(A_v=N(v)\cap H\). Let \(K\) be the graph induced by vertices with
\(|A_v|\ge3\).

The six-root need not be independent. The following conclusions use only
the pair caps:

- \(K\) has no triangle or four-cycle.
- Every vertex of \(K\) has degree at most three.
- A vertex with \(|A_v|\ge5\) is isolated in \(K\).
- A vertex with \(|A_v|=4\) has degree at most one in \(K\).
- Every component of \(K\) on at least three vertices uses only triple
  masks, and adjacent masks in that component meet in exactly one root.

These statements concern the induced graph on the high vertices, not their
full degree in the Conway graph.

## Triangles and four-cycles

If \(u,v,w\) form a triangle in \(K\), the adjacent pair \(u,v\) already
has its unique common neighbor \(w\). Thus \(A_u\cap A_v=\varnothing\),
and the same holds for the other two pairs. Three disjoint sets of size
at least three cannot fit inside six roots.

Suppose \(u,v,w,x\) form a four-cycle. The opposite pair \(u,w\) has the
two common high neighbors \(v,x\). Consequently its root masks are
disjoint. Since both masks have size at least three, they are complementary
triples in \(H\). The same holds for \(A_v,A_x\).

Each edge has at most one common root neighbor, so
\(|A_u\cap A_v|\le1\) and \(|A_u\cap A_x|\le1\). But the complementary
triples \(A_v,A_x\) partition \(H\), giving

\[
3=|A_u|=|A_u\cap A_v|+|A_u\cap A_x|\le2,
\]

a contradiction.

## The degree bound

An edge \(uv\) requires \(|A_u\cap A_v|\le1\). If \(|A_u|\ge5\),
every set \(A_v\) of size at least three meets it in at least two roots.
Thus \(u\) is isolated.

If \(|A_u|=4\), a neighbor must have a triple mask consisting of the
two roots outside \(A_u\), together with one root in \(A_u\). Two such
neighbors would share those two roots and the high vertex \(u\), which is
impossible. Hence \(d_K(u)\le1\).

Now suppose \(|A_u|=3\). If a neighbor has a four-element mask, it contains
all three roots outside \(A_u\). Any second neighbor contains at least two
of those three roots. The two neighbors would share those roots and \(u\).
Thus the presence of a four-mask neighbor forces \(d_K(u)=1\).

The same argument applies if a triple-mask neighbor is disjoint from
\(A_u\), since that neighbor is exactly \(H\setminus A_u\).

It follows that when \(d_K(u)\ge2\), every neighbor is a triple meeting
\(A_u\) once. Each neighbor contains a two-subset of the three roots in
\(H\setminus A_u\). Two neighbors cannot use the same two-subset, since
they also share \(u\). There are only three choices, proving
\(d_K(u)\le3\).

In the degree-three case the neighbors use all three two-subsets of the
complement. Their individual roots inside \(A_u\) are also distinct:
otherwise two neighbors would share that root, a complement root, and
\(u\). Thus a cubic high vertex determines a bijection between its three
root neighbors and the three omitted complement roots.

## A direct count inequality

Let \(n_j\) be the number of high vertices with exactly \(j\) root
neighbors, and let \(e(K)\) be the number of high-high edges. Summing the
degree bounds gives

\[
2e(K)\le3n_3+n_4.
\]

Summing this pointwise inequality over labelled root embeddings gives an
exact necessary linear inequality involving only one-free and two-free
induced-pattern moments. This note does not evaluate the inequality at a
count point or claim that it separates one.
