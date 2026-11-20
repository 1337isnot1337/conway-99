# Complete Fourier factorization of the F0 pair counts

The missing two-dimensional representations give a finite, exact way to link
all selector-pair counts to one Boolean selector set. The construction uses
320 additional integer coordinates and 6,496 scalar Gram identities. A change
of coordinates expresses those identities with 12,992 scalar products.

This file proves the algebra. The companion record constructs every linear
coefficient and checks the literal transports. No native model, local-mask
table replacement, solver query, incidence witness or graph is produced here.

## Inputs and scope

The action and representations are from
`f0-two-dimensional-moments-scope01.json`, SHA256
`948e256945fc817cc75ea46c969c055b21e61832a4f2177c481884e73338223f`.
The earlier complete pair inventory is
`f0-second-moments-preparation02.json.gz`, SHA256
`404d91da35c798ba248887c22a7500957947e24b71d5197dc44432460e6d219e`.
The complete inverse-mask record is
`f0-character-literal-lift-preparation01.json.gz`, SHA256
`241cd14c61b465025c72ffcaa65af8e5c48e9e5a0eda7ea7d252e9d74b22db1e`.

All three records have earlier exact checks. They concern the fixed F0 core.
The action is a relabeling of the fixed core and its candidate selectors. It
does not assume that a completed graph has an automorphism.

Let `G=S3 x C2`, of order twelve. Its action partitions the 480 selectors into
38 orbits of size twelve and four of size six. If `a_i` is the anchor of orbit
`i`, its stabilizer `H_i` is either the identity or the central subgroup
`{1,z}`. For each selector `a` choose a transport `t_a` with `t_a a_i=a`.

The irreducible real representations consist of four one-dimensional
characters and two two-dimensional representations, denoted plus and minus.
Both preserve the integer matrix

\[
H=\begin{pmatrix}2&-1\\-1&2\end{pmatrix}.
\]

The plus representation is trivial on `z`; the minus representation sends
`z` to minus the identity. A representation is active on an orbit when it is
trivial on that orbit's stabilizer. Consequently plus is active on all 42
orbits, while minus is active on the 38 orbits of size twelve.

## Fourier coordinates determine a local subset

For a Boolean selector vector `x` and an active representation define

\[
X_i^\rho=\sum_{a\in O_i}x_a\rho(t_a).
\]

This is independent of the choice of transport, because the representation
is trivial on the stabilizer. For a one-dimensional character this is the
existing signed population. The trivial character gives the population
`N_i`.

Fourier inversion on `G/H_i` gives

\[
|O_i|x_a=
\sum_{\chi\text{ active}}\chi(t_a^{-1})L_i^\chi+
\sum_{\rho\text{ active},\ \dim\rho=2}
2\operatorname{tr}\bigl(\rho(t_a^{-1})X_i^\rho\bigr).
\]

The coefficient construction verifies this equality on every literal unit
vector. It uses all pairs of selectors in each orbit, so the check establishes
the entire linear inverse. The existing signed-population sign conventions
also agree with the chosen transports.

There are 160 existing scalar character coordinates: 42 ordinary populations
and 118 nontrivial signed populations. The two-dimensional matrices contribute
`42*4+38*4=320` coordinates. The total is 480, as required for a complete
linear transform of the selector vector.

In a proposed exact lift, each orbit's existing inverse masks must be linked
to all of its Fourier coordinates. Choosing coordinates independently is not
valid. A local table row records the counts, signed populations and complete
two-dimensional data of one actual saved mask. Fourier inversion makes that
mask unique, even when several masks share the old one-dimensional profile.

## Cross-orbit identities

Take distinct selector orbits `i<j`. A literal pair `(a,b)` has relative group
element `g=t_a^{-1}t_b`, defined modulo `H_i H_j`. This ambiguity is central
and acts trivially in every representation active on both orbits.

Since each representation preserves `H`,

\[
\rho(t_a)^TH\rho(t_b)=H\rho(t_a^{-1}t_b).
\]

The matrix on the right is constant on each complete literal pair orbit `R`.
Let `P_R` be the number of selected unordered pairs in that orbit. There is
one orientation with the first selector in `i` and the second in `j`, so no
factor of two occurs. Expanding the product gives

\[
\boxed{(X_i^\rho)^THX_j^\rho
=\sum_{R\subset O_i\times O_j}P_R H\rho(g_R).}
\]

This formula remains valid when one or both selector orbits have size six.
The direct literal coefficient check covers those cases without inferring a
normalization from orbit size.

## Within-orbit identities

For a single orbit, the diagonal terms have `x_a^2=x_a` and contribute `N_i H`.
Each unordered pair contributes both orientations. Therefore

\[
\boxed{(X_i^\rho)^THX_i^\rho
=N_iH+\sum_{R\subset\binom{O_i}{2}}
P_R H\bigl(\rho(g_R)+\rho(g_R^{-1})\bigr).}
\]

The matrix is symmetric. It supplies three independent scalar identities per
active matrix. The two-orientation formula also handles elements that are
their own inverse; their coefficient is doubled as it must be.

