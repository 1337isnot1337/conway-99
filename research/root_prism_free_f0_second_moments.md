# Second selector moments for the F0 component

This is a point-independent preparation of a stronger necessary relaxation. It retains the complete fractional baseline and all 4,416 Boolean-normalized selector inequalities. It adds joint selector moments, lifted Gram equations, and exact spectral matrices. No optimizer or semidefinite separator has been run.

The scope remains the globally prism-free, F-free split18+18 shell, with component zero on one side. No selected incidence, second component, alignment or graph automorphism is assumed.

## Joint variables

There are 480 possible three-neighbor signatures. A hypothetical graph selects exactly sixty, with indicators z_a. Distinct outside vertices cannot repeat a signature because they would have three common core neighbors. Thus each z_a is binary.

Write x_a=E[z_a], and introduce

    Z_ab=E[z_a z_b],       Z_aa=x_a.

The expectation can be taken over the twelve actual relabelings of the fixed component. This proves the availability of an invariant feasible point whenever a graph exists. It does not require any relabeling to be a graph automorphism.

The pair conditions are

    0 <= Z_ab <= x_a,
    Z_ab <= x_b,
    Z_ab >= x_a+x_b-1.

Each exterior adjacency indicator is zero unless both endpoints are selected, so every universally eligible edge also satisfies

    0 <= y_ab <= Z_ab.

All 114,960 distinct unordered selector pairs are represented. Pairs outside the eligible edge domain still have a joint selector variable; no edge-compatibility rule is used to forbid coexistence.

## Lifted equalities and exact zeros

For every original selector Gram equality or population equality

    sum_b c_b z_b = r,

multiplication by z_a gives

    sum_b c_b Z_ab = r x_a.

The source lifts all 171 upper-triangular Gram positions and the population equation for every target a. The 21 zero Gram positions have empty support, so their 10,080 lifted rows are identities. Every other row is retained through an exact quotient map. All 990,720 row transports under the twelve core actions are checked.

A quota-one Gram row with support S and a in S gives

    sum_(b in S, b != a) Z_ab = 0.

Each summand is nonnegative. This certifies 4,320 zero moments. Every such pair has an explicit original Gram-row index and anchor.

The existing ninety prism/F conflicts state z_a+z_b<=1. Multiplying by z_a and using z_a squared=z_a gives Z_ab<=0. Together with nonnegativity this certifies another ninety zeros. These pairs are disjoint from the quota-one list. Their proofs use only the already certified motif conflicts.

The 4,410 zero pairs form 389 complete pair orbits. The preparation keeps their variables and adds explicit zero equalities. It does not silently remove coordinates or infer further zeros numerically.

## Complete quotient size

The action on unordered distinct pairs has 9,742 orbits. This count is independently checked by Burnside: an action with f fixed signatures and t two-cycles fixes binomial(f,2)+t unordered pairs.

| Quantity | Count |
|---|---:|
| Full selector variables | 480 |
| Full eligible exterior-edge variables | 68,394 |
| Full distinct selector-pair variables | 114,960 |
| Full variables, with diagonal moments aliased to selectors | 183,834 |
| Selector orbits | 42 |
| Edge orbits | 5,805 |
| Pair orbits | 9,742 |
| Total quotient variables | 15,589 |
| Full lifted Gram/population equations | 82,560 |
| Distinct nontrivial quotient lifted equations | 6,090 |
| Certified zero-orbit equalities | 389 |
| Quotient pair bounds | 28,868 |
| Quotient edge-to-pair inequalities | 5,805 |
| Combined linear equalities | 7,165 |
| Combined linear inequalities | 46,122 |
| Combined linear matrix nonzeros | 279,627 |

The previous 686 equality rows and 11,449 inequality rows are an unchanged prefix. All new linear coefficients have at most six bits. The quotient uses literal coefficient sums; it does not divide a row by an orbit size.

## Spectral conditions

