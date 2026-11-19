# A cubic trace identity for all-red grids

The cubic trace gives a shorter exclusion of eight all-red grids. Applied
to the twelve exact spectra in
[`eight_red_exclusion.md`](eight_red_exclusion.md), it excludes every one
directly. The covering argument there remains an independent verification
route for the same bound of seven all-red grids.

The identity also supplies an additional condition for seven all-red
grids. It does not by itself exclude that case or settle existence of the
99-vertex graph.

## Setup

Suppose there are b all-red grids, where b is seven or eight. They are
disjoint, and all interfaces between them are rook isomorphisms. Write
R for their union and U for the remaining 99-9b vertices. Let B and C be
the adjacency matrices on R and U, and let Q describe the incidences from
R to U.

Let W be the direct sum of the b rook eigenvalue-one spaces, let H=B|W,
and set T=Q|W and Z=im(T). As proved in the eight-grid note, Z is invariant
under C, W direct-sum Z is invariant under the full adjacency matrix, and

    TT* = 12I - C_Z^2 - C_Z,    C_Z = C|Z.

Put r=dim(Z) and s_j=trace(C_Z^j). The elementary trace identities are

    trace(H)=4b,    trace(H^2)=4b^2,
    12r-s_1-s_2=4b(11-b),
    7p=20b-3r+s_1,    0<=p<=4b-r.

Here p is the multiplicity of three on ker(T). The square trace follows
because every off-diagonal matching block acts orthogonally on a
four-dimensional rook space.

Every U vertex lies in two or three U triangles: every base projection
selects two, and its U degree is 14-b, at most seven. Let Y be the set
of vertices lying in exactly two U triangles and put y=|Y|.

## The character of a three-base matching loop

Let K be the nine-vertex rook adjacency matrix. Its eigenvalue-one
projector is

    E_1 = (K+2I)/3 - 2J/9.

Take the product P of the three matching maps around three distinct
all-red bases. This is a rook automorphism. It never sends a point to
a rook neighbor. To see this, normalize the direct matching between the
first and third bases to the identity. A pair at adjacent rook positions
already has two common neighbors inside those two bases. A path through
the second base would be a third common neighbor, which is impossible.

Thus trace(PK)=0. Also trace(PJ)=9. If fix(P) is the number of fixed
points of P, then

    trace(P|W_rook) = trace(P E_1) = (2/3) fix(P) - 2.       (1)

This uses only the projector formula and the common-neighbor bound.
It does not need a classification of the 72 rook automorphisms.

Let t_R count triangles with vertices in three different red bases.
The fixed points of the matching product for a given unordered triple
of bases correspond exactly to those triangles. Summing (1) over ordered
triples therefore gives 4t_R-2b(b-1)(b-2).

The terms in trace(H^3) using one base contribute 4b. Terms using exactly
two bases contribute 12b(b-1). Consequently

    trace(H^3)
      = 4b + 12b(b-1) - 2b(b-1)(b-2) + 4t_R.              (2)

## Counting the red cross-triangles

There are 9*binomial(b,2) edges between different red bases. Each lies
in a unique triangle. A matched cross-base edge has no common neighbor
in either endpoint's base, because the interface is a matching. Its
triangle therefore either uses a third red base or has its third vertex
in U.

For q in U, let t(q) be its number of U triangles. Its 14-b U neighbors
contain 2t(q) vertices paired by those triangles. Each remaining U
neighbor must be paired with a red-base neighbor in the seven-edge
matching induced on the full neighborhood of q. The number of edges
between red-base neighbors of q is therefore

    [b - (14-b-2t(q))]/2 = b-7+t(q).

Summing over U gives 108-y when b is seven or eight. Hence

    t_R = 27+y/3  if b=7,
    t_R = 48+y/3  if b=8.                                 (3)

In particular y is divisible by three, also obtained directly by
counting U triangle incidences.

## Computing the same cubic trace from the invariant block

On W direct-sum Z the full matrix is

    [ H   T* ]
    [ T   C_Z].

Its quadratic identity gives

    H^2+H+T*T=12I,    TH=-(C_Z+I)T.

Multiply the first identity by H and take traces. Use the second identity
and TT*=12I-C_Z^2-C_Z. This yields

    trace(H^3)
      = 4b(12-b) + 12r + 11s_1 - 2s_2 - s_3
      = 4b(23-2b) + 12s_1 - s_2 - s_3.                    (4)

Equating (2), (3), and (4) gives the new necessary condition

    s_3+s_2-12s_1
      = 2(b-8)(b-3)(b-11) - 4y/3.                         (5)

For eight bases this is -4y/3. For seven bases it is 32-4y/3.

### Divisibility by nine

For either seven or eight all-red bases, y is divisible by nine. The
rook character in (1) is an integer: each rook automorphism preserves the
full lattice W intersected with the integer coordinate lattice in the
rational eigenvalue-one space. Therefore every three-base matching product
has a fixed-point count divisible by three. Summing over unordered triples
of bases shows that t_R is divisible by three. Equation (3) then gives
that y/3 is divisible by three.

There is an independent spectral check. The characteristic polynomial of
the rational invariant restriction C_Z has integer coefficients: its
eigenvalues are algebraic integers, and its coefficients are rational.
Newton's identities give s_3 congruent to s_1 modulo three. The energy
identity therefore makes s_3+s_2-12s_1 congruent to -4b(11-b) modulo three.
Substitution in (5) again gives y/3 congruent to zero modulo three.

In particular, the y=24 spectra in the eight-grid census already violate
this divisibility condition. The full cubic audit also excludes them
directly, without using this corollary as an input.

## Exact exclusion of the twelve eight-grid spectra

The existing exact cycle census leaves twelve spectra on five partitions.
Their cubic traces fail (5):

| Residual cycles | y | Possible values of s_3+s_2-12s_1 | Required value |
|---|---:|---|---:|
| 3C6 | 18 | 36 | -24 |
| 4C6 | 24 | 36, 24, -96 | -32 |
| 2C6+C12 | 24 | 36, 30, 24 | -32 |
| 2C12 | 24 | 24, 18 | -32 |
| 3C6+C9 | 27 | 36, 27, 18 | -36 |

Thus the cycle census and cubic identity alone exclude eight all-red
grids. This route does not use the three-cover enumeration or the final
compression estimate from the earlier proof.

## Integer replay and independent controls

[`red_grid_cubic_trace.py`](../../experiments/workspace/red_grid_cubic_trace.py)
reads the saved exact cycle spectra. For each irreducible factor it builds
an integer companion matrix and cubes it using integer multiplication.
The script recomputes r,s_1,s_2,s_3, verifies the earlier trace equations,
and checks failure of (5) for all twelve records.

It also enumerates all 72 rook automorphisms as a control of (1). Exactly
eleven avoid sending a point to a rook neighbor: one fixes nine points,
six fix three, and four fix none. For each of these eleven maps it builds
the full 27-by-27 matrix of three rook bases and computes its cubic trace
against the integer matrix 9E_1. These direct matrix powers agree with
(2), including all multiplicity factors.

```sh
.venv/bin/python experiments/workspace/red_grid_cubic_trace.py
```

The exact records are in
[`red-grid-cubic-trace.json`](../../experiments/logs/grids-and-triangles/red-grid-cubic-trace.json).
No floating-point arithmetic or SAT result enters this audit.
