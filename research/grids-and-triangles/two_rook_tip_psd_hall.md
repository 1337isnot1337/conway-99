# Exact tip-PSD audit of the Hall-strengthened search

## Result and limits

The completed Hall-strengthened two-grid run saved 31 partial binary
points, with 30 distinct tip graphs. Its solver status is **unknown at
the wall budget**. This audit checks only the nine-tip necessary matrix

\[
H=3I-R+J-2Z,
\]

proved positive semidefinite for every completion in
`two_rook_tip_psd.md`.

Twenty-six saved points have positive definite `H`. Five have exact
integer negative vectors. No saved point has singular `H`.

Every one of the five negative tip graphs already violates the complete
tip common-neighbor cap

\[
(Z^2)_{ij}+Z_{ij}\le2\qquad(i\ne j).
\]

Thus the negative vectors give valid propagation cuts for a model that
has not yet imposed every cap. These five rejections do **not** establish
an exclusion beyond the complete common-neighbor cap system. They do
not exclude the two-grid core.

Exactly 21 of the 31 points satisfy every tip-only cap. All 21 pass the
PSD test. All 21 also have no tip edge whose labels are rook-adjacent.
The last fact explains their PSD feasibility through the factorization
below; it is an observation about these points, not a universal theorem
about all cap- and Hall-compatible tip graphs.

## Exact negative vectors and edge cuts

Indices below are zero-based indices in the saved Hall transcript. Each
vector uses point order `0,...,8`.

| Point | Integer vector `x` | `x^T H x` | Violating tip pairs |
| --- | --- | ---: | ---: |
| 12 | `(1,0,1,0,1,1,1,1,0)` | -2 | 14 |
| 19 | `(2,1,3,2,2,-1,1,2,3)` | -6 | 7 |
| 20 | `(3,-1,3,5,5,-2,0,3,3)` | -2 | 5 |
| 22 | `(2,2,0,1,2,3,-2,0,3)` | -2 | 3 |
| 24 | `(1,1,1,1,1,0,0,1,1)` | -2 | 16 |

The certificate stores a direct integer common-neighbor witness for
every violating tip pair. It also stores an independent rational
congruence witness for each indefinite matrix and a full positive
rational congruence for each of the other 26 matrices.

For these five vectors, dividing the general PSD inequality by four
and rounding its integer right side down gives

\[
\sum_{i<j}x_i x_jZ_{ij}\le b.
\]

| Point | Required bound `b` | Value in saved point |
| --- | ---: | ---: |
| 12 | 10 | 11 |
| 19 | 63 | 65 |
| 20 | 140 | 141 |
| 22 | 47 | 48 |
| 24 | 12 | 13 |

For the two binary vectors, these are induced-edge bounds on their
supports. For all vectors the certificate includes the complete signed
coefficient list. It also supplies an equivalent encoding with positive
weights on positive or negated edge literals. Both encodings are checked
against the saved point using integer arithmetic.

The vectors were simplified by checking the finite ternary-vector set,
then rounding rational rescalings of the congruence witness. Every
accepted vector is verified by exact multiplication; no approximate
eigenvalue is used to decide a sign.

## Automatic PSD when there are no rook-adjacent tip edges

Suppose `E(Z)` is disjoint from `E(R)`. For every unordered rook-nonedge
`{i,j}`, put `s_ij=1-2Z_ij`, which is either 1 or -1. Then

\[
H=\sum_{\{i,j\}\notin E(R),\ i\ne j}
(e_i+s_{ij}e_j)(e_i+s_{ij}e_j)^{\mathsf T},
\]

where the sum takes each unordered pair once. Every rook point has
four nonneighbors, so the diagonal entries of this sum are four.
Its entries on rook edges are zero, and its entries on rook nonedges
are `1-2Z_ij`, exactly as required. Hence `H` is PSD for every graph in
this subcase, without any common-neighbor or Hall assumptions.

This factorization is also checked directly for every saved point to
which it applies. The 21 cap-compatible points all belong to this
subcase. Whether the full tip cap and Hall constraints force this
subcase has not been established by this audit.

## A finite classification strategy, not executed

The repository's order-nine catalogue has 5,311 unlabeled graphs
satisfying the common-neighbor caps. For each such tip graph `Z`, one
can enumerate rook structures on its nine labelled vertices instead
of enumerating all `2^36` possible tip edge sets.

There are

\[
\frac{9!}{72}=5,040
\]

labelled rook structures. They can be generated from 280 partitions
into three unordered triples. For each partition, there are 36
orthogonal partitions into three triples. Dividing by interchange of
the two partitions gives `280*36/2=5040`.

This yields at most `5311*5040=26,767,440` relative placements before
quotienting by `Aut(Z)`. Orbit enumeration on the 5,040 rook structures
using generators of `Aut(Z)` avoids enumerating a large automorphism
group explicitly. For each relative placement, apply the 103-mask Hall
test first. Placements with no rook-edge overlap need no PSD elimination
because of the factorization above. Only the remaining placements need
exact matrix classification.

This is a finite coverage argument and a proposed ordering of checks.
No such catalogue run, completeness result, or running-time claim is
made here.

## Artifacts and replay

The new audit source is
`experiments/workspace/two_rook_tip_psd_hall_audit.py`. It imports the
frozen exact matrix helper `two_rook_tip_psd_audit.py`; it does not
change the earlier source or certificate.

The self-contained certificate is
`experiments/logs/grids-and-triangles/two-rook-tip-psd-hall-certificate.json`.
It embeds every audited tip graph and every arithmetic witness. Replay
therefore does not require the large search transcript. Supplying the
transcript additionally checks the source binding and point order.

The canonical search artifact is
`two-rook-iso-pair-integer-hall.json.gz`. The audit binds the SHA-256 of
its **decompressed JSON bytes**:

```text
ed560408a9dd8147dfea187206a9218fb43f98d787844c2eb1f493ca0669e059
```

The reader accepts either raw JSON or gzip. Compression metadata does
not affect this binding.

```sh
python experiments/workspace/two_rook_tip_psd_hall_audit.py \
  --input experiments/logs/grids-and-triangles/two-rook-iso-pair-integer-hall.json.gz \
  --certificate experiments/logs/grids-and-triangles/two-rook-tip-psd-hall-certificate.json
```

Omit `--input` for self-contained arithmetic replay. Add `--write`
with an input transcript to regenerate the certificate. Generation
and replay logs use the stem `two-rook-tip-psd-hall-`. No graph-completion
solver is launched by this audit.
