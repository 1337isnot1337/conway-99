# Integer triangle-class counts over five-vertex roots

This preparation concerns the 1,296 triangle classes in the complete five-root model. It retains all 21 root types and all coordinate functions and signed sums of two distinct classes. It does not load a count point or use an optimizer or eigensystem.

For a fixed labelled root embedding, let \(n_C\) count the actual unlabelled triangles in class \(C\). These are nonnegative integers. The stored first moments \(p_C\) and scalar products \(N_{CD}\) have this normalization, including the divisions for repeated outside masks. The labelled root mass is \(g=\operatorname{Aut}(H)N_H\).

For an integer vector \(v\) and integer shift \(a\),
\[
(v\cdot n-a)(v\cdot n-a-1)\geq0.
\]
Thus the necessary count inequality is
\[
v^TNv-(2a+1)v^Tp+a(a+1)g\geq0.
\]

The preparation includes \(v=e_i\), \(e_i+e_j\), and \(e_i-e_j\) for every \(i<j\). Negating \(v\) replaces \(a\) by \(-a-1\), so the first nonzero coefficient may be fixed to \(+1\). There are 127,296 such vectors.

## Exact partitions

The following identities hold for every labelled root embedding.

For a root vertex \(v\), all triangle classes containing \(v\) partition the seven triangles through \(v\):
\[
\sum_{C:\,v\in T_C\cap H}n_C=7.
\]

Let \(d_H(v)\) be its degree inside the root and \(t_H(v)\) the number of root triangles through it. Counting root edges incident with \(v\) shows that \(d_H(v)-t_H(v)\) of its seven triangles meet another root vertex. Therefore
\[
\sum_{C:\,T_C\cap H=\{v\}}n_C=7-d_H(v)+t_H(v).
\]

For distinct root vertices \(v,w\), let \(E(v,w)\) contain the classes whose triangle contains \(v\) and has an outside vertex adjacent to \(w\). Every outside common neighbor \(x\) of \(v,w\) belongs to the unique triangle through the edge \(vx\). That triangle has exactly one outside vertex adjacent to \(w\). Two such vertices would be adjacent and have the two distinct common neighbors \(v,w\). Consequently
\[
\sum_{C\in E(v,w)}n_C
= q_{vw}
=2-A_{vw}-(A_H^2)_{vw}.
\]
This also covers a triangle that contains \(w\) itself; such a triangle has only one outside slot.

There are 30 recorded partitions per root: five point stars, five single-root-intersection groups, and twenty ordered root-pair groups. Multiplication by any \(n_D\) gives their second-moment versions.

The preparation verifies all 630 first-moment identities and all 38,880 second-moment identities after the frozen exact order-nine count reduction. Every coefficient is an unbounded Python integer. This is a check of the entire coefficient vector, not an evaluation at one count point.

## Class bounds and literal Boolean identities

A class wholly inside the root has count one. Every other class has lower bound zero.

The partition identities give upper bounds after subtracting the known internal-triangle constants outside the selected class. Two further literal facts give bound one:

- A triangle containing a root edge is the unique triangle through that edge.
- An outside vertex with at least three prescribed root neighbors is unique. Its triangle through any specified adjacent root vertex is then unique.

For every class with upper bound one, the tensor identity \(N_{CC}=p_C\) is checked coefficientwise in the induced-count basis. All 883 such checks pass. The remaining bounds are:

| Upper bound | Number of classes |
|---:|---:|
| 1 | 883 |
| 2 | 308 |
| 3 | 1 |
| 4 | 4 |
| 5 | 30 |
| 6 | 53 |
| 7 | 17 |

No class is omitted because its point value might vanish.

For a pair sum, the individual upper bounds are tightened by every common partition. A zero literal product \(N_{CD}\) proves the two classes cannot coexist; this gives the further upper bound \(\max(b_C,b_D)\) for their sum. Differences use the corresponding signed bounds. These are proved bounds, not a claim to enumerate every attainable pair value.

