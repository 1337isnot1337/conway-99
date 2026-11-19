# Conditioning the F0 projectors on the complete fixed core

This note concerns component zero in the prism-free, F-free split
eighteen-plus-eighteen case. The other component and its fiber alignment
remain free. It adds the three central-triangle vertices to the eighteen
component vertices used in the earlier Schur calculation.

The calculation gives two exact necessary matrix inequalities. It does
not prove infeasibility or assume that a numerical proposal is feasible.

## The two graph projectors

For the adjacency matrix A of a hypothetical SRG(99,14,1,2), define

    Q_plus  = 27I - 9A + J,
    Q_minus = 44I + 11A - 2J.

Both matrices are positive semidefinite. Their nonzero eigenvalues are
63 on the negative-four eigenspace and 77 on the positive-three
eigenspace, respectively. Each annihilates the all-ones vector.

Let C be the adjacency matrix of the fixed eighteen-vertex component.
Its three six-vertex fibers have indicators f_1,f_2,f_3. Every component
vertex has exactly one neighbor in each fiber, so

    C f_i = 1,   C 1 = 3*1.

The old core matrices are

    K_plus  = 27I - 9C + J,
    K_minus = 44I + 11C - 2J.

They are positive definite. Their eigenvalues on the all-ones direction
are 18 and 41. On the two-dimensional space spanned by the fiber
indicators with coefficient sum zero, their eigenvalues are 27 and 44.

For an admissible component-neighbor triple a, let h_a be its indicator.
Set

    eta_i(a) = f_i^T h_a,
    d_i(a) = eta_i(a)-1.

Every triple has size three, so the three entries of d(a) sum to zero.
The existing full domain contains 480 triples. No triple is deleted in
this calculation.

## The three added vertices

Each central-triangle vertex has six neighbors in its corresponding
component fiber and no neighbor among the sixty exterior vertices.
Let R be the three-by-eighteen projector cross block from the central
triangle to the component. Its rows are

    R_plus,i  = 1^T - 9 f_i^T,
    R_minus,i = -2*1^T + 11 f_i^T.

The cross vector from the component to exterior signature a is

    u_plus,a  = 1 - 9 h_a,
    u_minus,a = -2*1 + 11 h_a.

The cross vector from the central triangle to that exterior vertex is
1 or -2 in all three entries. After conditioning on the component,
the residual vectors therefore are

    q_plus,i(a)  = -3 d_i(a),
    q_minus,i(a) = -77/41 - (11/4) d_i(a).

These formulas follow by separating each fiber indicator into its
constant part and its part perpendicular to 1. Direct exact matrix
inversion verifies all 480 residual vectors for each family.

The remaining central-triangle blocks are

    T_plus = 18I - 6J,

and the matrix T_minus with diagonal 1221/41 and off-diagonal 1089/82.
The plus block has kernel spanned by 1 and eigenvalue 18 on its
orthogonal complement. Every q_plus(a) lies in that complement.
The minus block is positive definite, with eigenvalue 33/2 on that
complement and eigenvalue 2310/41 on the constant direction.

Thus the additional Schur corrections between signatures a and b are

    Delta_plus(a,b)  = d(a)^T d(b)/2,
    Delta_minus(a,b) = 77/410 + (11/24) d(a)^T d(b).

For the plus family, the complete fixed 21-core has rank twenty.
Conditioning on the eighteen component vertices and any two of the
three central vertices gives the same correction. The third residual
row is their negative sum. This avoids any numerical pseudoinverse.
The minus 21-core has rank twenty-one and an ordinary rational inverse.

## The necessary averaged matrices

Let x_a be the selector moment, Y_ab the exterior-edge moment, and
Z_ab the joint-selector moment, with Z_aa=x_a and Y_aa=0. Let S_plus
and S_minus be the earlier eighteen-core Schur matrices. The new
necessary conditions are

    S_plus  - (1/2) [d(a)^T d(b) Z_ab]_(a,b) >= 0,

    S_minus - (77/410) Z
            - (11/24) [d(a)^T d(b) Z_ab]_(a,b) >= 0.

Here >=0 means positive semidefinite. The correction includes the
diagonal. In particular, its diagonal uses x_a, not x_a squared.

For an individual graph embedding, pad the selected sixty exterior
vertices by zeros to the complete 480-signature domain. Its selector
vector z has Z=zz^T. The full-core Schur complement is positive
semidefinite on this padded domain. Averaging these valid matrices
gives the displayed formulas with general moments x,Y,Z. This argument
does not impose a symmetry on the unknown graph or replace Z_ab by
x_a*x_b.

The two subtracted correction matrices are positive semidefinite for
every genuine selector moment matrix Z. Thus conditioning on the full
fixed core is at least as strong as conditioning on the component.
Whether it adds an independent constraint to the complete existing
averaged linear and PSD system is a separate question.

## The constant part of the minus correction

The constant correction can also be derived from the per-embedding
identity

    S_minus * 1 = (462/41) z.

Since sum(z)=60, projecting the positive semidefinite S_minus matrix
off its all-ones direction gives

    S_minus - (77/410) zz^T >= 0.

Averaging gives the term (77/410)Z above. The two fiber-contrast
directions account for the remaining term. This derivation uses
the per-embedding identity before averaging; replacing zz^T by the
outer product of averaged selectors would yield a different condition.

## Exact verification

The independent source
[root_prism_free_f0_full_core_schur_audit.py](../experiments/workspace/root_prism_free_f0_full_core_schur_audit.py)
reads only the frozen core/domain and the old exact projector record.
It does not read a numerical point or import the new kernel builder.
It performs the following checks:

- Reconstruct all three fibers and verify every component-to-fiber degree.
- Check the exact central Schur blocks and all 480 residual cross vectors.
- Check positive rational LDL pivots of the selected 20-core and full
  minus 21-core.
- Compare all 115,440 kernel entries in each family against a direct
  inversion of that larger core, the old saved entries, and the closed
  correction formulas.

The entire calculation passes in 6.610 seconds. A separate cold replay
reproduces its mathematical record exactly. No optimizer or point
contraction is used.

Clearing the final plus-kernel denominators requires only 60; the
largest absolute integer coefficient is 1,238. For the minus family,
the common denominator is 254,280 and all cleared coefficients have
a common factor eleven. Removing it leaves maximum coefficient
791,964. At vector-entry bound 1,024 and orbit size at most twelve,
the raw orbit-sum coefficients are bounded by 31,155,290,112 and
19,930,426,638,336, respectively. Both bounds are below 2^53, so exact
dyadic conversion remains available for a separately prepared query.

The report is
[f0-full-core-schur-independent-audit.json](../experiments/logs/root-prism-free/f0-full-core-schur-independent-audit.json).
Its replay is
[f0-full-core-schur-independent-audit-replay.json](../experiments/logs/root-prism-free/f0-full-core-schur-independent-audit-replay.json).
These are necessary-condition and source-verification results. They
contain no accepted graph, exclusion, or full-PSD claim about a point.
