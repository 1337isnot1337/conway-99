# At most seven all-red grids

A hypothetical strongly regular graph with parameters `(99,14,1,2)` has
at most seven all-red grids. Here a triangle is red if it belongs to six
induced three-by-three rook grids, and a grid is all-red if all six of its
lines are red.

The [nine-grid argument](red_grid_limit.md) already excludes nine all-red
grids. This note excludes eight. The proof uses two small exact finite
calculations: rational spectra for thirty cycle partitions, and covering
projections for 1,296 normalized three-sheeted covers of `K3,3`. Both
calculations are fully specified below. There is no SAT assumption or
floating-point sign decision in this proof.

This is an unconditional restriction on such a graph, not a proof of its
nonexistence. The total-grid bound remains 120.

## The twenty-seven remaining vertices

Assume eight all-red grids `R_1,...,R_8`. The preliminary facts proved in
[the grid note](red_grid_limit.md) are:

- The eight grids are disjoint.
- Every vertex outside a rook grid has exactly one neighbor in it.
- Every matching between two all-red grids is a rook isomorphism.
- The six grids through a red triangle partition its exterior neighbors.
- A distinct grid intersects an all-red grid in zero or three vertices,
  never in exactly one vertex.

Let `U` be the remaining 27 vertices and `C` its adjacency matrix. Each
vertex of `U` has eight neighbors in the red grids and six inside `U`.
Each vertex of a red grid has three neighbors in `U`. Therefore the
projection `pi_i:U -> R_i` to the unique neighbor has fibers of size three.

The inverse image of each red line consists of nine vertices and splits
into three triangles of `U`, each mapped bijectively onto that line. This
follows from the unique-grid partition through the red line. For a grid
through that line which meets `U`, each intersection with another red
base is zero or one parallel line; its intersection with `U` is one or
two remaining parallel lines. The grids not meeting `U` contribute nothing
to this inverse image.

Every projection consequently selects eighteen triangles of `U`. At each
point it selects two distinct triangles, one over its row and one over
its column. Degree six and `lambda=1` imply that every point belongs to
exactly two or three triangles of `U` in total.

Write `S` for the vertices belonging to exactly two triangles, and put
`n=|S|`. The edges belonging to no triangle of `U` form disjoint cycles
on `S`: those vertices have two such edges, and the other vertices have
none. Let `F` be their adjacency matrix, extended by zero on `U\S`.
Every cycle has length at least four. The triangle count

    3 * number of U-triangles = 2n + 3(27-n)

also gives `n` divisible by three.

A projection omits one triangle at each vertex of `U\S`. Its omitted
triangles partition that set. Every omitted triangle maps to an independent
triple of the rook grid. To see this, fix `q` with image `p`. For a rook
neighbor `r` of `p`, the selected row or column triangle supplies a unique
`U`-neighbor `v` of `q` with image `r`. The nonadjacent pair consisting of
`q` and the base vertex `r` already has its two common neighbors `p,v`.
No other `U`-neighbor of `q` can map to `r`. Moreover, two vertices in a
`U`-triangle cannot have the same image, since their unique common neighbor
is already in that triangle. The three omitted images are therefore
distinct and pairwise nonadjacent, a rook transversal.

## An invariant subspace and its trace equations

Order the full adjacency matrix as

    A = [ B   Q^T ]
        [ Q    C  ],

where `B` is on the 72 red-grid vertices and `Q` describes their edges to
`U`. Let `W` be the direct sum of the eight rook adjacency eigenspaces of
eigenvalue one. It has dimension 32. The rook-isomorphic interfaces make
`W` invariant under `B`, and

    trace(B restricted to W) = 32.

Define `T=Q|W` and `Z=im(T)`. The space `W` has a rational basis. Hence
`Z` is rational as well. It is orthogonal to the all-one vector on `U`,
because every base point has three preimages under each projection.

The block identity `A^2+A=12I+2J` gives

    C T = -T(B|W + I),
    Q^T Q = 12I + 2J - B^2 - B.

The first equation makes `Z` invariant under `C`. The second shows that
`Q^T Z` lies in `W`. Thus `W direct-sum Z` is invariant under `A`, with
block matrix

    [ B|W   T^* ]
    [  T     C|Z].

This space is orthogonal to the global constants, so its adjacency
spectrum consists only of three and minus four. Its lower-right block
identity is

    T T^* = 12I - (C|Z)^2 - C|Z.