The companion record constructs both boxed identities for all 903 unordered
pairs of selector orbits, including the 42 diagonal blocks. It checks all
114,960 literal unordered pairs and covers all 9,742 original pair orbits.
The 389 previously proved zero pair coordinates are omitted only after their
original coefficients have been recorded. The other coordinates use the
existing reduced count namespace. The six earlier plus-block forms on orbits
2, 3 and 4 are recovered exactly.

## Why all the identities recover every pair count

Necessity alone follows from the preceding expansions. For sufficiency, fix
the actual local masks supplied by the proposed tables. We must show that
their pair histograms are the only histograms satisfying every active
character and matrix identity.

For two distinct orbits let `K=H_i H_j`, and lift the local masks to functions
`f_i(h)=x_{h a_i}` and `f_j(h)=x_{h a_j}` on `G`. Define their correlation

\[
c(g)=\sum_{h\in G}f_i(h)f_j(hg).
\]

The map `h -> (h a_i,hg a_j)` covers the literal pair orbit with relative class
`gK` exactly `d=|H_i intersect H_j|` times. Thus
`c(g)=d P_{gK}`. The correlation is constant on the cosets of `K`.

For a representation active on both orbits, the Fourier transform of `f_i`
is `|H_i| X_i`. The Fourier transform of the correlation is the adjoint
product of those transforms. On the other hand, summing the constant value
on each coset gives the factor `d|K|=|H_i||H_j|`. Cancelling that factor gives
exactly the cross-orbit identity above. Representations that are not trivial
on `K` have zero transform and carry no missing condition.

The active representations form the complete Fourier transform of `G/K`.
Here `K` is either the identity or `{1,z}`, so the quotient has order twelve
or six. The construction checks the exact inverse kernel for every pair of
quotient elements. If two pair histograms have the same transforms, their
difference has zero inverse and every coordinate of the difference is zero.

Within one selector orbit, use the same argument with the autocorrelation.
Its identity coset is fixed by `N_i`. A nonidentity coset and its inverse
encode the corresponding unordered pair count. If the coset is its own
inverse, the autocorrelation contains twice that count. These factors are
nonzero, so the map from unordered pair counts remains injective. The
within-orbit boxed identity is its complete Fourier transform.

It follows that actual local-mask coordinates, all four one-dimensional
product families and both complete two-dimensional blocks are equivalent to
the exact pair histograms of one global Boolean selector set. A partial block
or a table of independent norms does not give this equivalence.

## Two products per scalar identity

Each matrix `X_i` has two vector columns. For a column `v=(x,y)` define
`a=2x-y` and `b=y`. The integer identity

\[
2v^THw=a(v)a(w)+3b(v)b(w)
\]

diagonalizes the metric without introducing fractions. Each scalar Gram
identity therefore needs two integer product variables and one linear row.
The local-mask tables determine `a,b` directly, so a spurious odd value of
`a+b` cannot create an invalid half-integer `x`.

The plus block has 84 columns, and the minus block has 76. Their lower
triangles contain

\[
\frac{84\cdot85}{2}+\frac{76\cdot77}{2}=6496
\]

entries. The proposed lift adds 320 coordinate variables and 12,992 product
variables. Together with the 3,288 existing one-dimensional products this
would give 16,280 products. Retaining every current variable gives 31,756
variables before any other formulation changes. These are exact inventory
counts, not measured solver costs or a speed claim.

## Relation to the original selector equations

The existing second-moment system retains every original selector equality
and its full Boolean RLT products. Let one equality be `L_r(x)=a_r*x-q_r=0`.
If the moments come from the actual selector set and its orbit under `G`,
then the retained rows give

\[
\mathbb E_G[L_r(x)]=0,\qquad
\mathbb E_G[x_aL_r(x)]=0\quad\text{for every selector }a.
\]

Multiplying the second identities by the coefficients of `a_r` and subtracting
`q_r` times the first gives

\[
\mathbb E_G[L_r(x)^2]=0.
\]

Every summand is a nonnegative real square. Thus every translate, including
the original selector set, satisfies the equality. This is a general exact
consequence of actual pair realization and the full retained RLT equations.
For a future native model, adding the 172 literal selector equalities through
the linear Fourier inverse can expose this consequence directly to propagation.
An accepted future incidence should still be checked against those original
172 equalities without relying on solver status.

## Recorded construction

Source:
`experiments/workspace/root_prism_free_f0_nonabelian_pair_factorization.py`,
SHA256 `790a929c65898d2a3bb038c9877d73dc022aa9c66d3983efe8a77ad833383871`.
Record:
`experiments/logs/root-prism-free/f0-nonabelian-pair-factorization01.json.gz`,
SHA256 `627577aea4a25c15e5d2846242adda9c6b7c97164b7ba47fb9a2cab5d3988fd8`.
The construction takes 5.775 seconds inside a 7.563-second owner. The raw
record has 2,605,132 bytes; its compressed archive has 320,319 bytes.

The next implementation must extend the saved local-mask tables, preserve
all existing count constraints and replay the native transport. The algebra
does not realize the exterior edge variables `Y`. It does not exclude F0,
the other component types, or the unrestricted graph problem.
