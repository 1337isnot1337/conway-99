# A fixed transversal coclique and its exterior signatures

This reduction retains the incidence pattern of a coclique containing seven
neighbors of one root. It is a necessary condition for a Conway graph. The
completed checks below do not prove nonexistence.

## The determined core

Let the root be o. Write its seven neighboring edges as {t_i,u_i}, with the
chosen transversal T={t_i} contained in a maximal coclique I. Write |I|=h and
S=I\T. Each vertex of S has exactly two neighbors of o, both among the u_i.
Its pair of indices is an edge of a simple graph L on seven vertices. Distinct
vertices of S have different pairs. Thus L has h−7 edges.

The graph on I together with o,u_1,...,u_7 is completely determined by L:
I is independent; o is adjacent to the t_i and u_i; u_i is adjacent to t_i
and to the S vertices whose labels contain i. There are no other edges.

Let M be the h-by-8 incidence matrix from I to (o,u_1,...,u_7), let
D=M^T M, and let B be the adjacency matrix of the star on these eight
vertices. The column-degree vector is

    d=(7, 1+deg_L(1), ..., 1+deg_L(7)).

Here D_00=7, D_0i=1, D_ii=d_i, and D_ij is the indicator of ij in L when
i,j are distinct positive indices.

The two positive semidefinite graph matrices are

    W=3I−A+J/9,        V=4I+A−2J/11.

Their restrictions to the coclique are 3I_h+J_h/9 and 4I_h−2J_h/11.
For h<22 both are positive definite. Taking their Schur complements gives

    S_− = 3I_8−B−D/3 + (d+3)(d+3)^T/[3(h+27)],
    S_+ = 4I_8+B−D/4 − (d−4)(d−4)^T/[4(22−h)].

Both matrices must be positive semidefinite. This argument uses the
restriction of a positive semidefinite matrix and the exact inverse of a
scalar matrix plus a multiple of J. No graph automorphism is assumed.

## An exact census at h=20

For a maximal coclique, every vertex outside it has a degree into I between
one and seven. The usual three incidence sums imply

    sum_(x outside I) (d(x)−3)(d(x)−4) = 2(h−22)(h−27).

Every summand is a nonnegative integer. The eight known vertices therefore
give, at h=20,

    12 + sum_i (deg_L(i)−2)(deg_L(i)−3) <= 28.

Of the 203,490 labeled 13-edge graphs on seven vertices, exactly 134,085
pass this budget. They have exactly 56 isomorphism types. Every one of the
56 types passes both core projector tests. Thus these core tests give no
additional exclusion at h=20.

`transversal_constraints.py --audit-twenty` checks this claim with integers.
It enumerates every labeled 13-edge graph, expands each representative under
all 7! vertex permutations, and verifies that the disjoint orbits cover the
admissible set exactly. For each representative it checks positive leading
principal minors of the seven unmatched-neighbor block in both scaled Schur
matrices. The full eight-point matrices have kernel vectors (4,1,...,1) and
(−3,1,...,1), respectively. The positive definite seven-point blocks and
these kernel vectors prove that the eight-point matrices are positive
semidefinite. The enumeration does not rely on a floating eigenvalue sign.

The replay output is
[`transversal-core20.json`](../../experiments/logs/independent-sets/transversal-core20.json).

## Exterior signatures

The remaining vertices retain their distinct pairs of signed root-neighbor
labels. For each such label w, a signature is its subset of neighbors in S.
Write q_i for the number of selected S labels containing i. The outer-row
anchor equations require q_i<=1 on either axis occurring in w, and q_i<=2
on every other axis. Also the degree into I is the signature size plus the
number of t-labels in w, and lies between one and seven.

There is a further exact spectral filter. Restrict each scaled Schur matrix
to u_1,...,u_7 and call the result K_− or K_+. These blocks are positive
definite for all 56 h=20 cases. For a candidate exterior vertex let e_i be
its adjacency to u_i, let c_i be its number of common neighbors in I with
u_i, and let a be its degree into I. Let d now denote the seven-vector of
degrees of the u_i into I. The two extended columns and diagonal entries are

    v_− = −(h+27)(3e+c) + (d+3)(a+3),
    b_− = (h+27)(9−a) + (a+3)^2,

    v_+ = (22−h)(4e−c) − (d−4)(a−4),
    b_+ = (22−h)(16−a) − (a−4)^2.

Each candidate must satisfy v_−^T K_−^−1 v_−<=b_− and
v_+^T K_+^−1 v_+<=b_+. The implementation writes each rational inverse as
an integer matrix divided by a positive integer, verifies the inverse by
matrix multiplication, and evaluates these inequalities with integers. It
checks an explicit bound before using 64-bit arithmetic.

For the surviving signatures, assign one nonnegative variable to each
(signed label, signature) pair. Require the variables for each signed label
to sum to one. For each vertex s in S and each near anchor a, require its
total selected exterior neighbors carrying a to be 2 minus the indicator
that s uses the axis of a. For distinct s,t in S, require their number of
common exterior neighbors to be 2 minus the number of shared u-labels.

These equations express the full common-neighbor identities on the
determined core. Fractional solutions only prove feasibility of this
relaxation. Even an integral signature selection would give a partial
adjacency matrix; the edges among the exterior vertices still need to be
constructed and checked.

The implementation is
[`transversal_constraints_incidence.py`](../../experiments/workspace/transversal_constraints_incidence.py).
Its LP output reports solver status and the maximum residual against every
original equality. A floating feasible point is not an exact certificate.

## Replay

From the repository root:

```sh
.venv/bin/python experiments/workspace/transversal_constraints.py --audit-twenty
OPENBLAS_NUM_THREADS=1 .venv/bin/python experiments/workspace/transversal_constraints_incidence.py --h 20 --seconds 15
```

The core audit needs NumPy, SymPy, and NetworkX. The exterior relaxation also
needs SciPy. These scripts do not use a size-20 bound for arbitrary maximum
cocliques. The size restriction applies only to the transversal cocliques
constructed in `hemisphere.md`.
