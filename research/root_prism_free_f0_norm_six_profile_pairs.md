# A small norm-six profile-pair experiment

This note records the frozen preparation for three local count experiments
on selector orbits 2 and 3. No local composition scan or full count query had
run at the preparation checkpoint. The preparation completed in 0.589 seconds.
The later terminal result is recorded separately in
`root_prism_free_f0_norm_six_profile_pair_result.md`.

Each selected local profile has population three and plus-representation
norm \(B_{ii}=6\), using the exact integer columns from
`root_prism_free_f0_two_dimensional_moments.py`. The frozen local inverse
tables supply every preimage. No selector subsets are enumerated again.

## The necessary restriction

For two integer representation vectors \(u,v\), with both H-norms equal to
six,

\[
36-B_{ij}^2=3\det[u,v]^2.
\]

Thus the possible integer inner products are
\(B_{ij}\in\{-6,-3,3,6\}\). In particular, zero passes the PSD and
divisibility-by-three tests but fails the integer-square test:
\(36/3=12\) is not an integer square.

For these two selector orbits, the prepared cross form has coefficient two
on original pair orbits 942, 946, 1079, and 1083, and coefficient minus one
on the other eight cross orbits. The total cross population is
\(N_2N_3=9\). Pair orbits 942 and 946 are proved zero. Original pair orbits
1079 and 1083 correspond to reduced native count columns 6717 and 6721.
Writing \(T=C_{6717}+C_{6721}\),

\[
B_{23}=3T-9.
\]

The integer Gram condition therefore requires

\[
T\in\{1,2,4,5\}
\]

whenever both populations are three and both diagonal norms are six. This is
a conditional necessary restriction on a literal selector realization. It
does not assert that a local assignment violating it satisfies the rest of
the full F0 count model.

## Declared coarse checks

The experiment keeps the following conditions before applying the square
test:

- Each endpoint uses one complete frozen local profile, including its
  within-orbit pair counts and all three signed populations.
- All specified local coordinates lie in the final native domains.
- All twelve cross-coordinate domains are retained exactly, including the
  three proved-zero coordinates and all interval holes.
- Each cross pair orbit is a literal perfect matching between the two
  twelve-element selector orbits. The source verifies all row and column
  incidences, so \(P_R\le\min(N_2,N_3)=3\) is also imposed.
- The trivial product and the three one-dimensional signed cross products
  hold exactly.

The experiment does not impose every other native row, exterior-edge
constraint, or global literal-selector compatibility condition. Its output
must remain a local count composition.

## Complete finite scope

Each of the twelve cross pair orbits has a fixed triple of real character
values. There are four character cosets, with three pair orbits in each.
If the four product right-hand sides are \((q_0,q_1,q_2,q_3)\), the total
mass in character coset \(\delta\) is

\[
m_\delta=\frac{q_0+\delta_1q_1+\delta_2q_2+\delta_3q_3}{4}.
\]

The source checks the character coefficients on all 144 literal cross
pairs. The four masses are nonnegative integers and sum to nine.

Distributing mass \(m\) among three nonnegative integer coordinates gives
\(\binom{m+2}{2}\) possibilities. Over four cosets of total mass nine, the
maximum product is 2,160, attained at a permutation of \((3,2,2,2)\).
Preparation checks all 220 mass allocations. Domains and zeros are applied
only after this complete count-composition scope is fixed.

Both selector orbits have 32 frozen population-three profiles with plus norm
six, all compatible with their currently specified native domains. The
selection rule retains the first profile for each signed triple, then orders
profile pairs by decreasing unrestricted composition bound and tuple-index
ties. It selects at most three different four-product target vectors.

The three frozen cases are:

| Case | Orbit 2 tuple | Orbit 3 tuple | Signed product targets | Coset masses | Composition bound |
| --- | ---: | ---: | --- | --- | ---: |
| 0 | 23 | 23 | \((1,1,1)\) | \((3,2,2,2)\) | 2,160 |
| 1 | 23 | 24 | \((1,-1,-1)\) | \((2,3,2,2)\) | 2,160 |
| 2 | 23 | 25 | \((-1,1,-1)\) | \((2,2,3,2)\) | 2,160 |

Every listed profile has three saved literal preimages. The total scan bound
is 6,480 compositions. Case 0 already has an empty coarse region: its first
coset requires mass three, but the only nonzero coordinate in that coset is
original pair orbit 1127, whose current upper bound is two. The case remains
in the frozen scope.

## Controls and planned output

Preparation checks the square identity on the 36 ordered pairs of the six
integer vectors of H-norm six, as well as the positive-semidefinite
zero-inner-product counterexample. These are small integer-vector controls,
not graph or count candidates.

The prepared scan uses a fixed 30-second bound. It counts every unrestricted
composition, every domain/zero/activation rejection, and each subsequent
Gram-test outcome. It records an exact stream hash of all coarse-passing
compositions and at most one rejected example of each failure kind per
case. Examples retain all twelve cross counts, the four exact product
values, the Gram matrix, and its integer determinant. A separate bounded
replay compares the complete finite result. Neither mode calls an optimizer.

The source and preparation are frozen at:

- `experiments/workspace/root_prism_free_f0_two_dimensional_profile_pairs.py`,
  SHA-256 `2b524a25818e57e97836fc5567657da862e939543f2d050268ef98590cb86899`;
- `experiments/logs/root-prism-free/f0-two-dimensional-norm-six-pairs-preparation01.json`,
  SHA-256 `3c7a7b045ac8580355bf33f73963cbdcac295349820d81baf603604c32d7822f`.

The final native target remains
`a738d318b6b8de471ee7383f1e6ea11949eed8f8ccf4892814fa2eac268ed153`.
No constraint from this experiment has been added to that target.
