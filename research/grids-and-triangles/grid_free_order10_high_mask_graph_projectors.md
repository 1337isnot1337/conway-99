# Exact spectral filtering of the complete high-graph domain

The complete principal-projector filter removes 22,146 of the 157,711 saved local graphs.
It retains 135,565 graphs, with an exact integer certificate for every removal.
All 200 positive-mass graphs in the earlier moment witness survive.
Thus this stronger finite domain still permits the saved moment point.
The [separate transferred witness](grid_free_order10_high_mask_graph_filtered_witness.md) requires no new optimizer call.

## Necessary principal matrices

In a Conway graph, the nontrivial adjacency eigenvalues are three and minus four.
The following matrices are positive multiples of its two nontrivial spectral projectors:

\[
P_+=27I-9A+J,\qquad P_-=44I+11A-2J.
\]

Their nonzero eigenvalues are 63 and 77, respectively.
Every principal submatrix is therefore positive semidefinite.
Apply these conditions to each graph in the [complete high-vertex domain](grid_free_order10_high_mask_graph_domain.md).
That graph contains the six independent roots and at most ten high vertices.
No prism or `x521` assumption enters this filter.

Write its adjacency matrix as

\[
B=\begin{pmatrix}0&M\\M^T&H\end{pmatrix}.
\]

Here `M` has six rows, and its columns are the high masks.
The matrix `H` describes the high-vertex edges.
Let `d` be the vector of column sizes of `M`.
The root blocks of both projectors are positive definite.
Their Schur complements are positive multiples of these integer matrices:

\[
Q_+=297I-99H+9J+3(d\mathbf1^T+\mathbf1d^T)-33M^TM+dd^T,
\]

\[
Q_-=256I+64H-16J-16M^TM+4(d\mathbf1^T+\mathbf1d^T)-dd^T.
\]

The first Schur complement is `Q_+/11`.
The second is `11 Q_-/64`.
These matrices have order at most ten, which reduces the exact arithmetic cost.
An independent source review derives both formulas directly from the root-block inverses.

## Exact negative vectors

For an integer vector `z` on the high vertices, set

\[
s=\mathbf1^Tz,\qquad D=d^Tz,\qquad u=Mz.
\]

The following integer vectors lift a Schur obstruction to the full principal matrix:

\[
v_+=(33u-3s\mathbf1-D\mathbf1,\;99z),
\]

\[
v_-=(-16u+4s\mathbf1-D\mathbf1,\;64z).
\]

Their quadratic values satisfy

\[
v_+^TP_+(B)v_+=891z^TQ_+z,
\qquad
v_-^TP_-(B)v_-=704z^TQ_-z.
\]

Every discarded graph has a saved integer `z` with a negative value.
The generator checks the lifted vector against the full literal adjacency matrix.
The cold replay checks that full quadratic again, without using the elimination routine.
The largest saved Schur-vector entry uses twenty bits.

## Classification and scope checks

The exact classifier uses fraction-free symmetric elimination.
A positive pivot gives the next Schur complement.
A zero pivot with a nonzero off-diagonal entry gives an explicit negative vector on two residual coordinates.
A zero residual row can be skipped.
Reverse elimination then gives a vector in the original Schur coordinates.

The controls compare the classifier with 3,707 independent principal minors on 306 symmetric matrices.
They also check 14,486 Schur entries and 498 integer lifts directly.
Both principal matrices pass on the nine-vertex rook graph.
The complete graph on five vertices supplies a negative-vector control.

The first scan stops after sixty seconds at column 153,727.
It removes 20,601 graphs and retains every unvisited column.
A separate cold replay checks every removal from this partial result.
A frozen continuation checks only the remaining 3,984 columns in 2.16 seconds.
It preserves the first rejection list exactly and repeats no previous classification.

The final filter covers all 157,711 columns and removes 22,146.
Every removal comes from the first projector.
The second projector removes no additional survivor.
The retained complement has 135,565 columns.
The final removal-only replay checks all 22,146 full-matrix negative vectors.
It does not repeat positive classification of the entire domain.

## The moment witness survives

Restricting the saved feature map to the retained graphs gives 17,922 distinct columns.
The restricted matrix has 200 rows and 757,947 nonzero entries.
Every positive-mass graph in the earlier exact witness belongs to this retained domain.
Consequently its existing rational masses still satisfy all 200 equations.
The transferred witness also checks both full projector characteristic polynomials on all 200 support graphs.

These certificates concern local graphs and a finite rational moment measure.
They do not supply an integer embedding measure or an exterior completion.
The next necessary condition asks whether the local graphs admit complete outside-incidence counts.

The [exterior-Gram identity](projector_exterior_gram_identity.md) proves a useful redundancy.
For every symmetric core of order less than 99, both principal PSD conditions equal centered exterior-Gram PSD.
A separate ordinary exterior-Gram PSD scan would add no restriction.

## Frozen records

The [projector manifest](../../experiments/logs/moments-and-counts/order10-high-mask-graph-projectors-manifest.json) binds the sources, both scan stages, and every removal certificate.
The transferred moment witness has a separate manifest and cold replay.

| Record | SHA-256 |
| --- | --- |
| Classifier source | `6582189b3d6f541bb46aec5e86123a507e8622e023e1f6f73093ab86cf53660d` |
| Independent source review | `0b95c44eb597be983b54be3a6a12ac48814216f867dfc713098b99aaff73c270` |
| Suffix continuation source | `ba9b596969fd69a3c6aa753de3ae9bd4a325daad357b4f740e61afeb40ed7b55` |
| Complete filter | `9160decc71391fe42ec3f523b773f90708645bb524067122884c6d42e4c9566f` |
| Complete removal replay | `c4811ece424b8aabb789b36c687ee00d76b70eb010a30bb23740edcf0ca764ed` |
