# A perfect-square condition on every 44 vertices

Write A for the adjacency matrix of a putative strongly regular graph with parameters (99,14,1,2). For every set T of 44 vertices, the determinant of the principal submatrix of D = 27 I - 9 A + J on T is a nonnegative integer square, including zero. This is a necessary condition on the unrestricted problem.

## Proof

The identity A² + A = 12 I + 2 J gives eigenvalues 14, 3, -4 of multiplicities 1, 54, 44. The two rational orthogonal projectors onto the nonconstant eigenspaces are P = D/63 (eigenvalue -4) and Q = (44 I + 11 A - 2 J)/77 (eigenvalue 3).

Let L and M be the lattices formed by all integral vectors in these respective rational subspaces, with their usual dot product. For a primitive intersection lattice with orthogonal projector P in the unimodular lattice Z^99, the projected lattice P Z^99 is precisely the dual lattice L*. Indeed an integer functional on L extends to one on Z^99, since L is a primitive direct summand as an abelian group. The standard dot product represents the extension by an integer vector, and projection represents its restriction. Conversely every such projection has integer dot product with L.

Thus 63 L* lies in L, and 77 M* lies in M. In particular the positive Gram determinant of L has prime divisors among 3 and 7, and that of M among 7 and 11. Orthogonality and the index-determinant formula give

    det(L) det(M) · 99 = [Z^99 : L ⊕ M ⊕ Z·1]^2.

The exponent of 3 in det(L) is even. The square-free part of det(L) therefore equals 1 or 7. The lattice L is even since 63 times the squared norm of any member x is xᵀ D x, and D has even diagonal. Its determinant is odd. For an even lattice of rank 2s and odd determinant, that determinant is (-1)^s modulo 4. To see this, split the Gram matrix over Z/4 into nonsingular two-dimensional blocks by choosing an odd off-diagonal entry. Such a block has even diagonal and determinant -1 modulo 4. Its inverse exists modulo 4, so eliminate its two cross rows by a triangular basis change. Evenness is preserved on the remaining summand. Iteration proves the formula. Here s = 22. This excludes the square-free part 7, since an odd square is 1 modulo 4. Hence det(L) is a square.

On 44 coordinates T, D[T] is 63 times the Gram matrix of the 44 projected coordinate vectors in L tensor Q. In any integral basis of L, its determinant is 63^44 det(L) times a squared rational determinant. It is both a rational square and an integer, hence an integer square.

## Additional restriction modulo 7

The 3-primary discriminant group of L is cyclic of order 9. Over the 3-adic integers Q is an integral projector, so its kernel K is an orthogonal unimodular summand. The all-ones vector w is primitive in K and has norm 99. Its orthogonal complement in K is the localization of L. In a unimodular lattice the discriminant groups of a primitive sublattice and its orthogonal complement are isomorphic as groups. In this rank-one case an explicit argument is available: the pairing with w maps K onto Z_3; its kernel is L_3, and the image of Z_3 w is 99 Z_3. Thus K/(L_3 + Z_3 w) is cyclic of order 9. Projecting K onto the rational span of L_3 identifies this quotient with L_3*/L_3.

Write det(L) = 9·7^r. The 7-primary group has exponent at most 7 and rank r. Over Z_7, split the ambient coordinate lattice as the direct sum of L_7 and a module complement (without requiring orthogonality). Projection onto the rational span of L_7 maps the coordinate lattice onto L_7*. Reduction of the image of D = 63 P modulo 7 therefore has dimension r: its rank is the dimension of (7 L_7*)/(7 L_7), since L_7 is primitive and the factor 9 is a unit. In particular r is the rank of D modulo 7 and is even by the determinant result.

Neither r = 0 nor r = 44 is possible. For r = 0, L is even with determinant 9 and cyclic discriminant group. For r = 44, every elementary divisor of the Gram matrix of L is divisible by 7. Divide the Gram form by 7 to obtain an even lattice of determinant 9, again with cyclic discriminant group (the scaling is a unit at 3). In either case take a generator y of the dual lattice modulo the lattice, of order 9. The evenness of 9y makes 81(y,y) even, and by duality 9(y,y) is integral. It follows that 9(y,y) is even, so adjoining 3y gives an even index-three overlattice. Its determinant is one. An even positive definite unimodular lattice has rank divisible by 8, whereas the rank here is 44. This proves that the rank of D modulo 7 is even and at most 42. No lower bound stronger than excluding zero is needed for this test.

## Application to an induced square

Its four corners have 44 distinct outside neighbors: four triangle tips, each adjacent to both ends of one side, and ten private neighbors at each of the four corners. Every completed graph must give a square determinant on precisely these 44 neighbors. There are 51 vertices outside the resulting 48-vertex ball. Failure on a sampled ball excludes only that local configuration.

## Prior work located on November 18

Dilan Djematene's October 2026 preprint "On the 7-rank of a putative strongly regular graph with parameters (99,14,1,2)" already derives the discriminant 9·7^r and the evenness and upper bound 42 for r. The perfect-square principal-minor test above follows from its determinant theorem. The same archive includes a distinct discriminant proof excluding order three and a computer-assisted exclusion of order two. The archive labels its work as awaiting independent review. Source: https://doi.org/10.5281/zenodo.23305123 . The searchable source is https://github.com/amazing-source/strongly-regular-graphs-research/tree/v1.0/papers .