The left side is positive definite on `Z`. In particular, `C|Z` has no
eigenvalue three. Let

    r = dim(Z),   s1 = trace(C|Z),   s2 = trace((C|Z)^2).

Every projection repeats a rook function three times. Using an orthonormal
basis of each of the eight four-dimensional rook spaces therefore gives
`trace(T^*T)=8*4*3=96`. Taking traces above yields

    12r - s1 - s2 = 96.                                      (1)

The space `ker(T)` is invariant under `B|W`; its dimension is `32-r` and
its eigenvalues are three and minus four. On its orthogonal complement,
`B|W` has trace `-r-s1`, by the intertwining equation. If `p` is the
multiplicity of three on `ker(T)`, the total trace 32 gives

    7p = 160 - 3r + s1,    0 <= p <= 32-r.                    (2)

These equations are exact.

## The cycle operator

A rook eigenvalue-one function is a sum of a zero-sum row function and a
zero-sum column function. Its sum on a rook transversal is zero.

Lift such a function from any base to `U`. Its four selected-triangle
neighbors sum to its own value, because the rook eigenvalue is one.
At a point in `U\S`, the two neighbors in the omitted triangle sum to
minus its value. The total is zero there. At a point in `S`, the two
remaining neighbors are its nontriangle-cycle neighbors. Consequently

    C T = D T,    D = I_S + F,

where `I_S` is one on the coordinates of `S` and zero elsewhere. Since
`Z` is invariant under `C`, it is also invariant under `D`, with

    C|Z = D|Z.

The operator `D` is one plus cycle adjacency on each residual cycle and
zero on `U\S`.

Every residual cycle has length divisible by three. Its indicator is a
`D`-eigenvector of eigenvalue three, so it is orthogonal to the invariant
space `Z`, whose spectrum excludes three. Every lifted rook row-difference
and column-difference function therefore sums to zero on that individual
cycle. Its projection has equal populations in the three rows and in the
three columns. Its length must be divisible by three.

The possible cycle lengths are consequently

    6, 9, 12, 15, 18, 21, 24, 27.

## Exact enumeration of the possible restricted spectra

For a cycle of length `ell`, the eigenvalues of `I+F` are
`1+2*cos(2*pi*k/ell)`. Since `Z` is a rational invariant subspace, the
characteristic polynomial of `D|Z` is a product of complete irreducible
rational factors of the characteristic polynomial of `D`. Its factor
multiplicities cannot exceed those of `D`.

Discard the eigenvalue three. Include the zero eigenvalues on `U\S`.
When this set is nonempty, reduce the available zero multiplicity by one:
`Z` is orthogonal to its indicator, because it is orthogonal to the global
constant vector and to every residual-cycle indicator.

There are thirty partitions of at most 27 into the permitted cycle
lengths, including the empty partition. For each, enumerate all remaining
irreducible-factor multiplicities subject to (1), (2), and `r<=26`.
Exactly twelve spectra survive, on five cycle partitions:

| `n` | Residual cycles | Surviving pairs `(r,s1)` |
| ---: | --- | --- |
| 18 | `3C6` | `(8,-3)` |
| 24 | `4C6` | `(8,-3), (9,0), (12,16)` |
| 24 | `2C6+C12` | `(8,-3), (9,0), (10,3)` |
| 24 | `2C12` | `(11,6), (12,9)` |
| 27 | `3C6+C9` | `(8,-3), (9,0), (10,3)` |

All spectra in the first and last rows contain the full three-dimensional
`D`-eigenspace of eigenvalue minus one on the three six-cycles.
In the three middle rows, seven spectra have `s1=3r-27`; the exception is
`(r,s1)=(12,16)`.

[`eight_red_cycle_spectra.py`](../../experiments/workspace/eight_red_cycle_spectra.py)
computes the cycle polynomials by the recurrence
`q_0=2, q_1=x, q_ell=x*q_(ell-1)-q_(ell-2)`, using the cycle polynomial
`q_ell(x-1)-2`. It factors them exactly over the rationals and checks
every bounded multiplicity tuple with integer arithmetic.

The independent
[`eight_red_hamming_spectral_audit.py`](../../experiments/workspace/eight_red_hamming_spectral_audit.py)
builds the eight cycle matrices directly, factors their characteristic
polynomials, generates partitions by combinations with replacement, and
uses Cartesian products for the multiplicity census. It reproduces all
thirty partitions and all twelve surviving spectra. The complete factor
records are in
[`eight-red-cycle-spectra.json`](../../experiments/logs/grids-and-triangles/eight-red-cycle-spectra.json).

