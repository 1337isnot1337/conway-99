# Exact identities for an unrestricted triangle neighborhood

This note assumes only a hypothetical strongly regular graph with parameters
`(99,14,1,2)`. It does not assume a saturated triangle, a grid, or a graph
automorphism. It records a reduction and the limits of several local tests;
it does not exclude all triangle neighborhoods.

The three fibers and the sixty exterior vertices are already described in
[`triangle_star.md`](triangle_star.md). The numerical individual-signature
projector tests already occur in
[`triangle_ball.py`](../../experiments/workspace/triangle_ball.py).
The contributions here are exact formulae for their core kernels and ranks,
an exact description of the visible core caps, and the sharper counts below.

## 1. The mandatory 39-vertex core

Let `T` be a triangle. Its other neighbors form three twelve-vertex fibers
`X_0,X_1,X_2`, indexed by their unique neighbor in `T`. Each fiber induces a
perfect matching. Between each pair of fibers there is a perfect matching.
After relabeling, the adjacency matrix on their union is

\[
D=\begin{pmatrix}M&I&I\\I&P&Q\\I&Q^T&R\end{pmatrix},
\]

where `M,P,R` are fixed-point-free involution matrices and `Q` is a
permutation matrix. We use the convention `Q[i,q(i)]=1`. Let `E` be the
36-by-3 fiber-indicator matrix. Then

\[
DE=EJ_3,\qquad D\mathbf1=3\mathbf1.
\]

Write `B` for the full 39-by-39 core adjacency matrix, with the triangle
first. Write `c` for the number of connected components of `D`. Every
component meets the three fibers in the same number `m` of vertices:
the cross-fiber matchings restrict to bijections. This number is even,
since the internal perfect matchings also remain in the component.

### Visible common-neighbor caps

The necessary core inequalities

\[
(B^2+B)_{uv}\le2\quad(u\ne v)
\]

hold if and only if `D` has no two equal open-neighbor rows.

Pairs involving the central triangle already have their required core
common-neighbor counts. Two different vertices in one fiber have no common
neighbor in `D`, and have their central triangle vertex in common. An
adjacent pair from different fibers can have a common `D`-neighbor only in
the third fiber, so it has at most one. A nonadjacent pair from different
fibers violates the cap exactly when it has three common `D`-neighbors.
Since `D` is cubic, this is exactly equality of its two neighbor rows.

Consequently, a component with `m=2` must be a triangular prism. The only
two possibilities on these six vertices are the prism and `K_{3,3}`;
the latter has equal neighbor rows. Adding the central triangle to a prism
component gives an induced 3-by-3 rook graph. Conversely, each rook grid
through `T` uses a whole prism component, since all three shell neighbors
of each of its six shell vertices are already inside that component.

## 2. The exterior incidence Gram and all its kernels

Let `X` be the 39-by-60 core-to-exterior incidence matrix. The strongly
regular identity gives

\[
XX^T=12I+2J-B-B^2.
\]

Its three central rows and columns vanish. Its shell block is

\[
G_D=12I+2J-D-D^2-EE^T.\tag{1}
\]

The block within a fiber with matching matrix `M_i` is

\[
9I+J-M_i.\tag{2}
\]

Each exterior vertex has two neighbors in each fiber, and they are not
mates. Formula (2) shows that every one of the sixty non-mate pairs in
each fiber occurs exactly once. Thus the sixty exterior vertices are
uniquely indexed by this pair catalogue in any chosen fiber. The other
two fiber pair assignments are bijections of their catalogues.

Let `W` be the 33-dimensional space of shell vectors whose sum is zero
in each fiber. On `W`, (1) is

\[
G_D|_W=(3I-D)(4I+D).
\]

The spectrum of a cubic graph lies in `[-3,3]`. The eigenvalue 3 of `D`
has multiplicity `c`. Exactly `c-1` of these directions lie in `W`.
The all-ones direction has eigenvalue 60 in `G_D`, and the two differences
of fiber indicators are in its kernel. Therefore

