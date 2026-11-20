# Joint PSD separation at the path-model proposal

This package prepares one bounded separation scan at the numerical proposal
`bfe03cf2ec0f9d00ee7ff756112a61ab368404d4ed29c7b50377f01c5ae8327e`.
It does not assert that this proposal is exactly feasible. The parent model
retains all 480 selector types and all 15,200 reduced variables. The scope is
the globally prism-free and F-free split $18+18$ case with component zero;
the other component and its alignment remain free.

The previously completed path-model query remains UNKNOWN. Its numerical
backend reported optimality, but no exact point or infeasibility certificate
was obtained. The satisfied core-pair clique rows and the unsuccessful
three-selector separation do not justify repeating that linear query.

## Three necessary matrices

For a genuine selection vector $z\in\{0,1\}^{480}$, write

\[
x_a=\mathbb E[z_a],\qquad Z_{ab}=\mathbb E[z_az_b],\qquad Z_{aa}=x_a.
\]

Then the full augmented selector matrix

\[
M=\begin{pmatrix}1&x^T\\x&Z\end{pmatrix}
\]

is positive semidefinite because it is an average of

\[
\begin{pmatrix}1\\z\end{pmatrix}
\begin{pmatrix}1&z^T\end{pmatrix}.
\]

The other two matrices are the frozen full-21-core Schur forms obtained from

\[
27I-9A+J\succeq0,\qquad44I+11A-2J\succeq0.
\]

For each form, conditioning on the fixed core, padding by the selected
vertices, and averaging gives

\[
S_+=27\operatorname{diag}(x)-9Y+Z-H_+\circ Z\succeq0,
\]

\[
S_-=44\operatorname{diag}(x)+11Y-2Z-H_-\circ Z\succeq0.
\]

The complete $480\times480$ rational kernels $H_+,H_-$ were already
checked against direct core inverses. Their full-core correction, diagonal
handling, 12 actual core actions, and all pair entries are unchanged here.
This scan reads those hash-bound certificates. It performs no inverse,
kernel census, eligibility census, or graph completion search.

The quotient uses convex averaging over verified core relabelings. It does
not assume that a completed graph has those automorphisms.

## Exact cut construction

An integer vector $(c,v)$ gives the necessary selector row

\[
-\sum_a(v_a^2+2cv_a)x_a-2\sum_{a<b}v_av_bZ_{ab}\le c^2.
\]

An integer $v$ gives $v^TS_\pm v\ge0$. The frozen constructors expand
these inequalities over all literal selectors, edges, and pairs, then sum
coefficients over the verified orbits. The 389 removed zero-pair coordinates
are substituted exactly. Each quotient evaluation is checked against its
separate full literal quadratic expansion.

The current parent also contains 162 single-coordinate edge-zero equalities.
The adapter records their actual equality-row indices and nonzero integer
coefficients. It removes those variables from both candidate rows and every
parent row before positive-gcd normalization. Both orientations of every
parent equality enter the comparison index. The original domain cache is
unchanged.

The scan requires a strictly positive exact dyadic violation of both the
literal cut and its zero-projected row. It records the identity relating
their gaps to the proposal's actual residual on the proved-zero coordinates;
it never assumes that the numerical zero coordinates are exactly zero.

A candidate is discarded if its projected row is already present, is a
positive multiple of a parent equality orientation, follows directly from
the unit box, or duplicates an earlier retained row. This filtering does
not test all linear consequences of the parent. A retained row can still be
redundant.

## Fixed scan scope

The requested allowance is one cooperative 60-second scan, including input
loading and output. There are three decompositions: one of order 481 and two
of order 480. Each family considers the eight smallest numerical directions
at scales $1,4,16,64,256,1024$, with integer entries bounded by 1024. At most
16 rows per family and 48 rows in total are retained. Every attempted vector,
exact gap, filtering decision, and retained certificate is saved.

The time check occurs between bounded operations. Any overrun is reported.
A timeout preserves the completed prefix. No optimizer is called, and there
is no automatic follow-up linear query.

Each retained row records its smallest and largest nonzero absolute integer
coefficients, signed extrema, and exact coefficient ratio. A positive dyadic
scale is also recorded that keeps every nonzero scaled coefficient at least

\[
2^{-29}=1/536870912.
\]

All conversions under this scale are checked exactly. Any later native model
must still verify that its complete sparse matrix survives transport to the
solver.

Numerical eigenvalues and relative row gaps have separate size labels. The
relative threshold is $10^{-10}$, used only as a reporting heuristic.
Tiny exact gaps can arise from residuals on universal null identities.
Neither a positive gap nor this label proves strict strengthening of the
linear relaxation. A scan with only numerical-zero-scale negative
eigenvalues does not justify another linear query by itself.

## Verification and preparation history

The base cache checks complete orbit partitions, all 12 actual core actions,
144 group products, the 389 original zero equalities, and current row hashes.
Its controls include six full literal/quotient identities, six positive
diagonal-moment controls, and 36 vector transports. These positive controls
test the PSD forms; they are not claimed to satisfy the entire model.

The zero adapter adds 1,500 exact Boolean equivalence checks and a control
whose numerical proposal has a nonzero value at a proved-zero coordinate.
Cold replay reconstructs the row filter and its equality witnesses. The
domain and kernel certificates are reused without rebuilding them.

Two preliminary base-preparation failures are preserved. The first compared
an inherited hash of the 21-core bit rows to an 18-core adjacency matrix.
The second expected repeated arrays where the bound model stores scalar unit
bounds. Both were metadata-schema mistakes caught before any cache, scan, or
optimizer output. The corrected base preparation and cold replay passed.

The intended scan source is
`experiments/workspace/root_prism_free_f0_joint_psd_zero_scan.py`.
The earlier cached wrapper remains frozen as its dependency and is not a
second authorized scan.