## The eighteen- and twenty-seven-vertex cases fail locally

For `n=18` or `n=27`, the entire minus-one eigenspace on the three
six-cycles lies in `Z`. In particular, the alternating vector on any one
of these cycles, zero elsewhere, belongs to `Z` and must satisfy `Cv=-v`.

No distance-two chord of the cycle is allowed: it would place a residual
cycle edge in a triangle, contrary to its definition. The only possible
additional edges among its six vertices join antipodes. These connect
opposite signs of the alternating vector. Thus

    v^T C v <= -2 * v^T v,

whereas `Cv=-v` would give `v^T C v=-v^T v`. This contradiction excludes
both rows of the table with `n` different from 24.

## Three vertices with an extra triangle give a common covering

It remains that `n=24`. The other three vertices must form the unique
omitted triangle for every base. Hence all eight projections select the
same eighteen triangles of `U`.

Make a graph `K` whose vertices are those triangles and whose edges are
the 27 points of `U`, joining the two selected triangles containing each
point. This is a simple cubic graph on eighteen vertices. Every projection
is a three-sheeted covering `K -> K3,3`.

Two projections cannot share a three-edge fiber: the corresponding base
vertices would have those three `U`-vertices as common neighbors.
[The common-triangle covering calculation](eight_red_common_triangles.md)
then leaves only `K=3K3,3`:

- For connected `K`, enumerate the `6^4=1,296` spanning-tree-normalized
  three-sheeted covers. Exactly 1,250 are connected. For each, enumerate
  the 280 partitions of either nine-point side into three triples and
  retain precisely the partitions with disjoint neighborhoods in each
  triple. The certificate identifies an edge belonging to at most four
  possible three-edge fibers across all projections. Eight projections
  would repeat a fiber, a contradiction.
- For components of orders six and twelve, each projection restricts to a
  double covering on the connected twelve-vertex component. Its
  [forced edge-pair lemma](nine_red_cover_audit.md#a-common-edge-pair-gives-the-stronger-auxiliary-bound-two)
  gives the same pair of edges in a common fiber for every projection.
  The corresponding `U`-vertices would have eight common base neighbors.
- The remaining component sizes are six, six, and six. Every component is
  `K3,3`, and its line graph is an induced rook grid. An extra edge inside
  one component would join a rook nonedge already having two common
  neighbors, contradicting `lambda=1`.

The connected-cover certificate is regenerated by
[`grid_eight_red_covers.py`](../../experiments/workspace/grid_eight_red_covers.py)
using only the Python standard library. Its independent subset check and
its per-edge fiber bound agree on every connected cover.

Thus `U` splits into three rook grids. Their interfaces with every red
base are rook isomorphisms: the common selected system consists precisely
of their row and column triangles, and each component covering has one
sheet. This assertion uses the common-system conclusion. It does not
assert that an arbitrary rook grid in `U` has an isomorphic interface.

## The last eight spectra fail a trace bound

Let `W_U` be the direct sum of the three rook eigenvalue-one spaces in
`U`. It has dimension twelve. All base-to-`U` interfaces are isomorphisms,
so `Z=im(T)` lies in `W_U`.

The compression of `C` to `W_U` has trace twelve. Each diagonal rook block
contributes four; off-diagonal interfaces contribute nothing to the trace.
The invariant subspace `Z` contributes trace `s1`. The complementary
compression on `W_U intersect Z^perp` has dimension `12-r` and eigenvalues
between minus four and three. These are Rayleigh bounds inherited from
the full graph, since every vector in `W_U` is orthogonal to constants.
Therefore

    -4(12-r) <= 12-s1 <= 3(12-r),

or equivalently

    3r-24 <= s1 <= 60-4r.                                   (3)

Seven of the remaining spectra have `s1=3r-27`, violating the lower bound
by three. The exception `(r,s1)=(12,16)` violates the upper bound twelve.
Every row of the exact census is now excluded.

Eight all-red grids are impossible. Combined with the nine-grid exclusion,
this proves that there are at most seven.

## Replay

From the repository root:

```sh
make verify-red-grid-bound
```

This regenerates the cycle census, checks it by direct matrix
characteristic polynomials, replays the double-cover lemma, and exhausts
the normalized three-covers. The elementary arguments connecting these
finite checks to the graph are given above; the programs do not constitute
a formal proof in a proof assistant.