\[
\operatorname{rank}(XX^T)=35-c.\tag{3}
\]

Its full kernel consists of the three central coordinate vectors, the
two fiber differences, and the `c-1` independent component-balance
vectors. In particular, for an exterior signature `h` on the shell and
a component `C` meeting each fiber in `m` vertices,

\[
|h\cap C|=m/2.\tag{4}
\]

There are no additional kernel equations from (1).

For reference, if `m=2r`, the numbers of exterior vertices with zero, one,
or two neighbors in `C` in any fixed fiber are respectively

\[
2(r-5)(r-6),\quad4r(6-r),\quad2r(r-1).
\]

These are simply the counts of non-mate pairs outside, across, or inside
the component's `2r` fiber vertices.

## 3. Both principal projector tests are automatic

The two scaled eigenspace projector matrices of the complete graph are

\[
L_-=3I-A+J/9,\qquad L_+=4I+A-2J/11.
\]

Their shell principal blocks are

\[
F_-=3I-D+J/9,\qquad F_+=4I+D-2J/11.
\]

The first is positive semidefinite: `3I-D` is a graph Laplacian, and the
added term is positive semidefinite. It has rank `37-c`. The second is
positive definite: on the constant direction its eigenvalue is `5/11`,
and on the orthogonal complement it is `4I+D`, whose eigenvalues are at
least 1.

The triangle rows add no rank. Define

\[
Y_-=E(-I_3/3+J_3/18),\qquad
Y_+=E(I_3+J_3)/4.
\]

The shell-to-triangle blocks are `W_-=-E+J/9` and `W_+=E-2J/11`.
Using `DE=EJ_3` gives

\[
F_\pm Y_\pm=W_\pm,\qquad
(L_\pm)_{T,T}=W_\pm^TY_\pm.
\]

Block congruence therefore reduces each 39-by-39 principal matrix to
`F_\pm` and a zero 3-by-3 block. Hence, for every choice of `M,P,R,Q`,

\[
L_-[B]\succeq0,\quad\operatorname{rank}L_-[B]=37-c;
\qquad
L_+[B]\succeq0,\quad\operatorname{rank}L_+[B]=36.\tag{5}
\]

These statements even hold for shells with false twins. They do not
replace the visible caps or the tests for individual exterior signatures.

### Exact forms of the existing single-signature tests

Suppose `h` is a binary shell signature with two points in each fiber and
the component balances (4). Put `u=h-\mathbf1/6` and `L=3I-D`. The two
single-column Schur bounds implemented numerically in `triangle_ball.py`
are exactly

\[
u^TL^+u\le37/12,\qquad
u^T(4I+D)^{-1}u\le19/5.\tag{6}
\]

Here `L^+` is the Moore-Penrose inverse. Equivalently, the second bound is
`h^T(4I+D)^{-1}h\le138/35`. For the negative projector, the constant part
of the cross vector contributes `1/36`; subtracting this from its
diagonal `28/9` gives `37/12`. For the positive projector, the constant
contribution is `1/55`; subtracting it from `42/11` gives `19/5`.
The triangle-coordinate consistency uses exactly the two-per-fiber
condition, and the negative-projector range uses exactly (4).

The complete mixed cap also requires

\[
(D+I)h\le2.\tag{7}
\]

Thus `D[h]` is a matching, and no unselected shell vertex has all three
of its shell neighbors selected. The existing `triangle_ball.evaluate`
does not explicitly enforce all of (7).

## 4. Counts valid for every shell

Let `f` be the number of fixed points of `q`. Every shell triangle uses
one vertex from each fiber, so `D` has exactly `f` triangles. If `d_T`
is the number of rook grids through `T`, the prism-component description
gives

\[
d_T=\#\{\text{six-vertex components of }D\},\qquad f\ge2d_T.
\]

