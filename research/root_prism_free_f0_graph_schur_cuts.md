# Graph-projector Schur cuts for the component-zero moment model

This package prepares two positive-semidefinite conditions that couple exterior
edge variables with selector pair moments. It makes no optimizer call. Its
preparation and cold replay make no eigendecomposition.

The conditional scope is unchanged: a globally prism-free and $F$-free
SRG(99,14,1,2), an edge shell that splits into two components of order 18, and
component zero on the first side. The second component and its fiber alignment
remain free. The 480 possible triples and all 68,394 eligible exterior edges are
retained. This is not a model of every hypothetical Conway graph.

The numerical input is the saved proposal from the
[32-selector-cut query](root_prism_free_f0_selector_psd_query_run01.md). That query
has terminal status UNKNOWN. Its numerical values have not passed an exact
feasibility check. They may propose integer vectors for universally necessary
inequalities; no conclusion about their feasibility is needed for that use.

## Global projectors and the fixed core

Let $A$ be the adjacency matrix of a hypothetical graph. Its equation is

$$
A^2+A=12I+2J.
$$

The eigenvalue on the constant vector is 14. On its orthogonal complement the
possible eigenvalues are 3 and $-4$. Consequently both matrices

$$
Q_+=27I-9A+J,\qquad Q_-=44I+11A-2J
$$

are positive semidefinite. Their nonzero eigenvalues are respectively 63 and 77.
The names `plus` and `minus` follow the existing preparation; they do not denote
the adjacency eigenspace on which each matrix is supported.

Write $C$ for the complete adjacency matrix of the fixed component of order 18.
The corresponding principal matrices are

$$
K_+=27I_{18}-9C+J_{18},\qquad
K_-=44I_{18}+11C-2J_{18}.
$$

Both are positive definite. The certificate verifies their exact positive LDL
pivots and integer inverse identities $K_\pm N_\pm=D_\pm I$, where

| Family | $D$ | Core-to-exterior column for triple $h_a$ |
|---|---:|---|
| plus | 4,860 | $\mathbf1-9h_a$ |
| minus | 3,822,676 | $11h_a-2\mathbf1$ |

Here $h_a$ is an incidence vector of weight three. These cross columns differ
from the mixed adjacency quota $2\mathbf1-h_a-Ch_a$. The source reconstructs
the correct cross columns directly.

For either family put

$$
H_{ab}=u_a^{\mathsf T}K^{-1}u_b,\qquad
\widehat H_{ab}=u_a^{\mathsf T}Nu_b=D H_{ab}.
$$

The kernel preparation checks all 480 diagonal entries and all 114,960
off-diagonal entries, including the reversed product order. It compares every
entry with the previously saved orbit formula.

## Taking the Schur complement before averaging

In an actual completion let $z_a$ indicate whether triple $a$ is present.
Triple uniqueness permits each actual exterior vertex to occupy one of the
480 positions. Pad every absent position by a zero row and column. If $Y$
records actual edges on the selected positions, the exterior principal block of
the padded projector is

$$
d\,\operatorname{diag}(z)+eY+c\,zz^{\mathsf T},
$$

where $(d,e,c)$ is $(27,-9,1)$ or $(44,11,-2)$. Its cross block has column
$z_a u_a$. Taking the Schur complement of the fixed positive-definite matrix
$K$ gives

$$
d\,\operatorname{diag}(z)+eY+c\,zz^{\mathsf T}
       -H\circ(zz^{\mathsf T})\succeq0.
$$

Now average valid relabelings under the verified 12-element group of the fixed
core. Put $x_a=\mathbb E z_a$, $Z_{ab}=\mathbb E(z_a z_b)$, and let $Y$
also denote the averaged edge matrix. Convexity preserves positive
semidefiniteness, giving

$$
S_+=27\operatorname{diag}(x)-9Y+Z-H_+\circ Z\succeq0,
$$
$$
S_-=44\operatorname{diag}(x)+11Y-2Z-H_-\circ Z\succeq0.
$$

This step does not assume an automorphism of the completed graph. It also does
not impose a rank constraint on the average. The variable $Z_{ab}$ represents
a second moment; it is not replaced by the product of the fractional values
$x_a x_b$.

## Diagonal and off-diagonal coefficients

The diagonal identities are $Z_{aa}=x_a$ and $Y_{aa}=0$. Therefore the
integer-scaled matrices have entries

$$
(D S)_{aa}=\bigl((d+c)D-\widehat H_{aa}\bigr)x_a,
$$
$$
(D S)_{ab}=(cD-\widehat H_{ab})Z_{ab}+eD\,Y_{ab}\quad(a\ne b).
$$

In particular, the two diagonal constants are 28 and 42, not 27 and 44.
For ineligible pairs the edge entry is zero; their pair moment still appears
unless it is one of the certified zero coordinates.

| Integer coefficient | plus range/value | minus range/value |
|---|---:|---:|
| Diagonal coefficient of $x_a$ | 65,286 to 100,278 | 112,651,968 to 131,682,364 |
| Off-diagonal coefficient of $Z_{ab}$ | −52,407 to 44,307 | −43,163,120 to 24,425,544 |
| Off-diagonal coefficient of $Y_{ab}$ | −43,740 | 42,049,436 |

These ranges are computed from all entries, not from floating eigenvectors.

