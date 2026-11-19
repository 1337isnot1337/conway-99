# Twelve edge states have literal integer spectral certificates

The twelve eligible edges in edge orbit 3 are impossible in an
SRG(99,14,1,2). Each specified 23-vertex induced graph has an integer
vector with negative quadratic value in the principal matrix
\(27I-9A+J\). This certifies the edge prohibition directly. It does not
forbid selecting the two endpoint signatures as a nonadjacent pair.

## Representative calculation

The fixed 21-core consists of the central triangle, with labels 0, 1, 2,
and component zero, with labels 3 through 20. The two additional vertices
21 and 22 have component signatures \(\{0,2,6\}\) and
\(\{1,2,13\}\), respectively; component labels are shifted by three.
The additional vertices are adjacent to one another and have no central
triangle neighbors. All 23-vertex adjacencies are specified.

In any SRG(99,14,1,2), the matrix \(Q=27I-9A+J\) is positive
semidefinite: its values on the constant, 3-eigenvalue, and
\(-4\)-eigenvalue spaces are 0, 0, and 63. Every principal matrix of
\(Q\) must therefore be positive semidefinite.

Use the 20 core coordinates \(0,1,3,4,\ldots,20\), omitting coordinate
2. Exact rational inversion of this principal core matrix gives the
following two-by-two Schur matrix for coordinates 21 and 22:

\[
S=\frac1{60}\begin{pmatrix}782&-865\\-865&914\end{pmatrix}.
\]

The determinant numerator is \(-33477\), and
\((1,1)S(1,1)^T=-17/30\). Extending this direction by
\(-K^{-1}U(1,1)^T\) on the chosen core, setting coordinate 2 to zero,
and multiplying by 540 gives the integer vector

```text
[270, 0, 0, 526, 482, 464, 76, -212, -256, 443, 25, 178,
 -133, -250, -263, 113, 355, 58, -103, -130, -293, 540, 540]
```

Direct integer evaluation, using only the saved adjacency rows, gives

\[
27\sum_i v_i^2-18\sum_{ij\in E}v_iv_j+
\left(\sum_i v_i\right)^2=-165240.
\]

The vector has squared norm 2130084 and largest entry magnitude 540.
Removing the endpoint edge changes this same quadratic value to 5083560.
The certificate therefore makes no nonedge or selector-pair exclusion.

## Complete orbit and independent construction

The source reconstructs all twelve 21-core relabelings from the frozen
actions on the 480 signatures. It verifies the literal core adjacency,
all signature images, group closure, and each transported 23-vertex
graph. The twelve resulting endpoint pairs agree exactly with the
rejected states in the coordinator's pair-minor census. They comprise
eligible edge orbit 3, whose quotient edge coordinate is 45.

Every transported vector has the same exact negative value. The cold
replay reconstructs the rational calculation and separately evaluates
all twelve saved vectors by the displayed integer formula. No Schur
builder, model source, numerical eigensolver, or optimizer is imported.

The construction source is
[root_prism_free_f0_full_core_edge_negative_certificate.py](../experiments/workspace/root_prism_free_f0_full_core_edge_negative_certificate.py).
Its certificate is
[f0-full-core-edge-negative-certificate.json](../experiments/logs/root-prism-free/f0-full-core-edge-negative-certificate.json),
with a separate
[cold replay](../experiments/logs/root-prism-free/f0-full-core-edge-negative-cold-replay.json).
The certificate stores each full induced adjacency matrix, integer
vector, transport, and exact quadratic value.

These twelve states also create visible prisms and are included in the
larger 162-orbit prism prohibition. The spectral proof itself uses the
SRG projector and the specified induced graph; it does not use the
global prism prohibition. The remaining eligible edge states and the
component-zero completion problem are not settled by this certificate.
