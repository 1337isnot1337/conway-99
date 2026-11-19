# Triangle-incidence projector tests through order ten

The current induced-count vector passes both complete four-root tests. All nine blocks for triangles disjoint from the root are positive semidefinite. All nine larger blocks, containing every triangle class, are also positive semidefinite. The larger blocks satisfy every checked point-incidence kernel identity. These results do not construct a graph or exclude the current count vector.

## The necessary projector

Let B be the point-triangle incidence matrix of a hypothetical SRG(99,14,1,2). Each point lies in seven triangles, each edge lies in one, and the graph has 231 triangles. Thus

```text
B B^T = 7I + A,
(7I + A)^(-1) = (6I-A)/30 + J/315.
```

The adjacency identity `A^2+A=12I+2J` verifies the inverse directly. The matrix

```text
Q = 210(I - B^T(7I+A)^(-1)B)
```

is 210 times the orthogonal projector onto the kernel of B. Its rank is 132. Its entries depend only on two triangles and their cross edges:

| Relation between triangles T and U | Q(T,U) |
|---|---:|
| T=U | 120 |
| One common point | -20 |
| Disjoint, with e cross edges | 7e-6 |

Distinct triangles cannot share an edge. The cross edges between disjoint triangles form a matching, so e is between zero and three. The [algebra and initial class census](triangle_projector_class_scope.md) give a separate derivation.

The projector onto the kernel of B vanishes on the image of B transpose. Conversely, a direct pullback of a vertex matrix through B vanishes on the kernel of B. This explains why the triangle projector is not itself one of the direct vertex-projector pullbacks. No claim is made that it is independent of every earlier flag inequality.

## Complete four-root classes

For each labelled embedding of a four-vertex root H, classify a triangle by its intersection with H and the multiset of H-neighborhood masks of its remaining vertices. Every class passing the literal common-neighbor caps is retained. Multiplicities of zero masks are allowed.

Let D be the matrix of class indicators on triangles. Then D transpose Q D is PSD for each root embedding. Summing these matrices gives a necessary PSD matrix whose entries are linear forms in unlabelled induced counts through order ten.

The first preparation retained only triangles disjoint from H. It has 352 classes in nine blocks, 7,524 lower-triangular entries and 88,084 nonzero tensor coefficients. The full preparation has 574 classes, 21,190 lower-triangular entries and 135,819 coefficients. Its block orders, in catalogue root order 8 through 16, are 107, 93, 72, 49, 79, 58, 41, 34 and 41. The earlier nine tensors are preserved exactly as principal submatrices.

The tensor enumerator uses unlabelled triangle sets and every labelled root isomorphism inside each induced graph F. Its coefficient multiplies N_F directly. There is no further automorphism factor or free-vertex factorial. An unordered pair of distinct triangles contributes twice only when both belong to the same matrix class; off-diagonal matrix entries receive one contribution.

For the extra full-class entries, the root may meet either triangle. If W is their union, the root contains every vertex of F outside W, plus enough vertices of W to make four. This enumerates every decomposition exactly once before root labelling. No extra graph of order ten is needed for an entry involving a triangle that meets the root.

## Preparation controls and exact query

Both preparations are independent of the count point. The disjoint preparation passes six induced-subset controls. The full preparation passes 29 such controls, using an independent ordered-pair sum on each host graph. The literal projector formula also passes a separate control on the 243-vertex Golay graph, with its corresponding projector constants.

The count vector has SHA256 `0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df`. Each tensor is contracted with unbounded integers. PSD is checked from the exact coefficients of det(tI+M). A real symmetric M is PSD exactly when all these coefficients are nonnegative: a negative eigenvalue would give a positive root, which a monic polynomial with nonnegative coefficients cannot have.

All eighteen blocks pass. Independent replays reconstruct every matrix entry and compute the characteristic polynomial with the opposite sign convention before comparison. No numerical eigenvalue or tolerance is used in accepting a block.

For the full classes, Q B transpose=0 also gives class-constant kernel vectors: the constant vector, four root-point incidence vectors, and sixteen incidence vectors for the outside H-neighborhood classes. All 189 matrix-vector checks pass. The full-block nullities are 20, 20, 18, 15, 20, 17, 16, 15 and 15.

## Reproduction and next boundary

The sources are `triangle_incidence_projector_moments.py` and `triangle_incidence_projector_full_classes.py`. The two preparation directories, query records, source reviews and independent replays are listed in the [publication manifest](../../experiments/logs/moments-and-counts/triangle-projector-publication-manifest.json). Their file hashes bind the exact models and count vector.

The independent replay programs require only the saved tensors, count vector and query outputs, plus python-flint. They do not enumerate graph types, import the query helpers or call an optimizer.

A separate stronger condition can Schur-complement a fixed triangle before summing over root embeddings. That requires ordinary second moments of class counts. Passing the matrices above does not establish that stronger condition. Its preparation and query must be recorded separately.