For an SRG adjacency matrix A, the defining equation is

    A squared + A = 12I+2J.

The nonconstant eigenvalues are 3 and -4. Therefore both matrices

    27I-9A+J,
    44I+11A-2J

are positive semidefinite. Their constant-vector eigenvalues are zero.

Embed the selected sixty outside vertices into the full signature index set, placing zero rows and columns at absent signatures. Averaging the embedded principal blocks gives the necessary PSD matrices

    27diag(x)-9Y+Z,
    44diag(x)+11Y-2Z.

The preparation also records Z PSD and the augmented moment matrix

    [[1,x transpose],[x,Z]] PSD.

These PSD requirements are recorded as exact affine matrix formulas. They are not implicitly replaced by linear constraints or claimed to hold merely because the linear relaxation is feasible.

## Stronger fixed-core Schur conditions

Let C be the adjacency matrix of the fixed eighteen-vertex component and h_a its signature column. Distinguish the mixed-equation quota

    q_a=2*1-h_a-C h_a

from the projector cross vectors. The latter are

    u_plus(a)=1-9h_a,
    u_minus(a)=11h_a-2*1.

The corresponding core matrices are

    K_plus=27I18-9C+J18,
    K_minus=44I18+11C-2J18.

Both are positive definite. Exact LDL decompositions and integer inverses are saved. Their inverse denominators are 4,860 and 3,822,676.

Define

    H_plus(a,b)=u_plus(a) transpose K_plus inverse u_plus(b),
    H_minus(a,b)=u_minus(a) transpose K_minus inverse u_minus(b).

Schur complementation before averaging gives the stronger necessary PSDs

    27diag(x)-9Y+Z-H_plus entrywise-times Z,
    44diag(x)+11Y-2Z-H_minus entrywise-times Z.

The entrywise product is required because the embedded cross-column is u_a z_a. Averaging z_a z_b gives Z_ab. It would be incorrect to substitute x_a x_b.

The source checks every one of the 115,440 diagonal-or-unordered H entries for each projector against its orbit value. It stores exact diagonal coefficients, off-diagonal pair coefficients and exterior-edge coefficients after multiplying by a positive common denominator. H numerators have at most seventeen and twenty-six bits respectively.

The PSD matrices have order 480; the augmented moment matrix has order 481. No rank condition is imposed after averaging. A bound on the rank of an individual graph matrix need not survive convex averaging.

## Controls and scope

Twelve relabelings of a previously checked binary sixty-signature incidence give a positive control for the selector, lifted-Gram, certified-zero and pair-bound block. The source verifies all 6,090 quotient lifted equations, 389 zero rows and 28,868 pair bounds for that average.

That control does not claim to satisfy the exterior mixed-edge equations or the later 4,416 selector cuts. Its extension was previously excluded. The preparation explicitly separates this limited algebraic control from feasibility of the complete new model.

A separate nine-vertex rook graph controls both projector constants, the cross-block formulas and exact Schur complementation. Both whole matrices and both Schur complements pass rational LDL checks.

The previously saved 191-bit rational point specifies only x and y. It supplies no Z assignment, so it neither proves nor refutes feasibility of this new relaxation. Any later linear or semidefinite query needs a separate gate, exact outcome replay, and an explicit statement of which PSD conditions were enforced.

## Frozen preparation

The source is root_prism_free_f0_second_moments.py, SHA256
29b1c26550ecc858c0cf35b8f527d61bcfba8a4078b14ff6ca90d914d300df18.

The completed preparation is f0-second-moments-preparation02.json.gz, SHA256
404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e.

Its linear matrix hash is
0f97fd60d2b0b24fa75e6a3d0ee96363b98fb7ea652611d3779ef38946ae8bd1.

The first attempt completed the mathematical calculation but failed while reporting a relative output path. The old source and artifact remain recorded. The correction only resolves the path before making it repository-relative. The completed preparation and its cold replay use fresh paths.
