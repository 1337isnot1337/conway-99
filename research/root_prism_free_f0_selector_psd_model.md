# F0 second moments with 32 certified selector PSD directions

## Scope

This preparation strengthens the complete fractional second-moment model for one occurrence of component zero in the split $18+18$ shell, under global prism-freeness and $F=0$. The other component and its fiber alignment remain free. All 480 first-component triples remain available. There is no fixed incidence, graph symmetry assumption, or claim about the other 65 component types.

The previous IPM run returned a numerical point. Its exact reconstruction stopped at the declared active-face resource limit, so it remains UNKNOWN. A separate, bounded eigenscan of that numerical proposal produced 32 exact valid selector-moment inequalities. Their validity does not require the proposing point to be feasible.

This package prepares one new linear query. No production optimizer was called during preparation.

## The added inequalities

For a hypothetical graph, extend the selected incidence to a binary vector $z\in\{0,1\}^{480}$, and average over the 12 verified relabelings of the fixed component. Write $x=E[z]$, $Z=E[zz^T]$. Then

\[
\begin{pmatrix}1&x^T\\x&Z\end{pmatrix}\succeq0.
\]

Each saved integer vector $(c,v)$ therefore gives

\[
-\sum_a(v_a^2+2cv_a)x_a
-2\sum_{a<b}v_av_b Z_{ab}\le c^2.
\]

All 32 retained vectors have $c=0$. The builder expands every coefficient in the full 480-selector domain, collects coefficients by the verified selector and unordered-pair orbits, substitutes only the 389 previously certified zero pair variables, and divides by a positive common divisor.

The entire earlier matrix remains an unchanged prefix. In particular, the complete mixed-edge equations, original selector Gram identities, lifted identities, all 4,416 selector inequalities, pair bounds, and edge-to-moment inequalities remain present. These 32 directions do not impose the whole positive semidefinite cone.

| Quantity | Earlier reduced model | New model |
|---|---:|---:|
| Variables | 15,200 | 15,200 |
| Equality rows | 5,973 | 5,973 |
| Inequality rows | 15,719 | 15,751 |
| Total rows | 21,692 | 21,724 |
| Nonzero coefficients | 183,702 | 380,052 |
| Explicit certified PSD directions | 0 | 32 |

The 32 new rows contain 196,350 terms. Their largest absolute integer coefficient is 91,273,080 (27 bits). All new right sides are zero.

## Numerical scaling and exact dual conversion

The mathematical matrix is integral. Old rows have numerical scale 1. For a new row with largest absolute coefficient $M$, its numerical version divides the entire row by

\[
s=2^{\lfloor\log_2 M\rfloor}.
\]

These positive scales preserve each inequality. Every binary64 conversion is checked by its exact integer ratio. The largest scale is $2^{26}=67,108,864$. Across all new numerical coefficients, the smallest nonzero absolute value is $2^{-20}$, and the largest is $3/2$.

The driver saves the raw numerical ray under the distinct name `existing_scaled_dual_ray_hex`. Before integer Farkas reconstruction, multiplier $\lambda_i$ is replaced by $\lambda_i/s_i$ as a Python `Fraction`. This conversion is never performed by floating-point division. A dedicated subnormal control verifies that a nonzero multiplier survives even when binary64 division would underflow.

A reconstructed certificate is checked against the original integral rows and the unit box. No inference uses only a numerical backend status.

## Acceptance and replay

The native driver retains one IPM call with crossover, one thread, and a 180-second owned process limit including setup. It reserves three seconds for numerical output. A separate exact stage has a 60-second owned process limit. These are proposed query limits awaiting the coordinator's launch gate; preparation itself calls no optimizer.

An accepted point must pass:

- Every row of the new exact quotient matrix.
- The original independent full-domain acceptance: 650,350 literal rows and 183,834 variable bounds.
- All 32 quadratic forms evaluated directly in the full 480-selector and 114,960 unordered-pair coordinates.

The active-face recovery is still a proposal mechanism with the prior resource bounds. A stopped recovery remains UNKNOWN. No extra optimization, hidden ray-generating solve, or automatic retry is available.

The standalone replay imports neither the new production helper nor the PSD cut generator. It cold-rebuilds the earlier equivalent reduction and reconstructs every new coefficient directly from the saved integer vector. Its exact infeasibility check uses the integral matrix after validating every row's necessity.

## Preparation checks

The model cold rebuild passed with canonical model SHA256 `d098a4b84405823aa38e9d2def7b675c6166507f7350937f1dc0f65af7274dcd` and matrix SHA256 `b49a35a0c19e43a70bc8957f0fe09e03f17113ff67caab40a4d4fa63307cca01`.

The separate independent preflight reconstructed all 32 new coefficient rows, all numerical scales, the complete original domain, and the original reduction. Additional focused controls checked all 32 quadratic forms on the average of 12 relabelings of an earlier binary incidence. This is only a positive selector-moment control; that old incidence is not asserted feasible for the present linear model. The same exact quadratic checker rejected all 32 directions at the losslessly preserved numerical proposal.

The parent point/ray controls, 420 new exact scaling and multiplier controls, the subnormal pullback control, and unchanged bounded-control-flow AST checks passed. No eigendecomposition or optimizer was repeated by this package.

## Entry points

- `root_prism_free_f0_selector_psd_model.py`: integral model and scale preparation, deterministic cold reconstruction.
- `root_prism_free_f0_selector_psd_exact.py`: exact point/ray acceptance and rational scale pullback.
- `root_prism_free_f0_selector_psd_query.py`: native preparation and the separately gated single query.
- `root_prism_free_f0_selector_psd_replay.py`: independent cold coefficient and terminal replay.
- `root_prism_free_f0_selector_psd_query_controls.py`: focused full-selector arithmetic controls and unchanged-control-flow checks.

The full cone, the two graph-projector Schur cones, and actual exterior graph completion remain outside this linear query.

