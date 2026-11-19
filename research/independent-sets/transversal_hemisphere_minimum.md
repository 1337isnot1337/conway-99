# A minimum Ramsey hemisphere survives the local spectral test

The current root-core relaxation does not imply that every 21-vertex
hemisphere has an independent eight-set. There is an explicit 35-edge,
triangle-free graph with independence number seven whose vertices can be
labeled by the 21 edges of K7 so that all local common-neighbor bounds and
both exact spectral projector tests hold. Its 63-label exterior incidence
relaxation is also numerically feasible.

This is a limitation of the relaxation, not a graph on 99 vertices. A
45-second Boolean signature-selection search did not decide whether this
particular labeling admits integral exterior incidences.

## Input graph and source

Goedgebeur and Radziszowski's
[Theorem 2](https://arxiv.org/html/1210.5826v4) gives
e(3,k+1,n)=5n-10k when 5k/2<n<=3k. Thus e(3,8,21)=35.
The input graph comes from the
[House of Graphs minimum Ramsey collection](https://houseofgraphs.org/data/ramsey/minramsey/Ramseygraphs_3_8_21_e35.g6).
It is saved as
[`transversal-hemisphere-minimal21.g6`](../../experiments/workspace/transversal-hemisphere-minimal21.g6).
The replay script verifies its order, edge count, absence of triangles, and
independence number directly. No catalogue uniqueness assertion is needed
for this witness.

Write A for its adjacency matrix. Its degrees are fourteen threes and
seven fours. The seven degree-four vertices induce a seven-cycle. Every
pair has at most two common neighbors.

## Exact core spectral criterion

Let o be the root, with near matching edges u_a t_a for a=0,...,6. The
hemisphere H consists of the 21 outer vertices whose labels use only the
u_a. Its 21-by-7 incidence matrix B has one row for every edge of K7:

    B 1 = 2 1,    B^T B = 5 I + J.

The induced 36-vertex core contains o, all fourteen near vertices, and H.
Each H vertex has its two prescribed u-neighbors and no t-neighbors.
Eliminate the fourteen near vertices from the two SRG spectral forms

    W = 3 I - A_core + J/9,
    V = 4 I + A_core - 2J/11.

The eliminated blocks are positive definite. Their exact Schur complements
on H are Q/8 and P/15, where

    Q = 24 I - 8 A - 3 B B^T + 2 J,
    P = 60 I + 15 A - 4 B B^T - 2 J.

The remaining root row is dependent: W annihilates the vector with root
coordinate 4, all fourteen near coordinates 1, and all H coordinates 0;
V annihilates the analogous vector with root coordinate -3. Hence these
two reduced matrices exactly test positive semidefiniteness of the two
36-vertex core forms. The replay verifies both Schur identities with
rational arithmetic.

The successful labeling, in graph6 vertex order, is

    01,23,02,13,03,34,25,05,24,45,06,
    35,16,12,46,04,56,15,26,36,14.

Here, for example, 35 means the unordered pair {3,5}. This labeling passes
every local codegree bound: for distinct core vertices i,j,

    (A_core^2 + A_core)[i,j] <= 2.

Both Q and P are positive definite. Exact symmetric elimination has
strictly positive rational pivots at all 21 steps. The full core forms
each have rank 35. Approximate least eigenvalues of Q and P are 0.5413 and
8.4494, respectively; the exact pivot checks establish the signs.

The search used integer spectral cuts. If c_ij records whether H vertices
i and j share an axis, an integer vector v gives the necessary inequality

    6 sum_{i<j} v_i v_j c_ij
       <= 18 sum_i v_i^2 - 8 v^T A v + 2 (sum_i v_i)^2.

Every inserted cut was checked to have an exact negative quadratic value
at the discarded labeling. Three such cuts sufficed to find the displayed
labeling. No exhaustive classification of the possible labelings was run.

## Exterior signatures

The remaining outer labels are 42 mixed u/t labels and 21 t/t labels.
For a remaining vertex x, let s be its zero-one adjacency vector to H.
Let e,t be the seven-vectors specifying its u- and t-anchors. Every
signature must satisfy

    B^T s <= 2 1 - e - t,
    (A+I) s <= 2 1 - B e.

For H vertices i,j, the remaining number of common neighbors is

    r_ij = 2 - A_ij - (A^2)_ij - (B B^T)_ij.

If r_ij=0, a signature cannot contain both i and j. The compatibility
graph has 1,732 clique signatures including the empty signature; its
largest signature has size seven.

There are also exact single-vertex spectral tests. Define

    q = 2 1 - 8 s - 3 B e - B t,
    p = 15 s - 4 B e + B t - 2 1.

The extended Schur matrices require

    q^T Q^-1 q <= 20,    p^T P^-1 p <= 50.

The implementation scales each inverse to an integer matrix with a
positive integer denominator and verifies the inverse identity. It then
performs these tests with unbounded integers. Between 113 and 327
signatures remain for each signed label, for 11,760 variables in total.

The LP gives each label total signature weight one. For every H vertex i
and axis a it requires the number of exterior neighbors carrying u_a to
be 2-B_ia-(AB)_ia and the number carrying t_a to be 2-B_ia. For each pair
of H vertices it requires exactly r_ij common exterior neighbors. These
are 567 equalities with 123,108 nonzero coefficients.

HiGHS returned a floating feasible solution with maximum equality
residual below 2.4e-13 and minimum variable greater than -1.5e-14. This
point is numerical evidence only. It is not an exact rational certificate.
The Boolean version returned UNKNOWN after its 45-second solver budget.
Neither search supplies the edges between exterior vertices.

## Reproduction

The exact core witness can be replayed without a SAT or LP solver:

```sh
.venv/bin/python experiments/workspace/transversal_constraints_hemisphere_verify.py
```

The graph and labeling discovery, exterior relaxation, and bounded Boolean
selection are separate scripts:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python experiments/workspace/transversal_constraints_hemisphere_spectral.py --seconds 45
OPENBLAS_NUM_THREADS=1 .venv/bin/python experiments/workspace/transversal_constraints_hemisphere_incidence.py --seconds 30
OPENBLAS_NUM_THREADS=1 .venv/bin/python experiments/workspace/transversal_constraints_hemisphere_integer.py --seconds 45
```

The saved input and outputs use the prefix
`transversal-hemisphere-minimal21` in
[`experiments/logs/independent-sets`](../../experiments/logs/independent-sets).
The first labeling found by the weaker local search failed Q; that result
is retained separately from the successful spectral labeling.
