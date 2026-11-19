# A squared-difference constraint at a four-cycle

The fifteen-flag four-cycle block has an exact symmetry decomposition
into blocks of orders 5,2,2,3,3, with the last 3×3 block repeated. The
previous negative direction lies in this repeated component. A single
diagonal entry already gives a simpler separating inequality: the sum
of the squares of the difference of two triangle-extension counts.

This calculation is separate from the earlier 39-term cut. It leaves
that cut, its replay, and the original caches unchanged.

## The two flag counts

Label the four-cycle so that its opposite pairs are {0,1} and {2,3}.
Its adjacency rows are (12,12,3,3). For a fixed labelled root embedding,
let f3 count external triangles with one vertex adjacent to exactly
root vertex 1, one to exactly root vertex 2, and one to exactly root
vertex 3. Here "exactly" refers to adjacency within the four-vertex
root. Let f4 count the analogous triangles attached to root vertices
0,2,3. These are flags 3 and 4 in the frozen fifteen-flag domain.

Every candidate graph satisfies

\[
\sum_{\phi}(f_3(\phi)-f_4(\phi))^2\geq0,
\]

where φ runs over all labelled four-cycle root embeddings. Thus the
integer direction e3−e4 gives a necessary moment inequality without
using any numerical eigenvector.

The two flags are interchanged by a root automorphism, so M33=M44.
The squared difference can equivalently be written 2(M33−M34). All
three product entries were reconstructed with the independent literal
edge/nonedge oracle.

In unlabelled induced catalogue counts, the primitive inequality is

\[
\begin{aligned}
0\leq {}&c_{303}-2c_{6366}\\
&+2(c_{45713}-c_{45714}+c_{45715}-c_{45716}\\
&\quad+c_{48322}-c_{48323}+c_{48324}-c_{48325}\\
&\quad+c_{48350}-c_{48351}+c_{48352}-c_{48353}\\
&\quad+c_{48869}-c_{48870}+c_{48871}-c_{48872}).
\end{aligned}
\]

The count indices use the frozen order-ten catalogue. The squared
difference is four times this primitive form. At the rejected repaired
point with SHA256 `190c779b4a8758d9df90ccc13a54538d8e120710e224b9150dd3aa4b591bd53d`,
the square sum evaluates to −11,200 and the primitive form to −2,800.
This is a necessary inequality for every candidate graph, not only for
prism-free graphs.

## Exact symmetry decomposition

All eight root automorphisms act by permutations on the fifteen flags.
The flag orbits are

\[
\{0\},\quad\{1,2\},\quad\{3,4,5,8\},\quad
\{6,9,11,13\},\quad\{7,10,12,14\}.
\]

The source verifies all 960 tensor-entry invariance comparisons, eight
automorphisms times 120 lower entries. This is equality of induced-count
coefficient forms, rather than equality only at the rejected point.

Let R be a root rotation of order four and S a reflection, with
SRS=R⁻¹. Their flag permutation matrices are orthogonal. For a,b in
{1,−1}, the projectors onto the one-dimensional-character spaces are

\[
P_{a,b}=\frac18(I+aR+R^2+aR^3)(I+bS).
\]

Their ranks, in the order (1,1),(1,−1),(−1,1),(−1,−1), are 5,0,2,2.
The remaining central projector is

\[
P_2=\tfrac12(I-R^2),
\]

of rank six. On this space, the +1 and −1 reflection eigenspaces each
have dimension three. R maps one to the other, and M commutes with R
and S. Therefore the two restrictions of M are congruent.

An integer basis of the +1 reflection part is

\[
b_1=e_3-e_4,\qquad
b_2=e_6+e_9-e_{11}-e_{13},\qquad
b_3=e_{10}-e_{14}.
\]

Writing B=(b1,b2,b3), the repeated block is K=BᵀMB. At the rejected
point it equals

\[
K=\begin{pmatrix}
-11200&964&-1084\\
964&2528&-200\\
-1084&-200&1600
\end{pmatrix}.
\]

The full integer change of basis has determinant −2,048. Thus it is
invertible, and PSD of M is equivalent to PSD of the blocks of orders
5,2,2,3; the final block occurs twice. The record contains all basis
columns and all six induced-count forms defining K. This explains the
negative component of the earlier direction and supplies a small
family for subsequent exact checks.

## The later exact count point

The later integer count witness has SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
At this point the primitive squared-difference form is 3,568, and the
unscaled square sum is 14,272. Its repeated block is

\[
K=\begin{pmatrix}
14272&1628&-408\\
1628&2560&-256\\
-408&-256&1608
\end{pmatrix}.
\]

The separate evaluator checks the complete integer congruence and all
44 principal minors of the four distinct blocks. Every principal minor
is nonnegative. Their ranks are 4, 2, 1, and 3, so the full fifteen-flag
C4 block is exactly positive semidefinite of rank 13. This is an exact
check at the integer count point. It does not certify the other 2,404
blocks, and it does not replace the separate numerical scan at the
unrounded proposal.

The evaluation source is
`experiments/workspace/grid_free_order10_higher_flags_c4_evaluate.py`.
Its output is
`experiments/logs/moments-and-counts/order10-higher-flags-c4-new-point-evaluation.json`,
with SHA256
`5649de474e5ccf67b6d492f7d5f9874311a0e9ee4c6452f39ef36d2a6127fff4`.
The exact evaluation takes 0.586 seconds and uses no eigensystem,
dense reduction, or optimizer.

## Verification and artifacts

Source:
`experiments/workspace/grid_free_order10_higher_flags_c4_structure.py`

Source SHA256:
`e355ededa0ec121356bfc7a5e90f45b6404ea0aa8b8116ecfa25518a239d6ddc`

Output:
`experiments/logs/moments-and-counts/order10-higher-flags-c4-structure.json`

Output SHA256:
`07c0e618bb3b3b530bf2a52c40f9baaba62935ffca73442c64d679a54d495fea`

The exact calculation takes 2.357 seconds. It uses integer/rational
group algebra and three fresh literal products. It uses no eigensystem,
dense core reduction, or optimizer. The result rejects the specified
count point; it does not prove nonexistence of the requested graph.
