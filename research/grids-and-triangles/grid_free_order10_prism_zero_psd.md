# Exact PSD certificates for the prism-zero count prefix

## Result and scope

All 1,416 previously cached order-nine moment and projector blocks are
positive semidefinite at the unchanged 58-coordinate prefix of the
[repaired prism-zero count witness](grid_free_order10_prism_zero_repair.md).
Every block has an exact certificate, and the complete certificate replay
passes without numerical eigensystems or an optimizer.

Combined with the count witness, this gives an exact feasible point for
the complete available order-ten count equations, their nonnegative
integer counts and certified upper bounds, the fourteen saved linear
cuts, and this selected family of 1,416 PSD inequalities. The prism, rook,
and broken-rook counts are zero.

It does not give a graph. It does not certify all possible order-nine or
order-ten PSD inequalities. In particular, the cached matrices here use
only the old 58-coordinate prefix; they are not new order-ten moment
blocks. These finite constraints cannot force a positive prism count.

The earlier count-witness artifact remains unchanged. This separate
certificate supplies the exact cached-PSD verification that was absent
from that checkpoint.

## Covered blocks

| Family | Number of blocks |
| --- | ---: |
| Ordinary rooted moment blocks | 292 |
| Induced rooted moment blocks | 292 |
| Induced spectral projector blocks | 416 |
| Induced Schur projector blocks | 416 |
| Total | 1,416 |

There are 18 exactly zero matrices. The other 1,398 blocks have
positive-definite principal quotients after justified kernel removal.
The largest original matrix and largest retained quotient both have
order 242.

Exactly 838 zero rows are removed across 276 blocks. Among the 832
projector blocks, 12 matrices are zero. The restricted established kernel
has rank eight in 812 blocks and rank seven in the other eight. The
rank-seven cases are handled by exact rank computation; the source does
not assume that all eight kernel vectors remain independent after zero
rows are removed.

## Exact matrix construction

The source loads the existing order-nine embedding forms and evaluates
them at the integer prefix. It checks that the resulting 6,535 induced
counts equal the corresponding entries of the independently saved
order-ten witness.

Each sparse cache tensor then produces a symmetric integer matrix. For
every product, the code computes an absolute-sum overflow bound using
Python integers. It uses fixed-width multiplication only when that bound
is below `2^63`; otherwise it computes the product with Python integers.
Before storing a matrix as signed 64-bit integers, it checks the range of
every entry. Matrix hashes use a fixed little-endian representation.

No sign decision depends on floating-point arithmetic. Floating-point
Cholesky is used only to propose an integer change of coordinates.

## Zero rows and kernel quotients

A zero diagonal entry does not by itself justify removal. The verifier
checks that the entire corresponding row is exactly zero. A negative
diagonal, or a zero diagonal with a nonzero off-diagonal entry, instead
produces an explicit negative integer quadratic form. Neither situation
occurs here.

For each nonzero projector block, the source constructs the eight
established kernel vectors from the seven-vertex root graph and its
allowed extension masks. It verifies `M K = 0` exactly. After zero rows
are removed, exact rational row reduction selects independent kernel
columns and pivot rows. The selected kernel minor has a nonzero exact
integer determinant. It need not have determinant one; the largest
absolute determinant in this certificate is 16,384.

The justification for taking a principal quotient is elementary. Let
`K` have independent columns in the kernel of a symmetric matrix `M`.
Let `J` be row indices for which `K[J,:]` is invertible, and let `I` be
the complementary indices. For any vector `v`, choose

\[
a=K[J,:]^{-1}v_J,\qquad u=v-Ka.
\]

Then `u[J]=0`, and `M K=0` gives

\[
v^T Mv=u_I^T M[I,I]u_I.
\]

Thus `M` is positive semidefinite exactly when the retained principal
matrix `M[I,I]` is positive semidefinite. No graph automorphism or
unproved rank assumption enters this reduction.

## Positive-definite quotient certificates

Each nonempty retained matrix `B` has a saved upper-triangular integer
matrix `Q` with nonzero diagonal. Exact arithmetic verifies that

\[
C=Q^TBQ
\]

satisfies

\[
C_{ii}>\sum_{j\ne i}|C_{ij}|
\]

for every row. This strict positive diagonal dominance implies that `C`
is positive definite. Since `Q` is invertible, `B` is also positive
definite. The kernel argument above then proves PSD of the original
block.

All 1,398 nonempty quotients succeeded at the first congruence scale,
`2^20`. The smallest exact dominance margin is
313,558,328,776,590. The 18 empty quotients correspond to exactly zero
matrices and require no congruence.

Generation completed in 64.683 seconds, within the 240-second bound, with
no unresolved or negative block. Peak process memory was about 209 MB.
The subsequent exact replay verified all 1,416 certificates. It did not
recompute a numerical eigensystem.

## Frozen files

Source:
`experiments/workspace/grid_free_order10_prism_zero_psd.py`

Source SHA-256:

```text
b15c339a3a25da0a2ee5cf2ce5161e48b1323750712445aa3c3d68a9a1e91aa3
```

Compressed certificate:
`experiments/logs/moments-and-counts/prism-zero-psd-certificate.json.gz`

Certificate SHA-256:

```text
29ba5e55844d11eef18e312411b9ecbff181fd21aab371298c780216a9cb5524
```

The certificate is 3,275,406 bytes. It binds the count witness, old count
cache, matrix caches, helper sources, every full and quotient matrix,
zero-row lists, exact kernel pivots, integer congruences, and dominance
margins. The same directory contains the generation log, exact replay
log, summary, statistics, and package manifest with prefix
`prism-zero-psd`.

Run the exact replay from the repository root:

```sh
.venv/bin/python experiments/workspace/grid_free_order10_prism_zero_psd.py replay \
  --certificate experiments/logs/moments-and-counts/prism-zero-psd-certificate.json.gz
```
