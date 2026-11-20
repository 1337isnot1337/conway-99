# Principal projectors and the exterior incidence Gram matrix

For every real symmetric (n\times n) matrix (B), with (n<99), the two principal-projector PSD conditions are equivalent to the centered exterior-incidence Gram PSD condition. Therefore an additional exterior-Gram PSD scan cannot remove a core that passes both principal projectors.

No degree bound is needed for this algebraic equivalence. The graph interpretation supplies the same matrices when (B) is the adjacency matrix of an induced core.

## Matrices

Write (\mathbf1) for the all-one vector, (J=\mathbf1\mathbf1^T), and set

\[
s=99-n,\qquad r=14\mathbf1-B\mathbf1,
\]

\[
P=27I-9B+J,\qquad Q=44I+11B-2J,
\]

\[
E=P/63,\qquad K=I-J/99,
\]

\[
G=12I-B-B^2+2J.
\]

Since (n<99), the matrix (K) is positive definite. Its eigenvalues are 1 on (\mathbf1^\perp) and (s/99) on the constant subspace, and

\[
K^{-1}=I+J/s.
\]

Direct substitution gives

\[
Q=77(K-E),\qquad r=s\mathbf1/9+7E\mathbf1.
\]

## Exact identity

The identity is

\[
\boxed{G-\frac{rr^T}{s}=49\bigl(E-EK^{-1}E\bigr).}
\]

One can verify it without matrix inverses or fractions. If (p=P\mathbf1), then (9r=s\mathbf1+p), and clearing denominators gives

\[
81sG-81rr^T=63sP-sP^2-pp^T.
\]

Substitute (P=27I-9B+J), (J^2=nJ), and (p=(27+n)\mathbf1-9B\mathbf1). The two sides agree term by term. The exact control source checks this integer form, including nonregular simple graphs and general symmetric integer matrices.

## Equivalence of PSD conditions

Let (F=K^{-1/2}EK^{-1/2}). Congruence gives

\[
E-EK^{-1}E=K^{1/2}(F-F^2)K^{1/2}.
\]

The matrix (F) is real symmetric. Hence (F-F^2\succeq0) holds exactly when every eigenvalue of (F) belongs to \([0,1]\). This is equivalent to (E\succeq0) and (K-E\succeq0). Positive rescaling then proves

\[
P\succeq0\text{ and }Q\succeq0
\quad\Longleftrightarrow\quad
G-rr^T/s\succeq0.
\]

Because (s>0), the same condition is equivalent by a Schur complement to

\[
\begin{pmatrix}s&r^T\\r&G\end{pmatrix}\succeq0.
\]

In particular, both projector conditions imply (G\succeq0).

## Graph interpretation and scope

An SRG with parameters ((99,14,1,2)) satisfies (A^2+A=12I+2J). Split its adjacency matrix into an induced core (B) and its exterior incidence matrix (X). Then

\[
XX^T=G,\qquad X\mathbf1=r.
\]

The augmented matrix above is the Gram matrix of the exterior all-one row together with the rows of (X). Thus the two principal projectors already impose even the centered exterior Gram condition, including the exterior population and core degree deficits.

This does not imply existence of a binary incidence matrix (X). Entry constraints, integrality, and compatibility with exterior edges can add restrictions. The equivalence concerns the stated real PSD conditions only. The restriction (n<99) is required; the displayed inverse of (K) does not exist at (n=99).

## Sources and exact controls

- [Principal-projector filtering source](../../experiments/workspace/grid_free_order10_high_mask_graph_projectors.py) defines the two principal matrices used in the domain filter.
- [Exact algebra controls](../../experiments/workspace/grid_free_order10_projector_gram_identity.py) check the cleared formulas without loading a graph domain, count point, tensor, or optimizer.
- The saved control result is `experiments/logs/moments-and-counts/order10-projector-gram-identity.json`.

The identity was independently derived in the coordinator and literature lanes. No exterior-Gram domain scan was run.
