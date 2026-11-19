# Structural constraints for one isomorphic rook pair

## Scope and results

Assume that an SRG(99,14,1,2) contains two disjoint induced rook grids
whose matching is a rook isomorphism. Label both grids by the points
of `F_3^2`, with the matching equal to the identity. Let `R` be the
nine-point rook adjacency matrix. The nine matched edges have nine
distinct tips `z_p`; write `Z` for their induced adjacency matrix.

This note does not exclude a single isomorphic pair. It establishes
structural constraints and records a complete small incidence reduction
inside the particular boundary case `Z=J-I-R`.

The finite result is as follows. In that complementary-rook case, an
exterior vertex has a signature `(p,q,t)`, one neighbor in each of the
three grids. Let `a` count the signatures for which both `p,t` and
`q,t` are rook-adjacent in the original labeling. If `a=0`, there are
exactly 16 labeled incidence designs. They have three orbits of sizes
12, 2, and 2 under simultaneous rook relabeling and exchange of the
first two grids. Exact integer Farkas certificates exclude the first
14 designs. The last orbit has an exact rational solution of the
mixed edge equations and duplicate-pair packing relaxation. Its edge
weights are fractional; it is not a graph completion.

The source and certificate therefore give both negative and positive
controls. They do not prove `a>=1`, exclude `Z=J-I-R`, or exclude the
18-vertex core. They impose no automorphism on a hypothetical graph.

The forced 81-column incidence used here is established in
[two_rook_iso_pair_integer.md](two_rook_iso_pair_integer.md). The
local Hall inequalities and the matrix `H` below are proved in
[two_rook_tip_hall.md](two_rook_tip_hall.md) and
[two_rook_tip_psd.md](two_rook_tip_psd.md).

## The tip edge bound and its equality case

The tip matrix satisfies

\[
H=3I-R+J-2Z\succeq0.
\]

Consequently

\[
0\le\mathbf1^{\mathsf T}H\mathbf1=72-4e(Z),
\qquad e(Z)\le18.
\]

There is also a proof using only the common-neighbor caps. For each
distinct pair of tips,

\[
(Z^2)_{ij}+Z_{ij}\le2.
\]

Summing over ordered distinct pairs gives

\[
\sum_i d_i^2
=\sum_{i\ne j}\bigl((Z^2)_{ij}+Z_{ij}\bigr)\le144.
\]

Cauchy gives `(2e(Z))^2 <= 9*144`. If `e(Z)=18`, equality holds
throughout. Every tip has degree four and every displayed pair cap is
an equality. Thus `Z` is an SRG(9,4,1,2), hence an abstract rook graph.

For completeness, this last identification is elementary. Each
vertex neighborhood is two disjoint edges, so every vertex belongs
to exactly two triangles. There are six triangles in total, and each
edge belongs to exactly one. Regard a graph vertex as an edge joining
its two triangles. This gives a simple cubic graph on six vertices.
It has no triangle, since three pairwise-intersecting triangles would
produce a second triangle through one of the original edges. A
triangle-free cubic graph on six vertices is `K_{3,3}`: the three
neighbors of a vertex are independent, and each must meet both of
the remaining two vertices. The original graph is its line graph,
the nine-point rook graph.

An abstract rook graph on the tips need not use the original rook
labeling. In particular, `Z=J-I-R` is also a rook graph, while the
identity interfaces to the first two grids reverse rook adjacency.
The earlier theorem excluding three grids with two isomorphic arms
does not apply to this configuration.

## An aligned tip triangle forces a local partition

Suppose `T` is one of the six lines of the original rook grid and
`Z[T]` is a triangle. Put `x=1_T`. Then

\[
x^{\mathsf T}Hx=3|T|+|T|^2-2e_R(T)-4e_Z(T)=0.
\]

Positive semidefiniteness gives `Hx=0`. For `u` outside `T`, there is
exactly one original rook neighbor of `u` in `T`, so

\[
0=(Hx)_u=2-2d_Z(u,T).
\]

Every outside tip therefore has exactly one neighbor in the triangle.
There are six such edges in total. Each tip in `T` already has two
original-rook-near tip neighbors. The Hall inequality
`d_near <= d_far` forces at least two far tip neighbors outside `T`.
All six available edges are used this way. Each tip in `T` has degree
four, and both of its outside neighbors are original-rook-far.

Two aligned tip triangles cannot lie on intersecting original rook
lines. Their common tip would have four near tip neighbors, whereas
the preceding argument forces its total degree to be four and Hall
requires at least as many far neighbors.

The kernel-extension equation supplies a second useful description.
For the matrix

\[
K=\tfrac34I+\tfrac14R-\tfrac7{36}J,
\]

one has `(Kx)_p=2/3` on `T` and `-1/3` outside it. A duplicate vertex
with original signature `(p,q)` consequently has zero neighbors in
`Z_T` if one of `p,q` lies in `T`, and exactly one if both lie outside.
Both cannot lie in `T`, because `p,q` are rook-nonadjacent.

