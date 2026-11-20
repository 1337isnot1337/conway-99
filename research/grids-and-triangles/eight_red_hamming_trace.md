# Eight all-red grids cannot leave only three-triangle vertices

Suppose a hypothetical `srg(99,14,1,2)` has eight all-red grids. Let `U`
be the 27 remaining vertices. It is impossible for every vertex of `U`
to lie in three triangles contained in `U`.

This excludes a larger class than the Hamming case in
[`eight_red_hamming.md`](eight_red_hamming.md). No classification of
27-vertex graphs, covering enumeration, or linearity of a projection is
assumed. The argument uses the red-grid facts in
[`red_grid_limit.md`](red_grid_limit.md): distinct all-red grids are
disjoint; every exterior vertex has one neighbor in a grid; and the
matching between two all-red grids is a rook-graph isomorphism.

## Selected and omitted triangles

Every vertex of `U` has six neighbors in `U`. Every red-base vertex has
three neighbors in `U`. For each red base `R_i`, write `pi_i: U -> R_i`
for the unique-neighbor map; every fiber has size three.

The inverse image of each red line consists of three disjoint triangles
of `U`, each mapped bijectively onto that line. Indeed, the six grids
through the red line partition its exterior neighbors. A grid through
that line meets every other all-red base in zero vertices or in a full
parallel line. Its remaining vertices in `U` therefore form zero, one,
or two parallel lines. Together these partition the nine-point inverse
image of the red line into three triangles.

At each `u ∈ U`, the row and column through `pi_i(u)` select two distinct
triangles through `u`. If every vertex lies in three `U`-triangles, these
leave exactly one omitted triangle at each vertex. Being selected is a
property of the whole triangle, so the omitted triangles partition `U`
into nine triangles for each base.

An omitted triangle maps to an independent triple in the base rook grid.
First, its images are distinct: any edge of that triangle already has
its unique common neighbor inside `U`, and its endpoints cannot also
have the same red-base neighbor.

Next let `p=pi_i(u)` and let `r` be adjacent to `p` in `R_i`. The selected
row or column triangle through `u` has a neighbor `v` of `u` with
`pi_i(v)=r`. The nonadjacent pair `(u,r)` already has its two common
neighbors `p,v`. Thus no other neighbor of `u` in `U` can map to `r`.
In particular neither omitted-triangle neighbor can map to any neighbor
of `p`. The three images of an omitted triangle are therefore pairwise
nonadjacent. They have one point in each row and each column of the
rook grid.

## Lifted rook functions lie in the kernel on U

Let `B` be a rook adjacency matrix. Its eigenvalue-one space consists of
functions

\[
f(a,b)=r_a+c_b,\qquad \sum_a r_a=\sum_b c_b=0,
\]

and has dimension four. The sum of such a function on any independent
three-point transversal is zero.

Lift `f` to `U` by `f(pi_i(u))`. At `u`, its four neighbors in the two
selected triangles map bijectively to the four rook neighbors of
`pi_i(u)`. Their function sum is `(Bf)(pi_i(u))=f(pi_i(u))`.
The other two neighbors lie in the omitted triangle. Its image is a
transversal, so their function sum is `-f(pi_i(u))`.

The total sum over the six neighbors is zero. Consequently every lifted
rook eigenvalue-one function lies in the kernel of the adjacency matrix
`C` on `U`.

## An invariant space of impossible dimension and trace

Order the full graph by the 72 red-base vertices and then `U`, and write

\[
A=\begin{pmatrix}H&Q\\Q^T&C\end{pmatrix}.
\]

Let `W` be the direct sum of the eight rook eigenvalue-one spaces on the
red bases. Its dimension is 32. All matching blocks of `H` are rook
isomorphisms, so `H` preserves `W`. Its diagonal blocks act as identity
on each four-dimensional summand; hence

\[
\operatorname{tr}(H|_W)=32.
\]

Set `T=Qᵀ|_W` and `Z=im(T)`. The preceding function calculation says
`C|_Z=0`.

The red/red block of the SRG identity is

\[
H^2+H+QQ^T=12I+2J.
\]

Both `H` and `J` preserve `W`, and `J` vanishes there. It follows that
`QQᵀ` preserves `W`. Thus `QZ ⊆ W`, and

\[
V=W\oplus Z
\]

is invariant under `A`. The two summands use disjoint vertex supports,
so this is an orthogonal direct sum. It is orthogonal to the global
constant vector: vectors in `W` sum to zero on each base, and
`Q 1_U=3·1_R`, so vectors in `QᵀW` also sum to zero.

On `V`, the adjacency operator has block form

\[
A|_V=\begin{pmatrix}H|_W&T^*\\T&0\end{pmatrix},
\qquad (A|_V)^2+A|_V=12I_V.
\]

Its lower-right block gives `TT*=12I_Z`. Therefore

\[
12\dim Z=\operatorname{tr}(TT^*)
=\operatorname{tr}(T^*T).
\]

For each base, the rows of its incidence matrix to `U` are disjoint
fibers of size three. Its diagonal Gram block is therefore `3I_9`.
Taking traces on the eight four-dimensional summands of `W` gives

\[
\operatorname{tr}(T^*T)=8\cdot4\cdot3=96.
\]

Hence `dim Z=8`, `dim V=40`, and `tr(A|_V)=32`. The polynomial
`x²+x-12` forces all eigenvalues of this symmetric restriction to be
three or minus four. If `r` is the multiplicity of three, then

\[
3r-4(40-r)=32,
\qquad 7r=192.
\]

This has no integer solution. The assumed all-three-triangle remainder
is impossible.

## What remains

Every vertex of an eight-red remainder lies in either two or three
internal triangles. This proof excludes the case in which all 27 lie
in three. It does not exclude mixed remainders or prove that eight
all-red grids are impossible.

The argument does not use the claim that every rook grid contained in
`U` has a rook-isomorphic matching to a red base. That claim is not
assumed here.

## Exact local control

`experiments/workspace/eight_red_hamming_trace.py` uses only Python's
standard library. It constructs an exact four-dimensional basis of the
rook eigenvalue-one space, checks all six transversals and their eighteen
pointed local identities, and checks the rank and trace arithmetic above.
These calculations audit the finite ingredients of the proof; the
invariant-space argument establishes the theorem without enumeration.

```bash
python experiments/workspace/eight_red_hamming_trace.py \
  --output experiments/logs/grids-and-triangles/eight-red-hamming-trace.json
```
