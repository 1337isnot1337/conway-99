# Exact Gram screen for the complete component-zero pair

All 39,168 compatible six-neighbor columns pass the exact one-column
Gram-downdate test. This removes no column from the complete domain.
It does not establish an incidence solution or a graph.

The core consists of two copies of the eighteen-vertex component zero,
with the identity relative fiber alignment and their common central
triangle. The scope remains the globally prism-free, \(x_{521}=0\),
split-shell case. The two component incidence designs are unrestricted.
The earlier fixed-design UNSAT result has a narrower scope and is not
used to remove columns here.

## Complete domain and kernel

The source rebuilds component zero from its normalized matching
description, compares it with the frozen 66-component catalogue, and
reconstructs both copies of its twenty-one-vertex local core. Let
\(B\) be the joined thirty-nine-vertex adjacency matrix. Its central
vertices have degree fourteen within the core; its shell vertices
have degree four. Define

\[
G=12I+2J-B^2-B.
\]

Every exterior incidence column is zero on the three central vertices.
Its two component triples \(a,b\) belong to their complete 480-triple
domains and satisfy

\[
\operatorname{prof}(a)+\operatorname{prof}(b)=(2,2,2).
\]

This gives exactly 39,168 columns. The source checks every column's
mixed cap against the full core. No saved sixty-triple design enters
the construction or screen.

Write \(V,W\) for the two components and \(U_0,U_1,U_2\) for the three
global twelve-vertex fibers. Six independent kernel vectors are

\[
e_0,e_1,e_2,\quad
1_{U_0}-1_{U_1},\quad
1_{U_0}-1_{U_2},\quad
1_V-1_W.
\]

The component populations and complementary profiles make every
candidate column orthogonal to all six vectors. The positive quotient
below proves that these vectors span the complete kernel.

## Integer positive quotient and exact inverse

Delete coordinates \(P=(0,1,2,3,9,21)\), and let \(I\) be the remaining
33 coordinates. Put \(K=G[I,I]\). Solving the six kernel equations gives
an embedding \(E\) whose rows indexed by \(I\) form the identity.
The certificate stores the integer matrix \(2E\) and verifies

\[
G=EKE^T.
\]

The denominator two is retained explicitly; the embedding is not
silently treated as integral. A complete rational LDL factorization
of \(K\) has positive diagonal entries. Thus \(K\succ0\) and
\(\operatorname{rank}G=33\). The certificate also supplies an integer
matrix \(Q\) with

\[
KQ=D I,\qquad D=4,577,040,
\]

and checks every entry of this identity. The exact principal
determinant is

\[
\det K=35,109,837,421,426,973,609,164,800,000.
\]

For a candidate column \(h\), set \(x=h[I]\). The verifier checks
\(h=Ex\). Consequently

\[
G-hh^T\succeq0
\quad\Longleftrightarrow\quad
h^TG^+h=x^TK^{-1}x=\frac{x^TQx}{D}\le1.
\]

All 39,168 values satisfy the inequality strictly. Their exact range is

\[
\frac{560009}{1144260}
\ \le h^TG^+h\ \le
\frac{6929}{9780}<1.
\]

The certificate records every numerator in the complete, deterministic
column order. Replay reconstructs that order and recomputes each value
with arbitrary-precision integers. No numerical eigenvalue test is used.

## A component formula for all inverse products

Let \(A\) be the eighteen-by-eighteen component Gram matrix and define
\(r(a,c)=a^TA^{-1}c\). The matrix \(A\) is positive definite; its exact
inverse has denominator 2,288,520. If \(h=(a,b)\) and \(k=(c,d)\) are
two complete columns, with \(p=\operatorname{prof}(a)\) and
\(q=\operatorname{prof}(c)\), then

\[
\boxed{
h^TG^+k
=r(a,c)+r(b,d)-\frac1{60}
-\frac{(p-1)\cdot(q-1)}{36}.
}
\]

