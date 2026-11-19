# Scalar triangle-class moments and the existing flag span

The scalar triangle-class family is redundant with a complete scalar flag family of the same root and free-vertex sizes, modulo the strongly regular graph extension identities. This statement concerns the scalar matrices N. It does not identify the two triangle vertex-projector kernels or their root-vertex Schur corrections with old scalar blocks.

The general low-degree elimination argument was already recorded in [Scalar triangle-class recovery and dependencies](triangle_projector_scalar_recovery.md). The following direct specialization makes the normalization explicit for triangles meeting a root. It applies to the 30 six-vertex roots used in [the six-root vertex-projector preparation](triangle_six_vertex_projectors.md), and does not need a triangle inside the root.

## Functions at a fixed labelled root embedding

Let H be an induced root. For a root-neighborhood mask B, let X_B count outside vertices having exactly that mask. For a triangle class C, let n_C count actual unlabelled triangles in that class. The triangle class is specified by its root intersection S and the sorted masks of its outside vertices.

A core triangle, with |S|=3, has constant count one. A class with |S|=2 has one outside vertex with a mask B containing the two adjacent root vertices. Its count is X_B. When |B| is at least three, this is a retained one-free flag. When B is exactly the adjacent pair {v,w},

\[
X_{\{v,w\}}=q_{vw}-\sum_{B\supsetneq\{v,w\}}X_B,
\qquad q_{vw}=2-A_H(v,w)-(A_H^2)_{vw}.
\]

The sum runs over every allowed exact mask. Impossible masks have zero count. This is the common-neighbor quota after subtracting visible root vertices.

Now let S={v}. The two outside vertices are adjacent, and their masks B,C both contain v. The masks intersect exactly in {v}: another common root neighbor would give their edge two common neighbors. If |B| and |C| are both at least two, each free vertex has degree at least three inside the flag. This is a retained two-free flag. Its two masks are distinct, so the fixed sorted labels have stabilizer one and the labelled flag count equals n_C without an extra factor.

Suppose one mask is {v} and the other is B with |B| at least two. If B contains a root neighbor of v, the edge from v to the B-vertex already has its unique common neighbor in the root. Such a one-root triangle class is impossible. Otherwise, for each vertex b of exact mask B, the unique triangle through the edge vb has its third vertex outside the root. Consequently,

\[
n_{\{v\};\{v\},B}
 =X_B-\sum_{C:\,v\in C,\ |C|\ge2}n_{\{v\};B,C}.
\]

Only literal cap-compatible classes occur in this sum. Each triangle is counted once through its uniquely identified B-vertex; B cannot equal C because both masks have size at least two. If |B|=2, eliminate X_B by the same residual-pair formula above, now possibly for a nonadjacent root pair.

The last class has S={v} and two equal masks {v}. Its count follows from the seven triangles through v:

\[
n_{\{v\};\{v\},\{v\}}
 =7-\sum_{C\ne(\{v\};\{v\},\{v\}),\,v\in S_C}n_C.
\]

This final class counts unlabelled triangles. Using the point-star identity avoids an erroneous factor two from its two indistinguishable outside slots.

## Consequence for the scalar Gram matrix

These identities express every n_C as an integer affine combination of the constant, all allowed one-free masks of size at least three, and adjacent two-free flags whose two masks each have size at least two. The latter vertices have total degree at least three because the mutual edge contributes one.

The [complete r6s2 cache](grid_free_order10_r6s2_full_cache.md) contains every required flag when H has six vertices. It retains the constant, all high-mask one-free flags, and every cap-compatible two-free flag with both free degrees at least three. All two-free flags used in this argument have distinct masks, so no residual free-label stabilizer enters the change of coordinates.

Write the pointwise identity as n=T f, including the constant in f. Summing over labelled root embeddings gives

\[
N=T M_f T^T.
\]

Products of these identities use at most six root vertices and four free vertices, so they belong to the order-ten extension system. The scalar N condition is therefore implied by complete r6s2 positive semidefiniteness together with those exact extension identities. This note does not construct or compare a full coefficientwise T tensor; it supplies the explicit pointwise reduction and identifies the existing flag domain. The separately checked N matrices remain useful direct certificates at the fixed count point.

This argument does not infer PSD of the entire r6s2 family from PSD of N. It also does not remove the new vertex-projector blocks: their entries weight triangle pairs by vertex-projector kernels and contain correlations beyond these unweighted scalar products.
