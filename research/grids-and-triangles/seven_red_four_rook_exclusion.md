# Seven all-red grids cannot leave four compatible rook grids

Suppose seven all-red grids have complement U consisting of four induced
rook grids, every U vertex lies in exactly two U triangles, and every
interface from an all-red base to a U grid is a rook isomorphism. These
conditions are contradictory.

This note proves the final conditional exclusion. The separate
four-sheeted-cover reduction is responsible for establishing these
hypotheses in the y=36 case; no classification of covers is used here.

## The rook eigenvalue-minus-two lift

Order the full adjacency matrix as

    A = [ B   Q^T ]
        [ Q    C  ],

where B is on the 63 vertices in the seven all-red bases, and C is on U.
Let W be the direct sum of the seven rook adjacency eigenspaces of
eigenvalue minus two. It has dimension 28. Since the interfaces between
all-red bases are rook isomorphisms, W is invariant under B. Write

    H = B|W,    T = Q|W,    Z = im(T),    C_Z = C|Z.

The block identity A^2+A=12I+2J implies

    CT = -T(H+I),
    Q^T Q = 12I+2J-B^2-B.

Thus Z is invariant under C and Q^T Z lies in W. The space W direct-sum Z
is invariant under the full adjacency matrix, with block matrix

    [ H   T* ]
    [ T   C_Z].

It is orthogonal to the global constants. In particular C_Z has all its
eigenvalues between minus four and three, and

    TT* = 12I-C_Z^2-C_Z.

Each base projection has fibers of size four. Therefore
trace(T*T)=7*4*4=112. If

    r=dim(Z),    s_j=trace(C_Z^j),

then

    12r-s_1-s_2=112.                                      (1)

The diagonal rook blocks give trace(H)=-56 and trace(H^2)=280. Let p be
the multiplicity of three on ker(T), whose other eigenvalue is minus four.
The intertwining equation makes the trace of H on the complementary
r-dimensional subspace equal to -r-s_1. Hence

    7p=56-3r+s_1.                                         (2)

Here p and r are integers.

## The cubic trace on the red bases

There are 9*binomial(7,2)=189 matching edges between different red bases.
Every U vertex has seven U neighbors and seven red-base neighbors. Its two
U triangles use four of those U neighbors. The other three U neighbors
must be paired with three red neighbors in the seven-edge neighborhood
matching. The remaining four red neighbors form two pairs.

Consequently 36*2=72 cross-base matching edges have their unique common
neighbor in U. The others lie in triangles across three red bases. The
number of these triangles is

    t_R=(189-72)/3=39.

Let K be the nine-point rook adjacency matrix. Its eigenvalue-minus-two
projector is

    E_{-2}=(I-K)/3+J/9.

For a matching product P around three red bases, no point is sent to a
rook neighbor: such a three-base path would add a third common neighbor
to a cross-base pair already having two inside its endpoint grids. Thus
trace(PK)=0, and

    trace(P|W_rook)=fix(P)/3+1.

The terms in trace(H^3) using one base, exactly two bases, and three
distinct bases give, respectively,

    -32*7,    -24*7*6,    2t_R+7*6*5.

Therefore

    trace(H^3)=-224-1008+78+210=-944.

The invariant block equations independently give

    trace(H^3)=-840+12s_1-s_2-s_3.

This follows by tracing H(H^2+H+T*T)=12H and substituting
TH=-(C_Z+I)T and (1). Consequently

    s_3+s_2-12s_1=104.                                    (3)

All constants can also be obtained from the general holonomy trace
calculation in [`red_grid_cubic_trace.md`](red_grid_cubic_trace.md).

## Compression to the four U rook spaces

Let V be the direct sum of the eigenvalue-minus-two spaces of the four
rook grids in U. It has dimension sixteen. The assumed isomorphic
base-to-U interfaces imply Z is a subspace of V.

The compression of C to V has trace -32: its four diagonal rook blocks
each contribute -8, and its off-diagonal matching blocks contribute
nothing to the trace. The complementary compression on V intersect Z^perp
has dimension 16-r and eigenvalues at least minus four. This Rayleigh
bound is inherited from the full graph, since every vector in V is
orthogonal to constants. It follows that

    -32-s_1 >= -4(16-r),
    s_1 <= 32-4r.

Together with (2), this gives

    7(p+r)=56+4r+s_1 <= 88,
    p+r <= 12.                                            (4)

No invariance of the complementary compression is assumed.

## A nonnegative polynomial has negative trace

For every real mu at least minus four,

    (mu+4)(mu+1)^2 >= 0.

This applies to every eigenvalue of C_Z, so

    trace((C_Z+4I)(C_Z+I)^2) >= 0.

Expand the polynomial and use (1), (2), and (3):

    trace((C_Z+4I)(C_Z+I)^2)
      = s_3+6s_2+9s_1+4r
      = 64r+16s_1-456
      = 112(p+r)-1352.

By (4), this is at most 112*12-1352=-8. The contradiction excludes the
stated four-rook remainder.

## Exact replay

[`seven_red_four_rook_exclusion.py`](../../experiments/workspace/seven_red_four_rook_exclusion.py)
checks every algebraic substitution symbolically over the rationals and
the final bound with integers. It also verifies the rook-minus-two
character formula on all eleven permissible holonomies. The polynomial
control uses the exact factorization t(t-3)^2 after t=mu+4, so its sign
on the required half-line does not depend on numerical sampling.

```sh
.venv/bin/python experiments/workspace/seven_red_four_rook_exclusion.py
```

The saved audit is
[`seven-red-four-rook-exclusion.json`](../../experiments/logs/grids-and-triangles/seven-red-four-rook-exclusion.json).