This identity is proved for the entire range, not inferred by sampling
column pairs. On the shell coordinates, form a symmetric matrix from
\(\operatorname{diag}(A^{-1},A^{-1})\) by adding

\[
\frac1{135}J_{18}
-\frac1{36}\operatorname{diag}(J_6,J_6,J_6)
\]

to the first component block. Call the resulting matrix \(H\), extending
it by zero on the central coordinates. The certificate checks
\(E^THE=K^{-1}\) after clearing all denominators. Substitution of the
size-three component columns gives the displayed formula.

There is also a direct decomposition. If \(S\) is the cubic component
shell matrix, then \(A=(12I-S^2-S)+C\), where
\(C=2J-\operatorname{diag}(J_6,J_6,J_6)\). The joined shell Gram is
\(\left(\begin{smallmatrix}A&C\\C&A\end{smallmatrix}\right)\).
On vectors whose sum in every six-fiber is zero, \(C\) vanishes, so the
two components contribute independently. The remaining fiber-constant
spaces give the two correction terms above.

In particular, the one-column leverage equals

\[
r(a,a)+r(b,b)-\frac1{60}
-\frac{\|p-1\|^2}{36}.
\]

Every computed leverage agrees with this expression. It adds no
restriction beyond profile compatibility in the present domain.

For any exact sixty-column incidence, the leverage sum must be
\(\operatorname{tr}(G^+G)=33\). This does not add an independent trace
constraint: each component's Gram equations give a sum of eighteen
for its component leverage. The 24 profiles \(111\) and 36 profiles
\(210\) make the correction sum equal to three, leaving \(36-3=33\).

## Two-column preparation and resource limit

For two columns, put \(n_h=D h^TG^+h\), \(n_k=D k^TG^+k\), and
\(t=D h^TG^+k\). The exact two-column test is

\[
(D-n_h)(D-n_k)-t^2\ge0.
\]

The formula above permits every \(t\) to be obtained from a single
480-by-480 component bilinear table and a profile dot product. That
table has 230,400 integer entries, or 1,843,200 bytes in an int64
representation. A dense 39,168-by-39,168 table would require
12,273,057,792 bytes in the same representation and is unnecessary.

There are 767,046,528 unordered pairs in the complete column domain.
This package does not enumerate them or claim any two-column exclusions.
Factoring the arithmetic reduces storage and work per pair; it does not
by itself eliminate the number of pairs to classify.

## Limit of the fixed-design parity route

A separate diagnostic reads the previously saved sixty-triple design
and reconstructs only the earlier 792-variable matching problem's
444 quota equations. Their reduction modulo two is consistent, with
rank 338. The certificate stores a particular modulo-two solution and
checks every equation.

That vector has integer quota defects. It is not an incidence witness.
The calculation rules out a linear contradiction over \(\mathbb F_2\)
using those quota equations alone. It says nothing about other moduli,
packing inequalities, or nonlinear parity arguments. The checked DRAT
proof remains the certificate for the fixed-design exclusion.

## Controls and replay

The nine-vertex rook graph supplies a rank-three core Gram matrix and
all five actual exterior columns, including its zero column. Every
actual column passes. A binary column outside the kernel range is
rejected, and a separate binary excess-leverage control has a direct
negative quadratic value of minus two. The modulo-two elimination
routine is checked against exhaustive assignment enumeration for all
64 two-by-two systems.

Source:
[root_prism_free_f0_pair_gram.py](../experiments/workspace/root_prism_free_f0_pair_gram.py).
Certificate:
[f0-pair-gram-certificate.json.gz](../experiments/logs/root-prism-free/f0-pair-gram-certificate.json.gz).
Generation and replay use the standard library and call no solver.

```sh
.venv/bin/python experiments/workspace/root_prism_free_f0_pair_gram.py \
  --certificate experiments/logs/root-prism-free/f0-pair-gram-certificate.json.gz \
  --replay
```
