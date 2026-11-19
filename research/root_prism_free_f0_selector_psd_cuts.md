# Exact cuts from the augmented selector moment matrix

This package prepares a PSD separation mechanism for the complete 480-selector
component-zero domain. It does not run a production spectral scan or change
the frozen linear model. A numerical proposal need not be feasible to suggest
a valid cut. The cut is proved by its exact integer vector and the frozen
moment formulas, not by the proposal's status.

## Necessary moment matrix

For a possible graph, let z be its binary vector of selected component triples.
Relabel the fixed component by each of the 12 verified core actions and average.
Write x for the average of z, and Z for the average of zz transpose. Then

\[
M=\begin{pmatrix}1&x^T\\x&Z\end{pmatrix}
 =\frac1{12}\sum_g
 \begin{pmatrix}1\\g z\end{pmatrix}
 \begin{pmatrix}1\\g z\end{pmatrix}^{T}\succeq0.
\]

This uses convex averaging of necessary conditions. It does not assume a
completed graph has any of the core automorphisms. All 480 selectors occur in
M, which has order 481. In particular, no support is discarded because a
numerical proposal assigns a small value to it.

The diagonal is Z_aa=x_a. For any integer vector (c,v), the exact inequality is

\[
-\sum_a(v_a^2+2cv_a)x_a
-2\sum_{a<b}v_av_bZ_{ab}\le c^2. \tag{1}
\]

The right side minus the left side equals (c,v) transpose M(c,v). For a
single binary incidence this is the square of c+sum(v_a z_a). For an average
it is the average of those squares. Rational vectors give the same family
after multiplication by a common denominator.

The linear model also has the population identities sum(x)=60 and Z1=60x.
On that exact affine space, augmented PSD is equivalent to Z being PSD:
for w=v+(c/60)1, one has w transpose Z w=(c,v) transpose M(c,v). The extractor
nevertheless uses the full 481 matrix. It does not assume an unresolved
numerical proposal satisfies those identities.

## Exact quotient and zero substitution

The frozen model has 42 selector orbits and 9,742 distinct-pair orbits. The
extractor expands (1) over every one of the 480 diagonal positions and 114,960
off-diagonal pairs. It sums the literal coefficients in each orbit. An
independent orbit-sum expression checks every aggregated coefficient.

Only the 389 pair-orbit variables with explicit zero equalities in the frozen
original model are substituted by zero. No eigenvector support assumption or
new zero is used. The resulting row is written in the unchanged 15,200-variable
reduced order. Every Y coefficient is zero. A common positive divisor of all
coefficients and the right side may be removed exactly; there is no rounding
of a threshold.

The domain loader verifies all 12 selector permutations, their composition
closure, every selector and pair orbit, and every substituted zero equality.
Transforming a vector by a core action gives the same quotient inequality.
No separate orbit copies are needed for an already invariant quotient point.

## Numerical proposal, exact acceptance

The prepared scanner reads the hash-bound reduced-coordinate output of a
numerical run. It records the proposing status and validity flag without
turning either into an acceptance condition. It expands x and Z, places the
constant 1 in the augmented corner, and makes one symmetric eigendecomposition.

At most eight negative numerical eigenvectors are proposed. Their entries are
rounded after rescaling at 1, 4, 16, 64, 256, 1,024 and 4,096. A primitive
integer vector, with its first nonzero entry positive, is retained as the
certificate. At most 32 distinct cuts are kept. This finite list is a
separator attempt, not a complete PSD test.

Every recorded coefficient comes from exact Python integer arithmetic.
Each orbit has at most 12 members, so with vector entries bounded by s=4,096,
the absolute raw quotient coefficient is at most 36s squared, or 603,979,776.
All such coefficients, and the right side, are represented exactly in
binary64 if a later linear model uses them.

For deciding whether the proposing array violates a cut, each saved binary64
value is converted losslessly to its integer-over-power-of-two form. The row
gap is evaluated exactly. A separate full-coordinate expansion of the
quadratic form must give the same value with opposite sign and the recorded
positive divisor. Only strict exact violations are kept. Inequalities that
already hold throughout the unit box are omitted.

A retained cut may still follow from other linear rows. No claim of a new
independent constraint is made merely because an infeasible proposal violates
it. A scan that finds no retained vector is unresolved. It is not a PSD
certificate, a feasible point, or an infeasibility proof for the model.

## Controls and replay scope

The generic controls check 4,662 Boolean evaluations of the literal square
identity. They include an infeasible numerical-style proposal that violates
a valid moment inequality, showing why proposal feasibility is unnecessary.

The full-domain controls average three Boolean incidences, including the
archived 60-triple component incidence, over the complete core group. Nine
vector/mixture checks reproduce the exact sum of squares after quotienting
and zero substitution. All 36 tested vector transports give the same quotient
row. These are controls for moment algebra only. They make no assertion that
the old incidence satisfies the stronger exterior constraints.

Preparation uses no optimizer or eigendecomposition. The prospective scan
has a cooperative 60-second allowance, one eigendecomposition and explicit
direction/cut limits; any cooperative overrun is recorded. The replay uses
only integer arithmetic, performs no eigendecomposition, reconstructs every
retained row and checks its exact proposal gap. A separate reviewed runtime
gate is required before scanning a production proposal. No PSD row enters an
LP automatically.

The core projector and Schur families from the full preparation remain
separate. This first mechanism implements only the augmented selector moment
matrix.