These are local restrictions. They do not exclude aligned parallel
tip triangles or imply that all tip edges join original-rook-far
points.

## A signed compression of the duplicate pairs

Let `C` be the induced adjacency matrix on all 81 vertices outside
the first two grids. Each has degree 12 in `C`. The core incidence
matrix `X` has rank 17, and the mixed equations give the spectrum

\[
\operatorname{spec}(C)=
12^1,\ (-3)^4,\ (-1)^4,\ 0^4,\ 2^4,\ 3^{36},\ (-4)^{28}.
\]

Here the first five spaces come from the constant vector and the
nonzero lifts of the core eigenspaces. On the 64-dimensional space
`ker X`, the SRG equation reduces to `C^2+C=12I`, so the remaining
eigenvalues are 3 and -4. Their multiplicities follow from dimension
and trace. In particular, `C` has 138 triangles.

There are 36 duplicate pairs, each consisting of the two exterior
vertices with the same original signature `(p,q)`. Write the members
of pair `i` as `a_i,b_i`, with either ordering. Define

\[
D_{ij}=C_{a_i a_j}-C_{a_i b_j}-C_{b_i a_j}+C_{b_i b_j}.
\]

The normalized differences `(e_{a_i}-e_{b_i})/sqrt(2)` are orthonormal
and lie in `ker X`. Their compression of `C` is `D/2`. If `P_-4` is
the rank-28 negative projector on `ker X`, its compression is

\[
\frac17\left(3I-\frac12D\right).
\]

It follows that

\[
\boxed{6I-D\succeq0,\qquad\operatorname{rank}(6I-D)\le28.}
\]

Thus the integer matrix `D` has eigenvalue 6 with multiplicity at
least eight, and every eigenvalue lies in `[-8,6]`. Its diagonal is
zero. Edges between two duplicate pairs form a partial matching,
so its off-diagonal entries belong to `{0,+1,-1,+2,-2}`. Reversing
the labels of a duplicate pair conjugates `D` by a diagonal sign
matrix. The result is independent of those arbitrary labels.

This rank constraint is necessary, not an exclusion. The finite
certificate below does not attempt a classification of such signed
matrices.

## The complementary-rook incidence design

Now assume `Z=F=J-I-R`. Then

\[
H=5I+R-J,
\]

whose kernel contains the constant vector. The kernel-extension
equation forces every remaining vertex to have exactly one tip
neighbor. The 27-vertex core is therefore

\[
B=\begin{pmatrix}R&I&I\\I&R&I\\I&I&F\end{pmatrix},
\]

and its outside incidence matrix has Gram matrix

\[
XX^{\mathsf T}=12I+2J-B^2-B
=\begin{pmatrix}
8I&2F&J-I\\2F&8I&J-I\\J-I&J-I&8I
\end{pmatrix}.
\]

Every one of the 72 outside vertices has a distinct signature
`(p,q,t)`. The exact candidate domain is

\[
p\ne q,\quad R_{pq}=0,\quad t\notin\{p,q\}.
\]

There are `36*7=252` candidates. Every candidate also satisfies the
visible mixed bound `(B+I)h <= 2`.

Each ordered far pair `(p,q)` must occur twice; each ordered distinct
pair `(p,t)` and `(q,t)` must occur once. Equivalently, for each tip
`t`, the eight signatures define a permutation `f_t` of the other
eight labels, extended by `f_t(t)=t`, such that `p,f_t(p)` are
rook-nonadjacent for `p!=t`.

There is an explicit exact incidence design. Set

\[
p_0=(0,5,7,8,6,1,4,2,3)
\]

and take all 72 signatures

\[
(p,\ t+p_0(p-t),\ t),\qquad p\ne t,
\]

with arithmetic in `F_3^2`. The four allowed displacement vectors
of `p_0` each occur twice. This verifies the far-pair margins, while
each `f_t` is a permutation, verifying the other margins. The audit
also checks the complete integer Gram identity directly. This design
is an incidence control; one of the Farkas certificates below proves
that it has no exterior edge completion.

### The parameter `a` and the complete `a=0` census

Classify a signature by the two indicators `R[p,t],R[q,t]`, and let
`n_ij` be the four class sizes. Since every ordered near pair occurs
once in each corresponding margin,

\[
n_{11}+n_{10}=n_{11}+n_{01}=36.
\]

The far margins give `n_00=n_11`. Thus, writing `a=n_11`,

\[
(n_{11},n_{10},n_{01},n_{00})=(a,36-a,36-a,a).
\]

When `a=0`, each `f_t` interchanges the four near and four far points
relative to `t`. The allowed far adjacencies between those two
four-element sets form an eight-cycle. There are exactly two
perfect matchings in each direction. Hence the nine tip permutations
are specified by 18 Boolean choices.

