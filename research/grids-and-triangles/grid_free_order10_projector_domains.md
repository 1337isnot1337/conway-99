# Eight-root projector domains and exact inverses

All 916 eight-vertex root types have positive definite principal matrices
for both projectors. The complete domains retain 68,176 outside
neighborhood classes, including every allowed mask of size zero, one,
or two. The exact preparation and its replay construct no order-ten
product tensors and make no assertion about feasibility of a count point.

The next intended target is the integer count witness with SHA256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
That witness is not evaluated by this domain package.

## The matrices and their normalization

For the adjacency matrix of a candidate graph, use

\[
Q_-=27I-9A+J=63E_{-4},\qquad
Q_+=44I+11A-2J=77E_3.
\]

These are the same projectors used in the existing
[seven-root certificate](grid_free_projector_order_nine.md).
Fix a labelled root graph H of order eight. For each embedding of H,
take the eight individual root vectors and the indicator of each full
outside neighborhood class. The spectral matrix sums their Q-Gram
matrices over all labelled root embeddings.

An outside mask is retained precisely when adding a vertex with that
root neighborhood respects every visible bound
\((A^2)_{ij}+A_{ij}\leq2\). The preparation checks all 256 masks directly
for every root, then compares the complete list with `extensions()`.
There is no degree-three filter. A low-degree class indicator can be a
sum of many outside vertex vectors.

Let \((d,e,c)\) be \((27,-9,1)\) or \((44,11,-2)\). Write E(F) for
the number of labelled induced embeddings of F. Thus
\(E(F)=|\operatorname{Aut}(F)|c_F\), where \(c_F\) is an unlabelled
induced count. Root-root entries are E(H) times the fixed root Gram
matrix. A root-class entry uses the corresponding one-vertex extension
count multiplied by \(c+e s_i\).

For class masks s,t, the class-class entry has a coincidence term only
when s=t. Its coefficient is d+c. The two distinct-vertex terms have
coefficients c and c+e, according to their mutual edge. The two free
vertices have designated labels, including when s=t. Their product
counts ordered pairs. No free-label stabilizer is divided out.

## Complete sizes

| Family | Blocks for both projectors | Matrix orders | Lower entries |
| --- | ---: | ---: | ---: |
| Spectral, with eight root vectors | 1,832 | 28 to 264 | 7,446,056 |
| Per-embedding Schur | 1,832 | 20 to 256 | 6,289,288 |
| Spectral after nine universal kernel pivots | 1,832 | 19 to 255 | 6,152,936 |
| Schur after nine universal kernel pivots | 1,832 | 11 to 247 | 5,128,072 |

The mask counts by size 0 through 8 are

\[
(916,\ 7328,\ 20839,\ 24096,\ 11755,\ 2733,\ 447,\ 57,\ 5).
\]

Before cap rejection or coefficient merging, the spectral tensors have
at most 13,871,696 coefficient placements, and the Schur tensors have at
most 12,714,928. These are construction bounds, not observed nonzero
counts. No product tensor was generated in this stage.

There are nine universal kernel vectors. In the spectral matrix they
come from the constant vector and the eight vectors
\((A+4I)e_i\) or \((A-3I)e_i\). In the Schur matrix their class
coordinates are simply

\[
(1,s_0,\ldots,s_7).
\]

The zero mask and eight singleton masks give a determinant-one pivot
matrix. Deleting these nine coordinates therefore preserves the PSD
question whenever the kernel equations hold. The domain counts above
record this possible quotient. A later tensor or point verifier must
check its actual kernel equations; the current package does not claim
to have checked unbuilt tensors.

## Exact root checks and arithmetic bounds

For each of the 916 roots and each projector, the source checks all
eight leading principal minors before computing an inverse. All 14,656
minors are positive. This proves positive definiteness by Sylvester's
criterion. The smallest checked minor is 28.

Write the rational inverse as D/h, with D integral and h positive.
The certificate records D and h. Replay verifies
\(GD=hI\), symmetry, and primitive normalization using Python integers.
It does not recompute a numerical inverse. The largest h is 3,870,933.

For a class mask s, define
\(b_s=c\mathbf1+e\,s\). The inverse product needed for Schur
projection is \(b_s^TDb_t\). Its common divisor with h can be determined
from the zero and singleton masks, because

\[
b_s=\sum_{i\in s}b_{\{i\}}-(|s|-1)b_\varnothing.
\]

These masks are present for every root. The preparation verifies this
integer spanning identity for every allowed mask. After the common
divisor is removed, the largest Schur denominator is 351,903.

The preparation also records explicit absolute-sum bounds for both
inverse-product multiplications. Their maxima are 1,532,400 and
61,400,295. The resulting conservative bound on a reduced Schur
coefficient is 20,361,771. These construction products fit signed
64-bit integers, but the source and replay use Python integers anyway.
Later contraction with large graph counts needs a separate accumulation
bound or arbitrary-precision arithmetic. These small construction
bounds do not justify fixed-width count contraction.

