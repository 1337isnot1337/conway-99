# Conditioning the projector matrices on the full 21-core

This package replaces the 18-core conditioning used in the
[first graph-Schur preparation](root_prism_free_f0_graph_schur_cuts.md) with
conditioning on the root triangle and the fixed component. It prepares exact
integer kernels and a separately gated two-family spectral extractor. No
linear optimizer is part of the preparation.

The scope remains component zero of a globally prism-free and $F$-free
split18+18 edge shell. The second component and its alignment remain free. All
480 selector positions, 68,394 eligible edges, and the existing 389 certified
zero pair coordinates are retained.

## The three additional core vertices

The full fixed core consists of a triangle and the first 18-vertex component.
Each triangle vertex meets one six-vertex fiber in each shell component.
Its degree is already $2+6+6=14$, so the 60 exterior vertices have no adjacency
to the root triangle.

For a triple $h_a$, write

$$
\eta_i(a)=|h_a\cap\text{fiber }i|,\qquad
d_i(a)=\eta_i(a)-1.
$$

Then $\sum_i d_i(a)=0$. The complete triple domain has seven possible profiles:
$(1,1,1)$ and the six permutations of $(2,1,0)$.

Use the projectors

$$
Q_+=27I-9A+J,\qquad Q_-=44I+11A-2J.
$$

Partition their fixed 21-core matrices with the triangle first and the previous
18-core second. After eliminating the 18-core, the triangle blocks are

$$
T_+=18I_3-6J_3,
$$

$$
(T_-)_{ii}=\frac{1221}{41},\qquad
(T_-)_{ij}=\frac{1089}{82}\quad(i\ne j).
$$

The plus block has rank two and kernel spanned by the constant vector. The
minus block is positive definite: its eigenvalue on the sum-zero plane is
$33/2$, and its eigenvalue on the constant line is $2310/41$.

The residual triangle-to-exterior columns are

$$
q_+(a)=-3d(a),\qquad
q_-(a)=-\frac{77}{41}\mathbf1-\frac{11}{4}d(a).
$$

The plus columns are orthogonal to the kernel of $T_+$. Two triangle vertices
therefore suffice for a positive-definite 20-core, and the omitted triangle
row is compatible with the same Schur complement. The minus construction
uses the positive-definite 21-core.

These fixed-core ranks are used only to compute the valid Schur complement.
They impose no rank restriction on an averaged 480-coordinate matrix.

## Exact corrections

Let $H^{18}$ denote the old core kernel. Eliminating the residual triangle
block gives

$$
H^{21}_{+,ab}
=H^{18}_{+,ab}+\frac12\,d(a)\cdot d(b),
$$

$$
H^{21}_{-,ab}
=H^{18}_{-,ab}+\frac{77}{410}
                  +\frac{11}{24}\,d(a)\cdot d(b).
$$

For the plus family the coefficient is $(-3)^2/18=1/2$. For the minus family,
the two orthogonal contributions are

$$
\frac{3(77/41)^2}{2310/41}=\frac{77}{410},
\qquad
\frac{(11/4)^2}{33/2}=\frac{11}{24}.
$$

The same corrections apply on the diagonal. In particular, a profile of type
$(2,1,0)$ has $d(a)\cdot d(a)=2$; a profile $(1,1,1)$ has value zero.
The preparation never drops these diagonal terms.

The full matrices are

$$
S^{21}_+=27\operatorname{diag}(x)-9Y+Z-H^{21}_+\circ Z,
$$

$$
S^{21}_-=44\operatorname{diag}(x)+11Y-2Z-H^{21}_-\circ Z.
$$

The derivation takes the Schur complement for each actual selection first and
then averages under the 12 verified core relabelings. It does not set
$Z_{ab}=x_ax_b$ and does not assume an automorphism of the completed graph.

## Two exact row identities

The existing mixed, population, and lifted diagonal Gram equalities give

$$
\sum_bY_{ab}=8x_a,\qquad
\sum_bZ_{ab}=60x_a,\qquad
\sum_bh_bZ_{ab}=10x_a\mathbf1.
$$

Since each fiber has six points, these also give
$\sum_b d(b)Z_{ab}=0$. The old core matrices satisfy
$K_+\mathbf1=18\mathbf1$ and $K_-\mathbf1=41\mathbf1$.
Using the old cross vectors $\mathbf1-9h_a$ and $11h_a-2\mathbf1$ yields