The 36 far-pair margin equations are linear in those choices. Exact
rational row reduction has rank 12 and leaves six free Boolean
coordinates. The audit checks all 64 assignments to these free
coordinates, reconstructs the pivot coordinates, and retains exactly
16 binary solutions. It checks every retained design against the full
27-core Gram matrix, then computes their orbits under the 144
simultaneous rook relabelings and optional exchange of the first two
grids. The orbit sizes are 12, 2, and 2. This is a complete reduction
of `a=0`, not a sample of designs.

## Exact edge obstructions and the surviving relaxation

For a fixed design, an exterior edge `v-w` is retained only if the
signatures overlap in at most one core vertex and both endpoints
have positive mixed quota at every core neighbor of the other.
There are 1,764 possible edges in each of the three representatives.
Every completion must satisfy

\[
XC=2J-(B+I)X,\qquad 0\le C_{vw}\le1.
\]

These equations also impose exterior degree 11 by summing over any
one of the three core grids. The two vertices in each duplicate
`(p,q)` pair already have two common neighbors in the core, so every
outside vertex meets at most one of them. The audit includes these
packing inequalities.

To reduce this **linear relaxation**, average any putative edge
solution over automorphisms of the fixed incidence data. This
preserves all its equations, inequalities, and bounds. No completed
graph is assumed to possess those automorphisms. The resulting
system has one edge weight per edge orbit. Nonnegative slack
variables turn duplicate-pair packing into equations.

| Incidence orbit size | Incidence automorphisms | Edge orbits | Exact outcome |
| --- | --- | --- | --- |
| 12 | 12 | 164 | Integer Farkas ray, right side -12 |
| 2 | 72 | 32 | Integer Farkas ray, right side -3 |
| 2 | 72 | 33 | Exact rational feasible point |

For each excluded case, the saved integer vector `y` satisfies
`y^T M >= 0` and `y^T b < 0` for the rebuilt equation system
`Mw=b`, `w>=0`. The first ray has 91 nonzero entries and the second
has 19. Both work without upper bounds on the edge variables. Their
scope therefore includes every binary edge completion of their
fixed incidence designs.

In all 14 excluded designs, every tip permutation has cycle type
`(1,2,2,2,2)`. In the surviving two designs, every tip permutation
has cycle type `(1,8)`. For the saved representative, the permutation
at tip 0 is

\[
(0,5,7,8,2,6,4,3,1).
\]

The saved rational point for its quotient has 21 fractional edge
weights among 33 edge orbits, with denominators dividing 48. Replay
checks every equation and every bound exactly, including all packing
slacks. It proves feasibility of this real relaxation only. No
outside common-neighbor equations or binary edge completion are
certified for that point.

## Exterior spectrum in the complementary-rook case

The 27-core spectrum follows by restricting to the three rook
eigenspaces. On constant vectors it is `6,3,3`; each of the four
rook-1 directions gives `0,+sqrt(6),-sqrt(6)`; each of the four
rook-minus-2 directions gives `-3,+sqrt(3),-sqrt(3)`. The incidence
Gram matrix has rank 25.

For the remaining 72-vertex exterior graph `C_D`, the mixed equation
therefore forces

\[
\begin{aligned}
\operatorname{spec}(C_D)= {}&11^1,\ (-1)^4,\ 2^4,\
&(-1+\sqrt6)^4,\ (-1-\sqrt6)^4,\
&(-1+\sqrt3)^4,\ (-1-\sqrt3)^4,\
&3^{27},\ (-4)^{20}.
\end{aligned}
\]

The trace cubes give exactly 96 triangles inside `D`. Each of the
27 core vertices has eight neighbors in `D`, paired into four edges
by the unique-common-neighbor condition. These give 108 triangles
with one core vertex. Thus each vertex of `D` lies in three such
mixed triangles and four triangles internal to `D`.

The edges of `C_D` that share a core neighbor form three disjoint
perfect matchings, one for each core grid. The remaining edges form
an eight-regular graph partitioned into its 96 triangles. These
identities are compatible with the required global spectrum and do
not by themselves yield a contradiction.

## Files and replay

- Source: `experiments/workspace/two_rook_pair_structural.py`.
- Certificate: `experiments/logs/grids-and-triangles/two-rook-pair-structural-certificate.json`.
- Generation and replay logs use the same stem.

Replay requires only the Python standard library:

```sh
python experiments/workspace/two_rook_pair_structural.py \
  --certificate experiments/logs/grids-and-triangles/two-rook-pair-structural-certificate.json
```

Generation adds `--write` and uses the repository environment's
SciPy/HiGHS Farkas proposal helper. A numerical solver result is
never accepted as an exclusion without the exact integer checks.
The certificate contains the complete 72-column designs, both
integer duals, and the rational positive control. The source
rebuilds the candidate domain, the complete 16-design census, all
orbit reductions, and all quotient matrices during replay.
