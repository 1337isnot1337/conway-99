# Exact integer checks for all eight-root class sizes

Every one of the 68,176 outside neighborhood classes passes the complete
one-variable shifted-integer quadratic family at the integer count
witness
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
There are 15,408 positive evaluations and 52,768 zero evaluations at
their minimizing shifts. No separator was found.

This is an exact finite moment check. It neither certifies full PSD
feasibility nor constructs a graph.

## Recovering the class-count moment

For a fixed root, let p contain the first moments of the outside class
sizes and let N contain their second moments. Let D₋ and D₊ be the
outside-class submatrices of the raw spectral blocks. Their definitions
give

\[
D_-=27\operatorname{diag}(p)-9E+N,
\qquad
D_+=44\operatorname{diag}(p)+11E-2N,
\]

where E counts the ordered adjacent pairs between classes. Therefore

\[
N=99\operatorname{diag}(p)-\frac{11D_-+9D_+}{7}.
\]

The source checks this division coefficientwise for every diagonal
entry, before substituting the count point. Each resulting diagonal
form is the one-vertex coincidence count plus the allowed two-vertex
extension counts. These are labelled embeddings, so repeated masks
count ordered pairs and require no free-label divisor.

## The complete single-class integer family

For an integer class size n and any integer k,

\[
(n-k)(n-k-1)\geq0.
\]

Let g be the number of labelled root embeddings, p=E[n], and t=E[n²].
The resulting count inequality is

\[
F(k)=t-(2k+1)p+k(k+1)g\geq0.
\]

If g>0, a minimizing integer is \(k=\lfloor p/g\rfloor\), since

\[
F(k+1)-F(k)=2((k+1)g-p),\qquad
F(k-1)-F(k)=2(p-kg).
\]

Both differences are nonnegative at that choice, and F is convex in k.
Thus checking this shift covers every integer shift for that class.
When g=0, the exact first and second moments are both zero, and every
shift evaluates to zero. Those classes remain in the scan.

All 68,176 coefficientwise divisions and minimizing-shift evaluations
pass using Python integers. Of the polynomials, 51,179 are identically
zero as induced-count forms. The complete class table includes 610
classes at zero-count roots and 1,285 classes with zero first moment.
No root or mask was removed from the domain.

## Artifacts and scope

Source:
`experiments/workspace/grid_free_order10_projector_integer_classes.py`

Source SHA256:
`1367a004222f5c38aefc45b55aa2abedb5ac95e8afd936eba2ad55161720966c`

The preparation, result and log have prefix
`experiments/logs/moments-and-counts/order10-projector-integer-classes`.
The complete class table is saved as `-values.json.gz`, with SHA256
`c9a13aab34ac0c9309da2044c8cdf2d4b674ee1b8f83cab7fb525afb4ebf7f32`.
Its compressed size is 479,627 bytes.

The run took 4.256 seconds with peak RSS 260,524 KiB. It loaded the
existing complete projector cache and small catalogue, and used no
eigensystem, optimizer or dense count reduction. The source contains a
fresh literal extension replay for any negative form, but no negative
form occurred, so that branch was not needed. No core cut was produced
or added to an optimizer.