$$
S^{18}_+\mathbf1=0,\qquad
S^{18}_-\mathbf1=\frac{462}{41}x.
$$

The new constant minus correction contributes
$(77/410)\cdot60x=(462/41)x$, while each profile correction has row sum zero.
Thus both full-core matrices satisfy

$$
S^{21}_+\mathbf1=S^{21}_-\mathbf1=0
$$

on exact solutions of those linear equalities. The frozen scan still uses all
480 coordinates. Small numerical modes along exact null directions can occur
when the proposing point does not satisfy its equalities exactly; they do not
certify a new obstruction.

## Integer normalization and bounds

After reducing the common denominators, the stored kernels represent
$60S^{21}_+$ and $254280S^{21}_-$. The latter integer kernel has a common
numerator divisor of 11. It is kept in the kernel certificate and is removed
as part of the ordinary positive gcd normalization of each cut. This preserves
an integer denominator for the exact evaluation of the original Schur form.

| Quantity | plus | minus |
|---|---:|---:|
| Schur coefficient denominator | 60 | 254,280 |
| Common numerator divisor | 1 | 11 |
| Diagonal coefficient range | 746 to 1,238 | 7,351,894 to 8,711,604 |
| Off-diagonal $Z$ coefficient range | −677 to 577 | −2,959,946 to 1,577,004 |
| Off-diagonal $Y$ coefficient | −540 | 2,797,080 |
| Raw quotient bound for $\lVert v\rVert_\infty\le1024$ | 15,904,800,768 | 109,617,346,510,848 |
| Bound in bits | 34 | 47 |
| Positive dyadic proposing-matrix scale | $2^{11}$ | $2^{24}$ |

Every raw coefficient is below $2^{53}$. All integer-to-binary64 coefficient
conversions and divisions by the proposed dyadic scales are checked exactly.
This does not establish numerical conditioning. The mathematical cuts remain
integer inequalities.

The adapter passes the Schur coefficient denominator to the unchanged
exact-gap routine through its legacy field named `inverse_denominator`.
That field is used only as the positive matrix denominator. It is not a claim
that 60 or 254,280 is the denominator of an entire full-core inverse.

## Verification and unchanged scan semantics

The coordinator's independent source
`root_prism_free_f0_full_core_schur_audit.py` directly inverts the positive
20-core and 21-core matrices. It compares all 115,440 entries per family with
the closed corrections above. Its record is bound by SHA256
`d8031c629bfb9f5b050c55e218b872aa68a0de08a84abff99da5e029fe572c75`.

The new kernel builder separately reconstructs the residual blocks from the
old 18-core integer inverses. It checks all 480 residual cross vectors, all
98 profile-product identities, all 115,440 corrected entries per family,
positive LDL pivots, all 12 actions, and the independently saved primitive
kernel hashes.

The full21 spectral adapter changes only input bindings, state loading, and
preparation metadata relative to the frozen 18-core extractor. A reproducible
AST control checks 24 unchanged functions, including literal coefficients,
quotient aggregation, exact proposal gaps, dyadic scaling, scan limits,
terminal recording, and replay. The controls also retain the 384 exact
nine-rook masked Schur identities, six full480 algebraic identities, six
positive diagonal controls, and 24 vector transports.

The separately gated scan uses the unchanged numerical proposal
`ca7ebcb40ea0b02054a79f6f6acb83f1f227325f7669b0b9336e3beed6fce5bf`.
It allows one full480 eigendecomposition per family, eight directions,
six scales up to 1024, at most 16 cuts per family, and 60 seconds including
setup. No optimizer is called. Each retained integer row needs exact
full-coordinate and quotient replay.

Any additional edge zeros from a separate pair-minor proof are not inserted
into this preparation or scan. They require their own bound model step.
The earlier 18-core cut package remains unchanged.

## Files

- Kernel builder: `experiments/workspace/root_prism_free_f0_full_core_schur_kernels.py`.
- Full kernel certificate: `experiments/logs/root-prism-free/f0-full-core-schur-kernels01.json.gz`.
- Extractor: `experiments/workspace/root_prism_free_f0_full_core_schur_cuts.py`.
- Source reuse control: `experiments/workspace/root_prism_free_f0_full_core_schur_reuse_control.py`.
- Preparation and cold replay: `f0-full-core-schur-cuts-preparation01.json` and
  `f0-full-core-schur-cuts-preparation01-cold-replay.json` in
  `experiments/logs/root-prism-free/`.

The separate publication manifest records source and artifact hashes.