The inequality need not be equality on a shell description. In particular,
`f=12` says `Q=I`; it does not by itself say that `D` has six components
or that `T` is saturated.

Internal fiber edges cannot occur inside an exterior signature. Each of
the 36 cross-fiber edges has one exterior common-neighbor slot, except
when its unique common neighbor is already the third vertex of a shell
triangle. Summing these slots gives the exact refinement of the earlier
bound in `triangle_star.md`:

\[
\sum_{w=1}^{60}e(D[h_w])=36-3f.\tag{8}
\]

At least `24+3f` exterior signatures are therefore independent sets.

Let `C` be the adjacency matrix on the sixty exterior vertices. It is
8-regular. If `j=e(D[h_w])`, the local perfect matching at `w` pairs
`6-2j` of its eight exterior neighbors with shell neighbors. The other
`2+2j` exterior neighbors form `1+j` edges. Thus `w` lies in `1+j`
triangles of the exterior graph, and

\[
t(C)=32-f.\tag{9}
\]

For completeness, the already-derived general characteristic polynomial
relation is

\[
\chi_C(x)=
\frac{(x-8)(x-3)^{18}(x+4)^7\chi_D(-x-1)}{(x+1)^2}.\tag{10}
\]

To derive it, remove the global constant and the two fiber differences
from the shell space. On the remaining space, `D` acts on `W`. For each
eigenvalue `\beta\ne3` there, the mixed equation sends a nonzero incidence
image to a `C`-eigenvector of eigenvalue `-1-\beta`. There are `34-c`
such directions. The constant exterior direction gives eigenvalue 8.
The remaining incidence kernel has dimension `25+c`; the strongly
regular identity restricts `C` there to eigenvalues 3 and -4. Its trace
determines their multiplicities as 18 and `7+c`. Finally, `D` has the
two zero eigenvalues from fiber differences, which account for the
denominator in (10).

Equation (10) is recorded here as a general identity. No new search on
saturated-triangle spreads or their exterior spectra was made in this
work.

## 5. Exact controls and the completed small probe

The standard-library verifier
[`triangle_root_constraints.py`](../../experiments/workspace/triangle_root_constraints.py)
checks the integer versions of (1), (3), and (5), the full kernel basis,
all visible caps, the shell triangle count, and the component pair profiles
on three explicit controls:

| `M=P=R` is the usual mate involution | `Q` | Shell components | False-twin pairs | `f` |
| --- | --- | --- | ---: | ---: |
| six matched pairs | identity | six triangular prisms | 0 | 12 |
| six matched pairs | mate involution | six copies of `K_{3,3}` | 36 | 0 |
| six matched pairs | `q(i)=i+2 mod 12` | one circular ladder on 36 vertices | 0 | 0 |

The negative control verifies that exactly the false-twin pairs violate
the core caps. Exact Fraction elimination also checks the stated ranks.
These are formula and indexing controls, not a complete census.

The single connected shift-by-two core was also passed to the preexisting
numerical `triangle_ball.evaluate`. It returned 26,352 candidate triples
of fiber pairs, with at least 404 for each prescribed pair in any one
fiber. These candidates passed that function's numerical projector/range
and selected-pair quota filters. They were not checked by that function
against the full mixed cap (7), and they are not an incidence design or
a graph completion. No core exclusion follows from this result.

Saved records are
[`triangle-root-constraints-exact.json`](../../experiments/logs/grids-and-triangles/triangle-root-constraints-exact.json)
and
[`triangle-root-constraints-shift2-probe.json`](../../experiments/logs/grids-and-triangles/triangle-root-constraints-shift2-probe.json).
The exact replay is:

```sh
python experiments/workspace/triangle_root_constraints.py --replay experiments/logs/grids-and-triangles/triangle-root-constraints-exact.json
```

The reduction does not remove any of the eleven unrestricted root matching
orbits. It identifies the binary pair-bijection and mixed-cap conditions
that remain after the automatic principal spectral tests.
