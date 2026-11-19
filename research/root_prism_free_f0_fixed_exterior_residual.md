# Residual second-incidence checks for a fixed exterior graph

## Scope and historical overlap

This inspector concerns a completely specified induced adjacency matrix D on the sixty exterior vertices. It is not valid to insert a provisional subset of exterior edges into the same equality and treat the resulting matrix as a Gram matrix.

The F0 shell consists of the central triangle, two eighteen-vertex components, and sixty exterior vertices. The central triangle has no neighbors among those sixty vertices. Let H be the specified first-component incidence, with eighteen rows and sixty binary columns of weight three. The second-component incidence H2 has exactly eighteen rows and also has binary columns of weight three. Its component type and relative fiber alignment remain unspecified.

The earlier coupling and first-fixed models constrain a second incidence while leaving exterior adjacency unspecified. The first-design and fixed-selection exterior models instead impose the common symmetric exterior edges, degrees, mixed equations and pair caps. Their source and notes were inspected; no existing fixed-D residual inspector was found in those F0 paths.

The new source is experiments/workspace/root_prism_free_f0_fixed_exterior_residual.py. It imports no solver. Its preparation uses synthetic controls only. No production exterior adjacency was evaluated.

## Residual identity

The SRG adjacency identity is

\[
A^2+A=12I+2J.
\]

Take its exterior-by-exterior block. The central triangle contributes zero. The two component incidences contribute H^T H and H2^T H2. Therefore

\[
R=12I+2J-H^{\mathsf T}H-D^2-D
  =H_2^{\mathsf T}H_2.
\]

The required conditions include

\[
R\succeq0,\qquad \operatorname{rank}(R)\le18,\qquad R_{uu}=3.
\]

The diagonal calculation uses the complete exterior degree eight:

\[
R_{uu}=12+2-3-8=3.
\]

For distinct exterior vertices,

\[
R_{uv}=2-\langle h_u,h_v\rangle-(D^2)_{uv}-D_{uv}.
\]

The previously checked common-neighbor cap makes this nonnegative. All subtracted terms are nonnegative integers, so R_uv is in {0,1,2}. The inspector checks these values explicitly.

These are conditions on one actual fixed adjacency and incidence. They are not rank conditions on a mixture of unrelated adjacency assignments.

## Binary triple inequalities

For binary coordinates a,b,c,

\[
a-ab-ac+bc=a(1-b)(1-c)+(1-a)bc\ge0.
\]

Sum this identity across the eighteen unknown second-component sites. For three distinct exterior vertices u,v,w, it gives

\[
R_{uv}+R_{uw}-R_{vw}\le R_{uu}=3.
\]

There are

\[
60\binom{59}{2}=102\,660
\]

oriented inequalities. A successful inspection checks all of them.

They do not follow from positive semidefiniteness alone. The matrix

\[
\begin{pmatrix}
3&2&2\\
2&3&0\\
2&0&3
\end{pmatrix}
\]

is positive definite: its one-by-one minors are three, its two-by-two principal minors are five, five and nine, and its determinant is three. Nevertheless, the first-centered inequality has left side four and upper bound three.

The converse distinction also matters. The six-by-six matrix with diagonal three, off-diagonal two between the two parts of a three-plus-three partition, and off-diagonal one within a part satisfies every triple inequality and entry bound. The vector (1,1,1,-1,-1,-1) has quadratic value minus six. The inspector therefore retains the PSD test.

These examples compare only the stated matrix conditions. They are not claimed to arise from a complete F0 model point.

## Exact certificates

All arithmetic uses Python integers and exact rational fractions. There is no numerical eigensystem.

The linear-algebra producer performs symmetric Schur elimination and stops after at most nineteen positive pivots. A rejection has one of the following independently checkable forms:

- An invalid residual diagonal or intersection entry.
- Three exterior indices and a strictly positive binary-metric gap.
- A primitive integer vector v with an exactly negative value v^T R v.
- Nineteen principal indices with an exactly nonzero determinant, proving rank at least nineteen.

The negative-vector construction retains the exact congruence transport through every elimination step. If the remaining diagonal is zero but an off-diagonal entry is nonzero, a signed two-coordinate vector supplies a negative direction.

A linear-algebra pass stores an exact decomposition

\[
R=\sum_{i=1}^{r}q_i u_i u_i^{\mathsf T},
\qquad q_i>0,\quad u_i\in\mathbb Z^{60},\quad r\le18.
\]

A positive principal minor confirms the recorded rank. The verifier reconstructs every matrix entry from these factors. It evaluates negative quadratic forms directly and uses a separate integer Bareiss determinant routine for minor certificates. It does not repeat the producer's Schur elimination.

A pass remains a necessary-condition result. A positive rational factorization does not construct a binary eighteen-row incidence, let alone a graph.

## Input and replay boundary

The future input consists of the frozen fixed-selection model and a bare JSON array of sixty integer adjacency bit rows, in the model's saved exterior-vertex order. The model producer is the reviewed source with SHA-256 2c8a0f7f2bc2a219c994f42618585879e16a6d3a5809627b9aea25be40798160. The fixed core and complete first-signature domain come from the baseline archive with SHA-256 703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782.

The inspector reconstructs the first incidence from its sixty distinct original signature IDs. It checks all 171 original component Gram entries and the population, all sixty exterior degrees, all 1,080 mixed equations, and all 1,770 exterior pair caps. It checks symmetry, zero diagonal and exact integer bit rows. The actual model file and adjacency file hashes are saved with the residual matrix and certificate.

This input validation does not replace the separate acceptance of all current literal cuts or the exterior SAT receipt. It does not apply the 162 additional Y-zero orbits. A defect excludes the specified H,D combination, not every incidence or the whole F0 case.

The replay reconstructs the residual from the original files, checks their exact bindings, and verifies the saved certificate independently. No production call is authorized merely by the synthetic preparation.

## Completed synthetic preparation

The preparation passes the following checks:

- Eight small or large-integer linear-algebra cases, including zero matrices, negative diagonals, zero-pivot indefinite matrices and a rank-nineteen positive matrix.
- The positive-definite triple-metric counterexample and two positive-definite matrices with invalid binary-intersection entries.
- The six-by-six metric-passing indefinite example.
- Sixty distinct binary triples on eighteen sites, giving an exact rank-eighteen Gram matrix; all 1,830 upper entries and all 102,660 oriented triple inequalities pass.
- Nine literal block partitions of the nine-vertex rook graph, using its corresponding SRG constant two, independently confirming the residual block formula.
- Rejection of mutations to an integer negative vector, a minor determinant, and a positive factor weight.

The preparation completed in 0.43010632699588314 seconds under a thirty-second shell deadline. It tested no production candidate, imported no native solver and made no optimizer call.
