# The complete rational kernel of the F0 mixed equalities

## Theorem

For the frozen F0 component, the matrix of all 8,640 shared mixed equations on all 68,394 eligible exterior edges has rational rank 7,731 and left-nullity 909. Its complete left kernel has an explicit basis: 756 coordinate vectors for empty mixed rows and 153 skew-site vectors.

Each empty mixed row has zero selector right-hand side. Every skew-site right-hand side is an explicit integer combination of the original Gram equations, with total constant zero. Therefore every rational selector vector satisfying the original Gram equations admits a rational solution of the unrestricted shared mixed and degree equalities. The corresponding statement also holds over the real numbers.

The edge solution in this theorem has no sign, upper-capacity or integrality requirement. This theorem does not establish feasibility of the shared linear program, which includes edge bounds. It does not construct a graph, exclude the component, or rule out additional congruences at other primes.

## Matrix and domain

Let h_a be the length-18 zero-one incidence vector of signature a, and let A be the adjacency matrix on the 18 non-root core sites. There are 480 admissible signatures, each of weight three. Their mixed targets are

\[
q_a=2\mathbf1-(I+A)h_a,\qquad \mathbf1^Tq_a=24.
\]

Let U have one row for each pair (a,i), and one column for every eligible unordered pair {a,b}. In column {a,b}, the block at anchor a is h_b and the block at anchor b is h_a. All other entries are zero. The mixed equations are

\[
Uz=Qx,\qquad (Qx)_{a,i}=q_a(i)x_a.
\]

All 480 signatures and all eligible edges remain separate. No symmetry of an unknown graph is imposed. The theorem applies to the frozen domain with SHA-256 `665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4`.

## Explicit kernel and rank

The complete domain has 756 mixed rows with no incident coefficient. The certificate lists every such row and checks q_a(i)=0 in each case. Their coordinate vectors give 756 independent elements of the left kernel.

For each pair of distinct sites i<j, define a skew matrix M with M_ij=1, M_ji=-1 and all other entries zero. At anchor a, use the potential Mh_a. Its coefficient on edge {a,b} is

\[
(Mh_a)^Th_b+(Mh_b)^Th_a
=h_a^T(M^T+M)h_b=0.
\]

Thus the 153 site pairs give 153 integer kernel vectors. The producer also directly contracts every one of these vectors against all 68,394 eligible edge columns: 10,464,282 integer coefficients are checked to be zero.

After deleting the 756 empty coordinates, a saved 153-square minor of these vectors is nonsingular modulo two. The cold checker reconstructs this minor from the sparse integer vectors and verifies rank 153. Its determinant is odd, hence nonzero over the rationals. The 153 skew vectors are therefore independent modulo the empty-row subspace. This proves

\[
\operatorname{rank}_{\mathbb Q}U\le 8640-756-153=7731.
\]

The independently accepted modulo-three calculation includes all 480 degree rows as well as all 8,640 mixed rows. Its edge-column rank is 7,731. An integer matrix has rational rank at least its rank modulo three. Over the rationals, each degree row is one third of the sum of the 18 mixed rows at its anchor: each h_b has weight three, and the target sum is 24. Adding the degree rows therefore does not increase rational rank. This gives the matching lower bound

\[
\operatorname{rank}_{\mathbb Q}U\ge7731.
\]

The bounds agree. The 909 exhibited independent vectors form the entire rational left kernel.

## Every kernel right-hand side follows from Gram

Write

\[
G_{rs}(x)=\sum_a h_a(r)h_a(s)x_a.
\]

The original Gram equations prescribe G_rs(x)=B_rs, including diagonal entries. For the skew vector at i<j, the induced selector coefficient is

\[
\sum_a\bigl(h_a(j)q_a(i)-h_a(i)q_a(j)\bigr)x_a.
\]

Substituting the expression for q_a and using h_a(i)^2=h_a(i) yields the explicit identity

\[
2G_{jj}(x)-2G_{ii}(x)
-\sum_k A_{ik}G_{jk}(x)
+\sum_k A_{jk}G_{ik}(x).
\]

The certificate stores each of these 153 Gram combinations. It verifies all 480 selector coefficients of each combination, and verifies that substituting the prescribed Gram constants gives zero. The cold checker repeats these 73,440 integer coefficient checks independently, using the saved combinations and reconstructed Gram rows.

All left-kernel vectors therefore annihilate Qx whenever x satisfies the original Gram equations. The image of U is the annihilator of its left kernel, so Uz=Qx is solvable over the rationals for rational x, and over the reals for real x. The degree equations then follow by the same division-by-three identity.

## Evidence and limits

The producer is `experiments/workspace/root_prism_free_f0_shared_rational_kernel.py`, SHA-256 `f017f6cc2b3674b21b9fb519e585c8d61495ae4db715fe40bd2715f38d1421b5`. It completed in 14.431 seconds. The complete certificate is `experiments/logs/root-prism-free/f0-shared-rational-kernel01.json.gz`, SHA-256 `e8a2d8303fe3ee67b33fbb05407b3310c36febef7e867c89acdd264b3fde0f8c`.

The separate checker is `experiments/workspace/root_prism_free_f0_shared_rational_kernel_cold.py`. It imports no producer or native module. It verifies the sparse skew forms, all zero-row right-hand sides, the saved nonsingular minor, every Gram identity, and the accepted modulo-three lower-bound binding. It does not rerun the large elimination. The result is `experiments/logs/root-prism-free/f0-shared-rational-kernel01-cold.json`.

The lower-bound premise is the independently reconstructed modulo-three edge rank, recorded in `f0-shared-mod3-projection-independent01.json`, SHA-256 `c9708a77fa7aa80e5fa31d4b9d4929766bf5656b7b7c901aa29a74c975035124`.

This closes the search for additional rational selector equalities obtained solely by eliminating these shared mixed and degree equations. Capacity bounds, positivity, integrality and nonlinear identities remain separate constraints. Rational rank does not control Smith torsion or rank drops at every other prime, so no conclusion about all congruences follows.
