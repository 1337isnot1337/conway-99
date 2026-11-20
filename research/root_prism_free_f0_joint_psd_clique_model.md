# The joint PSD and core-pair clique overlay

This model appends the 21 exactly replayed directions from the corrected joint PSD scan and all 258 published core-pair edge-clique inequalities. It preserves the complete preceding path-prism model: all 15,200 variables, all 27,764 rows, and every numerical row scale in that prefix. The 128 greedy clique rows proved to be parent equality consequences are absent.

The model is a necessary linear relaxation in the existing component-zero, globally prism-free and F-free local stratum. No selected incidence, graph automorphism, second-component incidence, or numerical proposal is fixed. The 12 core actions justify averaging necessary convex conditions; they are not imposed as automorphisms of a completed graph. The inherited 4,416 Boolean selector predicates and the original RLT rows remain present.

## Exact size and parent preservation

| Quantity | Parent | This model |
|---|---:|---:|
| Variables | 15,200 | 15,200 |
| Equalities | 6,135 | 6,135 |
| Inequalities | 21,629 | 21,908 |
| Total rows | 27,764 | 28,043 |
| Nonzero matrix coefficients | 905,276 | 1,086,559 |

All 279 new inputs append as distinct literal rows. The 21 PSD rows contain 178,481 terms; the 258 clique rows contain 2,802 terms. Literal distinction from the stored parent rows does not establish linear independence or nonredundancy under every parent constraint.

The parent is `f0-schur-path-model03.json.gz`, canonical SHA256 `7bc4682e3df009761c55d0740a30a0629d45e894807f79e3337fc1de4fa1aff3`. The new model is `f0-joint-psd-clique-model01.json.gz`, canonical SHA256 `e5aee717846cf7bb1b2e6072438d49b38627119fed65408d2159212f876ec21d`. Its exact mathematical matrix has SHA256 `607b3a6b1939b70538cbaf5e5d6e395b746745bf50ced097f12d81035723a234`.

The model file is deterministically gzipped. Source, parent, witness, review, and cold-replay hashes are stored in the model. Preparation and cold reconstruction compare the complete old row and scale prefixes, not only their dimensions. They reuse the certified parent records and reconstruct the new rows from their witnesses. No kernel inverse, complete motif census, eigendecomposition, or optimizer call is repeated.

## The 21 PSD rows

The corrected scan produced 16 augmented-selector moment directions and five full-21-core positive-projector Schur directions. It produced no accepted negative-projector direction. The 21 rows all have exact positive gaps at the saved binary64 proposal, before and after the certified-zero substitution. That proposal is not an exact feasible point.

For the selector family, an integer vector applied to the augmented moment matrix gives a quadratic form that must be nonnegative. The frozen constructor expands this form over all 480 selector labels, then sums coefficients over the verified pair orbits. For the graph family, the constructor uses the full-21-core Schur kernel derived and independently verified before the scan. Diagonal terms multiply selectors, eligible adjacency terms multiply edge variables, and off-diagonal incidence products multiply second-moment variables.

Each resulting inequality is reconstructed using the original integer direction and the frozen exact kernel. All 389 already eliminated second-moment coordinates are accounted for by the parent map. The 162 separately proved edge-zero equalities are then substituted in both the row and its comparison data. Division uses a positive common divisor. No direction or coefficient is inferred from a floating eigenvalue.

The exact gap identity tracks the removed zero-coordinate contribution explicitly, because a numerical proposal need not satisfy a proved zero exactly. Acceptance requires both the literal and the projected inequality to have a positive exact gap. Numerical significance labels remain descriptive. They do not prove independence from all affine identities or certify that the full PSD cone is enforced.

This overlay replays all 21 directions and both gaps. The scan's bounded outcome remains `TIME_LIMIT_PARTIAL`: 61.12 seconds, three decompositions and 89 recorded attempts. The incomplete negative-projector direction scan is not resumed here. The earlier NumPy-Boolean serialization failure and its narrowly corrected replacement remain separately preserved.

## The 258 core-pair clique rows

Fix an exterior vertex label \(b\) and two distinct core vertices \(i,j\). Let \(L\) be a set of candidate neighbors \(a\) of \(b\), each of whose core signatures contains \(i,j\). Two distinct vertices of \(L\) cannot both be adjacent to \(b\): they would have the three common neighbors \(i,j,b\), contradicting the common-neighbor upper bound two. Therefore every graph selection satisfies

\[
\sum_{a\in L} y_{ab}\le x_b.
\]

This includes the case \(x_b=0\), by edge activation. Taking convex averages preserves the inequality. Passing to the invariant quotient sums coincident edge coefficients; it does not replace a sum by one representative term. Terms already proved to have zero edge value can be removed.

The complete, separately certified census has 258 distinct quotient rows from 3,096 literal retained buckets. The append builder checks every stored neighbor, its eligible edge, its membership in the common core pair, and all 12 literal core transports. It reconstructs all 2,802 row coefficients. It consumes the frozen complete-census result and cold certificate instead of rerunning that census.

## Numerical representation

The mathematical rows remain integral. Numerical conversion divides each new row by its stored positive power of two. The scale rule preserves small terms as well as controlling large coefficients. Every coefficient and right-hand side converts exactly to binary64 after scaling; the largest mathematical coefficient still needs only 31 bits.

The separate no-run audit constructs the same CSC matrix and options as the prepared query, passes it to HiGHS, and retrieves it. All 1,086,559 values, indices, row bounds, column bounds and costs match exactly. The smallest absolute scaled coefficient is

\[
\frac{9}{2^{30}}=8.381903171539307\times10^{-9},
\]

which exceeds the unchanged native input threshold \(10^{-9}\). No matrix threshold is lowered. This checks native input preservation; it makes no claim about numerical conditioning or internal presolve accuracy. The audit calls neither `Highs.run` nor `getDualRay`, and its native optimization runtime is zero.

## Prepared query and exact acceptance

The prepared query reuses the preceding owned-child IPM driver with explicit source, matrix, dimension and metadata substitutions. Complete text and AST controls record those substitutions. The exact phase is unchanged apart from the ray length. Its model loader checks the full old row/scaling prefix, all 279 appended records, exact integer-to-dyadic conversion, and the bound cold reconstruction.

The proposed execution has one numerical child, capped at 180 seconds including setup, with one thread, IPM and crossover disabled. It saves finite numerical column values when available. It does not recover a basis or exact primal point. The parent must authorize execution separately from this preparation.

If numerical infeasibility is reported, the driver first asks whether a dual ray already exists. It calls the ray-returning API only after that guard succeeds, so it cannot silently launch a second optimization to obtain a ray. At most one separate 60-second exact phase pulls the row multipliers back through the positive dyadic scales and seeks an integer certificate.

For unrestricted equality multipliers \(\lambda\), nonnegative inequality multipliers \(\mu\), combined coefficient vector \(c\), and combined right-hand side \(B\), every feasible unit-box point obeys

\[
\sum_j\min(c_j,0)\le c^T x\le B.
\]

An exclusion requires the strict exact inequality \(B<\sum_j\min(c_j,0)\). The standalone replay reconstructs every appended witness row over the certified parent and checks this finite-box certificate using independent integer arithmetic. Numerical optimality, infeasibility, or a time limit alone yields no component exclusion. No whole-graph or whole-PSD feasibility claim is made by this preparation.
