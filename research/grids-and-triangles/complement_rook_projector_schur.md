# Small projector tests for the complementary-rook core

The negative spectral projector forbids 1,296 of the 209,952 eligible
exterior triangles. They form nine orbits under the 144 core relabelings.
Every candidate vertex and every pair passes both projector tests
strictly. The positive projector also accepts all 209,952 triangles.

These are necessary triangle restrictions. They do not exclude the
complementary-rook core. No source signature or eligible edge loses all
triangle support. No solver or large CNF is used in this census.

## Core and projector normalization

Let `R` be the adjacency matrix of the rook graph on the nine points
`0,...,8`, with coordinates `(p//3,p%3)`. The 27-vertex core has matrix

\[
B=\begin{pmatrix}
 R&I&I\\
 I&R&I\\
 I&I&J-I-R
\end{pmatrix}.
\]

The three bases are called `R`, `S`, and `T`. The intrinsic graph on `T`
is the complement of the fixed rook graph. Every exterior vertex has one
neighbor in each base. The complete admissible signature domain consists
of the 252 triples

\[
(p,q,t),\qquad p\ne q,\quad R_{pq}=0,\quad t\notin\{p,q\}.
\]

Write `h_s` for the corresponding 27-entry incidence column. The Gram
margins are `G=12I+2J-B^2-B`. The existing mixed demands and pair bounds
permit 20,934 possible exterior edges. Of these, 14,652 join disjoint
signatures. An actual exterior triangle must use three such edges:
an adjacent exterior pair already has its third vertex as a common
neighbor, so it cannot also share a core neighbor.

For a genuine SRG(99,14,1,2), the two nonprincipal spectral projectors
satisfy

\[
Q_-=27I-9A+J=63E_{-4}\succeq0,
\qquad
Q_+=44I+11A-2J=77E_3\succeq0.
\]

The formulas follow by evaluating the polynomials at the eigenvalues
`14,3,-4`; `J` has eigenvalue 99 on the constant vector and zero on its
orthogonal complement. In particular, both matrices vanish on the
constant vector.

## The singular core block

The core block `27I-9B+J` has rank 24. Its kernel is exactly the span of
the three base indicators. The coupling of a new signature to this
block is

\[
q_s=\mathbf1-9h_s.
\]

It sums to zero separately on each base, so every candidate signature
is compatible with all three kernel vectors. A singular Schur test must
check this compatibility; it cannot simply discard the kernel.

Delete core coordinates `8,17,26`, retaining the coordinate set `I`.
Let `K_-` be the resulting 24-by-24 principal submatrix. Each deleted
coordinate of a Gram vector is minus the sum of the other eight vectors
in its base. Thus, with the corresponding integral expansion matrix `F`,

\[
27I-9B+J=FK_-F^T,
\qquad q_s=F(q_s|_I).
\]

The program verifies both equalities exactly, computes a positive
rational LDL factorization of `K_-`, and verifies its scaled inverse by
matrix multiplication. Its inverse has common denominator 324. Hence
the correct residual inner product is

\[
q_s|_I^T K_-^{-1}q_t|_I.
\]

There is no extra factor from the deleted coordinates.

The positive core block `K_+=44I+11B-2J` is positive definite on all 27
coordinates. Its coupling is `r_s=11h_s-2*1`. The same exact LDL and
inverse checks apply; its inverse has common denominator 40,040.

## Residual matrices

For selected exterior signatures, let `e_st` be their adjacency bit.
The negative residual matrix has entries

\[
\begin{split}
(S_-)_{ss}&=28-q_s|_I^TK_-^{-1}q_s|_I,\\
(S_-)_{st}&=1-9e_{st}-q_s|_I^TK_-^{-1}q_t|_I\quad(s\ne t).
\end{split}
\]

The positive residual matrix has entries

\[
\begin{split}
(S_+)_{ss}&=42-r_s^TK_+^{-1}r_s,\\
(S_+)_{st}&=-2+11e_{st}-r_s^TK_+^{-1}r_t\quad(s\ne t).
\end{split}
\]

Both must be positive semidefinite. On this finite signature domain,
all entries have common denominators 4 and 520, respectively. The
computation uses Python integers and rational numbers throughout.

The signature types and one-point residual values are:

| Type | Condition | Signatures | Negative residual | Positive residual |
| --- | --- | ---: | ---: | ---: |
| 0 | Both `R[p,t]` and `R[q,t]` equal 1 | 72 | 33/2 | 15103/520 |
| 1 | Exactly one equals 1 | 144 | 35/2 | 231/8 |
| 2 | Both equal 0 | 36 | 37/2 | 14927/520 |

All 31,626 distinct signature pairs are checked for both values of
`e_st`, not only the eligible edges. They form 264 relabeling orbits.
Every two-by-two residual matrix is positive definite for both
projectors. This includes the 648 signature pairs already incompatible
with a Gram margin and the 10,044 additional pairs whose edge is
ineligible. There is no one-point or two-point restriction to add.

