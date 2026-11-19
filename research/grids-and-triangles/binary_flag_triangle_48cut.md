# Binary flag triangle inequalities at the 48-cut point

The latest integer count point passes all 170,183,860 binary triangle
inequalities in the complete eight-root scalar cache. This fills a
specific coverage gap: the two earlier complete scans used different
prism-zero count points.

The [earlier note](binary_flag_triangle_inequalities.md) proves the four
quadratic inequalities, describes the complete domains, and records the
original two runs. Its frozen source is reused unchanged here. The new
input is the point with SHA-256
`0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`.
It has all 48,965 nonnegative integral induced counts, the established
prism-containing zeros, `x521=0`, and the 48 retained linear cuts.

For three binary flags, the tested forms are

\[
1-X_i-X_j-X_k+X_iX_j+X_iX_k+X_jX_k
\]

and the three versions of

\[
X_i-X_iX_j-X_iX_k+X_jX_k.
\]

Each form is nonnegative on every Boolean assignment. Each product uses
at most two vertices outside its eight-vertex root, so all coefficients
belong to the existing order-ten count system.

The run retains all 916 root blocks and every allowed high-mask flag.
It checks the complete mask lists, exact binary diagonals, and sparse
coefficient bounds before integer arithmetic. There are no negative
expressions, exported instances, or new cuts. The process finishes within
the sixty-second bound, returning after 37.943 seconds. No optimizer,
eigensystem, or reduced count matrix is used.

This certifies the stated finite inequality family at this point. It
does not certify all moment matrices or establish graph existence.

The result is
`experiments/logs/moments-and-counts/order10-binary-triangles-48cut-scan01.json`,
with SHA-256
`9f9877d97b80bd9de303c2612a1ed00388c8d1e8a10927dd73ba93ae5713ee9a`.
The preparation and terminal launcher record use the same prefix.

```sh
.venv/bin/python experiments/workspace/root_binary_flag_triangles.py \
  --catalogue /tmp/conway99-order10-catalogue.pickle \
  --cache experiments/logs/moments-and-counts/order10-r8s1-full-blocks.pickle.gz \
  --witness experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json \
  --output /tmp/order10-binary-triangles-48cut-replay.json
```