## Integer cuts and the quotient

For any integer vector $v\in\mathbb Z^{480}$, the necessary condition
$v^{\mathsf T}S v\ge0$ gives the homogeneous linear inequality

$$
-\sum_a\bigl((d+c)D-\widehat H_{aa}\bigr)v_a^2x_a
-2eD\sum_{\{a,b\}\text{ eligible}}v_av_bY_{ab}
-2\sum_{a<b}(cD-\widehat H_{ab})v_av_bZ_{ab}\le0.
$$

The factor two occurs only on off-diagonal terms. The source first forms all
literal coefficients and then sums them over each orbit. A separate direct
orbit expression checks every resulting coefficient.

The original quotient has 42 selector, 5,805 edge, and 9,742 pair coordinates.
Each quotient variable is the common value of the entries in its orbit, so its
coefficient is their sum. No extra division by the group order belongs in this
row. The 389 certified zero pair coordinates are substituted using their
original singleton equality witnesses. All 480 selector positions remain.

The source reconstructs the 12 actual permutations of the full fixed 21-core
from their action on triple supports. It verifies adjacency, fibers, all triple
images, all edge and pair orbits, and kernel invariance. Transporting a vector
through any such permutation gives the same quotient inequality. This avoids
adding twelve copies of an identical quotient row.

A positive common divisor is removed from the integer coefficients. The exact
proposal test expands the original full480 quadratic independently and checks

$$
D\,v^{\mathsf T}S(\text{proposal})v
=-(\text{positive divisor})\times
   (\text{primitive row left-hand side}).
$$

The saved binary64 proposal is converted to an exact common power-of-two
denominator. A retained cut must have a strictly positive integer row gap.
Floating eigenvalues and solver status never certify the cut.

## Arithmetic bounds and numerical scaling

The frozen scan permits $\lVert v\rVert_\infty\le1024$. Exact orbit sizes give
the following bounds on raw quotient coefficient magnitudes:

| Family | Maximum bound | Bits |
|---|---:|---:|
| plus | 1,261,789,249,536 | 41 |
| minus | 1,656,947,598,163,968 | 51 |

Both bounds are below $2^{53}$, before zero substitution or gcd division.
Every literal integer coefficient therefore converts exactly to binary64.
The proposing matrices divide their integer numerators by $2^{17}$ and
$2^{27}$, respectively. These positive scalings leave their eigenvectors and
the signs of their eigenvalues unchanged.

For each retained primitive row the preparation records a positive power-of-two
scale based on its largest coefficient, and checks the binary64 conversion by
exact rational equality. It records the smallest and largest scaled nonzero
coefficient. Exact conversion does not rule out numerical conditioning problems;
small relative coefficients may still matter. The mathematical rows remain
integers.

## Controls and bounded scan plan

Preparation passed the following controls without a numerical eigensolver:

- One explicit nine-vertex rook graph, both projector polynomials, all 64 masks
  of six exterior positions, and three integer vectors per mask: 384 exact
  padded Schur identities. Positive semidefiniteness of the whole matrices and
  their Schur complements is checked by rational LDL. The rook graph tests the
  algebra; it is not presented as an SRG(99,14,1,2).
- Six full480 literal-versus-quotient identities, including both edge and pair
  terms and the 389 zero substitutions.
- Six positive diagonal-moment controls. These are controls for the matrix
  formula, not purported solutions of the incidence model.
- Twenty-four literal vector transports, one vector under all 12 core actions
  for each family.

The prepared production scan has the following fixed limits:

- At most 60 seconds including setup, checked between bounded operations.
- One full480 symmetric eigendecomposition for each of the two families.
- At most eight directions per family and scales $1,4,16,64,256,1024$.
- At most 16 retained cuts per family and 32 in total. Filling the first
  family's quota does not skip the second family.

A timeout preserves its exact prefix and records any cooperative overrun.
Reaching a cut limit is distinct from checking every direction. Absence of a
retained separator is not a proof of positive semidefiniteness. Preparation does
not authorize or perform an optimizer call.

## Files and replay

The kernel source is
`experiments/workspace/root_prism_free_f0_graph_schur_kernels.py`.
Its complete integer certificate is
`experiments/logs/root-prism-free/f0-graph-schur-kernels01.json.gz`.

The cut, controls, bounded scan, and exact replay source is
`experiments/workspace/root_prism_free_f0_graph_schur_cuts.py`.
The frozen scan preparation is
`experiments/logs/root-prism-free/f0-graph-schur-cuts-preparation01.json`.

The preparation binds the existing numerical proposal by SHA256
`ca7ebcb40ea0b02054a79f6f6acb83f1f227325f7669b0b9336e3beed6fce5bf`
and its mathematical model by
`d098a4b84405823aa38e9d2def7b675c6166507f7350937f1dc0f65af7274dcd`.
All source, certificate, control, and cold-replay bindings are listed in the
separate publication manifest.

```sh
python3 experiments/workspace/root_prism_free_f0_graph_schur_cuts.py replay-preparation \
  --preparation experiments/logs/root-prism-free/f0-graph-schur-cuts-preparation01.json \
  --output /tmp/f0-graph-schur-preparation-replay.json \
  --seconds 120
```

The scan is a separately gated action. A new linear feasibility query would
require its own bound model, row scales, source review, and exact acceptance.