## Complete triangle census

The disjoint-signature eligible graph has exactly 209,952 triangles.
Its ordered triangle-list hash agrees with the frozen
`complement-rook-triangle-domains.json` certificate. The triangles form
1,500 orbits under simultaneous rook relabeling and optional interchange
of the first two bases.

Every two-by-two principal minor is already positive. The determinant
therefore decides each three-by-three residual matrix:

| Projector | Positive definite | Indefinite | Singular |
| --- | ---: | ---: | ---: |
| Negative | 208,656 | 1,296 | 0 |
| Positive | 209,952 | 0 | 0 |

All rejected triangles consist of three type-1 signatures. The nine
representatives below use the signature indices from the complete
252-column domain. Each orbit has size 144. The three pattern names
describe the selected points in the actual core graphs `R,S,T`.

| Representative indices | Patterns in R, S, T | All-ones quadratic | Negative residual vector | Its quadratic |
| --- | --- | ---: | --- | ---: |
| 1,31,88 | path, path, path | -1/2 | (1,1,1) | -1/2 |
| 1,31,89 | path, path, path | -1/2 | (1,1,1) | -1/2 |
| 1,32,87 | path, path, path | -1/2 | (1,1,1) | -1/2 |
| 1,32,89 | path, path, path | -1/2 | (1,1,1) | -1/2 |
| 1,32,170 | path, path, path | -1 | (1,1,1) | -1 |
| 1,33,87 | path, path, path | -1/2 | (1,1,1) | -1/2 |
| 1,33,88 | path, path, path | -1/2 | (1,1,1) | -1/2 |
| 1,33,119 | path, one edge, path | 0 | (7,6,6) | -1/2 |
| 1,37,87 | path, path, one edge | 0 | (7,8,8) | -5/2 |

The certificate stores the actual point labels, all three selected
edges or nonedges in each base, and both the fixed-R and intrinsic-core
patterns. The all-ones vector alone does not prove the last two cases.

For example, indices `(1,31,88)` correspond to
`(0,4,2),(1,3,5),(3,1,6)`. Their negative residual is

\[
\begin{pmatrix}
35/2&-8&-9\\
-8&35/2&-19/2\\
-9&-19/2&35/2
\end{pmatrix}.
\]

Its determinant is `-251/2`, and its all-ones quadratic is `-1/2`.

Each residual witness is also lifted to an integer vector on the full
30-vertex induced graph. To obtain that vector, assign the core
coordinates `-K_-^{-1} Q u`, set deleted coordinates to zero, and use
`u` on the three exterior vertices. Clear denominators and divide the
common factor. The program directly verifies

\[
27\sum_i v_i^2-18\sum_{\{i,j\}\in E}v_iv_j+
\left(\sum_i v_i\right)^2<0.
\]

This gives a separate integer check of every representative without
relying on a numerical eigenvalue calculation. All nine induced
30-vertex graphs satisfy every visible common-neighbor cap: 435 pair
checks per representative. The exclusions therefore go beyond those
caps on these particular induced subgraphs. No claim is made that the
entire existing joint formula could not derive the same exclusions.

The artifact expands the nine orbits to 1,296 distinct forbidden
triangles and exports their three-literal clauses in the existing
global edge-variable order:

\[
\neg e_{st}\ \lor\ \neg e_{su}\ \lor\ \neg e_{tu}.
\]

Edge activation already requires all three endpoints to be selected,
so additional selector literals are unnecessary.

## Remaining triangle support

The exact source-wise count is constant within each signature type:

| Source type | Triangles before | Removed | Triangles after |
| --- | ---: | ---: | ---: |
| 0 | 2,226 | 0 | 2,226 |
| 1 | 2,583 | 27 | 2,556 |
| 2 | 2,712 | 0 | 2,712 |

Every eligible disjoint edge also retains triangle support. The minimum
remaining count is 24. The artifact records the full edge-support
histogram. These local exclusions alone eliminate no signature or edge.

## Exact replay

Files:

- `experiments/workspace/complement_rook_projector_schur.py`
- `experiments/logs/grids-and-triangles/complement-rook-projector-schur.json`
- `experiments/logs/grids-and-triangles/complement-rook-projector-schur-generation.log`
- `experiments/logs/grids-and-triangles/complement-rook-projector-schur-replay.log`

The program uses only the standard library. It reconstructs the core,
signature domain, eligible edges, group actions, and both exact inverse
calculations. It then repeats the complete pair and triangle census and
compares the result with the certificate.

```sh
python experiments/workspace/complement_rook_projector_schur.py \
  --certificate experiments/logs/grids-and-triangles/complement-rook-projector-schur.json
```

The scope is the complete one-point and two-point tests, and the
three-point tests whose three vertices form an eligible triangle. It is
not a census of all adjacency patterns on three exterior vertices.