## Complete finite shift intervals

Suppose the prepared bounds are \(L\leq v\cdot n\leq U\). If \(L<U\), it is enough to check every integer shift \(a=L,\ldots,U-1\), together with the first-moment bounds. Write \(m=v^Tp\) and \(q=v^TNv\). For \(g>0\),
\[
F(a+1)-F(a)=2((a+1)g-m),
\]
so a minimizing shift over all integers is \(\lfloor m/g\rfloor\). If \(m/g=U\), shift \(U-1\) ties shift \(U\). The prepared interval therefore contains a minimum. If \(L=U\), the function is constant and its first and second moments must be \(Lg\) and \(L^2g\).

A zero root mass is handled separately: all relevant exact moments must vanish. No root or class is removed from the coverage ledger.

The complete ledger contains 366,356 shifts. It preserves each vector and its interval, including cases identified as redundant.

## Redundancy checks before any point evaluation

The preparation distinguishes these exact reasons:

| Code | Reason | Shift instances |
|---|---|---:|
| Z | Zero induced-count coefficient form | 10,326 |
| I | Nonnegative induced-count coefficients | 72,408 |
| E | Zero under the exact order-nine extension reduction | 1,829 |
| O | Nonnegative ordinary-core coefficients after reduction | 15,394 |
| F | Endpoint factorial decomposition | 69,868 |
| T | Translation or reflection of an already included coordinate test | 1,102 |
| C | Remaining candidate | 195,429 |

An endpoint decomposition writes \(R=v\cdot n-L\) or \(R=U-v\cdot n\) as a nonnegative integer combination \(\sum_C w_Cn_C\). Then
\[
R(R-1)=
\sum_C w_C^2 n_C(n_C-1)
+\sum_C w_C(w_C-1)n_C
+2\sum_{C<D}w_Cw_Dn_Cn_D.
\]
Every coefficient is nonnegative. The scalar tensors have nonnegative induced-count coefficients, and each \(N_{CC}-p_C\) does as well. The equality with the original shifted polynomial is verified through the exact order-nine reduction.

These checks remove 170,927 instances. The 195,429 remaining instances reduce, up to a positive gcd, to 26,289 distinct 58-coordinate ordinary-core forms. Calling them candidates does not assert that they add independent conditions; other decompositions or existing families might still imply them.

The cache moments-order9.pickle has SHA256 8ac6843d1294ab3d24e6b71942ee653c1c86cc858d74101e8d2e8a3c53bca07c. Its 6,535 by 58 induced-count forms are divided by the exact scale 362,880, with every division checked. No order-ten dense reduction is loaded.

## Controls and prior work

Direct controls use 360 labelled five-root embeddings in the nine-vertex rook graph. They check 10,800 partition equations using its degree four, as well as all coordinate bounds. The proof uses the parameter-specific point-star count \(k/2\), so these controls do not confuse the rook graph with degree fourteen.

The existing [eight-root class-size scan](grid_free_order10_projector_integer_classes.md) tests outside-vertex counts. The [C4 distribution](grid_free_order10_c4_integer_distribution.md) covers a different fifteen-flag moment matrix, and the [five-class integer scan](grid_free_order10_five_boolean_integer.md) uses high-mask vertex classes over six roots. The present functions count triangles meeting five roots. The shifted-integer polynomial itself is the same standard necessity; no novelty claim is made for that algebra.

The source is experiments/workspace/triangle_class_integer_preparation.py, SHA256 edc1c76522a4925f8bdd22575d918f7eb995682c4f9b0c10ada80d48b89afca7. The complete preparation is under experiments/logs/moments-and-counts/triangle-class-integer-preparation01. It finished in 44.997 seconds within its 60-second bound.

No point-query outcome is part of this note. Any later negative form requires an exact contraction and a separate literal-product replay before use in a count optimization.

