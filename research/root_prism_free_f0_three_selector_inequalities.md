# Three-selector Boolean moment inequalities

The F0 model has binary selectors z_a, first moments x_a, and pair moments
Z_ab. The existing linear model and positive semidefinite conditions
need not describe moments of a joint Boolean distribution. The following
rows use that additional Boolean information.

For three distinct signatures a,b,c, the pointwise slack

\[
z_b+z_a z_c-z_a z_b-z_b z_c
\]

equals z_a*z_c when z_b=0, and (1-z_a)*(1-z_c) when z_b=1.
It is nonnegative. Averaging gives the triangle inequality

\[
Z_{ab}+Z_{bc}-Z_{ac}\le x_b.
\]

The second slack

\[
1-z_a-z_b-z_c+z_a z_b+z_a z_c+z_b z_c
\]

is one when all three bits agree and zero otherwise. It gives

\[
x_a+x_b+x_c-Z_{ab}-Z_{ac}-Z_{bc}\le1.
\]

The source checks all eight assignments directly. Neither argument
assumes that different selectors are independent. Both remain valid
under the same average over actual fixed-core relabelings used by the
existing quotient model.

## Relation to existing constraints

These inequalities can add information beyond pair bounds and an
augmented moment matrix being positive semidefinite. For example, take
three first moments equal to 1/2 and all distinct pair moments equal
to 1/8. Every pair satisfies its usual bounds. The Schur complement of
the constant entry in the augmented moment matrix is (3I-J)/8, which
is positive semidefinite. But the second displayed inequality has left
side 9/8, so it fails. This is a three-variable control, not a feasible
point of the full F0 model.

If Z_ac is already proved zero, the triangle inequality becomes
Z_ab+Z_bc<=x_b. Combining it with Y_ab<=Z_ab and Y_bc<=Z_bc gives the
corresponding homogeneous edge conflict. The zero pair and activation
bounds alone do not justify that extra linear inference unless the
triangle inequality or another sufficient row is present.

## Complete scope and symmetry coverage

There are 54,950,880 triangle rows with a distinguished center b and
an unordered pair of distinct endpoints. There are 18,316,960 unordered
perimeter rows. Under the twelve actual-core actions, their numbers of
formal row orbits are 4,580,202 and 1,527,066 respectively, before any
coefficient coincidences or fixed-zero substitutions.

Every center belongs to one of 42 selector orbits. The preparation
records an explicit action taking each of the 480 centers to its
representative. For the triangle family, it is therefore enough to
test each representative center and all unordered pairs of other
signatures. For the perimeter family, take any vertex of the triple
to its representative; the same anchored enumeration covers the
whole family, with allowed duplication.

Each family consequently needs 42*binom(479,2)=4,808,202 anchored pair
evaluations. This coverage uses invariance of a quotient assignment.
It does not assume that a core relabeling extends to an automorphism
of a hypothetical full graph.

The source checks all twelve fixed-core actions, all 144 compositions,
all 42 selector orbits and all 9,742 pair orbits. It binds the 389
eliminated pair variables to their original exact zero equations.
Repeated quotient coefficients are added, including cancellation.
There are 1,458 separate coefficient-alias controls.

## Prepared continuation

The point-independent preparation took 3.648994 seconds. It constructs
no complete row list and reads no fractional point. The source is
`experiments/workspace/root_prism_free_f0_three_selector_inequalities.py`,
SHA256 `1b3f77db3479971b51b40b0f48246d3944dd14c963cae2c77959c4400bd3d3bb`.
The preparation record is
`experiments/logs/root-prism-free/f0-three-selector-inequalities-scope01.json`,
SHA256 `c7f574ef0ed1a05a54dc33404c5c8a1fa4c6c059340d45503a4ceeea88d8c655`.

A later separator would bind one saved numerical proposal, use at most
eight numerical candidates per anchor and family, then retain at most
64 exact rows per family. Every retained row must have an exact dyadic
gap and the pointwise Boolean proof above. A numerical scan without a
found cut would not certify all rows exactly. The point binding,
arithmetic bounds, scan source and cold certificate replay still need
their separate preparation. No scan or optimization has run here.
