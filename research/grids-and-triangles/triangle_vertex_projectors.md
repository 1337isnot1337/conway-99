# Two vertex-derived triangle projectors

Let B be the 99 by 231 point-triangle incidence matrix. Then
BB^T=7I+A and B^T B=3I+L, where L is the triangle-intersection adjacency
matrix. The eigenvalues of L are 18, 7, 0 and -3, with multiplicities
1, 54, 44 and 132.

Write Qminus=27I-9A+J=63E_{-4} and
Qplus=44I+11A-2J=77E_3 for the vertex projector matrices.
The two triangle matrices

    Kminus = (1/9) B^T Qminus B = 21 E_{L=0},
    Kplus  = B^T Qplus B       = 770 E_{L=7}

are positive semidefinite. The factors follow because BB^T acts by 3
on E_{-4} and by 10 on E_3. Their entries are:

| Triangle pair | Kminus | Kplus |
| --- | ---: | ---: |
| The same triangle | 4 | 180 |
| Distinct triangles meeting once | 0 | 70 |
| Disjoint triangles with e cross edges | 1-e | 11e-18 |

These formulas also follow directly from the incidence factors. For
example, the negative numerator on one triangle is 27*3-9*6+9=36.
For two triangles meeting once, its value is 27-9*4+9=0.
The cross-edge count for disjoint triangles is between zero and three.

Together with the previously tested matrix Q=210E_{L=-3}, the projector
partition is

    Q/210 + Kminus/21 + Kplus/770 + J/231 = I.

For triangle classes at a fixed labelled root, let p be their first
moments, N their scalar count Gram matrix, and M_Q, Mminus, Mplus the
three class kernels summed over root embeddings. The exact identity is

    11 M_Q + 110 Mminus + 3 Mplus + 10 N = 2310 diag(p).

Thus the old complementary condition is

    210 diag(p)-M_Q = 10 Mminus + (3/11) Mplus + (10/11) N.

It tests a positive combination of the two new projector blocks and the
scalar block. It does not separate the two projector components.

## Relation to the existing vertex flags

For a class C and a vertex x, define f_C(x) as the number of triangles
in C containing x. Pushing the class indicator through B gives exactly
this vertex function. The two new blocks are vertex-projector Gram
matrices of the functions f_C.

This factorization is not a redundancy proof from the existing eight-root
projector blocks. Those blocks use root vectors and indicators of the full
neighborhood classes of one fixed root embedding. In f_C(x) f_D(y), the
other two vertices of the triangle through x and the other two vertices
of the triangle through y can be different. Conditioning on each partner
pair separately controls diagonal partner terms but does not supply the
cross-partner terms as a positive sum. All entries having order at most
ten does not establish a positive decomposition.

No strict independence theorem for the full existing relaxation is claimed.
The specified new matrices are justified directly, and no common-block
congruence or positive decomposition into the old tests has been found.
The existing vertex-projector source and its domain note make their smaller
function domain explicit.

## Complete four-root preparation

The separate source `triangle_vertex_projector_moments.py` uses the unchanged
full four-root class domains: all nine root types and all 574 classes,
including triangles meeting the root. It enumerates actual unlabelled
triangle pairs inside each induced graph of order four through ten and
every compatible labelled root map.

For an unordered distinct pair, an off-diagonal class entry is added once;
if both triangles have the same class, the diagonal entry is added twice.
A coincident pair is added once. No free-label automorphism division occurs
in this literal induced-subset enumeration.

The source reconstructs the entire old Q tensor exactly. It also rebuilds
the scalar tensors and compares the two previously frozen scalar blocks.
Every coefficient of the projector partition above is checked against
the frozen first-moment forms. Direct small-host controls enumerate ordered
triangle pairs independently and compare their matrices with induced-count
contraction. The literal incidence factors are checked on those hosts
without assuming that a host is a 99-vertex graph.

For the two four-root types containing a triangle T, the source also
prepares the per-embedding conditioned kernels

    4 Kminus(U,V) - Kminus(T,U) Kminus(T,V),
    180 Kplus(U,V) - Kplus(T,U) Kplus(T,V).

Their root cross values are constant on each complete triangle class.
The first is the positive scalar multiple of a rank-43 projector;
the second has rank 53. All class rows remain in the tensors, including
the coefficientwise zero row belonging to T.

The intended query contains 18 unconditioned blocks and four conditioned
blocks. Preparation uses no count point and is bounded to 120 seconds.
A separate source and model review is required before any point query.
The original Q sources, tensors and results are unchanged.
