# One-edge Schur obstructions and their guarded linear consequences

## Scope and activation

Let a,b,c be three distinct literal exterior signatures. The selector x_i and edge Y_ij are Boolean, and Y_ij <= x_i,x_j. The full-core Schur kernel is a necessary PSD matrix for every actual completion. Suppose its principal block on a,b,c is not PSD when all three selectors are present and the sole edge is ab.

The exact clause is
\[
 x_c+Y_{ab}-Y_{ac}-Y_{bc}\le1. \tag{G}
\]
If Y_ab=0 or x_c=0, endpoint activation makes the inequality automatic. If Y_ab=x_c=1, all three selectors are present, and (G) excludes precisely Y_ac=Y_bc=0. The guards x_a,x_b can be removed because Y_ab already implies them. The isolated selector guard x_c cannot be removed: x_a=x_b=Y_ab=1 and x_c=Y_ac=Y_bc=0 is not the rejected three-selector pattern.

The two other one-edge orientations give the corresponding permutations of (G). If the PSD certificate has an additional Boolean anchor/center premise g=1 which is not implied by these variables, retain it:
\[
 g+x_c+Y_{ab}-Y_{ac}-Y_{bc}\le2.
\]
A fixed core vertex contributes no variable guard. An exterior center must not silently be treated as fixed.

All these statements are literal, per completion. Their linear averages remain valid; an averaged selector product must be represented by its moment variable, not replaced by a product of averages.

## Relation to the triangle cover

Write t=Y_ab and s=Y_ac+Y_bc. The already accepted triangle cover is t+s<=2. On the all-selected face, (G) is t<=s. Neither row implies the other over the real cube: the Boolean patterns 100 and 111 witness the two directions.

The two-row edge relaxation
\[
0\le t,u,v\le1,\qquad t\le u+v,\qquad t+u+v\le2
\]
is exactly the convex hull of the six Boolean patterns other than 100 and 111. To see integrality, a vertex with 0<t<1 would need either both u,v bounds active, or both sloping inequalities active. The first option leaves t free or forces t=0; the second forces t=1. Thus every vertex has t=0 or1. The t=0 face is the four-vertex square; the t=1 face is the segment u+v=1. This is a statement about this relaxation, not a claim that all six patterns pass every other model constraint.

The triangle cover has valid selector-lifted forms
\[
 Y_{ab}+Y_{ac}+Y_{bc}\le x_i+x_j
 \quad\text{for each two-element subset }\{i,j\}\subset\{a,b,c\}. \tag{T}
\]
For Boolean selectors, if either chosen selector is absent, the endpoint inequalities prove the bound; if both are present, the original upper bound two suffices. Each lifted row implies the unguarded cover on the continuous box, since x_i+x_j<=2. Whether these rows are already in the native model has not been checked here.

In particular, the weaker consequence t+s<=1+x_c follows from a lifted row containing c and x_i<=1. Combining it with (G) gives
\[
 |s-x_c|\le1-t.
\]
Consequently,
\[
 Y_{ab}=1\quad\Longrightarrow\quad Y_{ac}+Y_{bc}=x_c. \tag{E}
\]
For an active edge ab, every active c covered by such a one-edge obstruction is adjacent to exactly one endpoint. The lifted upper side matters continuously: the unguarded triangle cover alone gives only s<=1 when t=1, even if x_c<1.

## A short literal certificate

The following coefficients are direct lookups in the accepted primitive plus kernel, not an acceptance of the unreplayed pattern census:

- selectors (a,b,c)=(8,73,265);
- signatures ([0,3,6],[1,2,8],[4,7,9]);
- primitive diagonals (878,878,1088);
- zero-edge off-diagonal coefficients (-209,272,274);
- edge coefficient -540, common divisor1, Schur scale60.

The accepted domain and kernel raw hashes are respectively
fa3bd2e5bb541d58cb647aa1d3df95a9d3c17e394836a657ad4f4bf6eb5f6bfe and
a963a88606a9fad78576d711f6ef7bf67eb03032176cebc2af5af700ea7c6708.
The three lexicographic pair coefficient positions are 3868,4060,32530.

