# Conditioning the triangle kernels on all root vertices

This family uses the two triangle kernels and the complete scalar triangle
moments from [the preceding preparation](triangle_vertex_projectors.md).
It creates no new catalogue product tensors and uses no count point during
preparation.

Let U be either vertex projector matrix

    Uminus = 27I-9A+J,
    Uplus  = 44I+11A-2J.

For a fixed labelled four-root H, write G=U[H,H]. The preparation checks
all four leading principal minors of G before computing its inverse.
All 72 minors across the two families and nine roots are positive.
The saved exact inverse is P/d, with G P=dI checked entry by entry.

For a triangle class C, let T be a literal representative. Its root-to-
triangle column has entries

    c_C(i) = 27*1[i in T] - 9*|N(i) intersect T| + 3  (minus),
    c_C(i) = 44*1[i in T] + 11*|N(i) intersect T| - 6  (plus).

These depend only on the class, including when T meets H. The source
checks all 4,592 root-cross entries directly in the literal graphs.

Let N_CD=sum_phi n_C(phi)n_D(phi) be the full scalar class-count moment.
The necessary residual matrices are

    Mminus - (1/9) (c_C^T Gminus^-1 c_D) entrywise-multiplied by N,
    Mplus  -       (c_C^T Gplus^-1 c_D) entrywise-multiplied by N.

This removes the root span separately in each embedding and then sums.
The correction uses N, not the product of mean class counts. The latter
would give only the ordinary Schur complement of the averaged matrix.

The source multiplies each residual by a positive integer and removes
the common positive coefficient divisor. Its 42,380 root-cross inverse
products are evaluated with Python integers. All 574 classes remain.
No row is removed using its value at a count point.

An internal triangle has incidence vector supported entirely in H.
Projection onto all four root vectors therefore dominates projection
onto that one triangle vector. For each of the four relevant cases,
the source also checks the exact 4 by 4 positive semidefinite matrix

    (z^T G z) P - d z z^T,

where z is the internal triangle indicator and G^-1=P/d.
All internal-triangle rows vanish coefficientwise in the derived tensors.

The complete preparation took 8.072 seconds. It produced 18 blocks with
135,249 negative-projector and 135,271 positive-projector tensor terms.
The same 37 direct host cases were checked against the derived coefficient
forms, using 18,580 labelled root embeddings and 72,406 ordered triangle
pairs. These controls re-enumerate literal host pairs; they do not repeat
the full catalogue product census.

The source is `triangle_vertex_root_schur.py`. Its frozen model is under
`experiments/logs/moments-and-counts/triangle-vertex-root-schur-preparation01/`.
The separate query source retains every matrix row and verifies exact
characteristic polynomials, the constant kernel, all four root point-star
kernels, and internal-triangle zero rows. At this preparation checkpoint,
no point query has run.
