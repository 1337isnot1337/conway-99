# A positive semidefinite constraint on the nine tips

## Result and scope

Let an SRG(99,14,1,2) contain two disjoint induced rook grids with a
rook-isomorphic matching. Label their points so that the matching is
the identity. Let `R` be the nine-point rook adjacency matrix. For each
point `p`, the matched core edge has a unique tip `z_p` outside the two
grids. Write `Z` for the adjacency matrix induced by these nine tips.
No rook structure is assumed for `Z`.

Then

\[
\boxed{H=3I-R+J-2Z\succeq0.}
\]

This is a necessary constraint on every completion of the two-grid
core. It is not an exclusion of that core. Both binary points saved in
`two-rook-iso-pair-integer.json` satisfy this inequality exactly:

| Saved point, zero-based | Result | Rank |
| --- | --- | --- |
| 0 | Positive semidefinite | 8 |
| 1 | Positive definite | 9 |

Thus neither point produces a negative vector for this nine-point
matrix. Point 0 has a kernel-extension obstruction, described below,
but its tip graph already contains a forbidden four-clique. That
rejection overlaps the existing common-neighbor cap clauses.

## Derivation from the full graph Gram matrix

If `A` is the full adjacency matrix, its eigenvalues are 14, 3, and
-4. The matrix

\[
Q=27I-9A+J
\]

has eigenvalues 0 and 63 and is positive semidefinite. Consider its
principal block on the 18 core vertices and the nine tips. The core
adjacency and core Gram block are

\[
B=\begin{pmatrix}R&I\\I&R\end{pmatrix},
\qquad S=27I_{18}-9B+J_{18}.
\]

The core-to-tip coupling and tip block are

\[
W=\begin{pmatrix}J_9-9I_9\\J_9-9I_9\end{pmatrix},
\qquad Q_Z=27I_9-9Z+J_9.
\]

The two vectors constant on one core grid and zero on the other are
the kernel of `S`. On the symmetric copies of the rook eigenspaces
with eigenvalues 1 and -2, `S` has eigenvalues 9 and 36. On the
antisymmetric copies it has eigenvalues 27 and 54. Thus `S` has rank
16, and `W` is orthogonal to its kernel.

Let `E_1,E_-2` be the rook spectral projectors:

\[
E_1=\frac{2I+R-\tfrac23J}{3},
\qquad E_{-2}=\frac{I-R+\tfrac13J}{3}.
\]

Set

\[
K=E_1+\frac14E_{-2},\qquad
U=\begin{pmatrix}K\\K\end{pmatrix}.
\]

Direct rational multiplication gives

\[
SU=-W,\qquad W^{\mathsf T}U=-18E_1-\frac92E_{-2}.
\]

The invertible congruence with block matrix
`[[I,U],[0,I]]` therefore transforms the 27-point principal Gram block
into the block diagonal matrix with blocks `S` and

\[
\begin{aligned}
Q_Z+W^{\mathsf T}U
&=27I-9Z+J-18E_1-\frac92E_{-2}\\
&=\frac92(3I-R+J-2Z).
\end{aligned}
\]

This proves the claimed PSD condition without inverting the singular
core block. The standalone checker verifies these identities using
fractions and also independently verifies that `S` is PSD of rank 16.

## Independent spectral interpretation

Write the full adjacency matrix in core/exterior form as
`[[B,X],[X^T,C]]`. The forced incidence satisfies

\[
XX^{\mathsf T}=12I+2J-B^2-B,\qquad
CX^{\mathsf T}=2J-X^{\mathsf T}(B+I).
\]

The four nonconstant core eigenspaces lift into exterior eigenspaces
of `C` with eigenvalues -3, -1, 0, and 2. On the nine tips, the two
antisymmetric lifted spaces vanish. The lifted -3 and 0 projectors
compress respectively to `E_1/3` and `E_-2/6`. The constant exterior
projector compresses to `J_9/81`.

On `ker X`, the exterior matrix has eigenvalues 3 and -4. Let `P_-4`
be its -4 projector. Eliminating the 3-projector from the identity
and adjacency decompositions gives

\[
7(P_{-4})_{Z,Z}
=3I-Z+\frac19J-2E_1-\frac12E_{-2}
=\frac12(3I-R+J-2Z).
\]

Thus `H/14` is a principal compression of a positive semidefinite
projector. The checker verifies the displayed projector identity
separately from the Schur calculation.

## Exact audit of the saved binary points

For each point, the certificate contains an invertible rational matrix
`T` and a nonnegative rational diagonal `D` such that

\[
T^{\mathsf T}HT=D.
\]

The verifier reconstructs `H` from the saved tip edges, checks the
identity exactly, checks that `det(T)` is nonzero, and counts the
positive diagonal entries. It does not use approximate eigenvalues.
The source record's SHA-256 is checked when that record is supplied
to replay.

The congruence routine also handles indefinite matrices. It returns
an integer vector `x` with `x^T H x<0`, verified by direct integer
arithmetic. The empty tip graph and a rook tip graph are PSD controls
of ranks 9 and 4. The complete tip graph is a negative control.

## Kernel-extension control for point 0

Point 0 has the integer kernel vector

\[
x=(0,1,0,1,0,1,0,1,0).
\]

Its lift to each core grid is

\[
u=Kx=\frac1{18}(-5,4,-5,4,4,4,-5,4,-5).
\]

The vector `(u,u,x)` has zero quadratic form in the 27-point Gram
block. In a positive semidefinite full Gram matrix, its extension by
zero must be a kernel vector of the full matrix. For any of the other
72 vertices `y`, with core signature `(p,q)`, its row then gives

\[
\sum_{t=0}^8 x_t A_{y,z_t}
=\frac{\sum_t x_t}{9}-u_p-u_q.
\]

The forced incidence includes two vertices of signature `(0,4)`.
For these vertices, the right side is `1/2`, whereas the left side
is an integer. Therefore this tip graph cannot occur in a completion.

This does not provide a new exclusion beyond the saved cap clauses:
the four tips indexed by the support `{1,3,5,7}` form a complete graph
in point 0. Such a four-clique already violates the requirement that
adjacent vertices have only one common neighbor. Point 1 is positive
definite and has no kernel-extension equation from this test.

## Linear inequalities for later edge searches

For any integer vector `x`, the PSD condition gives the necessary
linear inequality

\[
4\sum_{i<j}x_i x_j Z_{ij}\le
3\sum_i x_i^2+\left(\sum_i x_i\right)^2
-2\sum_{\{i,j\}\in E(R)}x_i x_j.
\]

A negative vector for a candidate tip matrix therefore gives a
globally valid weighted edge cut. The generic `edge_cut` helper in
the audit source returns the integer coefficients and right side in
this convention. No such negative-vector cut is generated from the
two saved points, because both tip matrices are PSD.

## Files and replay

- Source: `experiments/workspace/two_rook_tip_psd_audit.py`.
- Certificate: `experiments/logs/grids-and-triangles/two-rook-tip-psd-certificate.json`.
- Generation and replay logs use the same stem.

```sh
python experiments/workspace/two_rook_tip_psd_audit.py \
  --input experiments/logs/grids-and-triangles/two-rook-iso-pair-integer.json \
  --certificate experiments/logs/grids-and-triangles/two-rook-tip-psd-certificate.json
```

Add `--write` to regenerate the saved rational certificates. No SAT,
mixed-integer, or numerical semidefinite solver is used in this audit.