At the sole-edge-ab pattern the matrix is
\[
 M=\begin{pmatrix}878&-749&272\\-749&878&274\\272&274&1088\end{pmatrix}.
\]
The integer vector v=(2,2,-1) gives the directly checkable certificate
\[
 v^{\mathsf T}Mv
 =4(878)+4(878)+1088+8(-749)-4(272)-4(274)=-64.
\]
No determinant or eigenvalue computation is needed for this obstruction. The resulting literal row is
\[
 x_{265}+Y_{8,73}-Y_{8,265}-Y_{73,265}\le1.
\]
The three edge IDs are 2409,2551,20822. Direct lookup found none in the committed 1,884 literal edge-zero rows. This does not establish nonredundancy against other constraints.

On the all-selected face the same vector gives the PSD inequality
\[
 4256-4320Y_{ab}+2160(Y_{ac}+Y_{bc})\ge0,
\]
or 270t-135s<=266. Since s>=0,
270(t-s)<=266. The integer t-s is therefore at most zero. Thus the signed clause is already an integer rounding consequence of one small aggregate PSD inequality, with no determinant machinery.

For the fully activated moment formulation, the corresponding valid quadratic-form row is
\[
3512(x_a+x_b)+1088x_c
-1672Z_{ab}-1088Z_{ac}-1096Z_{bc}
-4320Y_{ab}+2160(Y_{ac}+Y_{bc})\ge0.
\]
Here Z_ij denotes the selector-product moment. Its specialization at x_a=x_b=x_c=Z_ab=Z_ac=Z_bc=1 is the preceding row.

More generally, if the first 2x2 principal block of a symmetric integer matrix
M=[[A,D,E],[D,B,F],[E,F,C]] is positive definite and det(M)<0, put p=AB-D^2 and
v=(DF-BE,DE-AF,p). Then
v^T M v=p det(M)<0.
This supplies an exact integer negative direction for an individual rejected pattern.

## What Gram and mixed rows do and do not prove

Pure selector Gram equations do not distinguish edge patterns on an already permitted selector assignment. They could still make the signed row vacuous by excluding joint selector activation; that separate implication has not been tested.

The mixed edge equations can imply particular signed rows, but this requires an exact combination or another explicit certificate. A negative Schur quadratic form does not by itself prove that the existing linear mixed-row relaxation already implies the Boolean cut. No such redundancy claim is made here.

There is a useful aggregate consequence after the signed rows are established. Let C_ab be any set of signatures for which (E) has been proved. Write h_c(i) for incidence with fixed-core vertex i and use the existing mixed equations
\[
 \sum_{d\ne a}h_d(i)Y_{ad}=q_a(i)x_a,\qquad
 \sum_{d\ne b}h_d(i)Y_{bd}=q_b(i)x_b.
\]
When Y_ab=1, nonnegative omitted terms give
\[
 \sum_{c\in C_{ab}}h_c(i)x_c
 \le q_a(i)+q_b(i)-h_a(i)-h_b(i). \tag{Q}
\]
This can be compared with existing selector capacities. A right side zero forces the corresponding selectors to be absent conditional on edge ab. Summing the two exterior degree-eight equations likewise gives
\[
 Y_{ab}=1\Longrightarrow\sum_{c\in C_{ab}}x_c\le14.
\]
These are consequences of the signed PSD rows plus mixed/degree equations, not independent evidence that the signed rows were redundant.

An unconditional linear aggregate is also available. Put m_i=sum_{c in C_ab}h_c(i). Summing (G), using the mixed equations and discarding only nonnegative omitted edge variables yields
\[
 \sum_{c\in C_{ab}}h_c(i)x_c
 +(m_i+h_a(i)+h_b(i))Y_{ab}
 -q_a(i)x_a-q_b(i)x_b\le m_i.
\]
No native query is needed to establish this identity.

For the displayed example, the mixed residual right sides at the three sites of h_c are 4,3,3, so the immediate zero-right-side test does not apply. This is only a three-entry lookup and arithmetic observation, not a mixed-row redundancy audit.

## Status

The reported distribution of 252 extra one-edge failures remains an unreplayed diagnostic. This note proves the general guarded implication conditional on an individual negative PSD certificate, and gives one short literal certificate whose coefficients are bound to the accepted kernels. It does not run or certify a new pattern census, construct a native model, solve a branch, or change any repository ref.