As a direct control, delete one vertex of the nine-vertex rook graph.
For its actual remaining class, the negative-projector Schur residual
is exactly zero. The positive-projector residual is
84,700 / 2,530, which is positive. Direct determinants agree with the
Schur identity. This checks a root-plus-one-vertex Gram calculation;
the nine-vertex graph is not treated as a 99-vertex count witness.

## Why the per-embedding Schur condition adds information

The existing `spectral_flags.py --schur` construction removes the root
span separately within each embedding, then sums. This operation is
different from taking the ordinary Schur complement after summing the
spectral matrices.

Let G be the positive definite root Gram matrix, and let n_s(φ) be the
size of class s at root embedding φ. Set

\[
g=\sum_\phi1,\qquad p_s=\sum_\phi n_s(\phi),\qquad
N_{st}=\sum_\phi n_s(\phi)n_t(\phi),\qquad
H_{st}=b_s^TG^{-1}b_t.
\]

Let D denote the summed outside-class projector Gram matrix. For g>0,
the ordinary Schur complement of the averaged spectral matrix is

\[
D-H\circ\frac{pp^T}{g}.
\]

The per-embedding construction instead requires

\[
D-H\circ N\succeq0.
\]

Their difference is

\[
H\circ\left(N-\frac{pp^T}{g}\right).
\]

Both factors are PSD when the full class-count moment matrix is PSD,
so this difference is PSD by the Schur product theorem. The
per-embedding condition can therefore be stronger. It is not obtained
by a fixed congruence of the averaged spectral block alone. For an
algebraic example, g=2, p=2, N=4, H=1, D=3 gives PSD averaged spectral
and scalar-count moment matrices, but the per-embedding residual is
−1. This example distinguishes the matrix inequalities; it is not a
graph construction.

The full class-count moment is already an affine image of the scalar
high-mask moment, using the exact degree and common-neighbor identities.
To see this, let B be the root adjacency matrix and define

\[
d_i=14-\deg_H(i),\qquad
q_{ij}=2-B_{ij}-(B^2)_{ij}.
\]

For a fixed root embedding, the low-mask class sizes satisfy

\[
\begin{aligned}
n_{\{i,j\}}&=q_{ij}-\sum_{s\supseteq\{i,j\},\ |s|\geq3}n_s,\\
n_{\{i\}}&=d_i-\sum_{j\ne i}q_{ij}
 +\sum_{s\ni i,\ |s|\geq3}(|s|-2)n_s,\\
n_\varnothing&=91-\sum_i d_i+\sum_{i<j}q_{ij}
 -\sum_{|s|\geq3}\binom{|s|-1}{2}n_s.
\end{aligned}
\]

If q_ij=0, that pair mask and every higher mask containing it are
forbidden by the caps. The displayed relation then reads 0=0. A mask
of size at least three is binary, since two vertices with that mask
would have at least three common neighbors. All relations are at the
same labelled root embedding, so summing their products introduces no
automorphism divisor. They explain how the existing complete r8s1
scalar family supplies the required class-count covariance.

The case g=0 must be handled separately. A PSD scalar moment matrix
alone need not force its entire lower block to vanish. Here the
nonnegative induced counts and the original unmarked extension
identities force every one-vertex and then every two-vertex extension
count to be zero. Thus both projector blocks are zero when the root
count is zero. The reusable domains omit no root or mask on this basis.

## Files and replay

Source:
`experiments/workspace/grid_free_order10_projector_domains.py`

Source SHA256:
`3c5973dd74b3daadff09dc7ec967a7ab156afe06b6140d5520d0093dabc455c0`

Certificate, before deterministic gzip compression:
`experiments/logs/moments-and-counts/order10-eight-root-projector-domains.json`

Uncompressed SHA256:
`b1a35b1d8dbabf870331fc591e6d332ed503a447b2cdc81f83c6b5d5c8bcbf1f`

The compressed artifact has the same path with `.gz` appended. Decompress
it without changing its contents, then run:

```sh
python experiments/workspace/grid_free_order10_projector_domains.py \
  --catalogue /tmp/conway99-order10-catalogue.pickle \
  --replay experiments/logs/moments-and-counts/order10-eight-root-projector-domains.json \
  --output /tmp/order10-eight-root-projector-domains-replay.json
```

Generation took 8.142 seconds with peak RSS 128,800 KiB. The saved
integer replay took 6.885 seconds. The frozen manifest binds the source,
compressed certificate, note, and generation/replay records. This is a
complete domain and inverse preparation for the two specified families,
not a certificate for the full order-ten PSD cone.
